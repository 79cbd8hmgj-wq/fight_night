from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path, PurePosixPath
from typing import cast
from unittest import mock

import pycdlib

from .psp_sfo import build_runtime_param_sfo
from .revision import ReferenceRevision, hash_file

_LOCKED_REVISION_ID = "ULUS10066-v1.00"
_SHA1_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_ROLES = frozenset({"executable", "game_data", "metadata", "padding"})
_RUNTIME_ISO_NAME = "fight-night-runtime.iso"
_RUNTIME_REPORT_NAME = "runtime-image.json"
_RUNTIME_SOURCE_MODE = "repository_runtime_image"
_RUNTIME_VOLUME_ID = "FNR3_ULUS10066"
_PYCDLIB_VERSION = "1.21.0"
_FIXED_MASTERING_TIME = 946684800.0


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


@dataclass(frozen=True, slots=True)
class RuntimeImageFileReport:
    destination: str
    size: int
    sha256: str
    role: str
    generated: bool


@dataclass(frozen=True, slots=True)
class RuntimeImageReport:
    schema_version: int
    revision_id: str
    source_mode: str
    retail_iso_sha256: str
    payload_manifest_sha256: str
    boot_sha256: str
    eboot_sha256: str
    generated_metadata: tuple[tuple[str, str], ...]
    runtime_iso_size: int
    runtime_iso_sha256: str
    deterministic: bool
    files: tuple[RuntimeImageFileReport, ...]

    def to_json(self) -> str:
        return (
            json.dumps(
                {
                    "boot_sha256": self.boot_sha256,
                    "deterministic": self.deterministic,
                    "eboot_sha256": self.eboot_sha256,
                    "files": [
                        {
                            "destination": item.destination,
                            "generated": item.generated,
                            "role": item.role,
                            "sha256": item.sha256,
                            "size": item.size,
                        }
                        for item in self.files
                    ],
                    "generated_metadata": [
                        {"destination": destination, "sha256": sha256}
                        for destination, sha256 in self.generated_metadata
                    ],
                    "payload_manifest_sha256": self.payload_manifest_sha256,
                    "retail_iso_sha256": self.retail_iso_sha256,
                    "revision_id": self.revision_id,
                    "runtime_iso_sha256": self.runtime_iso_sha256,
                    "runtime_iso_size": self.runtime_iso_size,
                    "schema_version": self.schema_version,
                    "source_mode": self.source_mode,
                },
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n"
        )


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


def prepare_runtime_image(
    repository_root: Path,
    output_root: Path,
    manifest: RuntimePayloadManifest,
    revision: ReferenceRevision,
    *,
    force: bool = False,
) -> RuntimeImageReport:
    if (
        manifest.revision_id != revision.revision_id
        or revision.revision_id != _LOCKED_REVISION_ID
    ):
        raise RuntimeImageError(
            "runtime image revision does not match the locked Fight Night revision"
        )

    verified = verify_runtime_payload(repository_root, manifest)
    boot = _required_verified_destination(verified, "PSP_GAME/SYSDIR/BOOT.BIN")
    eboot = _required_verified_destination(verified, "PSP_GAME/SYSDIR/EBOOT.BIN")
    param_sfo = build_runtime_param_sfo(revision)
    param_sha256 = hashlib.sha256(param_sfo).hexdigest()

    destination = output_root.absolute()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not force:
        raise FileExistsError(f"runtime output already exists: {destination}")

    temporary = destination.parent / f".{destination.name}.tmp-{uuid.uuid4().hex}"
    try:
        temporary.mkdir(parents=False, exist_ok=False)
        runtime_iso = temporary / _RUNTIME_ISO_NAME
        _master_runtime_iso(runtime_iso, verified, param_sfo)
        runtime_iso_size = runtime_iso.stat().st_size
        runtime_iso_sha256 = hash_file(runtime_iso)

        file_reports = [
            RuntimeImageFileReport(
                destination=entry.destination.as_posix(),
                size=entry.size,
                sha256=entry.sha256,
                role=entry.role,
                generated=False,
            )
            for entry in verified
        ]
        file_reports.append(
            RuntimeImageFileReport(
                destination="PSP_GAME/PARAM.SFO",
                size=len(param_sfo),
                sha256=param_sha256,
                role="metadata",
                generated=True,
            )
        )
        report = RuntimeImageReport(
            schema_version=1,
            revision_id=revision.revision_id,
            source_mode=_RUNTIME_SOURCE_MODE,
            retail_iso_sha256=revision.iso_sha256,
            payload_manifest_sha256=manifest.sha256,
            boot_sha256=boot.sha256,
            eboot_sha256=eboot.sha256,
            generated_metadata=(("PSP_GAME/PARAM.SFO", param_sha256),),
            runtime_iso_size=runtime_iso_size,
            runtime_iso_sha256=runtime_iso_sha256,
            deterministic=True,
            files=tuple(sorted(file_reports, key=lambda item: item.destination.casefold())),
        )
        (temporary / _RUNTIME_REPORT_NAME).write_text(report.to_json(), encoding="utf-8")

        if destination.exists():
            shutil.rmtree(destination)
        os.replace(temporary, destination)
        return report
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def _master_runtime_iso(
    output: Path,
    entries: tuple[VerifiedRuntimePayloadEntry, ...],
    param_sfo: bytes,
) -> None:
    _require_pycdlib_version()
    iso = pycdlib.PyCdlib()
    param_stream = io.BytesIO(param_sfo)
    initialized = False
    try:
        with _fixed_pycdlib_time():
            iso.new(
                interchange_level=3,
                joliet=3,
                sys_ident="PSP GAME",
                vol_ident=_RUNTIME_VOLUME_ID,
                app_ident_str="fnr3-re runtime recovery",
            )
            initialized = True
            destinations = [entry.destination for entry in entries]
            destinations.append(PurePosixPath("PSP_GAME/PARAM.SFO"))
            for directory in _runtime_directories(destinations):
                iso.add_directory(
                    iso_path=_iso_directory_path(directory),
                    joliet_path=_joliet_path(directory),
                )

            iso.add_fp(
                param_stream,
                len(param_sfo),
                iso_path=_iso_file_path(PurePosixPath("PSP_GAME/PARAM.SFO")),
                joliet_path=_joliet_path(PurePosixPath("PSP_GAME/PARAM.SFO")),
            )
            for entry in sorted(entries, key=lambda item: item.destination.as_posix().casefold()):
                iso.add_file(
                    str(entry.source_path),
                    iso_path=_iso_file_path(entry.destination),
                    joliet_path=_joliet_path(entry.destination),
                )
            iso.write(str(output))
    finally:
        if initialized:
            iso.close()


def _runtime_directories(paths: list[PurePosixPath]) -> tuple[PurePosixPath, ...]:
    directories: set[PurePosixPath] = set()
    for path in paths:
        parent = path.parent
        while parent != PurePosixPath("."):
            directories.add(parent)
            parent = parent.parent
    return tuple(
        sorted(
            directories,
            key=lambda path: (len(path.parts), path.as_posix().casefold()),
        )
    )


def _iso_directory_path(path: PurePosixPath) -> str:
    return "/" + "/".join(part.upper() for part in path.parts)


def _iso_file_path(path: PurePosixPath) -> str:
    return _iso_directory_path(path) + ";1"


def _joliet_path(path: PurePosixPath) -> str:
    return "/" + path.as_posix()


def _required_verified_destination(
    entries: tuple[VerifiedRuntimePayloadEntry, ...],
    destination: str,
) -> VerifiedRuntimePayloadEntry:
    target = destination.casefold()
    match = next(
        (entry for entry in entries if entry.destination.as_posix().casefold() == target),
        None,
    )
    if match is None:
        raise RuntimeImageError(f"runtime payload is missing required destination: {destination}")
    return match


def _require_pycdlib_version() -> None:
    try:
        observed = package_version("pycdlib")
    except PackageNotFoundError as exc:
        raise RuntimeImageError("pycdlib is not installed") from exc
    if observed != _PYCDLIB_VERSION:
        raise RuntimeImageError(
            f"runtime image mastering requires pycdlib {_PYCDLIB_VERSION}, got {observed}"
        )


@contextmanager
def _fixed_pycdlib_time() -> Iterator[None]:
    with (
        mock.patch("pycdlib.headervd.time.time", return_value=_FIXED_MASTERING_TIME),
        mock.patch("pycdlib.pycdlib.time.time", return_value=_FIXED_MASTERING_TIME),
    ):
        yield


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
