from __future__ import annotations

import json
from pathlib import Path
import struct

import rabbitizer
from pspdisasm.elf32 import parse_elf32


def word_at(raw: bytes, elf, address: int) -> int | None:
    off = elf.vaddr_to_offset(address)
    if off is None or off + 4 > len(raw):
        return None
    return struct.unpack_from("<I", raw, off)[0]


def disasm(raw: bytes, elf, start: int, end: int) -> list[str]:
    rows: list[str] = []
    for address in range(start, end, 4):
        word = word_at(raw, elf, address)
        if word is None:
            break
        ins = rabbitizer.Instruction(
            word,
            category=rabbitizer.InstrCategory.R4000ALLEGREX,
        )
        ins.vram = address
        rows.append(f"0x{address:08X}: {word:08X}  {ins.disassemble()}")
    return rows


def main() -> None:
    raw = Path("BOOT.BIN").read_bytes()
    elf = parse_elf32(raw)

    ranges = {
        "source_selection": disasm(raw, elf, 0x0019F130, 0x0019F250),
        "record_initialization": disasm(raw, elf, 0x0019F240, 0x0019F330),
        "duplicate_source_scan": disasm(raw, elf, 0x0019F32C, 0x0019F410),
        "replacement_tail": disasm(raw, elf, 0x0019F400, 0x0019F530),
    }

    accesses = []
    offsets = {0x00, 0x01, 0x02, 0x03, 0x04, 0x09, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x14, 0x1C, 0x24, 0x28}
    names = {0x20:"LB",0x21:"LH",0x23:"LW",0x24:"LBU",0x25:"LHU",0x28:"SB",0x29:"SH",0x2B:"SW"}
    for sec in elf.sections:
        if sec.kind != "executable":
            continue
        limit = sec.offset + sec.size - (sec.size % 4)
        for off in range(sec.offset, limit, 4):
            address = sec.addr + (off - sec.offset)
            if not 0x0019EFD0 <= address < 0x0019F530:
                continue
            word = struct.unpack_from("<I", raw, off)[0]
            op = word >> 26
            imm = word & 0xFFFF
            if op in names and imm in offsets:
                accesses.append({
                    "address": f"0x{address:08X}",
                    "op": names[op],
                    "offset": f"0x{imm:02X}",
                    "base_reg": (word >> 21) & 0x1F,
                    "value_reg": (word >> 16) & 0x1F,
                })

    print("CAREER_POPULATION_SOURCE_PROBE_BEGIN")
    print(json.dumps({"ranges": ranges, "field_accesses": accesses}, indent=2))
    print("CAREER_POPULATION_SOURCE_PROBE_END")


if __name__ == "__main__":
    main()
