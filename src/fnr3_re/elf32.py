from __future__ import annotations

from dataclasses import dataclass
from typing import Final

ELF_HEADER_SIZE: Final = 52
PROGRAM_HEADER_SIZE: Final = 32
SECTION_HEADER_SIZE: Final = 40
PT_LOAD: Final = 1
SHT_NOBITS: Final = 8
SHT_STRTAB: Final = 3
EM_MIPS: Final = 8


class Elf32Error(ValueError):
    """Raised when an ELF32 image is malformed or unsupported."""


@dataclass(frozen=True, slots=True)
class Elf32Header:
    object_type: int
    machine: int
    version: int
    entry_point: int
    program_header_offset: int
    section_header_offset: int
    flags: int
    header_size: int
    program_header_entry_size: int
    program_header_count: int
    section_header_entry_size: int
    section_header_count: int
    section_name_table_index: int


@dataclass(frozen=True, slots=True)
class ProgramHeader:
    index: int
    segment_type: int
    file_offset: int
    virtual_address: int
    physical_address: int
    file_size: int
    memory_size: int
    flags: int
    alignment: int

    @property
    def is_load(self) -> bool:
        return self.segment_type == PT_LOAD

    @property
    def file_end(self) -> int:
        return self.file_offset + self.file_size

    @property
    def virtual_file_end(self) -> int:
        return self.virtual_address + self.file_size

    @property
    def virtual_memory_end(self) -> int:
        return self.virtual_address + self.memory_size


@dataclass(frozen=True, slots=True)
class SectionHeader:
    index: int
    name: str
    section_type: int
    flags: int
    address: int
    file_offset: int
    size: int
    link: int
    info: int
    alignment: int
    entry_size: int

    @property
    def is_nobits(self) -> bool:
        return self.section_type == SHT_NOBITS


@dataclass(frozen=True, slots=True)
class Elf32Image:
    header: Elf32Header
    program_headers: tuple[ProgramHeader, ...]
    sections: tuple[SectionHeader, ...]
    source_size: int

    @property
    def load_segments(self) -> tuple[ProgramHeader, ...]:
        return tuple(segment for segment in self.program_headers if segment.is_load)

    @property
    def image_base(self) -> int:
        segments = self.load_segments
        if not segments:
            raise Elf32Error("ELF has no load segments")
        return min(segment.virtual_address for segment in segments)

    def virtual_to_file_offset(self, address: int, *, size: int = 1) -> int:
        _validate_address_range(address, size)
        file_backed: list[ProgramHeader] = []
        memory_backed: list[ProgramHeader] = []
        end = address + size
        for segment in self.load_segments:
            if (
                segment.virtual_address <= address
                and end <= segment.virtual_memory_end
            ):
                memory_backed.append(segment)
                if end <= segment.virtual_file_end:
                    file_backed.append(segment)
        if len(file_backed) == 1:
            segment = file_backed[0]
            return segment.file_offset + address - segment.virtual_address
        if len(file_backed) > 1:
            raise Elf32Error(f"virtual address 0x{address:x} has ambiguous file mappings")
        if memory_backed:
            raise Elf32Error(f"virtual address 0x{address:x} is not backed by file data")
        raise Elf32Error(f"virtual address 0x{address:x} is not mapped by a load segment")

    def file_offset_to_virtual(self, file_offset: int, *, size: int = 1) -> int:
        _validate_address_range(file_offset, size)
        end = file_offset + size
        matches = [
            segment
            for segment in self.load_segments
            if segment.file_offset <= file_offset and end <= segment.file_end
        ]
        if len(matches) == 1:
            segment = matches[0]
            return segment.virtual_address + file_offset - segment.file_offset
        if len(matches) > 1:
            raise Elf32Error(f"file offset 0x{file_offset:x} has ambiguous load mappings")
        raise Elf32Error(f"file offset 0x{file_offset:x} is not mapped by a load segment")

    def virtual_to_module_relative(self, address: int) -> int:
        if address < self.image_base:
            raise Elf32Error(
                f"virtual address 0x{address:x} is below image base 0x{self.image_base:x}"
            )
        return address - self.image_base

    def module_relative_to_virtual(self, address: int) -> int:
        if address < 0:
            raise Elf32Error("module-relative address must be non-negative")
        return self.image_base + address


