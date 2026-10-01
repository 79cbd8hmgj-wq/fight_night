from __future__ import annotations

import json
from pathlib import Path
import struct

import rabbitizer
from pspdisasm.elf32 import parse_elf32


TARGETS = (
    0x001A3FBC,  # proven fight-contract eligibility evaluator
    0x001A319C,  # automatic eligible-offer selector
    0x001A2FA0,  # select/copy contract template by ID
    0x001FF210,  # OnSelectFightContract
    0x001FFE1C,  # selected-ID follow-up
    0x001FF4AC,  # accepted player-contract scheduling path
    0x00194518,  # AssignCareerMatch
)

# Fields whose exact dataflow matters for the current Career 2.0 offer slice.
CONTRACT_OFFSETS = {
    0x14,
    0x18,
    0x1C,
    0x20,
    0x24,
    0x30,
    0x34,
    0x44,
    0x50,
}


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
    limit = min(start + 0x5000, address + 0x4000)
    while cursor < limit:
        word = vaddr_word(raw, elf, cursor)
        if word == 0x03E00008:
            return start, cursor + 8
        cursor += 4
    return start, min(start + 0x2000, limit)


def disasm_range(
    raw: bytes,
    elf,
    start: int,
    end: int,
    limit: int = 900,
) -> list[str]:
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


