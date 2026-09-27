from __future__ import annotations

import struct
from pathlib import Path

from pspdisasm.disassembler import disassemble_file


BOOT = Path('BOOT.BIN')
SWITCH_TABLE_VADDR = 0x00505FD8
SWITCH_COUNT = 0x4C
TARGET_FUNC = 0x0010C9C8


def vaddr_to_offset(data: bytes, vaddr: int) -> int:
    if data[:4] != b'\x7fELF':
        raise RuntimeError('BOOT.BIN is not ELF')
    phoff = struct.unpack_from('<I', data, 0x1C)[0]
    phentsize = struct.unpack_from('<H', data, 0x2A)[0]
    phnum = struct.unpack_from('<H', data, 0x2C)[0]
    for i in range(phnum):
        off = phoff + i * phentsize
        p_type, p_offset, p_vaddr, _p_paddr, p_filesz, _p_memsz, _flags, _align = (
            struct.unpack_from('<8I', data, off)
        )
        if p_type == 1 and p_vaddr <= vaddr < p_vaddr + p_filesz:
            return p_offset + (vaddr - p_vaddr)
    raise RuntimeError(f'vaddr 0x{vaddr:08X} not in a PT_LOAD file range')


def main() -> None:
    data = BOOT.read_bytes()
    result = disassemble_file(BOOT)
    by_address = {fn.address: fn for fn in result.functions}

    fn = by_address[TARGET_FUNC]
    print(f'=== FIELD5 CALLER {fn.name} @ 0x{fn.address:08X} size=0x{fn.size:X} ===')
    print(fn.assembly)

    table_off = vaddr_to_offset(data, SWITCH_TABLE_VADDR)
    entries = struct.unpack_from(f'<{SWITCH_COUNT}I', data, table_off)
    print('\n=== FIELD5 SWITCH TABLE 0..75 ===')
    for i, target in enumerate(entries):
        print(f'{i:02d}: 0x{target:08X}')

    print('\n=== UNIQUE TARGETS / CASE INDICES ===')
    groups: dict[int, list[int]] = {}
    for i, target in enumerate(entries):
        groups.setdefault(target, []).append(i)
    for target, indices in sorted(groups.items()):
        print(f'0x{target:08X}: {indices}')

    print('\n=== CALLERS OF FIELD5 MAPPER ===')
    printed: set[str] = set()
    for ref in result.references:
        if ref.kind != 'call' or ref.target_address != TARGET_FUNC:
            continue
        name = ref.source_function or '<unknown>'
        print(f'CALL 0x{ref.source_address:08X} {name} -> 0x{TARGET_FUNC:08X}')
        fn_by_name = next((x for x in result.functions if x.name == name), None)
        if fn_by_name is not None and name not in printed:
            printed.add(name)
            print(f'--- {fn_by_name.name} @ 0x{fn_by_name.address:08X} size=0x{fn_by_name.size:X} ---')
            refs = [
                st for st in result.strings
                if any(fn_by_name.address <= src < fn_by_name.address + fn_by_name.size for src in st.referenced_by)
            ]
            for st in refs:
                print(f'STRING 0x{st.address:08X}: {st.value!r}')
            print(fn_by_name.assembly)

    print('\n=== REFERENCES FROM FIELD5 CALLER ===')
    for ref in result.references:
        if ref.source_function == fn.name:
            target = 'None' if ref.target_address is None else f'0x{ref.target_address:08X}'
        print(f'0x{ref.source_address:08X} {ref.kind} -> {target}')


if __name__ == '__main__':
    main()
