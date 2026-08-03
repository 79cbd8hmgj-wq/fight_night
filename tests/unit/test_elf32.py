from __future__ import annotations

import pytest

from fnr3_re.elf32 import Elf32Error, parse_elf32
from tests.support.elf32 import build_test_elf


def test_parses_psp_elf_header_segments_and_sections() -> None:
    image = parse_elf32(build_test_elf())

    assert image.header.object_type == 0xFFA0
    assert image.header.machine == 8
    assert image.header.entry_point == 0x1000
    assert image.header.program_header_count == 2
    assert image.header.section_header_count == 5
    assert image.image_base == 0x1000
    assert [(segment.virtual_address, segment.file_offset) for segment in image.load_segments] == [
        (0x1000, 0x100),
        (0x2000, 0x200),
    ]
    assert [section.name for section in image.sections] == [
        "",
        ".text",
        ".data",
        ".bss",
        ".shstrtab",
    ]
    assert image.sections[3].is_nobits
    assert image.sections[3].address == 0x2010
    assert image.sections[3].size == 0x20


def test_translates_file_backed_virtual_addresses() -> None:
    image = parse_elf32(build_test_elf())

    assert image.virtual_to_file_offset(0x1004) == 0x104
    assert image.virtual_to_file_offset(0x200F) == 0x20F
    assert image.file_offset_to_virtual(0x104) == 0x1004
    assert image.file_offset_to_virtual(0x20F) == 0x200F


def test_rejects_bss_or_unmapped_address_translation() -> None:
    image = parse_elf32(build_test_elf())

    with pytest.raises(Elf32Error, match="not backed by file data"):
        image.virtual_to_file_offset(0x2010)
    with pytest.raises(Elf32Error, match="not mapped by a load segment"):
        image.virtual_to_file_offset(0x5000)
    with pytest.raises(Elf32Error, match="not mapped by a load segment"):
        image.file_offset_to_virtual(0x350)


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda data: data.__setitem__(slice(0, 4), b"NOPE"), "ELF magic"),
        (lambda data: data.__setitem__(4, 2), "ELF class"),
        (lambda data: data.__setitem__(5, 2), "ELF endianness"),
        (lambda data: data.__setitem__(slice(18, 20), b"\x03\x00"), "machine"),
        (lambda data: data.__setitem__(slice(40, 42), b"\x00\x00"), "header size"),
        (lambda data: data.__setitem__(slice(32, 36), b"\xff\xff\xff\x7f"), "section table"),
    ],
)
def test_rejects_malformed_or_unsupported_elfs(mutator: object, message: str) -> None:
    payload = bytearray(build_test_elf())
    mutator(payload)

    with pytest.raises(Elf32Error, match=message):
        parse_elf32(payload)


def test_rejects_segment_with_file_size_larger_than_memory_size() -> None:
    payload = bytearray(build_test_elf())
    payload[0x34 + 20 : 0x34 + 24] = (0x10).to_bytes(4, "little")

    with pytest.raises(Elf32Error, match="file size exceeds memory size"):
        parse_elf32(payload)


def test_rejects_ambiguous_overlapping_load_segments() -> None:
    payload = bytearray(build_test_elf())
    payload[0x54 + 8 : 0x54 + 12] = (0x1010).to_bytes(4, "little")

    with pytest.raises(Elf32Error, match="overlapping load segments"):
        parse_elf32(payload)
