from pathlib import Path

from pspdisasm.disassembler import disassemble_file

r = disassemble_file(Path('BOOT.BIN'))
by_addr = {fn.address: fn for fn in r.functions}

targets = [
    0x00185008,
    0x001857E4,
    0x001A9020,
    0x00186108,
]

for address in targets:
    fn = by_addr.get(address)
    print(f'\n=== TARGET 0x{address:08X} ===')
    if fn is None:
        print('not found')
        continue
    print(f'{fn.name} size=0x{fn.size:X}')
    end = fn.address + fn.size
    for st in r.strings:
        if any(fn.address <= src < end for src in st.referenced_by):
            print(f'STRING 0x{st.address:08X}: {st.value!r}')
    print(fn.assembly)

    print('CALLERS:')
    for ref in r.references:
        if ref.kind == 'call' and ref.target_address == address:
            print(f'  0x{ref.source_address:08X} {ref.source_function or "<unknown>"}')
