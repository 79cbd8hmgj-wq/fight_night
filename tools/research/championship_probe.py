from __future__ import annotations

import json
from pathlib import Path

from pspdisasm import disassemble_file
from pspdisasm.elf32 import parse_elf32

TARGETS = [
    "GetRankingInformation",
    "aCurrentBeltHolders",
    "GetMyCareerStatsInfo",
    "aiTitleBeltsWon",
    "aiTitleBeltsDefended",
    "aiTitleBeltsLost",
    "aiTitleBeltsForfeited",
    "GetTrophyCaseInfo",
    "GetTrophyInfo",
    "GetViewAwardInfo",
    "strTrophyName",
    "strTrophyOwner",
    "strTimesDefended",
    "iTrophyID",
    "aTrophyIDs",
    "aTrophyTypes",
]

def offset_to_vaddr(elf, offset: int) -> int | None:
    for ph in elf.program_headers:
        if ph.type == 1 and ph.offset <= offset < ph.offset + ph.filesz:
            return ph.vaddr + (offset - ph.offset)
    for sec in elf.sections:
        if sec.type != 8 and sec.offset <= offset < sec.offset + sec.size:
            return sec.addr + (offset - sec.offset)
    return None

def function_for_address(result, address: int):
    for fn in result.functions:
        if fn.address <= address < fn.address + fn.size:
            return fn
    return None

def main() -> None:
    path = Path("BOOT.BIN")
    raw = path.read_bytes()
    elf = parse_elf32(raw)
    result = disassemble_file(path)

    refs_by_target: dict[int, list] = {}
    for ref in result.references:
        refs_by_target.setdefault(ref.target_address, []).append(ref)

    target_rows = []
    functions = {}
    for target in TARGETS:
        needle = target.encode("ascii") + b"\0"
        offsets = []
        start = 0
        while True:
            off = raw.find(needle, start)
            if off < 0:
                break
            offsets.append(off)
            start = off + 1

        locations = []
        for off in offsets:
            va = offset_to_vaddr(elf, off)
            refs = refs_by_target.get(va or -1, [])
            ref_rows = []
            for ref in refs:
                fn = function_for_address(result, ref.source_address)
                if fn is not None:
                    functions[fn.address] = fn
                ref_rows.append({
                    "source": f"0x{ref.source_address:08X}",
                    "kind": ref.kind,
                    "source_function": ref.source_function,
                    "containing_function": (
                        f"{fn.name}@0x{fn.address:08X}" if fn is not None else None
                    ),
                })
            locations.append({
                "file_offset": f"0x{off:X}",
                "vaddr": f"0x{va:08X}" if va is not None else None,
                "references": ref_rows,
            })
        target_rows.append({"target": target, "locations": locations})

    fn_rows = []
    for address, fn in sorted(functions.items()):
        callers = [
            {
                "source": f"0x{r.source_address:08X}",
                "source_function": r.source_function,
            }
            for r in result.references
            if r.kind == "call" and r.target_address == address
        ]
        outgoing = [
            {
                "source": f"0x{r.source_address:08X}",
                "target": f"0x{r.target_address:08X}",
                "kind": r.kind,
                "target_function": (
                    function_for_address(result, r.target_address).name
                    if function_for_address(result, r.target_address) is not None
                    else None
                ),
            }
            for r in result.references
            if fn.address <= r.source_address < fn.address + fn.size
        ]
        fn_rows.append({
            "name": fn.name,
            "address": f"0x{fn.address:08X}",
            "size": fn.size,
            "callers": callers,
            "outgoing": outgoing,
            "assembly": fn.assembly.splitlines()[:300],
        })

    print("CHAMPIONSHIP_PROBE_BEGIN")
    print(json.dumps({"targets": target_rows, "functions": fn_rows}, indent=2))
    print("CHAMPIONSHIP_PROBE_END")

if __name__ == "__main__":
    main()
