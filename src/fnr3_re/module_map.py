from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath

from .elf32 import Elf32Image, parse_elf32
from .iso import verify_workspace
from .manifests import load_workspace_manifest
from .psp_container import PspContainer, parse_psp_container


class ModuleMapError(ValueError):
    """Raised when an executable module cannot be identified or inventoried."""


class ModuleKind(StrEnum):
    PLAIN_ELF = "plain_elf"
    PSP_CONTAINER = "psp_container"


@dataclass(frozen=True, slots=True)
class ModuleSegment:
    index: int
    file_offset: int | None
    virtual_address: int
    file_size: int | None
    memory_size: int
    flags: int | None
    alignment: int


@dataclass(frozen=True, slots=True)
class ModuleSection:
    index: int
    name: str
    section_type: int
    flags: int
    address: int
    file_offset: int
    size: int
    nobits: bool


@dataclass(frozen=True, slots=True)
class ModuleRecord:
    path: str
    kind: ModuleKind
    file_size: int
    sha256: str
    iso_file_offset: int | None
    iso_lba: int | None
    module_name: str | None
    entry_point: int
    image_base: int | None
    runtime_base: int | None
    stored_elf_offset: int | None
    address_mapping_status: str
    object_type: int | None
    elf_flags: int | None
    bss_size: int
    container_elf_size: int | None
    container_psp_size: int | None
    module_info_offset: int | None
    segments: tuple[ModuleSegment, ...]
    sections: tuple[ModuleSection, ...]
    unresolved: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ModuleMap:
    revision_id: str
    modules: tuple[ModuleRecord, ...]
    schema_version: int = 1

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


def inspect_module(
    path: str,
    payload: bytes | bytearray | memoryview,
    *,
    iso_file_offset: int | None = None,
    iso_lba: int | None = None,
) -> ModuleRecord:
    data = bytes(payload)
    if data.startswith(b"\x7fELF"):
        return _record_plain_elf(
            path,
            data,
            parse_elf32(data),
            iso_file_offset=iso_file_offset,
            iso_lba=iso_lba,
        )
    if data.startswith(b"~PSP"):
        return _record_psp_container(
            path,
            data,
            parse_psp_container(data),
            iso_file_offset=iso_file_offset,
            iso_lba=iso_lba,
        )
    raise ModuleMapError(f"unsupported executable module format: {path}")


def build_repository_module_map(root: Path) -> ModuleMap:
    modules = tuple(
        inspect_module(path.name, path.read_bytes())
        for path in (root / "BOOT.BIN", root / "EBOOT.BIN")
    )
    return ModuleMap(revision_id="tracked-repository-samples", modules=modules)


def build_workspace_module_map(workspace: Path) -> ModuleMap:
    validation = verify_workspace(workspace)
    if not validation.valid:
        raise ModuleMapError(
            "workspace validation failed: " + "; ".join(validation.diagnostics)
        )
    manifest = load_workspace_manifest(workspace / "manifests" / "workspace.json")
    candidates = [
        entry
        for entry in manifest.files
        if entry.classification
        in {"main_executable", "packed_executable", "prx_module"}
    ]
    modules: list[ModuleRecord] = []
    for entry in candidates:
        path = _workspace_path(workspace / "original", entry.path)
        payload = path.read_bytes()
        observed_hash = hashlib.sha256(payload).hexdigest()
        if observed_hash != entry.sha256:
            raise ModuleMapError(
                f"module hash differs from workspace manifest: {entry.path}"
            )
        modules.append(
            inspect_module(
                entry.path,
                payload,
                iso_file_offset=entry.offset,
                iso_lba=entry.lba,
            )
        )
    return ModuleMap(revision_id=manifest.revision_id, modules=tuple(modules))


def _record_plain_elf(
    path: str,
    payload: bytes,
    image: Elf32Image,
    *,
    iso_file_offset: int | None,
    iso_lba: int | None,
) -> ModuleRecord:
    segments = tuple(
        ModuleSegment(
            index=segment.index,
            file_offset=segment.file_offset,
            virtual_address=segment.virtual_address,
            file_size=segment.file_size,
            memory_size=segment.memory_size,
            flags=segment.flags,
            alignment=segment.alignment,
        )
        for segment in image.load_segments
    )
    sections = tuple(
        ModuleSection(
            index=section.index,
            name=section.name,
            section_type=section.section_type,
            flags=section.flags,
            address=section.address,
            file_offset=section.file_offset,
            size=section.size,
            nobits=section.is_nobits,
        )
        for section in image.sections
    )
    bss_size = sum(section.size for section in image.sections if section.is_nobits)
    return ModuleRecord(
        path=path,
        kind=ModuleKind.PLAIN_ELF,
        file_size=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        iso_file_offset=iso_file_offset,
        iso_lba=iso_lba,
        module_name=None,
        entry_point=image.header.entry_point,
        image_base=image.image_base,
        runtime_base=None,
        stored_elf_offset=0,
        address_mapping_status=(
            "static_elf_mapped_runtime_base_pending"
            if iso_file_offset is not None
            else "static_elf_mapped_iso_offset_pending"
        ),
        object_type=image.header.object_type,
        elf_flags=image.header.flags,
        bss_size=bss_size,
        container_elf_size=None,
        container_psp_size=None,
        module_info_offset=None,
        segments=segments,
        sections=sections,
        unresolved=(
            "runtime load base",
            "module lifetime and owner",
            "import and export ownership",
        ),
    )


def _record_psp_container(
    path: str,
    payload: bytes,
    container: PspContainer,
    *,
    iso_file_offset: int | None,
    iso_lba: int | None,
) -> ModuleRecord:
    segments = tuple(
        ModuleSegment(
            index=index,
            file_offset=None,
            virtual_address=container.segment_addresses[index],
            file_size=None,
            memory_size=container.segment_sizes[index],
            flags=None,
            alignment=container.segment_alignments[index],
        )
        for index in range(container.segment_count)
    )
    return ModuleRecord(
        path=path,
        kind=ModuleKind.PSP_CONTAINER,
        file_size=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        iso_file_offset=iso_file_offset,
        iso_lba=iso_lba,
        module_name=container.module_name,
        entry_point=container.entry_point,
        image_base=None,
        runtime_base=None,
        stored_elf_offset=None,
        address_mapping_status="packed_container_requires_decrypted_elf",
        object_type=None,
        elf_flags=None,
        bss_size=container.bss_size,
        container_elf_size=container.elf_size,
        container_psp_size=container.psp_size,
        module_info_offset=container.module_info_offset,
        segments=segments,
        sections=(),
        unresolved=(
            "decrypted ELF correspondence",
            "runtime load base",
            "module lifetime and owner",
            "import and export ownership",
        ),
    )


def _workspace_path(root: Path, path: str) -> Path:
    pure = PurePosixPath(path)
    candidate = root.joinpath(*pure.parts)
    root_resolved = root.resolve()
    candidate_resolved = candidate.resolve(strict=False)
    if not candidate_resolved.is_relative_to(root_resolved):
        raise ModuleMapError(f"workspace path escapes root: {path}")
    return candidate
