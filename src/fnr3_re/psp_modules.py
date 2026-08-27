from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .iso import _workspace_path, verify_workspace
from .manifests import load_workspace_manifest

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
