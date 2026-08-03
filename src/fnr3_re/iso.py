from __future__ import annotations

import hashlib
import os
import shutil
import stat
import uuid
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path, PurePosixPath
from typing import BinaryIO

from .manifests import (
    ManifestDirectory,
    ManifestFile,
    WorkspaceManifest,
    WorkspaceValidationResult,
    classify_iso_path,
    load_workspace_manifest,
)
from .revision import ReferenceRevision, validate_image

SECTOR_SIZE = 2048
PVD_SECTOR = 16
PVD_ROOT_RECORD_OFFSET = 156


class IsoFormatError(ValueError):
    """Raised when an ISO9660 image is unsafe, ambiguous, or malformed."""


@dataclass(frozen=True, slots=True)
class IsoEntry:
    path: str
    lba: int
    offset: int
    size: int
    flags: int
    order: int
    directory: bool


@dataclass(frozen=True, slots=True)
class IsoInventory:
    image: Path
    volume_id: str
    sector_size: int
    volume_sectors: int
    volume_size: int
    directories: tuple[IsoEntry, ...]
    files: tuple[IsoEntry, ...]


@dataclass(frozen=True, slots=True)
class _RawDirectoryEntry:
    identifier: bytes
    lba: int
    size: int
    flags: int
    directory: bool
    special: bool


