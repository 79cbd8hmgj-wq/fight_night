from pathlib import Path

from pspdisasm.disassembler import disassemble_file


result = disassemble_file(Path("BOOT.BIN"))
by_name = {fn.name: fn for fn in result.functions}
targets = {
    0x0010C9C8,
    0x0013D5CC,
    0x00197DAC,
    0x0019CFF8,
    0x0019EFD0,
}
seen = set()
for ref in result.references:
    if ref.kind != "call" or ref.target_address not in targets:
        continue
    print(
        f"CALL 0x{ref.source_address:08X} "
        f"{ref.source_function or '<unknown>'} -> "
        f"0x{ref.target_address:08X}"
    )
    name = ref.source_function
    if name and name in by_name and name not in seen:
        seen.add(name)
        fn = by_name[name]
        print(f"--- {fn.name} @ 0x{fn.address:08X} size=0x{fn.size:X} ---")
        print(fn.assembly)