def parse_elf32(payload: bytes | bytearray | memoryview) -> Elf32Image:
    data = bytes(payload)
    if len(data) < ELF_HEADER_SIZE:
        raise Elf32Error("ELF header is truncated")
    if data[0:4] != b"\x7fELF":
        raise Elf32Error("ELF magic is invalid")
    if data[4] != 1:
        raise Elf32Error(f"unsupported ELF class: {data[4]}")
    if data[5] != 1:
        raise Elf32Error(f"unsupported ELF endianness: {data[5]}")
    if data[6] != 1:
        raise Elf32Error(f"unsupported ELF identification version: {data[6]}")

    header = Elf32Header(
        object_type=_u16(data, 16),
        machine=_u16(data, 18),
        version=_u32(data, 20),
        entry_point=_u32(data, 24),
        program_header_offset=_u32(data, 28),
        section_header_offset=_u32(data, 32),
        flags=_u32(data, 36),
        header_size=_u16(data, 40),
        program_header_entry_size=_u16(data, 42),
        program_header_count=_u16(data, 44),
        section_header_entry_size=_u16(data, 46),
        section_header_count=_u16(data, 48),
        section_name_table_index=_u16(data, 50),
    )
    _validate_header(header, len(data))

    program_headers = tuple(
        _parse_program_header(
            data,
            index,
            header.program_header_offset + index * header.program_header_entry_size,
        )
        for index in range(header.program_header_count)
    )
    _validate_program_headers(program_headers, len(data))

    raw_sections = tuple(
        _parse_raw_section_header(
            data,
            index,
            header.section_header_offset + index * header.section_header_entry_size,
        )
        for index in range(header.section_header_count)
    )
    _validate_raw_sections(raw_sections, len(data))
    names = _read_section_names(data, header, raw_sections)
    sections = tuple(
        SectionHeader(
            index=raw.index,
            name=names[raw.index],
            section_type=raw.section_type,
            flags=raw.flags,
            address=raw.address,
            file_offset=raw.file_offset,
            size=raw.size,
            link=raw.link,
            info=raw.info,
            alignment=raw.alignment,
            entry_size=raw.entry_size,
        )
        for raw in raw_sections
    )

    image = Elf32Image(
        header=header,
        program_headers=program_headers,
        sections=sections,
        source_size=len(data),
    )
    if not image.load_segments:
        raise Elf32Error("ELF has no load segments")
    return image


@dataclass(frozen=True, slots=True)
class _RawSectionHeader:
    index: int
    name_offset: int
    section_type: int
    flags: int
    address: int
    file_offset: int
    size: int
    link: int
    info: int
    alignment: int
    entry_size: int


def _validate_header(header: Elf32Header, file_size: int) -> None:
    if header.machine != EM_MIPS:
        raise Elf32Error(f"unsupported ELF machine: {header.machine}")
    if header.version != 1:
        raise Elf32Error(f"unsupported ELF version: {header.version}")
    if header.header_size != ELF_HEADER_SIZE:
        raise Elf32Error(f"invalid ELF header size: {header.header_size}")
    if header.program_header_count:
        if header.program_header_entry_size != PROGRAM_HEADER_SIZE:
            raise Elf32Error(
                "invalid ELF program-header entry size: "
                f"{header.program_header_entry_size}"
            )
        _validate_table(
            header.program_header_offset,
            header.program_header_entry_size,
            header.program_header_count,
            file_size,
            "program table",
        )
    elif header.program_header_entry_size not in {0, PROGRAM_HEADER_SIZE}:
        raise Elf32Error(
            "invalid ELF program-header entry size: "
            f"{header.program_header_entry_size}"
        )
    if header.section_header_count:
        if header.section_header_entry_size != SECTION_HEADER_SIZE:
            raise Elf32Error(
                "invalid ELF section-header entry size: "
                f"{header.section_header_entry_size}"
            )
        _validate_table(
            header.section_header_offset,
            header.section_header_entry_size,
            header.section_header_count,
            file_size,
            "section table",
        )
        if header.section_name_table_index >= header.section_header_count:
            raise Elf32Error(
                "ELF section-name table index is outside the section table"
            )
    elif header.section_name_table_index != 0:
        raise Elf32Error("ELF section-name index is set without a section table")


