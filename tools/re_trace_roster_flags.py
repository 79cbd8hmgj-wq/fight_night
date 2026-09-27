from pathlib import Path

from pspdisasm.disassembler import disassemble_file


result = disassemble_file(Path("BOOT.BIN"))
by_name = {fn.name: fn for fn in result.functions}

print("=== refs to roster flag table ===")
seen = set()
for ref in result.references:
    if 0x0056477C <= ref.target_address < 0x00564820:
        print(
            f"0x{ref.source_address:08X} "
            f"{ref.source_function or '<unknown>'} -> "
            f"0x{ref.target_address:08X} ({ref.kind})"
        )
        name = ref.source_function
        if name and name in by_name and name not in seen:
            seen.add(name)
            fn = by_name[name]
            print(f"--- {fn.name} @ 0x{fn.address:08X} size=0x{fn.size:X} ---")
            print(fn.assembly)

print("=== callers of T_00278ABC ===")
for ref in result.references:
    if ref.kind == "call" and ref.target_address == 0x00278ABC:
        print(
            f"0x{ref.source_address:08X} "
            f"{ref.source_function or '<unknown>'} -> 0x00278ABC"
        )
        name = ref.source_function
        if name and name in by_name and name not in seen:
            seen.add(name)
            fn = by_name[name]
            print(f"--- {fn.name} @ 0x{fn.address:08X} size=0x{fn.size:X} ---")
            print(fn.assembly)
