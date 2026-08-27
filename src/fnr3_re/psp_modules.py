from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass, is_dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from .iso import _remove_path, _workspace_path, verify_workspace
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
    required_api = (
        "ModuleAnalysisInput",
        "build_relocated_load_view",
        "link_modules",
    )
    if not all(hasattr(toolkit, name) for name in required_api):
        return None
    if nid_db_paths and not hasattr(toolkit, "load_nid_databases"):
        raise PspModuleAnalysisError(
            "toolkit does not support external NID databases"
        )

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


def _jsonable(value: object) -> object:
    if is_dataclass(value):
        return _jsonable(asdict(cast(Any, value)))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bytes):
        return {"omitted_bytes": len(value)}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(_jsonable(value), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _safe_module_id(module: PspModuleRun) -> str:
    normalized = module.candidate.workspace_path.replace("\\", "/").casefold()
    normalized = normalized.replace("/", "__")
    normalized = re.sub(r"[^a-z0-9._-]+", "_", normalized).strip("._-")
    base = normalized or "module"
    return f"{base}-{module.candidate.sha256[:12].lower()}"


def _inventory_payload(module: PspModuleRun) -> dict[str, object]:
    candidate = module.candidate
    return {
        "classification": candidate.classification,
        "is_boot": candidate.is_boot,
        "iso_byte_offset": candidate.iso_byte_offset,
        "iso_lba": candidate.iso_lba,
        "needs_decryption": module.needs_decryption,
        "sha256": candidate.sha256,
        "size": candidate.size,
        "status": module.status,
        "workspace_path": candidate.workspace_path,
    }


def _write_run_tree(run: PspAnalysisRun, destination: Path) -> None:
    modules_root = destination / "modules"
    links_root = destination / "links"
    modules_root.mkdir(parents=True)
    links_root.mkdir()

    toolchain = run.toolchain
    _write_json(
        destination / "toolchain.json",
        {
            "expected_revision": toolchain.expected_revision,
            "observed_revision": toolchain.observed_revision,
            "package_version": toolchain.package_version,
            "repository": toolchain.repository,
            "revision_locked": toolchain.revision_locked,
        },
    )

    for module in sorted(run.modules, key=lambda item: item.candidate.workspace_path.casefold()):
        module_root = modules_root / _safe_module_id(module)
        module_root.mkdir()
        if module.status in {"failed", "needs_decryption"}:
            _write_json(module_root / "inventory.json", _inventory_payload(module))
            if module.error is not None:
                _write_json(module_root / "error.json", {"error": module.error})
            continue

        _write_json(module_root / "executable.json", module.model)
        _write_json(module_root / "placement.json", module.placement)
        _write_json(module_root / "disassembly.json", module.disassembly)
        _write_json(module_root / "advanced.json", module.advanced)
        _write_json(
            module_root / "typing.json",
            module.typing if module.typing is not None else {"available": False},
        )

    links = run.links
    if links is None:
        module_links: object = {
            "links": [],
            "modules": [],
            "resolutions": [],
            "warnings": [],
        }
        propagated_symbols: object = []
    else:
        module_links = {
            "links": getattr(links, "links", []),
            "modules": getattr(links, "modules", []),
            "resolutions": getattr(links, "resolutions", []),
            "warnings": getattr(links, "warnings", []),
        }
        propagated_symbols = getattr(links, "propagated_symbols", [])
    _write_json(links_root / "module_links.json", module_links)
    _write_json(links_root / "propagated_symbols.json", propagated_symbols)


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_safe_output_target(workspace: Path, target: Path) -> None:
    if workspace.is_symlink():
        raise PspModuleAnalysisError("workspace output root must not be a symlink")
    try:
        relative = target.relative_to(workspace)
    except ValueError as exc:
        raise PspModuleAnalysisError("output path escapes workspace") from exc

    cursor = workspace
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise PspModuleAnalysisError(f"symlinked output path is not allowed: {cursor}")

    workspace_resolved = workspace.resolve()
    target_resolved = target.resolve(strict=False)
    if os.path.commonpath((str(workspace_resolved), str(target_resolved))) != str(
        workspace_resolved
    ):
        raise PspModuleAnalysisError("resolved output path escapes workspace")


def _remove_if_present(path: Path) -> None:
    if path.exists() or path.is_symlink():
        _remove_path(path)


def _replace_output_pair(
    working_temp: Path,
    working_target: Path,
    manifest_temp: Path,
    manifest_target: Path,
    *,
    token: str,
) -> None:
    working_backup = working_target.with_name(f".{working_target.name}.bak-{token}")
    manifest_backup = manifest_target.with_name(f".{manifest_target.name}.bak-{token}")
    working_backed_up = False
    manifest_backed_up = False
    working_installed = False
    manifest_installed = False

    try:
        if working_target.exists():
            os.replace(working_target, working_backup)
            working_backed_up = True
        if manifest_target.exists():
            os.replace(manifest_target, manifest_backup)
            manifest_backed_up = True

        os.replace(working_temp, working_target)
        working_installed = True
        os.replace(manifest_temp, manifest_target)
        manifest_installed = True
    except Exception:
        if working_installed:
            _remove_if_present(working_target)
        if manifest_installed:
            _remove_if_present(manifest_target)
        if working_backed_up and working_backup.exists():
            os.replace(working_backup, working_target)
            working_backed_up = False
        if manifest_backed_up and manifest_backup.exists():
            os.replace(manifest_backup, manifest_target)
            manifest_backed_up = False
        raise
    finally:
        if working_backed_up:
            _remove_if_present(working_backup)
        if manifest_backed_up:
            _remove_if_present(manifest_backup)


def write_psp_analysis_run(run: PspAnalysisRun) -> Path:
    from .psp_evidence import build_psp_evidence_manifest

    workspace = run.workspace
    working_target = workspace / "working" / "pspdisasm"
    manifest_target = workspace / "manifests" / "pspdisasm-module-evidence.json"
    workspace_manifest = workspace / "manifests" / "workspace.json"

    _assert_safe_output_target(workspace, working_target)
    _assert_safe_output_target(workspace, manifest_target)
    if not workspace_manifest.is_file():
        raise PspModuleAnalysisError(f"workspace manifest does not exist: {workspace_manifest}")

    working_target.parent.mkdir(parents=True, exist_ok=True)
    manifest_target.parent.mkdir(parents=True, exist_ok=True)
    token = uuid4().hex
    working_temp = working_target.with_name(f".{working_target.name}.tmp-{token}")
    manifest_temp = manifest_target.with_name(f".{manifest_target.name}.tmp-{token}")

    try:
        _write_run_tree(run, working_temp)
        evidence = build_psp_evidence_manifest(
            run,
            workspace_manifest_sha256=_hash_file(workspace_manifest),
        )
        manifest_temp.write_text(evidence.to_json(), encoding="utf-8")
        _replace_output_pair(
            working_temp,
            working_target,
            manifest_temp,
            manifest_target,
            token=token,
        )
        return manifest_target
    finally:
        _remove_if_present(working_temp)
        _remove_if_present(manifest_temp)
