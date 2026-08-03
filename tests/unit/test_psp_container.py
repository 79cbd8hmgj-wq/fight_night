from __future__ import annotations

import pytest

from fnr3_re.psp_container import PspContainerError, parse_psp_container


def build_container() -> bytes:
    payload = bytearray(0x150)
    payload[0:4] = b"~PSP"
    payload[4:6] = (0x1000).to_bytes(2, "little")
    payload[6:8] = (1).to_bytes(2, "little")
    payload[8] = 2
    payload[9] = 3
    payload[10:38] = b"FixtureModule".ljust(28, b"\x00")
    payload[38] = 1
    payload[39] = 2
    payload[40:44] = (0x120).to_bytes(4, "little")
    payload[44:48] = len(payload).to_bytes(4, "little")
    payload[48:52] = (0x1234).to_bytes(4, "little")
    payload[52:56] = (0x80).to_bytes(4, "little")
    payload[56:60] = (0x40).to_bytes(4, "little")
    for index, alignment in enumerate((0x100, 0x40, 0, 0)):
        start = 60 + index * 2
        payload[start : start + 2] = alignment.to_bytes(2, "little")
    for index, address in enumerate((0x1000, 0x2000, 0, 0)):
        start = 68 + index * 4
        payload[start : start + 4] = address.to_bytes(4, "little")
    for index, size in enumerate((0x80, 0x40, 0, 0)):
        start = 84 + index * 4
        payload[start : start + 4] = size.to_bytes(4, "little")
    return bytes(payload)


def test_parses_reference_psp_container_header() -> None:
    container = parse_psp_container(build_container())

    assert container.module_name == "FixtureModule"
    assert container.module_attributes == 0x1000
    assert container.compression_attributes == 1
    assert container.module_version == (2, 3)
    assert container.header_version == 1
    assert container.segment_count == 2
    assert container.elf_size == 0x120
    assert container.psp_size == 0x150
    assert container.entry_point == 0x1234
    assert container.module_info_offset == 0x80
    assert container.bss_size == 0x40
    assert container.segment_alignments == (0x100, 0x40)
    assert container.segment_addresses == (0x1000, 0x2000)
    assert container.segment_sizes == (0x80, 0x40)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (b"", "header is truncated"),
        (b"NOPE" + b"\x00" * 100, "magic"),
        (build_container()[:99], "header is truncated"),
    ],
)
def test_rejects_malformed_containers(payload: bytes, message: str) -> None:
    with pytest.raises(PspContainerError, match=message):
        parse_psp_container(payload)


def test_rejects_invalid_segment_count_or_sizes() -> None:
    count = bytearray(build_container())
    count[39] = 5
    with pytest.raises(PspContainerError, match="segment count"):
        parse_psp_container(count)

    psp_size = bytearray(build_container())
    psp_size[44:48] = (0x151).to_bytes(4, "little")
    with pytest.raises(PspContainerError, match="PSP size"):
        parse_psp_container(psp_size)

    elf_size = bytearray(build_container())
    elf_size[40:44] = (0x200).to_bytes(4, "little")
    with pytest.raises(PspContainerError, match="ELF size"):
        parse_psp_container(elf_size)


def test_rejects_non_ascii_or_empty_module_name() -> None:
    non_ascii = bytearray(build_container())
    non_ascii[10] = 0xFF
    with pytest.raises(PspContainerError, match="module name is not ASCII"):
        parse_psp_container(non_ascii)

    empty = bytearray(build_container())
    empty[10:38] = b"\x00" * 28
    with pytest.raises(PspContainerError, match="module name is empty"):
        parse_psp_container(empty)
