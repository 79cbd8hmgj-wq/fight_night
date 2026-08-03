from __future__ import annotations

import hashlib
import json
import os
import uuid
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, cast

from .iso import scan_iso, verify_workspace
from .manifests import ManifestFile, WorkspaceManifest, load_workspace_manifest
from .revision import ReferenceRevision, validate_image

_BUILD_PLAN_SCHEMA = 1
_BUILD_REPORT_SCHEMA = 1
_COPY_CHUNK_SIZE = 1024 * 1024


class BuildError(ValueError):
    """Raised when a build plan or workspace cannot safely produce an ISO."""


@dataclass(frozen=True, slots=True)
class BytePatch:
    patch_id: str
    path: str
    file_offset: int
    expected: bytes
    replacement: bytes

    def __post_init__(self) -> None:
        if not self.patch_id.strip():
            raise ValueError("patch id is required")
        _validate_relative_path(self.path)
        if self.file_offset < 0:
            raise ValueError("patch file_offset must be non-negative")
        if not self.expected:
            raise ValueError("patch expected bytes are required")
        if not self.replacement:
            raise ValueError("patch replacement bytes are required")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> BytePatch:
        return cls(
            patch_id=_required_string(payload, "id"),
            path=_required_string(payload, "path"),
            file_offset=_required_int(payload, "file_offset"),
            expected=_required_hex(payload, "expected_hex"),
            replacement=_required_hex(payload, "replacement_hex"),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "expected_hex": self.expected.hex(),
            "file_offset": self.file_offset,
            "id": self.patch_id,
            "path": self.path,
            "replacement_hex": self.replacement.hex(),
        }


