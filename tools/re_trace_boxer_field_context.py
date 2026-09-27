from pathlib import Path

from pspdisasm.disassembler import disassemble_file


result = disassemble_file(Path("BOOT.BIN"))
by_name = {fn.name: fn for fn in result.functions}
by_addr = {s.address: s for s in result.strings}

targets = {
    "func_0010C9C8",
    "func_00197DAC",
    "func_0019CFF8",
    "func_0019EFD0",
    "func_00187DE0",
    "func_00189178",
    "func_0018A110",
}

for name in sorted(targets):
    fn = by_name.get(name)
    if fn is None:
        continue
    lo, hi = fn.address, fn.address + fn.size
    print(f"=== {name} 0x{lo:08X}-0x{hi:08X} ===")
    refs = [
        ref for ref in result.references
        if lo <= ref.source_address < hi and ref.target_address in by_addr
    ]
    for ref in refs:
        st = by_addr[ref.target_address]
        print(
            f"0x{ref.source_address:08X} -> 0x{st.address:08X}: "
            f"{st.value!r}"
        )

print("=== jump tables ===")
for jt in result.jump_tables:
    if jt.source_function in targets:
        print(
            f"{jt.source_function} table=0x{jt.address:08X} "
            f"source=0x{jt.source_address:08X} targets="
            + ",".join(f"0x{x:08X}" for x in jt.targets)
        )
