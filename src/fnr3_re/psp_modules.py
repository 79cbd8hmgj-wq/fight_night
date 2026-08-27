from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, cast

from .iso import _workspace_path, verify_workspace
from .manifests import load_workspace_manifest
from .psp_toolchain import PspToolchainInfo, load_psp_toolchain

FNR3_REVISION_ID = "ULUS10066-v1.00"
FNR3_ISO_SHA256 = "b11da5afe208d9791eecd9f6a44d0f57946f7d9de165b7d8dd22f5ee740f4ee2"
FNR3_ISO_SIZE = 1137737728


class PspModuleAnalysisError(RuntimeError):
    """Raised when a PSP module analysis workspace is invalid or unsupported."""


@dataclass(frozen=True, slots=True)
class PspModuleCandidate:
    workspace_path: str
    local_path: Path
    sha256: str
    size: int
    iso_lba: int
    iso_byte_offset: int
    classification: str
    is_boot: bool


@dataclass(slots=True)
class PspModuleRun:
    candidate: PspModuleCandidate
    status: str
    needs_decryption: bool
    model: Any | None = None
    placement: Any | None = None
    disassembly: Any | None = None
    advanced: Any | None = None
    typing: Any | None = None
    error: str | None = None


@dataclass(slots=True)
class PspAnalysisRun:
    workspace: Path
    toolchain: PspToolchainInfo
    modules: tuple[PspModuleRun, ...]
    links: Any | None = None


def discover_psp_module_candidates(workspace: Path) -> tuple[PspModuleCandidate, ...]:
    try:
        validation = verify_workspace(workspace)
    except ValueError as exc:
        raise PspModuleAnalysisError(f"workspace verification failed: {exc}") from exc
    if not validation.valid:
        raise PspModuleAnalysisError(
            "workspace verification failed: " + "; ".join(validation.diagnostics)
        )

    manifest = load_workspace_manifest(workspace / "manifests" / "workspace.json")
    observed_revision = (
        manifest.revision_id,
        manifest.source_iso_sha256,
        manifest.source_iso_size,
    )
    expected_revision = (FNR3_REVISION_ID, FNR3_ISO_SHA256, FNR3_ISO_SIZE)
    if observed_revision != expected_revision:
        raise PspModuleAnalysisError(
            "workspace is not the locked ULUS10066-v1.00 reference"
        )

    original = workspace / "original"
    candidates: list[PspModuleCandidate] = []
    for entry in manifest.files:
        local_path = _workspace_path(original, entry.path)
        upper_path = entry.path.upper()
        declared_candidate = (
            upper_path
            in {
                "PSP_GAME/SYSDIR/BOOT.BIN",
                "PSP_GAME/SYSDIR/EBOOT.BIN",
            }
            or upper_path.endswith(".PRX")
        )
        with local_path.open("rb") as stream:
            signature = stream.read(4)
        recognized_candidate = signature in {b"\x7fELF", b"~PSP"}
        if not declared_candidate and not recognized_candidate:
            continue
        candidates.append(
            PspModuleCandidate(
                workspace_path=entry.path,
                local_path=local_path,
                sha256=entry.sha256,
                size=entry.size,
                iso_lba=entry.lba,
                iso_byte_offset=entry.offset,
                classification=entry.classification,
                is_boot=upper_path == "PSP_GAME/SYSDIR/BOOT.BIN",
            )
        )

    return tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                not candidate.is_boot,
                candidate.workspace_path.casefold(),
            ),
        )
    )


def _module_failure(
    run: PspModuleRun,
    exc: Exception,
    *,
    phase: str,
) -> None:
    if run.candidate.is_boot:
        raise PspModuleAnalysisError(
            f"boot module {phase} failed: {exc}"
        ) from exc
    run.status = "failed"
    run.error = str(exc)


def _parse_toolkit_elf(toolkit: Any, data: bytes) -> Any:
    parser = getattr(toolkit, "parse_elf32", None)
    if parser is None:
        parser_module = import_module(f"{toolkit.__name__}.elf32")
        parser = parser_module.parse_elf32
    return parser(data)


def _relocated_link_model(toolkit: Any, run: PspModuleRun) -> Any:
    if run.model is None or run.placement is None:
        raise PspModuleAnalysisError("link preparation requires model and placement")
    if not run.placement.requires_relocation:
        return run.model
    data = run.candidate.local_path.read_bytes()
    elf = _parse_toolkit_elf(toolkit, data)
    return toolkit.build_relocated_load_view(
        data,
        elf,
        run.model,
        load_address=run.placement.load_address,
    ).model


def _link_analyzed_modules(
    toolkit: Any,
    runs: list[PspModuleRun],
    nid_db_paths: tuple[Path, ...],
) -> Any | None:
    link_inputs: list[Any] = []
    for run in runs:
        if (
            run.status != "analyzed"
            or run.model is None
            or run.disassembly is None
            or run.placement is None
        ):
            continue
        try:
            linked_model = _relocated_link_model(toolkit, run)
        except Exception as exc:
            _module_failure(run, exc, phase="link preparation")
            continue
        link_inputs.append(
            toolkit.ModuleAnalysisInput(
                model=linked_model,
                disassembly=run.disassembly,
            )
        )

    if not link_inputs:
        return None
    database = toolkit.load_nid_databases(nid_db_paths) if nid_db_paths else None
    try:
        return toolkit.link_modules(link_inputs, database=database)
    except Exception as exc:
        raise PspModuleAnalysisError(f"cross-module linking failed: {exc}") from exc


def analyze_psp_modules(
    workspace: Path,
    *,
    nid_db_paths: tuple[Path, ...] = (),
    allow_unpinned_toolkit: bool = False,
) -> PspAnalysisRun:
    toolchain = load_psp_toolchain(allow_unpinned=allow_unpinned_toolkit)
    toolkit = cast(Any, toolchain.module)
    candidates = discover_psp_module_candidates(workspace)
    runs: list[PspModuleRun] = []
    placement_inputs: list[Any] = []

    for candidate in candidates:
        run = PspModuleRun(
            candidate=candidate,
            status="pending",
            needs_decryption=False,
        )
        try:
            model = toolkit.analyze_file(candidate.local_path)
        except Exception as exc:
            _module_failure(run, exc, phase="analysis")
            runs.append(run)
            continue

        run.model = model
        run.needs_decryption = bool(model.needs_decryption)
        if run.needs_decryption:
            run.status = "needs_decryption"
            runs.append(run)
            continue

        placement_inputs.append(
            toolkit.ModulePlacementInput(
                path=candidate.workspace_path,
                is_boot=candidate.is_boot,
                model=model,
            )
        )
        runs.append(run)

    placements = (
        {
            placement.path: placement
            for placement in toolkit.plan_module_placements(placement_inputs)
        }
        if placement_inputs
        else {}
    )

    for run in runs:
        if run.status != "pending" or run.model is None:
            continue
        placement = placements[run.candidate.workspace_path]
        run.placement = placement
        load_address = placement.load_address if placement.requires_relocation else None
        try:
            run.disassembly = toolkit.disassemble_file(
                run.candidate.local_path,
                load_address=load_address,
            )
            run.advanced = toolkit.analyze_advanced(run.model, run.disassembly)
        except Exception as exc:
            _module_failure(run, exc, phase="disassembly")
            continue
        run.status = "analyzed"

    links = _link_analyzed_modules(toolkit, runs, nid_db_paths)
    return PspAnalysisRun(
        workspace=workspace,
        toolchain=toolchain,
        modules=tuple(runs),
        links=links,
    )
