from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

MANIFEST_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class ManifestDirectory:
    path: str
    lba: int
    offset: int
    size: int
    order: int

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> ManifestDirectory:
        return cls(
            path=_required_string(payload, "path"),
            lba=_required_int(payload, "lba"),
            offset=_required_int(payload, "offset"),
            size=_required_int(payload, "size"),
            order=_required_int(payload, "order"),
        )


@dataclass(frozen=True, slots=True)
class ManifestFile:
    path: str
    lba: int
    offset: int
    size: int
    sha256: str
    order: int
    classification: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> ManifestFile:
        return cls(
            path=_required_string(payload, "path"),
            lba=_required_int(payload, "lba"),
            offset=_required_int(payload, "offset"),
            size=_required_int(payload, "size"),
            sha256=_required_sha256(payload, "sha256"),
            order=_required_int(payload, "order"),
            classification=_required_string(payload, "classification"),
        )


@dataclass(frozen=True, slots=True)
class WorkspaceManifest:
    revision_id: str
    source_iso_size: int
    source_iso_sha256: str
    volume_id: str
    sector_size: int
    volume_sectors: int
    directories: tuple[ManifestDirectory, ...]
    files: tuple[ManifestFile, ...]
    schema_version: int = MANIFEST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != MANIFEST_SCHEMA_VERSION:
            raise ValueError(f"unsupported workspace manifest schema: {self.schema_version}")
        if not self.revision_id.strip():
            raise ValueError("revision_id is required")
        if self.source_iso_size <= 0:
            raise ValueError("source_iso_size must be positive")
        _validate_sha256(self.source_iso_sha256, "source_iso_sha256")
        if self.sector_size <= 0 or self.volume_sectors <= 0:
            raise ValueError("sector_size and volume_sectors must be positive")
        _validate_unique_paths(self.directories, "directory")
        _validate_unique_paths(self.files, "file")

    def to_json(self) -> str:
        return (
            json.dumps(
                asdict(self),
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n"
        )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> WorkspaceManifest:
        directories_payload = _required_sequence(payload, "directories")
        files_payload = _required_sequence(payload, "files")
        return cls(
            revision_id=_required_string(payload, "revision_id"),
            source_iso_size=_required_int(payload, "source_iso_size"),
            source_iso_sha256=_required_sha256(payload, "source_iso_sha256"),
            volume_id=_required_string(payload, "volume_id"),
            sector_size=_required_int(payload, "sector_size"),
            volume_sectors=_required_int(payload, "volume_sectors"),
            directories=tuple(
                ManifestDirectory.from_mapping(_mapping_item(item, "directories"))
                for item in directories_payload
            ),
            files=tuple(
                ManifestFile.from_mapping(_mapping_item(item, "files"))
                for item in files_payload
            ),
            schema_version=_required_int(payload, "schema_version"),
        )


@dataclass(frozen=True, slots=True)
class WorkspaceValidationResult:
    workspace: Path
    valid: bool
    diagnostics: tuple[str, ...]

    def to_json(self) -> str:
        return (
            json.dumps(
                {
                    "diagnostics": list(self.diagnostics),
                    "valid": self.valid,
                    "workspace": str(self.workspace),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )


def load_workspace_manifest(path: Path) -> WorkspaceManifest:
    try:
        decoded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid workspace manifest: {exc}") from exc
    if not isinstance(decoded, Mapping):
        raise ValueError("invalid workspace manifest: root must be an object")
    return WorkspaceManifest.from_mapping(cast(Mapping[str, Any], decoded))


def classify_iso_path(path: str) -> str:
    normalized = path.upper()
    if normalized == "PSP_GAME/SYSDIR/BOOT.BIN":
        return "main_executable"
    if normalized == "PSP_GAME/SYSDIR/EBOOT.BIN":
        return "packed_executable"
    suffix = Path(path).suffix.lower()
    classifications = {
        ".prx": "prx_module",
        ".big": "ea_big_archive",
        ".viv": "ea_viv_archive",
        ".abk": "ea_audio_bank",
        ".bnk": "audio_bank",
        ".zlb": "zlb_package",
        ".pmf": "psp_movie",
        ".at3": "psp_audio",
        ".sfo": "psp_metadata",
    }
    return classifications.get(suffix, "resource")


def _validate_unique_paths(items: Sequence[ManifestDirectory | ManifestFile], label: str) -> None:
    paths = [item.path.casefold() for item in items]
    if len(paths) != len(set(paths)):
        raise ValueError(f"duplicate {label} path in workspace manifest")


def _required_string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _required_int(payload: Mapping[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    return value


def _required_sha256(payload: Mapping[str, Any], key: str) -> str:
    value = _required_string(payload, key)
    _validate_sha256(value, key)
    return value


def _validate_sha256(value: str, label: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{label} must be 64 lowercase hexadecimal characters")


def _required_sequence(payload: Mapping[str, Any], key: str) -> Sequence[Any]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return value


def _mapping_item(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} entries must be objects")
    return cast(Mapping[str, Any], value)
