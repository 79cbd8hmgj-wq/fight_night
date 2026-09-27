from pathlib import Path

from pspdisasm.disassembler import disassemble_file


result = disassemble_file(Path("BOOT.BIN"))
by_name = {fn.name: fn for fn in result.functions}


def window(fn_name: str, source: int, radius: int = 18) -> None:
    fn = by_name[fn_name]
    index = next(i for i, insn in enumerate(fn.instructions) if insn.address == source)
    lo = max(0, index - radius)
    hi = min(len(fn.instructions), index + radius + 2)
    print(f"\n=== {fn_name} around 0x{source:08X} ===")
    for insn in fn.instructions[lo:hi]:
        mark = ">>" if insn.address == source else "  "
        print(f"{mark} 0x{insn.address:08X}  {insn.text}")


for ref in result.references:
    if ref.kind != "call":
        continue
    if ref.source_function == "func_0010BB58" and ref.target_address in {
        0x0010C9C8,
        0x003E5860,
        0x001091D8,
    }:
        print(
            f"BRIDGE call 0x{ref.source_address:08X}: "
            f"func_0010BB58 -> 0x{ref.target_address:08X}"
        )
        window("func_0010BB58", ref.source_address)

for ref in result.references:
    if ref.kind == "call" and ref.target_address == 0x0010BB58:
        print(
            f"CALLER 0x{ref.source_address:08X}: "
            f"{ref.source_function or '<unknown>'} -> func_0010BB58"
        )
        if ref.source_function in by_name:
            window(ref.source_function, ref.source_address, 12)

# The Decision Announcement Script owner is a separate commentary lead.
fn = by_name.get("func_000B065C")
if fn is not None:
    print(f"\n=== func_000B065C @ 0x{fn.address:08X} size=0x{fn.size:X} ===")
    for st in result.strings:
        if st.value == "Decision Announcement Script":
            for src in st.referenced_by:
                if fn.address <= src < fn.address + fn.size:
                    window("func_000B065C", src, 16)
