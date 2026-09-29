from __future__ import annotations

import json
from pathlib import Path
import struct

import rabbitizer
from pspdisasm.elf32 import parse_elf32


TARGETS = (
    0x001B6A40,  # player post-fight/result orchestration
    0x001B7894,  # retail Career History writer call site
    0x001939DC,  # retail Career History writer
    0x001928F0,  # progression-record getter
    0x001929C4,  # career-slot -> absolute weight-class getter
    0x0019AAAC,  # shared career result/progression routine
)

FOCUSED_RANGES = (
    (0x001B6A40, 0x001B7400, "player_post_fight_head"),
    (0x001B7400, 0x001B78A0, "player_history_setup"),
    (0x0019C300, 0x0019CB20, "career_result_setup_and_winner_selection"),
    (0x0019CB20, 0x0019D000, "career_result_title_tail"),
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
    limit = min(start + 0x4000, address + 0x3000)
    while cursor < limit:
        word = vaddr_word(raw, elf, cursor)
        if word == 0x03E00008:
            return start, cursor + 8
        cursor += 4
    return start, min(start + 0x1800, limit)


def disasm_range(raw: bytes, elf, start: int, end: int, limit: int = 800) -> list[str]:
    rows: list[str] = []
    for addr in range(start, end, 4):
        word = vaddr_word(raw, elf, addr)
        if word is None:
            break
        ins = rabbitizer.Instruction(
            word,
            category=rabbitizer.InstrCategory.R4000ALLEGREX,
        )
        ins.vram = addr
        rows.append(f"0x{addr:08X}: {word:08X}  {ins.disassemble()}")
        if len(rows) >= limit:
            rows.append("...TRUNCATED...")
            break
    return rows


def jal_callers(raw: bytes, elf, target: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
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
                        max(start, addr - 0x70),
                        min(end, addr + 0x90),
                        100,
                    ),
                }
            )
    return rows


def scan_immediate_accesses(
    raw: bytes,
    elf,
    *,
    start: int,
    end: int,
    offsets: set[int],
) -> list[dict[str, object]]:
    op_names = {
        0x20: "LB",
        0x21: "LH",
        0x23: "LW",
        0x24: "LBU",
        0x25: "LHU",
        0x28: "SB",
        0x29: "SH",
        0x2B: "SW",
        0x09: "ADDIU",
    }
    rows: list[dict[str, object]] = []
    for sec in elf.sections:
        if sec.kind != "executable":
            continue
        for addr, word in words_for_section(raw, sec):
            if not start <= addr < end:
                continue
            op = word >> 26
            imm = word & 0xFFFF
            if op not in op_names or imm not in offsets:
                continue
            rows.append(
                {
                    "address": f"0x{addr:08X}",
                    "op": op_names[op],
                    "offset": f"0x{imm:04X}",
                    "base_reg": (word >> 21) & 0x1F,
                    "value_reg": (word >> 16) & 0x1F,
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
            "callers": jal_callers(raw, elf, target),
        }

    focused = {
        name: disasm_range(raw, elf, start, end)
        for start, end, name in FOCUSED_RANGES
    }

    # Fields needed by the prospective Career 2.0 ledger:
    # profile date +0x9C, working/committed slot +0x2A/+0x2B,
    # slot->absolute-class bytes +0x2D..+0x2F, current player index +0x4E,
    # progression rank +0x04, packed match descriptor +0x24,
    # scheduled date +0x28, and selected-contract type +0x34.
    candidate_accesses = scan_immediate_accesses(
        raw,
        elf,
        start=0x001B6A40,
        end=0x001B7A00,
        offsets={0x04, 0x24, 0x28, 0x2A, 0x2B, 0x2D, 0x2E, 0x2F, 0x34, 0x3C, 0x4E, 0x9C, 0x121},
    )

    print("CAREER_LEGACY_LEDGER_PROBE_BEGIN")
    print(
        json.dumps(
            {
                "functions": functions,
                "focused_ranges": focused,
                "candidate_field_accesses": candidate_accesses,
            },
            indent=2,
        )
    )
    print("CAREER_LEGACY_LEDGER_PROBE_END")


if __name__ == "__main__":
    main()