@dataclass(frozen=True, slots=True)
class BuildPlan:
    revision_id: str
    patches: tuple[BytePatch, ...]
    schema_version: int = _BUILD_PLAN_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_version != _BUILD_PLAN_SCHEMA:
            raise ValueError(f"unsupported build plan schema: {self.schema_version}")
        if not self.revision_id.strip():
            raise ValueError("build plan revision_id is required")
        patch_ids = [patch.patch_id for patch in self.patches]
        if len(patch_ids) != len(set(patch_ids)):
            raise ValueError("duplicate patch id")

    @classmethod
    def empty(cls, revision_id: str) -> BuildPlan:
        return cls(revision_id=revision_id, patches=())

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> BuildPlan:
        patches_payload = payload.get("patches")
        if not isinstance(patches_payload, list):
            raise ValueError("patches must be a list")
        return cls(
            revision_id=_required_string(payload, "revision_id"),
            patches=tuple(
                BytePatch.from_mapping(_required_mapping(item, "patch"))
                for item in patches_payload
            ),
            schema_version=_required_int(payload, "schema_version"),
        )

    def to_json(self) -> str:
        return (
            json.dumps(
                {
                    "patches": [patch.to_mapping() for patch in self.patches],
                    "revision_id": self.revision_id,
                    "schema_version": self.schema_version,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )


@dataclass(frozen=True, slots=True)
class ChangedRange:
    patch_id: str
    file_offset: int
    iso_offset: int
    length: int
    expected_hex: str
    replacement_hex: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "expected_hex": self.expected_hex,
            "file_offset": self.file_offset,
            "iso_offset": self.iso_offset,
            "length": self.length,
            "patch_id": self.patch_id,
            "replacement_hex": self.replacement_hex,
        }


@dataclass(frozen=True, slots=True)
class ChangedFile:
    path: str
    source_sha256: str
    output_sha256: str
    ranges: tuple[ChangedRange, ...]

    def to_mapping(self) -> dict[str, object]:
        return {
            "output_sha256": self.output_sha256,
            "path": self.path,
            "ranges": [changed_range.to_mapping() for changed_range in self.ranges],
            "source_sha256": self.source_sha256,
        }


@dataclass(frozen=True, slots=True)
class BuildReport:
    revision_id: str
    source_sha256: str
    plan_sha256: str
    output_sha256: str
    output_size: int
    no_change: bool
    changed_files: tuple[ChangedFile, ...]
    schema_version: int = _BUILD_REPORT_SCHEMA

    def to_json(self) -> str:
        return (
            json.dumps(
                {
                    "changed_files": [item.to_mapping() for item in self.changed_files],
                    "no_change": self.no_change,
                    "output_sha256": self.output_sha256,
                    "output_size": self.output_size,
                    "plan_sha256": self.plan_sha256,
                    "revision_id": self.revision_id,
                    "schema_version": self.schema_version,
                    "source_sha256": self.source_sha256,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )


@dataclass(frozen=True, slots=True)
class _PreparedFile:
    manifest: ManifestFile
    payload: bytes
    changed_file: ChangedFile


def load_build_plan(path: Path) -> BuildPlan:
    try:
        decoded = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(decoded, Mapping):
            raise ValueError("root must be an object")
        return BuildPlan.from_mapping(cast(Mapping[str, Any], decoded))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"invalid build plan: {exc}") from exc


def rebuild_image(
    reference_image: Path,
    workspace: Path,
    output: Path,
    revision: ReferenceRevision,
    plan: BuildPlan,
    *,
    force: bool = False,
    report_path: Path | None = None,
) -> BuildReport:
    """Reconstruct the exact ISO layout and apply guarded fixed-size byte patches."""

    output = output.absolute()
    selected_report_path = (
        report_path.absolute()
        if report_path is not None
        else output.with_name(f"{output.name}.build.json")
    )
    _validate_output_paths(
        reference_image, workspace, output, selected_report_path
    )
    _require_available_output(output, selected_report_path, force=force)

    validation = validate_image(reference_image, revision)
    if not validation.valid:
        raise BuildError(
            "reference image validation failed: " + "; ".join(validation.diagnostics)
        )
    workspace_validation = verify_workspace(workspace)
    if not workspace_validation.valid:
        raise BuildError(
            "workspace validation failed: " + "; ".join(workspace_validation.diagnostics)
        )

    manifest = load_workspace_manifest(workspace / "manifests" / "workspace.json")
    _validate_manifest_identity(manifest, revision)
    if plan.revision_id != revision.revision_id:
        raise BuildError(
            f"build plan revision mismatch: expected {revision.revision_id}, "
            f"got {plan.revision_id}"
        )
    _verify_reference_file_extents(reference_image, manifest)
    prepared_files = _prepare_patches(workspace, manifest, plan)

    output.parent.mkdir(parents=True, exist_ok=True)
    selected_report_path.parent.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    temporary_output = output.with_name(f".{output.name}.tmp-{token}")
    temporary_report = selected_report_path.with_name(
        f".{selected_report_path.name}.tmp-{token}"
    )

    try:
        _copy_file(reference_image, temporary_output)
        if prepared_files:
            with temporary_output.open("r+b") as stream:
                for prepared in prepared_files:
                    stream.seek(prepared.manifest.offset)
                    stream.write(prepared.payload)
                stream.flush()
                os.fsync(stream.fileno())
        _validate_rebuilt_layout(temporary_output, manifest)
        output_sha256 = _hash_file(temporary_output)
        no_change = not prepared_files
        if no_change and output_sha256 != revision.iso_sha256:
            raise BuildError(
                "no-change rebuild hash mismatch: "
                f"expected {revision.iso_sha256}, got {output_sha256}"
            )

        report = BuildReport(
            revision_id=revision.revision_id,
            source_sha256=revision.iso_sha256,
            plan_sha256=hashlib.sha256(plan.to_json().encode("utf-8")).hexdigest(),
            output_sha256=output_sha256,
            output_size=temporary_output.stat().st_size,
            no_change=no_change,
            changed_files=tuple(item.changed_file for item in prepared_files),
        )
        temporary_report.write_text(report.to_json(), encoding="utf-8")
        _replace_output_pair(
            temporary_output,
            output,
            temporary_report,
            selected_report_path,
            force=force,
        )
        return report
    except Exception:
        temporary_output.unlink(missing_ok=True)
        temporary_report.unlink(missing_ok=True)
        raise


def _prepare_patches(
    workspace: Path,
    manifest: WorkspaceManifest,
    plan: BuildPlan,
) -> tuple[_PreparedFile, ...]:
    manifest_by_path = {entry.path.casefold(): entry for entry in manifest.files}
    patches_by_path: dict[str, list[BytePatch]] = defaultdict(list)
    exact_paths: dict[str, str] = {}
    for patch in plan.patches:
        canonical = patch.path.casefold()
        entry = manifest_by_path.get(canonical)
        if entry is None:
            raise BuildError(f"patch file does not exist: {patch.path}")
        exact_paths[canonical] = entry.path
        patches_by_path[canonical].append(patch)

    prepared: list[_PreparedFile] = []
    for canonical in sorted(patches_by_path, key=lambda key: manifest_by_path[key].order):
        entry = manifest_by_path[canonical]
        original_path = _workspace_path(workspace / "original", exact_paths[canonical])
        original = original_path.read_bytes()
        if len(original) != entry.size:
            raise BuildError(f"workspace file size changed before build: {entry.path}")
        if hashlib.sha256(original).hexdigest() != entry.sha256:
            raise BuildError(f"workspace file hash changed before build: {entry.path}")

        patches = sorted(
            patches_by_path[canonical],
            key=lambda patch: (patch.file_offset, patch.patch_id),
        )
        previous_end = -1
        changed_ranges: list[ChangedRange] = []
        modified = bytearray(original)
        for patch in patches:
            if len(patch.expected) != len(patch.replacement):
                raise BuildError(f"replacement length differs for patch: {patch.patch_id}")
            patch_end = patch.file_offset + len(patch.expected)
            if patch_end > len(original):
                raise BuildError(f"patch range is outside file: {patch.patch_id}")
            if patch.file_offset < previous_end:
                raise BuildError(f"overlapping patches in {entry.path}")
            observed = original[patch.file_offset:patch_end]
            if observed != patch.expected:
                raise BuildError(
                    f"expected original bytes differ for patch {patch.patch_id}: "
                    f"expected {patch.expected.hex()}, got {observed.hex()}"
                )
            modified[patch.file_offset:patch_end] = patch.replacement
            changed_ranges.append(
                ChangedRange(
                    patch_id=patch.patch_id,
                    file_offset=patch.file_offset,
                    iso_offset=entry.offset + patch.file_offset,
                    length=len(patch.expected),
                    expected_hex=patch.expected.hex(),
                    replacement_hex=patch.replacement.hex(),
                )
            )
            previous_end = patch_end

        output_payload = bytes(modified)
        prepared.append(
            _PreparedFile(
                manifest=entry,
                payload=output_payload,
                changed_file=ChangedFile(
                    path=entry.path,
                    source_sha256=entry.sha256,
                    output_sha256=hashlib.sha256(output_payload).hexdigest(),
                    ranges=tuple(changed_ranges),
                ),
            )
        )
    return tuple(prepared)


def _verify_reference_file_extents(reference: Path, manifest: WorkspaceManifest) -> None:
    with reference.open("rb") as stream:
        for entry in manifest.files:
            stream.seek(entry.offset)
            payload = stream.read(entry.size)
            if len(payload) != entry.size:
                raise BuildError(f"reference file extent is truncated: {entry.path}")
            observed = hashlib.sha256(payload).hexdigest()
            if observed != entry.sha256:
                raise BuildError(
                    f"reference file extent hash mismatch: {entry.path}; "
                    f"expected {entry.sha256}, got {observed}"
                )


def _validate_manifest_identity(
    manifest: WorkspaceManifest,
    revision: ReferenceRevision,
) -> None:
    if manifest.revision_id != revision.revision_id:
        raise BuildError(
            f"workspace revision mismatch: expected {revision.revision_id}, "
            f"got {manifest.revision_id}"
        )
    if manifest.source_iso_size != revision.iso_size:
        raise BuildError("workspace source ISO size does not match locked revision")
    if manifest.source_iso_sha256 != revision.iso_sha256:
        raise BuildError("workspace source ISO hash does not match locked revision")


def _validate_rebuilt_layout(image: Path, manifest: WorkspaceManifest) -> None:
    inventory = scan_iso(image)
    observed_files = [
        (entry.path, entry.offset, entry.size, entry.order) for entry in inventory.files
    ]
    expected_files = [
        (entry.path, entry.offset, entry.size, entry.order) for entry in manifest.files
    ]
    if observed_files != expected_files:
        raise BuildError("rebuilt ISO file layout differs from workspace manifest")
    observed_directories = [
        (entry.path, entry.offset, entry.size, entry.order)
        for entry in inventory.directories
    ]
    expected_directories = [
        (entry.path, entry.offset, entry.size, entry.order)
        for entry in manifest.directories
    ]
    if observed_directories != expected_directories:
        raise BuildError("rebuilt ISO directory layout differs from workspace manifest")


def _validate_output_paths(
    reference: Path,
    workspace: Path,
    output: Path,
    report: Path,
) -> None:
    reference_resolved = reference.resolve()
    output_resolved = output.resolve(strict=False)
    report_resolved = report.resolve(strict=False)
    workspace_resolved = workspace.resolve()
    if output_resolved == reference_resolved:
        raise BuildError("output path must not replace the reference image")
    if report_resolved == reference_resolved:
        raise BuildError("report path must not replace the reference image")
    if output_resolved == report_resolved:
        raise BuildError("output and report paths must differ")
    for label, candidate in (("output", output_resolved), ("report", report_resolved)):
        if os.path.commonpath((str(workspace_resolved), str(candidate))) == str(
            workspace_resolved
        ):
            raise BuildError(f"{label} path must be outside workspace")


def _require_available_output(output: Path, report: Path, *, force: bool) -> None:
    if force:
        return
    existing = [str(path) for path in (output, report) if path.exists()]
    if existing:
        raise FileExistsError("build output already exists: " + ", ".join(existing))


def _replace_output_pair(
    temporary_output: Path,
    output: Path,
    temporary_report: Path,
    report: Path,
    *,
    force: bool,
) -> None:
    token = uuid.uuid4().hex
    output_backup = output.with_name(f".{output.name}.bak-{token}")
    report_backup = report.with_name(f".{report.name}.bak-{token}")
    output_moved = False
    report_moved = False
    try:
        if output.exists():
            if not force:
                raise FileExistsError(f"build output already exists: {output}")
            os.replace(output, output_backup)
            output_moved = True
        if report.exists():
            if not force:
                raise FileExistsError(f"build report already exists: {report}")
            os.replace(report, report_backup)
            report_moved = True
        os.replace(temporary_output, output)
        os.replace(temporary_report, report)
    except Exception:
        output.unlink(missing_ok=True)
        report.unlink(missing_ok=True)
        if output_moved and output_backup.exists():
            os.replace(output_backup, output)
        if report_moved and report_backup.exists():
            os.replace(report_backup, report)
        raise
    finally:
        output_backup.unlink(missing_ok=True)
        report_backup.unlink(missing_ok=True)


def _copy_file(source: Path, destination: Path) -> None:
    with source.open("rb") as source_stream, destination.open("xb") as output_stream:
        while chunk := source_stream.read(_COPY_CHUNK_SIZE):
            output_stream.write(chunk)
        output_stream.flush()
        os.fsync(output_stream.fileno())


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(_COPY_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def _workspace_path(root: Path, path: str) -> Path:
    pure = PurePosixPath(path)
    candidate = root.joinpath(*pure.parts)
    root_resolved = root.resolve()
    candidate_resolved = candidate.resolve(strict=False)
    if os.path.commonpath((str(root_resolved), str(candidate_resolved))) != str(root_resolved):
        raise BuildError(f"workspace path escapes root: {path}")
    return candidate


def _validate_relative_path(path: str) -> None:
    pure = PurePosixPath(path)
    if pure.is_absolute() or not pure.parts:
        raise ValueError(f"invalid patch path: {path}")
    if any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError(f"invalid patch path: {path}")
    if "\\" in path or "\x00" in path:
        raise ValueError(f"invalid patch path: {path}")


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


def _required_hex(payload: Mapping[str, Any], key: str) -> bytes:
    value = _required_string(payload, key)
    try:
        decoded = bytes.fromhex(value)
    except ValueError as exc:
        raise ValueError(f"{key} must be even-length hexadecimal") from exc
    if not decoded or len(value) != len(decoded) * 2:
        raise ValueError(f"{key} must be even-length hexadecimal")
    return decoded


def _required_mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return cast(Mapping[str, Any], value)
