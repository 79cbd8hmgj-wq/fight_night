from __future__ import annotations

import json
from pathlib import Path
import struct

import rabbitizer
from pspdisasm.elf32 import parse_elf32


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
    imm = sign16(word & 0xFFFF)
    return op == 0x09 and rs == 29 and rt == 29 and imm < 0


def function_bounds(raw: bytes, elf, address: int) -> tuple[int, int]:
    start = address & ~3
    for candidate in range(start, max(-4, start - 0x1000), -4):
        word = vaddr_word(raw, elf, candidate)
        if word is not None and is_stack_prologue(word):
            start = candidate
            break
    end = min(start + 0x2000, address + 0x1800)
    cursor = max(address, start)
    while cursor < end:
        word = vaddr_word(raw, elf, cursor)
        if word == 0x03E00008:
            return start, cursor + 8
        cursor += 4
    return start, min(end, start + 0x800)


def disasm_range(raw: bytes, elf, start: int, end: int, limit: int = 96) -> list[str]:
    rows = []
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


def access_inventory(raw: bytes, elf, lo: int, hi: int, offsets: set[int], ops: dict[int, str]) -> list[dict]:
    rows = []
    for sec in elf.sections:
        if sec.kind != "executable":
            continue
        for addr, word in words_for_section(raw, sec):
            if not (lo <= addr < hi):
                continue
            op = word >> 26
            imm = word & 0xFFFF
            if op not in ops or imm not in offsets:
                continue
            start, end = function_bounds(raw, elf, addr)
            rows.append({
                "address": f"0x{addr:08X}",
                "op": ops[op],
                "offset": f"0x{imm:02X}",
                "base_reg": (word >> 21) & 0x1F,
                "value_reg": (word >> 16) & 0x1F,
                "function_start": f"0x{start:08X}",
                "context": disasm_range(raw, elf, max(start, addr - 0x30), min(end, addr + 0x44), 48),
            })
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
            rows.append({
                "call_site": f"0x{addr:08X}",
                "caller_start": f"0x{start:08X}",
                "context": disasm_range(raw, elf, max(start, addr - 0x38), min(end, addr + 0x50), 56),
            })
    return rows


def main() -> None:
    raw = Path("BOOT.BIN").read_bytes()
    elf = parse_elf32(raw)

    byte_ops = {0x20: "LB", 0x24: "LBU", 0x28: "SB"}
    half_ops = {0x21: "LH", 0x25: "LHU", 0x29: "SH"}

    profile_slot_map = access_inventory(
        raw, elf, 0x00190000, 0x001B0000, {0x2D, 0x2E, 0x2F}, byte_ops
    )
    boxer_weight = access_inventory(
        raw, elf, 0x00180000, 0x001B0000, {0x6C}, half_ops
    )

    callers = {
        "0x0018600C_weight_classifier": jal_callers(raw, elf, 0x0018600C),
        "0x001929C4_slot_to_weight_class": jal_callers(raw, elf, 0x001929C4),
        "0x0019527C_change_active_rank_class": jal_callers(raw, elf, 0x0019527C),
    }

    focused = {
        "slot_mapping_getter": disasm_range(raw, elf, 0x001929B8, 0x00192A10, 48),
        "rank_class_change": disasm_range(raw, elf, 0x0019527C, 0x00195430, 160),
        "weight_classifier": disasm_range(raw, elf, 0x0018600C, 0x001860C0, 72),
    }

    print("CAREER_WEIGHT_MOVEMENT_PROBE_BEGIN")
    print(json.dumps({
        "profile_slot_mapping_accesses": profile_slot_map,
        "persistent_boxer_weight_accesses": boxer_weight,
        "callers": callers,
        "focused_ranges": focused,
    }, indent=2))
    print("CAREER_WEIGHT_MOVEMENT_PROBE_END")


if __name__ == "__main__":
    main()
