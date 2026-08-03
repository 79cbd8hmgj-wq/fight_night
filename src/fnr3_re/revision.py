from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, cast

SECTOR_SIZE = 2048
PVD_SECTOR = 16
PVD_ROOT_RECORD_OFFSET = 156
SFO_PATH = "PSP_GAME/PARAM.SFO"


@dataclass(frozen=True, slots=True)
class ReferenceRevision:
    revision_id: str
    disc_id: str
    disc_version: str
    title: str
    psp_system_version: str
    iso_size: int
    iso_sha256: str

    def __post_init__(self) -> None:
        text_fields = {
            "revision_id": self.revision_id,
            "disc_id": self.disc_id,
            "disc_version": self.disc_version,
            "title": self.title,
            "psp_system_version": self.psp_system_version,
        }
        for name, value in text_fields.items():
            if not value.strip():
                raise ValueError(f"{name} is required")
        if self.iso_size <= 0:
            raise ValueError("iso_size must be positive")
        if len(self.iso_sha256) != 64 or any(
            character not in "0123456789abcdef" for character in self.iso_sha256
        ):
            raise ValueError("iso_sha256 must be 64 lowercase hexadecimal characters")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> ReferenceRevision:
        return cls(
            revision_id=_required_string(payload, "revision_id"),
            disc_id=_required_string(payload, "disc_id"),
            disc_version=_required_string(payload, "disc_version"),
            title=_required_string(payload, "title"),
            psp_system_version=_required_string(payload, "psp_system_version"),
            iso_size=_required_int(payload, "iso_size"),
            iso_sha256=_required_string(payload, "iso_sha256"),
        )


