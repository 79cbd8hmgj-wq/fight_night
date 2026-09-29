from __future__ import annotations

import json
from pathlib import Path

from pspdisasm.elf32 import parse_elf32

from championship_probe import (
    disasm_range,
    function_bounds,
    offset_to_vaddr,
    pointer_locations,
    references_to_address,
    vaddr_word,
    words_for_section,
)

INJURY_STRINGS = (
    b"dec chance for injury",
    b"inc opp chance for injury",
)

# Recovered from the debug/review modifier-system evidence package.
MODIFIER_FUNCTIONS = {
    "raw_value_getter": 0x00091DF4,
    "apply_to_float": 0x00091E04,
    "scaled_value_getter": 0x00091E58,
}
INJURY_IDS = {12, 13}


def jal_target(address: int, word: int) -> int | None:
    if word >> 26 != 0x03:
        return None
    return ((address + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)


def immediate_loads_before(raw: bytes, elf, callsite: int, lookback: int = 12) -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    for addr in range(max(0, callsite - lookback * 4), callsite, 4):
        word = vaddr_word(raw, elf, addr)
        if word is None:
            continue
        op = word >> 26
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        imm = word & 0xFFFF
        # ORI reg,$zero,imm or ADDIU reg,$zero,imm.
        if rs == 0 and op in {0x0D, 0x09} and imm in INJURY_IDS:
            rows.append({
                "address": f"0x{addr:08X}",
                "register": rt,
                "value": imm,
            })
    return rows


def main() -> None:
    raw = Path("BOOT.BIN").read_bytes()
    elf = parse_elf32(raw)

    string_hits = []
    for needle in INJURY_STRINGS:
        pos = 0
        while True:
            off = raw.find(needle + b"\0", pos)
            if off < 0:
                break
            va = offset_to_vaddr(elf, off)
            pointers = pointer_locations(raw, elf, va) if va is not None else []
            table_candidates = []
            for pointer in pointers:
                # If the pointer occupies slot 12 or 13 of the 52-entry name table,
                # both injury strings should infer the same table base.
                injury_id = 12 if needle.startswith(b"dec ") else 13
                base = pointer - injury_id * 4
                table_candidates.append({
                    "pointer_location": f"0x{pointer:08X}",
                    "inferred_name_table_base": f"0x{base:08X}",
                    "table_base_code_xrefs": [
                        f"0x{x:08X}" for x in references_to_address(raw, elf, base)
                    ],
                })
            string_hits.append({
                "string": needle.decode("ascii"),
                "file_offset": f"0x{off:X}",
                "vaddr": f"0x{va:08X}" if va is not None else None,
                "direct_code_xrefs": (
                    [f"0x{x:08X}" for x in references_to_address(raw, elf, va)]
                    if va is not None else []
                ),
                "pointer_table_candidates": table_candidates,
            })
            pos = off + 1

    modifier_callers = []
    career_direct_calls = []
    modifier_calls_by_function: dict[tuple[int, int], list[dict[str, str]]] = {}
    for sec in elf.sections:
        if sec.kind != "executable" or sec.size < 4:
            continue
        for addr, word in words_for_section(raw, sec):
            target = jal_target(addr, word)
            if target not in MODIFIER_FUNCTIONS.values():
                continue
            start, end = function_bounds(raw, elf, addr)
            callee = next(name for name, value in MODIFIER_FUNCTIONS.items() if value == target)
            modifier_calls_by_function.setdefault((start, end), []).append({
                "callsite": f"0x{addr:08X}",
                "callee": callee,
            })
            loads = immediate_loads_before(raw, elf, addr)
            if loads:
                entry = {
                    "callsite": f"0x{addr:08X}",
                    "callee": callee,
                    "function_start": f"0x{start:08X}",
                    "injury_id_loads": loads,
                    "context": disasm_range(raw, elf, max(start, addr - 0x30), min(end, addr + 0x20)),
                }
                modifier_callers.append(entry)
            if 0x00190000 <= addr < 0x001B0000:
                career_direct_calls.append({
                    "callsite": f"0x{addr:08X}",
                    "callee": callee,
                    "function_start": f"0x{start:08X}",
                })

    modifier_candidate_functions = []
    for (start, end), calls in sorted(modifier_calls_by_function.items()):
        immediate_ids = []
        for addr in range(start, end, 4):
            word = vaddr_word(raw, elf, addr)
            if word is None:
                continue
            op = word >> 26
            rs = (word >> 21) & 0x1F
            rt = (word >> 16) & 0x1F
            imm = word & 0xFFFF
            if rs == 0 and op in {0x0D, 0x09} and imm in INJURY_IDS:
                immediate_ids.append({
                    "address": f"0x{addr:08X}",
                    "register": rt,
                    "value": imm,
                })
        if not immediate_ids:
            continue
        lo = min(
            [int(row["address"], 16) for row in immediate_ids]
            + [int(row["callsite"], 16) for row in calls]
        )
        hi = max(
            [int(row["address"], 16) for row in immediate_ids]
            + [int(row["callsite"], 16) for row in calls]
        )
        modifier_candidate_functions.append({
            "function_start": f"0x{start:08X}",
            "function_end": f"0x{end:08X}",
            "modifier_calls": calls,
            "injury_id_immediates": immediate_ids,
            "call_contexts": [
                {
                    **call,
                    "assembly": disasm_range(
                        raw,
                        elf,
                        max(start, int(call["callsite"], 16) - 0x28),
                        min(end, int(call["callsite"], 16) + 0x2C),
                    ),
                }
                for call in calls
            ],
            "injury_id_contexts": [
                {
                    **row,
                    "assembly": disasm_range(
                        raw,
                        elf,
                        max(start, int(row["address"], 16) - 0x18),
                        min(end, int(row["address"], 16) + 0x1C),
                    ),
                }
                for row in immediate_ids
            ],
        })

    modifier_function_bodies = {
        name: disasm_range(raw, elf, address, address + 0x90)
        for name, address in MODIFIER_FUNCTIONS.items()
    }

    print("CAREER_INJURY_PROBE_BEGIN")
    print(json.dumps({
        "injury_strings": string_hits,
        "injury_modifier_callers": modifier_callers,
        "modifier_candidate_functions": modifier_candidate_functions,
        "modifier_function_bodies": modifier_function_bodies,
        "career_region_direct_injury_modifier_calls": career_direct_calls,
        "known_career_recovery_field": {
            "field": "progression record+0x13",
            "role": "weekly post-fight availability/recovery cooldown",
            "note": "This probe does not assume +0x13 carries diagnosis or severity.",
        },
    }, indent=2))
    print("CAREER_INJURY_PROBE_END")


if __name__ == "__main__":
    main()
