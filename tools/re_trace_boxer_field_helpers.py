from pathlib import Path

from pspdisasm.disassembler import disassemble_file


result = disassemble_file(Path("BOOT.BIN"))
by_name = {fn.name: fn for fn in result.functions}
targets = {
    0x00185374,
    0x001853F0,
    0x00185434,
    0x00185468,
    0x0018549C,
    0x001854DC,
    0x00185B30,
    0x00185F34,
    0x00185FA0,
    0x001860A0,
    0x00186108,
}

printed = set()
for ref in result.references:
    if ref.kind != "call" or ref.target_address not in targets:
        continue
    print(
        f"CALL 0x{ref.source_address:08X} "
        f"{ref.source_function or '<unknown>'} -> "
        f"0x{ref.target_address:08X}"
    )
    name = ref.source_function
    if name and name in by_name and name not in printed:
        printed.add(name)
        fn = by_name[name]
        print(f"--- {fn.name} @ 0x{fn.address:08X} size=0x{fn.size:X} ---")
        print(fn.assembly)
