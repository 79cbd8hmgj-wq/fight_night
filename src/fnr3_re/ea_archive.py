from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .refpack import is_refpack

_SUPPORTED_MAGICS = {b"BIGF", b"BIG4"}
_DEFAULT_ALIGNMENTS = {b"BIGF": 0x10, b"BIG4": 0x40}
_MAX_MEMBER_COUNT = 1_000_000
_MAX_ARCHIVE_SIZE = 0xFFFFFFFF


class EaArchiveError(ValueError):
    """Raised when an EA BIG/VIV archive is malformed or unsafe."""


@dataclass(frozen=True, slots=True)
class EaArchiveMember:
    name: str
    offset: int
    size: int
    data: bytes
    order: int
    sha256: str
    refpack_compressed: bool


@dataclass(frozen=True, slots=True)
class EaArchive:
    magic: bytes
    total_size: int
    header_size: int
    alignment: int
    members: tuple[EaArchiveMember, ...]
    source: bytes


def parse_ea_archive(payload: bytes | bytearray | memoryview) -> EaArchive:
    data = bytes(payload)
    if len(data) < 16:
        raise EaArchiveError("archive header is truncated")
    magic = data[:4]
    if magic not in _SUPPORTED_MAGICS:
        raise EaArchiveError(f"unsupported EA archive magic: {magic!r}")

    total_size = int.from_bytes(data[4:8], "little")
    member_count = int.from_bytes(data[8:12], "big")
    header_size = int.from_bytes(data[12:16], "big")
    if total_size != len(data):
        raise EaArchiveError(
            f"archive size mismatch: header declares {total_size}, file has {len(data)}"
        )
    if member_count > _MAX_MEMBER_COUNT:
        raise EaArchiveError(f"archive member count exceeds limit: {member_count}")
    if header_size < 16 or header_size > total_size:
        raise EaArchiveError(f"invalid archive header size: {header_size}")

    position = 16
    raw_members: list[tuple[str, int, int]] = []
    seen_names: set[str] = set()
    for _ in range(member_count):
        if position + 8 > header_size:
            raise EaArchiveError("directory record is truncated")
        offset = int.from_bytes(data[position : position + 4], "big")
        size = int.from_bytes(data[position + 4 : position + 8], "big")
        position += 8
        terminator = data.find(b"\x00", position, header_size)
        if terminator < 0:
            raise EaArchiveError("member name is not NUL-terminated")
        encoded_name = data[position:terminator]
        try:
            name = encoded_name.decode("ascii")
        except UnicodeDecodeError as exc:
            raise EaArchiveError("archive member name is not ASCII") from exc
        _safe_member_parts(name)
        canonical = _canonical_member_name(name)
        if canonical in seen_names:
            raise EaArchiveError(f"duplicate archive member: {name}")
        seen_names.add(canonical)
        raw_members.append((name, offset, size))
        position = terminator + 1

    if position != header_size:
        raise EaArchiveError(
            f"archive header size mismatch: directory ends at {position}, header ends at {header_size}"
        )

    ranges: list[tuple[int, int, str]] = []
    members: list[EaArchiveMember] = []
    for order, (name, offset, size) in enumerate(raw_members):
        if offset < header_size:
            raise EaArchiveError(f"member payload overlaps archive header: {name}")
        if offset > total_size or size > total_size - offset:
            raise EaArchiveError(f"member payload is outside archive: {name}")
        if size:
            ranges.append((offset, offset + size, name))
        member_data = data[offset : offset + size]
        members.append(
            EaArchiveMember(
                name=name,
                offset=offset,
                size=size,
                data=member_data,
                order=order,
                sha256=hashlib.sha256(member_data).hexdigest(),
                refpack_compressed=is_refpack(member_data),
            )
        )
    _reject_overlaps(ranges)

    return EaArchive(
        magic=magic,
        total_size=total_size,
        header_size=header_size,
        alignment=_infer_alignment(raw_members, magic),
        members=tuple(members),
        source=data,
    )


def build_ea_archive(
    members: Sequence[tuple[str, bytes]],
    *,
    magic: bytes = b"BIGF",
    alignment: int | None = None,
) -> bytes:
    if magic not in _SUPPORTED_MAGICS:
        raise EaArchiveError(f"unsupported EA archive magic: {magic!r}")
    selected_alignment = _DEFAULT_ALIGNMENTS[magic] if alignment is None else alignment
    _validate_alignment(selected_alignment)
    if len(members) > _MAX_MEMBER_COUNT:
        raise EaArchiveError(f"archive member count exceeds limit: {len(members)}")

    normalized: list[tuple[str, bytes, bytes]] = []
    seen_names: set[str] = set()
    header_size = 16
    for name, member_payload in members:
        _safe_member_parts(name)
        canonical = _canonical_member_name(name)
        if canonical in seen_names:
            raise EaArchiveError(f"duplicate archive member: {name}")
        seen_names.add(canonical)
        try:
            encoded_name = name.encode("ascii")
        except UnicodeEncodeError as exc:
            raise EaArchiveError("archive member name is not ASCII") from exc
        member_data = bytes(member_payload)
        normalized.append((name, encoded_name, member_data))
        header_size += 8 + len(encoded_name) + 1

    cursor = _align(header_size, selected_alignment)
    layout: list[tuple[str, bytes, bytes, int]] = []
    for name, encoded_name, member_data in normalized:
        offset = cursor
        layout.append((name, encoded_name, member_data, offset))
        cursor = _align(offset + len(member_data), selected_alignment)
    total_size = 0 if not layout else layout[-1][3] + len(layout[-1][2])
    total_size = max(header_size, total_size)
    if total_size > _MAX_ARCHIVE_SIZE:
        raise EaArchiveError(f"archive exceeds 32-bit size limit: {total_size}")

    output = bytearray(total_size)
    output[:4] = magic
    output[4:8] = total_size.to_bytes(4, "little")
    output[8:12] = len(layout).to_bytes(4, "big")
    output[12:16] = header_size.to_bytes(4, "big")
    position = 16
    for _name, encoded_name, member_data, offset in layout:
        output[position : position + 4] = offset.to_bytes(4, "big")
        output[position + 4 : position + 8] = len(member_data).to_bytes(4, "big")
        position += 8
        output[position : position + len(encoded_name)] = encoded_name
        position += len(encoded_name)
        output[position] = 0
        position += 1
        output[offset : offset + len(member_data)] = member_data
    if position != header_size:
        raise AssertionError("EA archive directory size calculation diverged")
    return bytes(output)


