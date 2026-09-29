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


def disasm_range(raw: bytes, elf, start: int, end: int, limit: int = 220) -> list[str]:
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


def jal_callers(raw: bytes, elf, target: int) -> list[dict]:
    callers = []
    for sec in elf.sections:
        if sec.kind != "executable" or sec.size < 4:
            continue
        for addr, word in words_for_section(raw, sec):
            if (word >> 26) != 0x03:
                continue
            dest = ((addr + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)
            if dest != target:
                continue
            start, end = function_bounds(raw, elf, addr)
            callers.append({
                "call_site": f"0x{addr:08X}",
                "caller_start": f"0x{start:08X}",
                "context": disasm_range(raw, elf, max(start, addr - 0x40), min(end, addr + 0x60), 64),
            })
    return callers


def main() -> None:
    raw = Path("BOOT.BIN").read_bytes()
    elf = parse_elf32(raw)

    field_accesses = []
    interesting_ops = {
        0x20: "LB",
        0x24: "LBU",
        0x28: "SB",
    }
    for sec in elf.sections:
        if sec.kind != "executable":
            continue
        for addr, word in words_for_section(raw, sec):
            if not (0x00190000 <= addr < 0x001B0000):
                continue
            op = word >> 26
            if op not in interesting_ops or (word & 0xFFFF) != 0x13:
                continue
            start, end = function_bounds(raw, elf, addr)
            field_accesses.append({
                "address": f"0x{addr:08X}",
                "op": interesting_ops[op],
                "base_reg": (word >> 21) & 0x1F,
                "value_reg": (word >> 16) & 0x1F,
                "function_start": f"0x{start:08X}",
                "context": disasm_range(raw, elf, max(start, addr - 0x38), min(end, addr + 0x50), 64),
            })

    pointer_adjusts = []
    for sec in elf.sections:
        if sec.kind != "executable":
            continue
        for addr, word in words_for_section(raw, sec):
            if not (0x00190000 <= addr < 0x001B0000):
                continue
            if (word >> 26) != 0x09 or (word & 0xFFFF) != 0x13:
                continue
            start, end = function_bounds(raw, elf, addr)
            pointer_adjusts.append({
                "address": f"0x{addr:08X}",
                "base_reg": (word >> 21) & 0x1F,
                "dest_reg": (word >> 16) & 0x1F,
                "function_start": f"0x{start:08X}",
                "context": disasm_range(raw, elf, max(start, addr - 0x30), min(end, addr + 0x60), 64),
            })

    # Functions already proven to participate in the population availability path.
    focused = {
        "cooldown_value_helper": disasm_range(raw, elf, 0x00192410, 0x00192580, 160),
        "cooldown_consumer_helper": disasm_range(raw, elf, 0x001929D4, 0x00192A80, 96),
        "weekly_countdown_decay": disasm_range(raw, elf, 0x00194320, 0x001943C0),
        "population_matchmaking": disasm_range(raw, elf, 0x00195564, 0x00195810),
        "due_population_fights": disasm_range(raw, elf, 0x0019E790, 0x0019EFD0),
        "population_replacement": disasm_range(raw, elf, 0x0019EFD0, 0x0019F530),
        "shared_result_tail": disasm_range(raw, elf, 0x0019AAAC, 0x0019BB68, 500),
        "post_fight_career": disasm_range(raw, elf, 0x0019CFF8, 0x0019DFE8, 500),
        "player_result_cooldown_a": disasm_range(raw, elf, 0x0019C6E0, 0x0019C820, 180),
        "player_result_cooldown_b": disasm_range(raw, elf, 0x0019CE40, 0x0019CF60, 180),
        "ai_result_cooldown": disasm_range(raw, elf, 0x0019ECB0, 0x0019EF50, 260),
    }

    targets = [0x00194320]
    caller_inventory = {
        f"0x{target:08X}": jal_callers(raw, elf, target)
        for target in targets
    }

    print("CAREER_AVAILABILITY_PROBE_BEGIN")
    print(json.dumps({
        "record_plus_0x13_direct_accesses": field_accesses,
        "record_plus_0x13_pointer_adjusts": pointer_adjusts,
        "callers": caller_inventory,
        "focused_ranges": focused,
    }, indent=2))
    print("CAREER_AVAILABILITY_PROBE_END")


if __name__ == "__main__":
    main()
