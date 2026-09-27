from __future__ import annotations

from pathlib import Path

from pspdisasm.disassembler import disassemble_file


DEFINITION_TARGETS = {
    0x00184B00,
    0x00185008,
    0x00185374,
    0x001853F0,
    0x00185434,
    0x00185468,
    0x0018549C,
    0x001854DC,
    0x00185A80,
    0x00185B30,
    0x00185B60,
    0x00185D84,
    0x00185F34,
    0x00185FA0,
    0x0018600C,
    0x001860A0,
    0x00186108,
    0x00186284,
    0x001A9020,
    0x001AF728,
    0x001B0FE8,
}

CALL_TARGETS = DEFINITION_TARGETS | {
    0x001851CC,
    0x0018553C,
}


def _instruction_window(fn, source_address: int, radius: int = 10) -> str:
    instructions = fn.instructions
    index = next(
        (i for i, instruction in enumerate(instructions) if instruction.address == source_address),
        None,
    )
    if index is None:
        return "<source instruction not found>"
    lo = max(0, index - radius)
    hi = min(len(instructions), index + radius + 2)
    lines = []
    for instruction in instructions[lo:hi]:
        marker = ">>" if instruction.address == source_address else "  "
        lines.append(
            f"{marker} 0x{instruction.address:08X}: "
            f"0x{instruction.word:08X}  {instruction.text}"
        )
    return "\n".join(lines)


def main() -> None:
    result = disassemble_file(Path("BOOT.BIN"))
    by_address = {fn.address: fn for fn in result.functions}
    by_name = {fn.name: fn for fn in result.functions}

    print("=== TARGET DEFINITIONS ===")
    for address in sorted(DEFINITION_TARGETS):
        fn = by_address.get(address)
        if fn is None:
            print(f"\n=== MISSING 0x{address:08X} ===")
            continue
        print(f"\n=== {fn.name} @ 0x{fn.address:08X} size=0x{fn.size:X} ===")
        print(fn.assembly)

    print("\n=== TARGET CALL SITES ===")
    for ref in result.references:
        if ref.kind != "call" or ref.target_address not in CALL_TARGETS:
            continue
        name = ref.source_function or "<unknown>"
        print(
            f"\nCALL 0x{ref.source_address:08X} {name} "
            f"-> 0x{ref.target_address:08X}"
        )
        fn = by_name.get(name)
        if fn is not None:
            print(_instruction_window(fn, ref.source_address))


if __name__ == "__main__":
    main()
