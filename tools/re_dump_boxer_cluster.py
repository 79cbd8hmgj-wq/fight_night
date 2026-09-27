from __future__ import annotations

from pathlib import Path

from pspdisasm.disassembler import disassemble_file


def main() -> None:
    result = disassemble_file(Path('BOOT.BIN'))
    lo = 0x00184F00
    hi = 0x00186580
    print('=== BOXER CLUSTER ===')
    for fn in result.functions:
        if lo <= fn.address < hi:
            print(f'\n=== {fn.name} @ 0x{fn.address:08X} size=0x{fn.size:X} ===')
            print(fn.assembly)

    targets = {
        0x001ACD40,
        0x0018553C,
        0x001851CC,
        0x00185D84,
        0x0018600C,
        0x00186284,
    }
    print('\n=== CALLERS OF KEY BOXER/XDB HELPERS ===')
    by_name = {fn.name: fn for fn in result.functions}
    emitted: set[str] = set()
    for ref in result.references:
        if ref.kind == 'call' and ref.target_address in targets:
            name = ref.source_function or '<unknown>'
            print(f'0x{ref.source_address:08X} {name} -> 0x{ref.target_address:08X}')
            if name in by_name and name not in emitted:
                emitted.add(name)
                fn = by_name[name]
                print(f'--- caller {fn.name} @ 0x{fn.address:08X} size=0x{fn.size:X} ---')
                print(fn.assembly)


if __name__ == '__main__':
    main()
