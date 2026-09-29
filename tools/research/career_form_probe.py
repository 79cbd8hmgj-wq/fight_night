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
)

TARGETS = (
    "strFightHypeBoxerCRO",
    "GetMyCareerStatsInfo",
    "aiRankRating",
    "astrCurrentRival",
    "astrRivalFightRecord",
    "iRivalMatchup",
    "GetHallofFameInfo",
)


def main() -> None:
    raw = Path("BOOT.BIN").read_bytes()
    elf = parse_elf32(raw)

    results = []
    seen_functions: set[tuple[int, int]] = set()
    function_contexts = []

    for target in TARGETS:
        needle = target.encode("ascii") + b"\0"
        off = raw.find(needle)
        if off < 0:
            results.append({"target": target, "found": False})
            continue
        va = offset_to_vaddr(elf, off)
        direct = references_to_address(raw, elf, va) if va is not None else []
        pointers = pointer_locations(raw, elf, va) if va is not None else []
        pointer_xrefs = []
        for pointer in pointers[:16]:
            refs = references_to_address(raw, elf, pointer)
            if refs:
                pointer_xrefs.append({
                    "pointer_location": f"0x{pointer:08X}",
                    "code_xrefs": [f"0x{x:08X}" for x in refs],
                })
                direct.extend(refs)

        unique_refs = sorted(set(direct))
        results.append({
            "target": target,
            "found": True,
            "vaddr": f"0x{va:08X}" if va is not None else None,
            "direct_or_pointer_code_xrefs": [f"0x{x:08X}" for x in unique_refs],
            "pointer_xrefs": pointer_xrefs,
        })

        for ref in unique_refs:
            start, end = function_bounds(raw, elf, ref)
            key = (start, end)
            if key in seen_functions:
                continue
            seen_functions.add(key)
            function_contexts.append({
                "start": f"0x{start:08X}",
                "end": f"0x{end:08X}",
                "trigger_ref": f"0x{ref:08X}",
                "assembly": disasm_range(
                    raw,
                    elf,
                    max(start, ref - 0x50),
                    min(end, ref + 0xA0),
                ),
            })

    print("CAREER_FORM_PROBE_BEGIN")
    print(json.dumps({
        "targets": results,
        "function_contexts": function_contexts,
    }, indent=2))
    print("CAREER_FORM_PROBE_END")


if __name__ == "__main__":
    main()
