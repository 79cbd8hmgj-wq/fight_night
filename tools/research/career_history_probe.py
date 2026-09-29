from __future__ import annotations

import json
from pathlib import Path
import struct

import rabbitizer
from pspdisasm.elf32 import parse_elf32


TARGETS = (
    0x001939DC,  # fight-history ring writer
    0x00193BB8,  # fight-history ring reader
    0x001B7894,  # completed-fight caller
    0x001EE220,  # GetCareerHistoryInfo provider
)


def sign16(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def words_for_section(raw: bytes, section):
    end = section.offset + section.size - (section.size % 4)
    for off in range(section.offset, end, 4):
        yield section.addr + (off - section.offset), struct.unpack_from("<I", raw, off)[0]


def vaddr_word(raw: bytes, elf, address: int) -> int | None:
    off = elf.vaddr_to_offset(address)
    if off is None or off + 4 > len(raw):
        return None
    return struct.unpack_from("<I", raw, off)[0]


def is_stack_prologue(word: int) -> bool:
    op = word >> 26
    rs = (word >> 21) & 0x1F
    rt = (word >> 16) & 0x1F
    return op == 0x09 and rs == 29 and rt == 29 and sign16(word & 0xFFFF) < 0


def function_bounds(raw: bytes, elf, address: int) -> tuple[int, int]:
    start = address & ~3
    for candidate in range(start, max(-4, start - 0x1000), -4):
        word = vaddr_word(raw, elf, candidate)
        if word is not None and is_stack_prologue(word):
            start = candidate
            break
    cursor = max(address, start)
    limit = min(start + 0x3000, address + 0x2800)
    while cursor < limit:
        word = vaddr_word(raw, elf, cursor)
        if word == 0x03E00008:
            return start, cursor + 8
        cursor += 4
    return start, min(start + 0x1000, limit)


def disasm_range(raw: bytes, elf, start: int, end: int, limit: int = 500) -> list[str]:
    rows: list[str] = []
    for addr in range(start, end, 4):
        word = vaddr_word(raw, elf, addr)
        if word is None:
            break
        ins = rabbitizer.Instruction(word, category=rabbitizer.InstrCategory.R4000ALLEGREX)
        ins.vram = addr
        rows.append(f"0x{addr:08X}: {word:08X}  {ins.disassemble()}")
        if len(rows) >= limit:
            rows.append("...TRUNCATED...")
            break
    return rows


def jal_callers(raw: bytes, elf, target: int) -> list[dict]:
    rows = []
    for sec in elf.sections:
        if sec.kind != "executable":
            continue
        for addr, word in words_for_section(raw, sec):
            if (word >> 26) != 0x03:
                continue
            dest = ((addr + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)
            if dest != target:
                continue
            start, end = function_bounds(raw, elf, addr)
            rows.append(
                {
                    "call_site": f"0x{addr:08X}",
                    "caller_start": f"0x{start:08X}",
                    "context": disasm_range(
                        raw,
                        elf,
                        max(start, addr - 0x80),
                        min(end, addr + 0xA0),
                        120,
                    ),
                }
            )
    return rows


def main() -> None:
    raw = Path("BOOT.BIN").read_bytes()
    elf = parse_elf32(raw)

    functions = {}
    for target in TARGETS:
        start, end = function_bounds(raw, elf, target)
        functions[f"0x{target:08X}"] = {
            "function_start": f"0x{start:08X}",
            "function_end": f"0x{end:08X}",
            "assembly": disasm_range(raw, elf, start, end),
            "jal_callers": jal_callers(raw, elf, target),
        }

    print("CAREER_HISTORY_PROBE_BEGIN")
    print(json.dumps({"functions": functions}, indent=2))
    print("CAREER_HISTORY_PROBE_END")


if __name__ == "__main__":
    main()