@dataclass(frozen=True, slots=True)
class ImageValidationResult:
    image: Path
    revision_id: str
    valid: bool
    diagnostics: tuple[str, ...]
    observed_size: int | None
    observed_sha256: str | None
    observed_metadata: dict[str, str]

    def to_json(self) -> str:
        return (
            json.dumps(
                {
                    "diagnostics": list(self.diagnostics),
                    "image": str(self.image),
                    "observed_metadata": self.observed_metadata,
                    "observed_sha256": self.observed_sha256,
                    "observed_size": self.observed_size,
                    "revision_id": self.revision_id,
                    "valid": self.valid,
                },
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n"
        )


@dataclass(frozen=True, slots=True)
class _DirectoryEntry:
    name: str
    extent: int
    size: int
    directory: bool


def load_reference_revision(path: Path) -> ReferenceRevision:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid revision configuration: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("invalid revision configuration: root must be an object")
    return ReferenceRevision.from_mapping(cast(Mapping[str, Any], payload))


def hash_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def validate_image(image: Path, revision: ReferenceRevision) -> ImageValidationResult:
    diagnostics: set[str] = set()
    if not image.is_file():
        return ImageValidationResult(
            image=image,
            revision_id=revision.revision_id,
            valid=False,
            diagnostics=("image file does not exist",),
            observed_size=None,
            observed_sha256=None,
            observed_metadata={},
        )

    observed_size = image.stat().st_size
    observed_sha256 = hash_file(image)
    if observed_size != revision.iso_size:
        diagnostics.add(f"ISO size mismatch: expected {revision.iso_size}, got {observed_size}")
    if observed_sha256 != revision.iso_sha256:
        diagnostics.add(
            f"ISO SHA-256 mismatch: expected {revision.iso_sha256}, got {observed_sha256}"
        )

    observed_metadata: dict[str, str] = {}
    try:
        observed_metadata = parse_param_sfo(read_iso9660_file(image, SFO_PATH))
    except (OSError, ValueError) as exc:
        diagnostics.add(f"invalid ISO9660 image: {exc}")
    else:
        expected_metadata = {
            "DISC_ID": revision.disc_id,
            "DISC_VERSION": revision.disc_version,
            "TITLE": revision.title,
            "PSP_SYSTEM_VER": revision.psp_system_version,
        }
        for key, expected in expected_metadata.items():
            observed = observed_metadata.get(key)
            if observed is None:
                diagnostics.add(f"PARAM.SFO missing required key: {key}")
            elif observed != expected:
                diagnostics.add(f"PARAM.SFO {key} mismatch: expected {expected}, got {observed}")

    ordered = tuple(sorted(diagnostics))
    return ImageValidationResult(
        image=image,
        revision_id=revision.revision_id,
        valid=not ordered,
        diagnostics=ordered,
        observed_size=observed_size,
        observed_sha256=observed_sha256,
        observed_metadata=observed_metadata,
    )


def read_iso9660_file(image: Path, iso_path: str) -> bytes:
    parts = [part.upper() for part in iso_path.replace("\\", "/").split("/") if part]
    if not parts or any(part in {".", ".."} for part in parts):
        raise ValueError("ISO path must contain normal path components")

    with image.open("rb") as stream:
        root = _read_root_directory(stream)
        current = root
        for index, part in enumerate(parts):
            entries = _read_directory(stream, current)
            match = next((entry for entry in entries if entry.name.upper() == part), None)
            if match is None:
                raise ValueError(f"ISO path not found: {iso_path}")
            final = index == len(parts) - 1
            if final:
                if match.directory:
                    raise ValueError(f"ISO path is a directory: {iso_path}")
                return _read_extent(stream, match.extent, match.size)
            if not match.directory:
                raise ValueError(f"ISO path component is not a directory: {part}")
            current = match
    raise AssertionError("unreachable ISO path traversal")


def _read_root_directory(stream: BinaryIO) -> _DirectoryEntry:
    stream.seek(PVD_SECTOR * SECTOR_SIZE)
    pvd = stream.read(SECTOR_SIZE)
    if len(pvd) != SECTOR_SIZE:
        raise ValueError("primary volume descriptor is truncated")
    if pvd[0] != 1 or pvd[1:6] != b"CD001" or pvd[6] != 1:
        raise ValueError("primary volume descriptor signature is invalid")
    record = _parse_directory_record(pvd, PVD_ROOT_RECORD_OFFSET)
    if record is None or not record.directory:
        raise ValueError("root directory record is invalid")
    return record


def _read_directory(stream: BinaryIO, directory: _DirectoryEntry) -> tuple[_DirectoryEntry, ...]:
    payload = _read_extent(stream, directory.extent, directory.size)
    entries: list[_DirectoryEntry] = []
    offset = 0
    while offset < len(payload):
        record_length = payload[offset]
        if record_length == 0:
            offset = ((offset // SECTOR_SIZE) + 1) * SECTOR_SIZE
            continue
        record = _parse_directory_record(payload, offset)
        if record is None:
            raise ValueError(f"directory record at offset {offset} is malformed")
        if record.name not in {".", ".."}:
            entries.append(record)
        offset += record_length
    return tuple(entries)


def _parse_directory_record(payload: bytes, offset: int) -> _DirectoryEntry | None:
    if offset < 0 or offset >= len(payload):
        return None
    record_length = payload[offset]
    if record_length < 34 or offset + record_length > len(payload):
        return None
    name_length = payload[offset + 32]
    name_start = offset + 33
    name_end = name_start + name_length
    if name_end > offset + record_length:
        return None
    raw_name = payload[name_start:name_end]
    if raw_name == b"\x00":
        name = "."
    elif raw_name == b"\x01":
        name = ".."
    else:
        try:
            name = raw_name.decode("ascii")
        except UnicodeDecodeError as exc:
            raise ValueError("directory identifier is not ASCII") from exc
        name = name.split(";", 1)[0]
    return _DirectoryEntry(
        name=name,
        extent=int.from_bytes(payload[offset + 2 : offset + 6], "little"),
        size=int.from_bytes(payload[offset + 10 : offset + 14], "little"),
        directory=bool(payload[offset + 25] & 0x02),
    )


def _read_extent(stream: BinaryIO, extent: int, size: int) -> bytes:
    if extent < 0 or size < 0:
        raise ValueError("negative extent or size")
    stream.seek(extent * SECTOR_SIZE)
    payload = stream.read(size)
    if len(payload) != size:
        raise ValueError("extent is truncated")
    return payload


def parse_param_sfo(payload: bytes) -> dict[str, str]:
    if len(payload) < 20 or payload[0:4] != b"\x00PSF":
        raise ValueError("PARAM.SFO header is invalid")
    key_table_offset = int.from_bytes(payload[8:12], "little")
    data_table_offset = int.from_bytes(payload[12:16], "little")
    entry_count = int.from_bytes(payload[16:20], "little")
    if entry_count > 4096:
        raise ValueError("PARAM.SFO entry count is unreasonable")
    table_end = 20 + entry_count * 16
    if table_end > len(payload) or key_table_offset < table_end or data_table_offset > len(payload):
        raise ValueError("PARAM.SFO table offsets are invalid")

    values: dict[str, str] = {}
    for index in range(entry_count):
        entry_offset = 20 + index * 16
        key_offset = int.from_bytes(payload[entry_offset : entry_offset + 2], "little")
        value_type = int.from_bytes(payload[entry_offset + 2 : entry_offset + 4], "little")
        value_length = int.from_bytes(payload[entry_offset + 4 : entry_offset + 8], "little")
        max_length = int.from_bytes(payload[entry_offset + 8 : entry_offset + 12], "little")
        data_offset = int.from_bytes(payload[entry_offset + 12 : entry_offset + 16], "little")
        key_start = key_table_offset + key_offset
        key = _read_c_string(payload, key_start, data_table_offset)
        value_start = data_table_offset + data_offset
        if value_length > max_length or value_start + value_length > len(payload):
            raise ValueError(f"PARAM.SFO value bounds are invalid for key {key}")
        raw_value = payload[value_start : value_start + value_length]
        if value_type in {0x0004, 0x0204}:
            try:
                values[key] = raw_value.rstrip(b"\x00").decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError(f"PARAM.SFO value for {key} is not UTF-8") from exc
        elif value_type == 0x0404 and value_length >= 4:
            values[key] = str(int.from_bytes(raw_value[:4], "little"))
        else:
            raise ValueError(f"PARAM.SFO value type 0x{value_type:04x} is unsupported")
    return values


def _read_c_string(payload: bytes, start: int, limit: int) -> str:
    if start < 0 or start >= len(payload) or limit > len(payload) or start >= limit:
        raise ValueError("PARAM.SFO key offset is invalid")
    end = payload.find(b"\x00", start, limit)
    if end < 0:
        raise ValueError("PARAM.SFO key is not terminated")
    try:
        return payload[start:end].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("PARAM.SFO key is not UTF-8") from exc


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