def immediate_field_accesses(
    raw: bytes,
    elf,
    start: int,
    end: int,
) -> list[dict[str, object]]:
    names = {
        0x20: "LB",
        0x21: "LH",
        0x23: "LW",
        0x24: "LBU",
        0x25: "LHU",
        0x28: "SB",
        0x29: "SH",
        0x2B: "SW",
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
            if op not in names or imm not in CONTRACT_OFFSETS:
                continue
            rows.append(
                {
                    "address": f"0x{addr:08X}",
                    "op": names[op],
                    "offset": f"0x{imm:02X}",
                    "base_reg": (word >> 21) & 0x1F,
                    "value_reg": (word >> 16) & 0x1F,
                }
            )
    return rows


def jal_callers(raw: bytes, elf, target: int) -> list[str]:
    rows: list[str] = []
    for sec in elf.sections:
        if sec.kind != "executable":
            continue
        for addr, word in words_for_section(raw, sec):
            if (word >> 26) != 0x03:
                continue
            dest = ((addr + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)
            if dest == target:
                rows.append(f"0x{addr:08X}")
    return rows


def field_access_windows(
    raw: bytes,
    elf,
    start: int,
    end: int,
    *,
    offsets: tuple[int, ...],
    radius_instructions: int = 10,
) -> dict[str, list[dict[str, object]]]:
    """Emit compact context around each unresolved contract-field access.

    The existing broad disassembly is useful for manual reading but makes it
    easy to miss the exact compare/branch sequence surrounding a field load.
    These windows keep the evidence mechanical: no semantic name is assigned
    until the instruction-level dataflow proves it.
    """

    wanted = set(offsets)
    rows: dict[str, list[dict[str, object]]] = {
        f"0x{offset:02X}": [] for offset in offsets
    }
    load_store_ops = {0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2B}

    for addr in range(start, end, 4):
        word = vaddr_word(raw, elf, addr)
        if word is None:
            continue
        op = word >> 26
        imm = word & 0xFFFF
        if op not in load_store_ops or imm not in wanted:
            continue

        window_start = max(start, addr - radius_instructions * 4)
        window_end = min(end, addr + (radius_instructions + 1) * 4)
        rows[f"0x{imm:02X}"].append(
            {
                "access_address": f"0x{addr:08X}",
                "base_reg": (word >> 21) & 0x1F,
                "value_reg": (word >> 16) & 0x1F,
                "assembly": disasm_range(
                    raw,
                    elf,
                    window_start,
                    window_end,
                    radius_instructions * 2 + 1,
                ),
            }
        )

    return rows


def direct_jal_targets(
    raw: bytes,
    elf,
    start: int,
    end: int,
) -> list[dict[str, str]]:
    """List direct calls made by the bounded eligibility routine."""

    rows: list[dict[str, str]] = []
    for addr in range(start, end, 4):
        word = vaddr_word(raw, elf, addr)
        if word is None or (word >> 26) != 0x03:
            continue
        target = ((addr + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)
        rows.append(
            {
                "call_site": f"0x{addr:08X}",
                "target": f"0x{target:08X}",
            }
        )
    return rows


def decode_word_table(
    raw: bytes,
    elf,
    *,
    table_vaddr: int,
    count: int,
    first_index: int = 0,
) -> list[dict[str, object]]:
    """Decode an absolute-address word table used by a recovered jump dispatch."""

    rows: list[dict[str, object]] = []
    for offset in range(count):
        entry_vaddr = table_vaddr + offset * 4
        target = vaddr_word(raw, elf, entry_vaddr)
        rows.append(
            {
                "index": first_index + offset,
                "entry_vaddr": f"0x{entry_vaddr:08X}",
                "target": None if target is None else f"0x{target:08X}",
            }
        )
    return rows


def disasm_dispatch_targets(
    raw: bytes,
    elf,
    entries: list[dict[str, object]],
    *,
    instructions: int = 24,
) -> list[dict[str, object]]:
    """Emit a small window at each unique dispatch target."""

    seen: set[int] = set()
    rows: list[dict[str, object]] = []
    for entry in entries:
        target_text = entry["target"]
        if not isinstance(target_text, str):
            continue
        target = int(target_text, 16)
        if target in seen:
            continue
        seen.add(target)
        rows.append(
            {
                "target": target_text,
                "types": [
                    item["index"]
                    for item in entries
                    if item["target"] == target_text
                ],
                "assembly": disasm_range(
                    raw,
                    elf,
                    target,
                    target + instructions * 4,
                    instructions,
                ),
            }
        )
    return rows


def main() -> None:
    raw = Path("BOOT.BIN").read_bytes()
    elf = parse_elf32(raw)

    functions: dict[str, object] = {}
    for target in TARGETS:
        start, end = function_bounds(raw, elf, target)
        functions[f"0x{target:08X}"] = {
            "function_start": f"0x{start:08X}",
            "function_end": f"0x{end:08X}",
            "jal_callers": jal_callers(raw, elf, start),
            "field_accesses": immediate_field_accesses(raw, elf, start, end),
            "assembly": disasm_range(raw, elf, start, end),
        }

    # The eligibility evaluator contains many early-return blocks reached from
    # its type-dispatch jump table, so "first jr $ra" is not a valid function
    # boundary here.  Keep this range explicit until the whole CFG is modeled.
    eligibility_start = 0x001A3FBC
    eligibility_end = 0x001A4520
    unresolved_field_windows = field_access_windows(
        raw,
        elf,
        eligibility_start,
        eligibility_end,
        offsets=(0x24, 0x30, 0x44, 0x50),
        radius_instructions=12,
    )
    eligibility_calls = direct_jal_targets(
        raw,
        elf,
        eligibility_start,
        eligibility_end,
    )

    # 0x001A403C subtracts one from contract type, bounds it to 27 entries,
    # then indexes the absolute target table at 0x00508A08.
    eligibility_type_dispatch = decode_word_table(
        raw,
        elf,
        table_vaddr=0x00508A08,
        count=27,
        first_index=1,
    )
    eligibility_type_windows = disasm_dispatch_targets(
        raw,
        elf,
        eligibility_type_dispatch,
        instructions=28,
    )

    # Keep focused windows small enough to remain usable in CI logs while
    # exposing the two unresolved current-version questions: +0x50 record gate
    # and selection -> scheduling dataflow.
    focused = {
        "eligibility_shared_gates": disasm_range(
            raw,
            elf,
            0x001A4100,
            0x001A42D0,
            220,
        ),
        "eligibility_type_tail": disasm_range(
            raw,
            elf,
            0x001A42CC,
            0x001A4520,
            220,
        ),
        "selection_and_followup": disasm_range(
            raw,
            elf,
            0x001FF1E0,
            0x001FFF20,
            500,
        ),
        "accepted_offer_schedule": disasm_range(
            raw,
            elf,
            0x001FF380,
            0x001FF4C8,
            220,
        ),
    }

    print("CAREER_OFFER_PROBE_BEGIN")
    print(
        json.dumps(
            {
                "functions": functions,
                "eligibility_unresolved_field_windows": unresolved_field_windows,
                "eligibility_direct_calls": eligibility_calls,
                "eligibility_type_dispatch": eligibility_type_dispatch,
                "eligibility_type_windows": eligibility_type_windows,
                "focused": focused,
            },
            indent=2,
        )
    )
    print("CAREER_OFFER_PROBE_END")


if __name__ == "__main__":
    main()
