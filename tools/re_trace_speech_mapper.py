from pathlib import Path

from pspdisasm.disassembler import disassemble_file


r = disassemble_file(Path("BOOT.BIN"))
by_name = {fn.name: fn for fn in r.functions}
by_addr = {fn.address: fn for fn in r.functions}

def emit_addr(addr: int) -> None:
    fn = by_addr.get(addr)
    if fn is None:
        print(f"NO FUNCTION 0x{addr:08X}")
        return
    print(f"=== {fn.name} @ 0x{fn.address:08X} size=0x{fn.size:X} ===")
    for st in r.strings:
        if any(fn.address <= src < fn.address + fn.size for src in st.referenced_by):
            print(f"STRING 0x{st.address:08X}: {st.value!r}")
    print(fn.assembly)

for addr in (0x0010C9C8, 0x00108F9C, 0x0010BB58, 0x003E5860):
    emit_addr(addr)

print("=== CALLERS OF SPEECH-CANDIDATE FUNCTIONS ===")
for target in (0x00108F9C, 0x0010BB58, 0x003E5860):
    print(f"-- target 0x{target:08X} --")
    for ref in r.references:
        if ref.kind == "call" and ref.target_address == target:
            print(f"0x{ref.source_address:08X} {ref.source_function or '<unknown>'}")

print("=== SPEECH/COMMENTARY STRINGS AND OWNERS ===")
for st in r.strings:
    low = st.value.lower()
    if any(k in low for k in ("speech", "comment", "announce", "pocketdj")):
        owners = []
        for src in st.referenced_by:
            owner = next((fn for fn in r.functions if fn.address <= src < fn.address + fn.size), None)
            if owner is not None:
                owners.append(f"{owner.name}@0x{src:08X}")
        print(f"0x{st.address:08X}: {st.value!r} owners={owners}")