def rebuild_ea_archive(
    archive: EaArchive,
    replacements: Mapping[str, bytes] | None = None,
    *,
    expected_sha256: Mapping[str, str] | None = None,
) -> bytes:
    selected_replacements = dict(replacements or {})
    expected = dict(expected_sha256 or {})
    names = {member.name for member in archive.members}
    for name in selected_replacements:
        if name not in names:
            raise EaArchiveError(f"replacement member does not exist: {name}")
    for name in expected:
        if name not in names:
            raise EaArchiveError(f"guarded member does not exist: {name}")
    if not selected_replacements:
        return archive.source

    rebuilt_members: list[tuple[str, bytes]] = []
    for member in archive.members:
        if member.name in selected_replacements:
            guarded_hash = expected.get(member.name)
            if guarded_hash is not None and guarded_hash != member.sha256:
                raise EaArchiveError(
                    f"original member hash mismatch: {member.name}; "
                    f"expected {guarded_hash}, got {member.sha256}"
                )
            rebuilt_members.append((member.name, bytes(selected_replacements[member.name])))
        else:
            rebuilt_members.append((member.name, member.data))
    return build_ea_archive(
        rebuilt_members,
        magic=archive.magic,
        alignment=archive.alignment,
    )


def extract_ea_archive(
    archive: EaArchive,
    destination: Path,
    *,
    force: bool = False,
) -> tuple[dict[str, object], ...]:
    destination = destination.absolute()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not force:
        raise FileExistsError(f"archive destination already exists: {destination}")

    temporary = destination.parent / f".{destination.name}.tmp-{uuid.uuid4().hex}"
    backup = destination.parent / f".{destination.name}.bak-{uuid.uuid4().hex}"
    manifest: list[dict[str, object]] = []
    try:
        temporary.mkdir()
        for member in archive.members:
            output = temporary.joinpath(*_safe_member_parts(member.name))
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(member.data)
            manifest.append(
                {
                    "name": member.name,
                    "offset": member.offset,
                    "order": member.order,
                    "refpack_compressed": member.refpack_compressed,
                    "sha256": member.sha256,
                    "size": member.size,
                }
            )
        (temporary / "archive-manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _replace_directory(temporary, destination, backup, force=force)
    except Exception:
        _remove_path(temporary)
        if backup.exists() and not destination.exists():
            os.replace(backup, destination)
        raise
    finally:
        _remove_path(backup)
    return tuple(manifest)


def _safe_member_parts(name: str) -> tuple[str, ...]:
    if not name or "\x00" in name:
        raise EaArchiveError(f"unsafe archive member path: {name!r}")
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or not path.parts:
        raise EaArchiveError(f"unsafe archive member path: {name!r}")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise EaArchiveError(f"unsafe archive member path: {name!r}")
    if ":" in path.parts[0]:
        raise EaArchiveError(f"unsafe archive member path: {name!r}")
    return tuple(path.parts)


def _canonical_member_name(name: str) -> str:
    return "/".join(_safe_member_parts(name)).casefold()


def _infer_alignment(raw_members: Sequence[tuple[str, int, int]], magic: bytes) -> int:
    offsets = [offset for _name, offset, _size in raw_members if offset]
    if not offsets:
        return _DEFAULT_ALIGNMENTS[magic]
    divisor = offsets[0]
    for offset in offsets[1:]:
        divisor = math.gcd(divisor, offset)
    power_of_two = divisor & -divisor
    return max(1, min(power_of_two, 0x1000))


def _validate_alignment(alignment: int) -> None:
    if alignment <= 0 or alignment & (alignment - 1):
        raise EaArchiveError("archive alignment must be a positive power of two")
    if alignment > 0x100000:
        raise EaArchiveError(f"archive alignment is unreasonable: {alignment}")


def _align(value: int, alignment: int) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


def _reject_overlaps(ranges: list[tuple[int, int, str]]) -> None:
    ordered = sorted(ranges, key=lambda item: item[0])
    for previous, current in zip(ordered, ordered[1:], strict=False):
        if current[0] < previous[1]:
            raise EaArchiveError(
                f"overlapping member payloads: {previous[2]} and {current[2]}"
            )


def _replace_directory(
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
                raise FileExistsError(f"archive destination already exists: {destination}")
            os.replace(destination, backup)
            moved_existing = True
        os.replace(temporary, destination)
    except Exception:
        if moved_existing and destination.exists():
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
        shutil.rmtree(path)
    else:
        path.unlink()
