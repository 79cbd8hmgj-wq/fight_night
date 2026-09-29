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
    end = min(start + 0x2400, address + 0x1800)
    cursor = max(address, start)
    while cursor < end:
        word = vaddr_word(raw, elf, cursor)
        if word == 0x03E00008:
            return start, cursor + 8
        cursor += 4
    return start, min(end, start + 0x1000)


def disasm_range(raw: bytes, elf, start: int, end: int, limit: int = 260) -> list[str]:
    out = []
    for addr in range(start, end, 4):
        word = vaddr_word(raw, elf, addr)
        if word is None:
            break
        ins = rabbitizer.Instruction(word, category=rabbitizer.InstrCategory.R4000ALLEGREX)
        ins.vram = addr
        out.append(f"0x{addr:08X}: {word:08X}  {ins.disassemble()}")
        if len(out) >= limit:
            out.append("...TRUNCATED...")
            break
    return out


def jal_callers(raw: bytes, elf, target: int) -> list[dict]:
    rows = []
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
            rows.append({
                "call_site": f"0x{addr:08X}",
                "caller_start": f"0x{start:08X}",
                "caller_end": f"0x{end:08X}",
                "context": disasm_range(raw, elf, max(start, addr - 0x70), min(end, addr + 0xA0), 100),
            })
    return rows


def main() -> None:
    raw = Path("BOOT.BIN").read_bytes()
    elf = parse_elf32(raw)

    profile_offsets = {0x2A, 0x2B, 0x2D, 0x2E, 0x2F}
    direct_byte_accesses = []
    op_names = {0x20: "LB", 0x24: "LBU", 0x28: "SB"}
    for sec in elf.sections:
        if sec.kind != "executable":
            continue
        for addr, word in words_for_section(raw, sec):
            if not (0x00190000 <= addr < 0x00210000):
                continue
            op = word >> 26
            imm = word & 0xFFFF
            if op not in op_names or imm not in profile_offsets:
                continue
            start, end = function_bounds(raw, elf, addr)
            direct_byte_accesses.append({
                "address": f"0x{addr:08X}",
                "op": op_names[op],
                "offset": f"0x{imm:02X}",
                "base_reg": (word >> 21) & 0x1F,
                "value_reg": (word >> 16) & 0x1F,
                "function_start": f"0x{start:08X}",
                "context": disasm_range(raw, elf, max(start, addr - 0x40), min(end, addr + 0x60), 72),
            })

    targets = [0x001929C4, 0x0019527C, 0x00197230, 0x0019FBD8, 0x0019FBF4]
    callers = {f"0x{x:08X}": jal_callers(raw, elf, x) for x in targets}

    # Decode the 26-entry scheduler dispatch table used by contract types 2..27.
    scheduler_type_targets = {}
    table_off = elf.vaddr_to_offset(0x00508C60)
    if table_off is not None:
        for i in range(26):
            target = struct.unpack_from("<I", raw, table_off + i * 4)[0]
            scheduler_type_targets[str(i + 2)] = f"0x{target:08X}"

    focused = {
        "career_slot_mapping_getter": disasm_range(raw, elf, 0x001929B8, 0x00192A80, 160),
        "active_slot_transition": disasm_range(raw, elf, 0x0019527C, 0x00195430, 300),
        "post_result_transition_helper": disasm_range(raw, elf, 0x00197230, 0x00197700, 360),
        "career_transition_helpers": disasm_range(raw, elf, 0x0019FB80, 0x0019FD80, 260),
        "post_fight_weight_transition": disasm_range(raw, elf, 0x0019CEB0, 0x0019D0A0, 260),
        "career_initialization": disasm_range(raw, elf, 0x0019D8C0, 0x0019DB80, 260),
        "special_contract_scheduler": disasm_range(raw, elf, 0x001A4F50, 0x001A55A0, 420),
        "weight_change_fine_print": disasm_range(raw, elf, 0x00203020, 0x002030C8, 64),
        "weight_change_predicate": disasm_range(raw, elf, 0x001A3560, 0x001A36A0, 96),
    }

    print("CAREER_WEIGHT_PROBE_BEGIN")
    print(json.dumps({
        "profile_weight_slot_accesses": direct_byte_accesses,
        "callers": callers,
        "focused_ranges": focused,
        "scheduler_type_targets": scheduler_type_targets,
    }, indent=2))
    print("CAREER_WEIGHT_PROBE_END")


if __name__ == "__main__":
    main()