def scan_iso(image: Path) -> IsoInventory:
    if not image.is_file():
        raise IsoFormatError("ISO image does not exist")
    actual_size = image.stat().st_size
    with image.open("rb") as stream:
        pvd = _read_exact(stream, PVD_SECTOR * SECTOR_SIZE, SECTOR_SIZE, "primary volume")
        if pvd[0] != 1 or pvd[1:6] != b"CD001" or pvd[6] != 1:
            raise IsoFormatError("primary volume descriptor signature is invalid")

        logical_block_size = _both_endian_u16(pvd, 128, "logical block size")
        if logical_block_size != SECTOR_SIZE:
            raise IsoFormatError(
                f"unsupported logical block size: expected {SECTOR_SIZE}, got {logical_block_size}"
            )
        volume_sectors = _both_endian_u32(pvd, 80, "volume space size")
        if volume_sectors <= 0:
            raise IsoFormatError("volume space size must be positive")
        volume_size = volume_sectors * logical_block_size
        if volume_size > actual_size:
            raise IsoFormatError(
                f"ISO image is truncated: volume declares {volume_size} bytes, "
                f"file has {actual_size}"
            )
        try:
            volume_id = pvd[40:72].decode("ascii").rstrip(" ")
        except UnicodeDecodeError as exc:
            raise IsoFormatError("volume identifier is not ASCII") from exc
        if not volume_id:
            raise IsoFormatError("volume identifier is empty")

        root_raw = _parse_directory_record(pvd, PVD_ROOT_RECORD_OFFSET, logical_block_size)
        if root_raw is None or not root_raw.directory:
            raise IsoFormatError("root directory record is invalid")
        _validate_extent(root_raw.lba, root_raw.size, volume_size, "root directory")

        directories: list[IsoEntry] = [
            IsoEntry(
                path=".",
                lba=root_raw.lba,
                offset=root_raw.lba * logical_block_size,
                size=root_raw.size,
                flags=root_raw.flags,
                order=0,
                directory=True,
            )
        ]
        files: list[IsoEntry] = []
        seen_paths = {"."}
        seen_directory_extents = {(root_raw.lba, root_raw.size)}
        allocated_ranges: list[tuple[int, int, str]] = [
            _allocated_range(directories[0], logical_block_size)
        ]
        next_directory_order = 1
        next_file_order = 0

        def walk(parent_path: str, directory: IsoEntry) -> None:
            nonlocal next_directory_order, next_file_order
            payload = _read_exact(
                stream,
                directory.offset,
                directory.size,
                f"directory {directory.path}",
            )
            offset = 0
            while offset < len(payload):
                record_length = payload[offset]
                if record_length == 0:
                    offset = ((offset // logical_block_size) + 1) * logical_block_size
                    continue
                raw = _parse_directory_record(payload, offset, logical_block_size)
                if raw is None:
                    raise IsoFormatError(
                        f"directory record at {directory.path}+0x{offset:x} is malformed"
                    )
                offset += record_length
                if raw.special:
                    continue
                if raw.flags & 0x80:
                    raise IsoFormatError("multi-extent files are unsupported")
                name = _normalize_identifier(raw.identifier)
                path = name if parent_path == "." else f"{parent_path}/{name}"
                canonical_path = path.casefold()
                if canonical_path in seen_paths:
                    raise IsoFormatError(f"duplicate ISO path: {path}")
                seen_paths.add(canonical_path)
                _validate_extent(raw.lba, raw.size, volume_size, path)

                if raw.directory:
                    extent_key = (raw.lba, raw.size)
                    if extent_key in seen_directory_extents:
                        raise IsoFormatError(f"directory extent reused by multiple paths: {path}")
                    seen_directory_extents.add(extent_key)
                    entry = IsoEntry(
                        path=path,
                        lba=raw.lba,
                        offset=raw.lba * logical_block_size,
                        size=raw.size,
                        flags=raw.flags,
                        order=next_directory_order,
                        directory=True,
                    )
                    next_directory_order += 1
                    directories.append(entry)
                    allocated_ranges.append(_allocated_range(entry, logical_block_size))
                    walk(path, entry)
                else:
                    entry = IsoEntry(
                        path=path,
                        lba=raw.lba,
                        offset=raw.lba * logical_block_size,
                        size=raw.size,
                        flags=raw.flags,
                        order=next_file_order,
                        directory=False,
                    )
                    next_file_order += 1
                    files.append(entry)
                    if entry.size:
                        allocated_ranges.append(_allocated_range(entry, logical_block_size))

        walk(".", directories[0])
        _reject_overlapping_ranges(allocated_ranges)

    return IsoInventory(
        image=image,
        volume_id=volume_id,
        sector_size=logical_block_size,
        volume_sectors=volume_sectors,
        volume_size=volume_size,
        directories=tuple(directories),
        files=tuple(files),
    )


def build_workspace(
    image: Path,
    destination: Path,
    revision: ReferenceRevision,
    *,
    force: bool = False,
) -> WorkspaceManifest:
    validation = validate_image(image, revision)
    if not validation.valid:
        details = "; ".join(validation.diagnostics)
        raise ValueError(f"reference image validation failed: {details}")
    inventory = scan_iso(image)

    destination = destination.absolute()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.parent / f".{destination.name}.tmp-{uuid.uuid4().hex}"
    backup = destination.parent / f".{destination.name}.bak-{uuid.uuid4().hex}"
    if destination.exists() and not force:
        raise FileExistsError(f"workspace already exists: {destination}")

    manifest: WorkspaceManifest
    try:
        original = temporary / "original"
        working = temporary / "working"
        modified = temporary / "modified"
        manifests = temporary / "manifests"
        original.mkdir(parents=True)
        working.mkdir()
        modified.mkdir()
        manifests.mkdir()

        for entry in inventory.directories:
            if entry.path == ".":
                continue
            _workspace_path(original, entry.path).mkdir(parents=True, exist_ok=False)

        manifest_files: list[ManifestFile] = []
        with image.open("rb") as stream:
            for entry in inventory.files:
                output = _workspace_path(original, entry.path)
                output.parent.mkdir(parents=True, exist_ok=True)
                digest = _copy_extent(stream, entry, output)
                manifest_files.append(
                    ManifestFile(
                        path=entry.path,
                        lba=entry.lba,
                        offset=entry.offset,
                        size=entry.size,
                        sha256=digest,
                        order=entry.order,
                        classification=classify_iso_path(entry.path),
                    )
                )

        manifest = WorkspaceManifest(
            revision_id=revision.revision_id,
            source_iso_size=revision.iso_size,
            source_iso_sha256=revision.iso_sha256,
            volume_id=inventory.volume_id,
            sector_size=inventory.sector_size,
            volume_sectors=inventory.volume_sectors,
            directories=tuple(
                ManifestDirectory(
                    path=entry.path,
                    lba=entry.lba,
                    offset=entry.offset,
                    size=entry.size,
                    order=entry.order,
                )
                for entry in inventory.directories
            ),
            files=tuple(manifest_files),
        )
        (manifests / "workspace.json").write_text(manifest.to_json(), encoding="utf-8")
        _make_original_read_only(original)
        _replace_workspace(temporary, destination, backup, force=force)
    except Exception:
        _remove_path(temporary)
        if backup.exists() and not destination.exists():
            os.replace(backup, destination)
        raise
    finally:
        _remove_path(backup)

    return manifest


def verify_workspace(workspace: Path) -> WorkspaceValidationResult:
    diagnostics: set[str] = set()
    manifest_path = workspace / "manifests" / "workspace.json"
    try:
        manifest = load_workspace_manifest(manifest_path)
    except ValueError as exc:
        return WorkspaceValidationResult(
            workspace=workspace,
            valid=False,
            diagnostics=(str(exc),),
        )

    original = workspace / "original"
    for required in (original, workspace / "working", workspace / "modified"):
        if not required.is_dir():
            diagnostics.add(f"missing workspace directory: {required.name}")

    expected_files = {entry.path.casefold(): entry for entry in manifest.files}
    if original.is_dir():
        for candidate in original.rglob("*"):
            if candidate.is_symlink():
                relative = candidate.relative_to(original).as_posix()
                diagnostics.add(f"symbolic link is not allowed in original: {relative}")
            elif candidate.is_file():
                relative = candidate.relative_to(original).as_posix()
                if relative.casefold() not in expected_files:
                    diagnostics.add(f"unexpected original file: {relative}")

    for entry in manifest.files:
        path = _workspace_path(original, entry.path)
        if not path.is_file() or path.is_symlink():
            diagnostics.add(f"missing original file: {entry.path}")
            continue
        observed_size = path.stat().st_size
        if observed_size != entry.size:
            diagnostics.add(f"size mismatch: {entry.path}")
        if _hash_file(path) != entry.sha256:
            diagnostics.add(f"hash mismatch: {entry.path}")
        writable_bits = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
        if path.stat().st_mode & writable_bits:
            diagnostics.add(f"original file is writable: {entry.path}")

    for directory_entry in manifest.directories:
        path = (
            original
            if directory_entry.path == "."
            else _workspace_path(original, directory_entry.path)
        )
        if not path.is_dir() or path.is_symlink():
            diagnostics.add(f"missing original directory: {directory_entry.path}")

    ordered = tuple(sorted(diagnostics))
    return WorkspaceValidationResult(
        workspace=workspace,
        valid=not ordered,
        diagnostics=ordered,
    )


def _read_exact(stream: BinaryIO, offset: int, size: int, label: str) -> bytes:
    if offset < 0 or size < 0:
        raise IsoFormatError(f"negative offset or size for {label}")
    stream.seek(offset)
    payload = stream.read(size)
    if len(payload) != size:
        raise IsoFormatError(f"{label} is truncated")
    return payload


def _parse_directory_record(
    payload: bytes,
    offset: int,
    logical_block_size: int,
) -> _RawDirectoryEntry | None:
    if offset < 0 or offset >= len(payload):
        return None
    record_length = payload[offset]
    if record_length < 34 or offset + record_length > len(payload):
        return None
    if offset % logical_block_size + record_length > logical_block_size:
        return None
    name_length = payload[offset + 32]
    name_start = offset + 33
    name_end = name_start + name_length
    if name_end > offset + record_length:
        return None
    lba = _both_endian_u32(payload, offset + 2, "directory extent")
    size = _both_endian_u32(payload, offset + 10, "directory size")
    sequence = _both_endian_u16(payload, offset + 28, "volume sequence number")
    if sequence != 1:
        raise IsoFormatError(f"unsupported volume sequence number: {sequence}")
    identifier = payload[name_start:name_end]
    return _RawDirectoryEntry(
        identifier=identifier,
        lba=lba,
        size=size,
        flags=payload[offset + 25],
        directory=bool(payload[offset + 25] & 0x02),
        special=identifier in {b"\x00", b"\x01"},
    )


def _normalize_identifier(identifier: bytes) -> str:
    try:
        decoded = identifier.decode("ascii")
    except UnicodeDecodeError as exc:
        raise IsoFormatError("ISO identifier is not ASCII") from exc
    if any(character in decoded for character in ("/", "\\", "\x00")):
        raise IsoFormatError(f"unsafe ISO identifier: {decoded!r}")
    name, separator, version = decoded.rpartition(";")
    if separator:
        if not version.isdigit() or not name:
            raise IsoFormatError(f"invalid ISO version suffix: {decoded!r}")
        decoded = name
    if not decoded or decoded in {".", ".."}:
        raise IsoFormatError(f"unsafe ISO identifier: {decoded!r}")
    pure = PurePosixPath(decoded)
    if pure.is_absolute() or len(pure.parts) != 1 or pure.name != decoded:
        raise IsoFormatError(f"unsafe ISO identifier: {decoded!r}")
    return decoded


def _both_endian_u16(payload: bytes, offset: int, label: str) -> int:
    if offset < 0 or offset + 4 > len(payload):
        raise IsoFormatError(f"{label} is truncated")
    little = int.from_bytes(payload[offset : offset + 2], "little")
    big = int.from_bytes(payload[offset + 2 : offset + 4], "big")
    if little != big:
        raise IsoFormatError(f"{label} endian values disagree")
    return little


def _both_endian_u32(payload: bytes, offset: int, label: str) -> int:
    if offset < 0 or offset + 8 > len(payload):
        raise IsoFormatError(f"{label} is truncated")
    little = int.from_bytes(payload[offset : offset + 4], "little")
    big = int.from_bytes(payload[offset + 4 : offset + 8], "big")
    if little != big:
        raise IsoFormatError(f"{label} endian values disagree")
    return little


def _validate_extent(lba: int, size: int, volume_size: int, label: str) -> None:
    if lba < 0 or size < 0:
        raise IsoFormatError(f"negative extent for {label}")
    offset = lba * SECTOR_SIZE
    if offset > volume_size or size > volume_size - offset:
        raise IsoFormatError(f"extent outside declared volume: {label}")


def _allocated_range(entry: IsoEntry, logical_block_size: int) -> tuple[int, int, str]:
    allocated_size = (
        (entry.size + logical_block_size - 1) // logical_block_size * logical_block_size
    )
    return (entry.offset, entry.offset + allocated_size, entry.path)


def _reject_overlapping_ranges(ranges: list[tuple[int, int, str]]) -> None:
    ordered = sorted((item for item in ranges if item[0] != item[1]), key=lambda item: item[0])
    for previous, current in pairwise(ordered):
        if current[0] < previous[1]:
            raise IsoFormatError(
                f"overlapping extents: {previous[2]} and {current[2]}"
            )


def _workspace_path(root: Path, iso_path: str) -> Path:
    pure = PurePosixPath(iso_path)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError(f"unsafe workspace path: {iso_path}")
    candidate = root.joinpath(*pure.parts)
    root_resolved = root.resolve()
    candidate_resolved = candidate.resolve(strict=False)
    if os.path.commonpath((str(root_resolved), str(candidate_resolved))) != str(root_resolved):
        raise ValueError(f"workspace path escapes root: {iso_path}")
    return candidate


def _copy_extent(stream: BinaryIO, entry: IsoEntry, output: Path) -> str:
    digest = hashlib.sha256()
    remaining = entry.size
    stream.seek(entry.offset)
    with output.open("wb") as destination:
        while remaining:
            chunk = stream.read(min(1024 * 1024, remaining))
            if not chunk:
                raise IsoFormatError(f"file extent is truncated: {entry.path}")
            destination.write(chunk)
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.hexdigest()


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _make_original_read_only(original: Path) -> None:
    for path in original.rglob("*"):
        if path.is_file():
            path.chmod(0o444)
    directories = [path for path in original.rglob("*") if path.is_dir()]
    for path in sorted(directories, key=lambda item: len(item.parts), reverse=True):
        path.chmod(0o555)
    original.chmod(0o555)


def _replace_workspace(
    temporary: Path,
    destination: Path,
    backup: Path,
    *,
    force: bool,
) -> None:
    moved_existing = False
    try:
        if destination.exists():
            if not force:
                raise FileExistsError(f"workspace already exists: {destination}")
            os.replace(destination, backup)
            moved_existing = True
        os.replace(temporary, destination)
    except Exception:
        if destination.exists() and moved_existing:
            _remove_path(destination)
        if moved_existing and backup.exists():
            os.replace(backup, destination)
        raise
    if moved_existing:
        _remove_path(backup)


def _remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        for candidate in path.rglob("*"):
            if candidate.is_file():
                candidate.chmod(0o644)
            elif candidate.is_dir():
                candidate.chmod(0o755)
        path.chmod(0o755)
        shutil.rmtree(path)
    else:
        path.chmod(0o644)
        path.unlink()
