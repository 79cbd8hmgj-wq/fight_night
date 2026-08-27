from __future__ import annotations

import struct


def build_minimal_mips_elf(
    *,
    file_type: int = 0xFFA0,
    alignments: tuple[int, ...] = (0x10,),
) -> bytes:
    phoff = 0x34
    phentsize = 0x20
    payload = bytearray(0x400)
    payload[:16] = b"\x7fELF\x01\x01\x01" + b"\x00" * 9
    struct.pack_into(
        "<HHIIIIIHHHHHH",
        payload,
        16,
        file_type,
        8,
        1,
        0,
        phoff,
        0,
        0,
        0x34,
        phentsize,
        len(alignments),
        0x28,
        0,
        0,
    )
    for index, alignment in enumerate(alignments):
        offset = 0x100 + index * 0x80
        vaddr = index * 0x8000
        struct.pack_into(
            "<IIIIIIII",
            payload,
            phoff + index * phentsize,
            1,
            offset,
            vaddr,
            vaddr,
            0x20,
            0x40,
            5,
            alignment,
        )
        payload[offset : offset + 4] = b"\x00\x00\x00\x00"
    return bytes(payload)


def build_encrypted_psp_container() -> bytes:
    payload = bytearray(0x150)
    payload[:4] = b"~PSP"
    payload[0x0A:0x0C] = (1).to_bytes(2, "little")
    payload[0x0C:0x10] = b"TEST"
    return bytes(payload)
