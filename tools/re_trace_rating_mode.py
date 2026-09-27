from pathlib import Path

from pspdisasm.disassembler import disassemble_file

r = disassemble_file(Path("BOOT.BIN"))
by_name = {fn.name: fn for fn in r.functions}

def emit(fn_name: str) -> None:
    fn = by_name.get(fn_name)
    if fn:
        print(f"=== {fn.name} @ 0x{fn.address:08X} size=0x{fn.size:X} ===")
        print(fn.assembly)

for name in ("T_00187434", "func_00187548", "func_0018ADCC", "T_001D48A4"):
    emit(name)

print("=== CALLERS ===")
for target in (0x00187434, 0x00187548, 0x0018ADCC):
    print(f"-- target 0x{target:08X} --")
    seen = set()
    for ref in r.references:
        if ref.kind == "call" and ref.target_address == target:
            print(f"0x{ref.source_address:08X} {ref.source_function or '<unknown>'}")
            if ref.source_function and ref.source_function not in seen:
                seen.add(ref.source_function)
                emit(ref.source_function)

print("=== STRINGS 0x0050A000..0x0050B800 ===")
for st in r.strings:
    if 0x0050A000 <= st.address < 0x0050B800:
        print(f"0x{st.address:08X} {st.value!r} refs={','.join(f'0x{x:08X}' for x in st.referenced_by)}")
