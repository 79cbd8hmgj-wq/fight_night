from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast

from .revision import hash_file

_LOCKED_REVISION_ID = "ULUS10066-v1.00"
_SHA1_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_ROLES = frozenset({"executable", "game_data", "metadata", "padding"})


class RuntimeImageError(ValueError):
    """Raised when repository runtime-image preparation cannot be trusted."""


@dataclass(frozen=True, slots=True)
class RuntimePayloadEntry:
    source: PurePosixPath
    destination: PurePosixPath
    size: int
    git_blob_sha1: str
    role: str
    sha256: str | None = None


@dataclass(frozen=True, slots=True)
class RuntimePayloadManifest:
    schema_version: int
    revision_id: str
    entries: tuple[RuntimePayloadEntry, ...]
    sha256: str


@dataclass(frozen=True, slots=True)
class VerifiedRuntimePayloadEntry:
    source_path: Path
    destination: PurePosixPath
    size: int
    sha256: str
    role: str


def load_runtime_payload_manifest(path: Path) -> RuntimePayloadManifest:
    if path.is_symlink():
        raise RuntimeImageError("runtime payload manifest must not be a symlink")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RuntimeImageError(f"unable to read runtime payload manifest: {exc}") from exc
    try:
        decoded = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeImageError(f"invalid runtime payload manifest JSON: {exc}") from exc
    if not isinstance(decoded, dict):
        raise RuntimeImageError("runtime payload manifest root must be an object")
    root = cast(dict[str, object], decoded)

    schema_version = _required_int(root, "schema_version")
    if schema_version != 1:
        raise RuntimeImageError(f"unsupported runtime payload manifest schema: {schema_version}")

    revision_id = _required_str(root, "revision_id")
    if revision_id != _LOCKED_REVISION_ID:
        raise RuntimeImageError(
            f"runtime payload manifest revision must be {_LOCKED_REVISION_ID}, got {revision_id}"
        )

    raw_entries = root.get("entries")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise RuntimeImageError("runtime payload manifest entries must be a non-empty list")

    entries: list[RuntimePayloadEntry] = []
    sources: set[str] = set()
    destinations: set[str] = set()
    for index, value in enumerate(raw_entries):
        if not isinstance(value, dict):
            raise RuntimeImageError(f"runtime payload entry {index} must be an object")
        item = cast(dict[str, object], value)
        source = _safe_relative_path(_required_str(item, "source"), "source")
        destination = _safe_relative_path(
            _required_str(item, "destination"),
            "destination",
        )
        source_key = source.as_posix().casefold()
        destination_key = destination.as_posix().casefold()
        if source_key in sources:
            raise RuntimeImageError(f"duplicate source path: {source.as_posix()}")
        if destination_key in destinations:
            raise RuntimeImageError(f"duplicate destination path: {destination.as_posix()}")
        sources.add(source_key)
        destinations.add(destination_key)

        size = _required_int(item, "size")
        if size <= 0:
            raise RuntimeImageError("runtime payload entry size must be positive")
        git_blob_sha1 = _required_str(item, "git_blob_sha1")
        if _SHA1_PATTERN.fullmatch(git_blob_sha1) is None:
            raise RuntimeImageError("runtime payload entry git_blob_sha1 must be lowercase SHA-1")
        role = _required_str(item, "role")
        if role not in _ALLOWED_ROLES:
            raise RuntimeImageError(f"unsupported runtime payload role: {role}")
        sha256_value = item.get("sha256")
        sha256: str | None
        if sha256_value is None:
            sha256 = None
        elif isinstance(sha256_value, str) and _SHA256_PATTERN.fullmatch(sha256_value):
            sha256 = sha256_value
        else:
            raise RuntimeImageError("runtime payload entry sha256 must be lowercase SHA-256")

        entries.append(
            RuntimePayloadEntry(
                source=source,
                destination=destination,
                size=size,
                git_blob_sha1=git_blob_sha1,
                role=role,
                sha256=sha256,
            )
        )

    return RuntimePayloadManifest(
        schema_version=schema_version,
        revision_id=revision_id,
        entries=tuple(entries),
        sha256=hashlib.sha256(raw).hexdigest(),
    )


def verify_runtime_payload(
    repository_root: Path,
    manifest: RuntimePayloadManifest,
) -> tuple[VerifiedRuntimePayloadEntry, ...]:
    if manifest.revision_id != _LOCKED_REVISION_ID:
        raise RuntimeImageError(
            "runtime payload manifest revision is not the locked Fight Night revision"
        )
    if repository_root.is_symlink():
        raise RuntimeImageError("repository root must not be a symlink")
    try:
        root = repository_root.resolve(strict=True)
    except OSError as exc:
        raise RuntimeImageError(f"repository root does not exist: {repository_root}") from exc
    if not root.is_dir():
        raise RuntimeImageError("repository root must be a directory")

    verified: list[VerifiedRuntimePayloadEntry] = []
    for entry in manifest.entries:
        source_path = _resolve_repository_file(root, entry.source)
        if source_path.stat().st_size != entry.size:
            raise RuntimeImageError(
                f"runtime payload size mismatch for {entry.source.as_posix()}"
            )
        sha256 = hash_file(source_path)
        if entry.sha256 is not None and sha256 != entry.sha256:
            raise RuntimeImageError(
                f"runtime payload SHA-256 mismatch for {entry.source.as_posix()}"
            )
        git_blob_sha1 = _git_blob_sha1(root, entry.source)
        if git_blob_sha1 != entry.git_blob_sha1:
            raise RuntimeImageError(
                f"runtime payload Git blob mismatch for {entry.source.as_posix()}"
            )
        verified.append(
            VerifiedRuntimePayloadEntry(
                source_path=source_path,
                destination=entry.destination,
                size=entry.size,
                sha256=sha256,
                role=entry.role,
            )
        )
    return tuple(verified)


def _required_str(mapping: dict[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise RuntimeImageError(f"runtime payload manifest {key} must be a non-empty string")
    return value


def _required_int(mapping: dict[str, object], key: str) -> int:
    value = mapping.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise RuntimeImageError(f"runtime payload manifest {key} must be an integer")
    return value


def _safe_relative_path(value: str, label: str) -> PurePosixPath:
    if not value or "\\" in value:
        raise RuntimeImageError(f"runtime payload {label} path is invalid")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in value.split("/")):
        raise RuntimeImageError(f"runtime payload {label} path must be safe and relative")
    return path


def _resolve_repository_file(root: Path, relative: PurePosixPath) -> Path:
    candidate = root.joinpath(*relative.parts)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise RuntimeImageError(
                f"runtime payload source path contains a symlink: {relative.as_posix()}"
            )
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise RuntimeImageError(
            f"runtime payload source is missing: {relative.as_posix()}"
        ) from exc
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise RuntimeImageError(
            f"runtime payload source escapes repository root: {relative.as_posix()}"
        ) from exc
    if not resolved.is_file():
        raise RuntimeImageError(f"runtime payload source is not a file: {relative.as_posix()}")
    return resolved


def _git_blob_sha1(root: Path, relative: PurePosixPath) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "hash-object", "--no-filters", "--", relative.as_posix()],
            check=False,
            capture_output=True,
            text=True,
            timeout=30.0,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeImageError("unable to execute git hash-object for runtime payload") from exc
    digest = result.stdout.strip()
    if result.returncode != 0 or _SHA1_PATTERN.fullmatch(digest) is None:
        diagnostic = result.stderr.strip()
        suffix = f": {diagnostic}" if diagnostic else ""
        raise RuntimeImageError(f"git hash-object failed for {relative.as_posix()}{suffix}")
    return digest
