from __future__ import annotations


def build_test_elf() -> bytes:
    shstrtab = b"\x00.text\x00.data\x00.bss\x00.shstrtab\x00"
    section_names = {
        ".text": shstrtab.index(b".text"),
        ".data": shstrtab.index(b".data"),
        ".bss": shstrtab.index(b".bss"),
        ".shstrtab": shstrtab.index(b".shstrtab"),
    }
    output = bytearray(0x4C8)

    output[0:16] = b"\x7fELF\x01\x01\x01" + b"\x00" * 9
    output[16:18] = (0xFFA0).to_bytes(2, "little")
    output[18:20] = (8).to_bytes(2, "little")
    output[20:24] = (1).to_bytes(4, "little")
    output[24:28] = (0x1000).to_bytes(4, "little")
    output[28:32] = (0x34).to_bytes(4, "little")
    output[32:36] = (0x400).to_bytes(4, "little")
    output[36:40] = (0x10A23001).to_bytes(4, "little")
    output[40:42] = (52).to_bytes(2, "little")
    output[42:44] = (32).to_bytes(2, "little")
    output[44:46] = (2).to_bytes(2, "little")
    output[46:48] = (40).to_bytes(2, "little")
    output[48:50] = (5).to_bytes(2, "little")
    output[50:52] = (4).to_bytes(2, "little")

    _program_header(
        output,
        0x34,
        segment_type=1,
        file_offset=0x100,
        virtual_address=0x1000,
        physical_address=0x1000,
        file_size=0x20,
        memory_size=0x20,
        flags=5,
        alignment=0x100,
    )
    _program_header(
        output,
        0x54,
        segment_type=1,
        file_offset=0x200,
        virtual_address=0x2000,
        physical_address=0x2000,
        file_size=0x10,
        memory_size=0x30,
        flags=6,
        alignment=0x100,
    )

    output[0x100:0x120] = bytes(range(0x20))
    output[0x200:0x210] = bytes(range(0x80, 0x90))
    output[0x300 : 0x300 + len(shstrtab)] = shstrtab

    _section_header(output, 0x400)
    _section_header(
        output,
        0x428,
        name=section_names[".text"],
        section_type=1,
        flags=6,
        address=0x1000,
        file_offset=0x100,
        size=0x20,
        alignment=16,
    )
    _section_header(
        output,
        0x450,
        name=section_names[".data"],
        section_type=1,
        flags=3,
        address=0x2000,
        file_offset=0x200,
        size=0x10,
        alignment=4,
    )
    _section_header(
        output,
        0x478,
        name=section_names[".bss"],
        section_type=8,
        flags=3,
        address=0x2010,
        file_offset=0x210,
        size=0x20,
        alignment=4,
    )
    _section_header(
        output,
        0x4A0,
        name=section_names[".shstrtab"],
        section_type=3,
        file_offset=0x300,
        size=len(shstrtab),
        alignment=1,
    )
    return bytes(output)


def _program_header(
    output: bytearray,
    offset: int,
    *,
    segment_type: int,
    file_offset: int,
    virtual_address: int,
    physical_address: int,
    file_size: int,
    memory_size: int,
    flags: int,
    alignment: int,
) -> None:
    values = (
        segment_type,
        file_offset,
        virtual_address,
        physical_address,
        file_size,
        memory_size,
        flags,
        alignment,
    )
    for index, value in enumerate(values):
        start = offset + index * 4
        output[start : start + 4] = value.to_bytes(4, "little")


def _section_header(
    output: bytearray,
    offset: int,
    *,
    name: int = 0,
    section_type: int = 0,
    flags: int = 0,
    address: int = 0,
    file_offset: int = 0,
    size: int = 0,
    link: int = 0,
    info: int = 0,
    alignment: int = 0,
    entry_size: int = 0,
) -> None:
    values = (
        name,
        section_type,
        flags,
        address,
        file_offset,
        size,
        link,
        info,
        alignment,
        entry_size,
    )
    for index, value in enumerate(values):
        start = offset + index * 4
        output[start : start + 4] = value.to_bytes(4, "little")