def _parse_program_header(data: bytes, index: int, offset: int) -> ProgramHeader:
    return ProgramHeader(
        index=index,
        segment_type=_u32(data, offset),
        file_offset=_u32(data, offset + 4),
        virtual_address=_u32(data, offset + 8),
        physical_address=_u32(data, offset + 12),
        file_size=_u32(data, offset + 16),
        memory_size=_u32(data, offset + 20),
        flags=_u32(data, offset + 24),
        alignment=_u32(data, offset + 28),
    )


def _validate_program_headers(
    headers: tuple[ProgramHeader, ...], file_size: int
) -> None:
    load_ranges: list[tuple[int, int, int]] = []
    for header in headers:
        if header.file_size > header.memory_size:
            raise Elf32Error(
                f"program header {header.index} file size exceeds memory size"
            )
        if header.file_offset > file_size or header.file_size > file_size - header.file_offset:
            raise Elf32Error(f"program header {header.index} file range is outside ELF")
        if header.alignment not in {0, 1} and header.alignment & (header.alignment - 1):
            raise Elf32Error(
                f"program header {header.index} alignment is not a power of two"
            )
        if header.is_load and header.memory_size:
            load_ranges.append(
                (
                    header.virtual_address,
                    header.virtual_memory_end,
                    header.index,
                )
            )
    load_ranges.sort()
    for previous, current in zip(load_ranges, load_ranges[1:], strict=False):
        if current[0] < previous[1]:
            raise Elf32Error(
                f"overlapping load segments: {previous[2]} and {current[2]}"
            )


def _parse_raw_section_header(
    data: bytes, index: int, offset: int
) -> _RawSectionHeader:
    return _RawSectionHeader(
        index=index,
        name_offset=_u32(data, offset),
        section_type=_u32(data, offset + 4),
        flags=_u32(data, offset + 8),
        address=_u32(data, offset + 12),
        file_offset=_u32(data, offset + 16),
        size=_u32(data, offset + 20),
        link=_u32(data, offset + 24),
        info=_u32(data, offset + 28),
        alignment=_u32(data, offset + 32),
        entry_size=_u32(data, offset + 36),
    )


def _validate_raw_sections(
    sections: tuple[_RawSectionHeader, ...], file_size: int
) -> None:
    for section in sections:
        if section.section_type != SHT_NOBITS:
            if (
                section.file_offset > file_size
                or section.size > file_size - section.file_offset
            ):
                raise Elf32Error(f"section {section.index} file range is outside ELF")
        if section.alignment not in {0, 1} and section.alignment & (section.alignment - 1):
            raise Elf32Error(
                f"section {section.index} alignment is not a power of two"
            )


def _read_section_names(
    data: bytes,
    header: Elf32Header,
    sections: tuple[_RawSectionHeader, ...],
) -> tuple[str, ...]:
    if not sections:
        return ()
    string_section = sections[header.section_name_table_index]
    if string_section.section_type != SHT_STRTAB:
        raise Elf32Error("ELF section-name table is not a string table")
    table = data[
        string_section.file_offset : string_section.file_offset + string_section.size
    ]
    names: list[str] = []
    for section in sections:
        if section.name_offset >= len(table):
            raise Elf32Error(f"section {section.index} name offset is outside string table")
        terminator = table.find(b"\x00", section.name_offset)
        if terminator < 0:
            raise Elf32Error(f"section {section.index} name is not NUL-terminated")
        encoded = table[section.name_offset:terminator]
        try:
            names.append(encoded.decode("ascii"))
        except UnicodeDecodeError as exc:
            raise Elf32Error(f"section {section.index} name is not ASCII") from exc
    return tuple(names)


def _validate_table(
    offset: int,
    entry_size: int,
    count: int,
    file_size: int,
    label: str,
) -> None:
    if offset > file_size:
        raise Elf32Error(f"ELF {label} offset is outside file")
    total_size = entry_size * count
    if total_size > file_size - offset:
        raise Elf32Error(f"ELF {label} is truncated")


def _validate_address_range(address: int, size: int) -> None:
    if address < 0:
        raise Elf32Error("address must be non-negative")
    if size <= 0:
        raise Elf32Error("translation size must be positive")
    if address + size > 0x1_0000_0000:
        raise Elf32Error("address range exceeds 32-bit space")


def _u16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 2], "little")


def _u32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "little")
