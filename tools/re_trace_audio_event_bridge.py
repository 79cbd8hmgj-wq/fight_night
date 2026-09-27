from pathlib import Path

from pspdisasm.disassembler import disassemble_file

r = disassemble_file(Path('BOOT.BIN'))

for target in (0x003E5860, 0x003E4A94):
    print(f'\n=== CONTAINING FUNCTION FOR 0x{target:08X} ===')
    fn = next((f for f in r.functions if f.address <= target < f.address + f.size), None)
    if fn is None:
        print('none')
    else:
        print(f'{fn.name} @ 0x{fn.address:08X} size=0x{fn.size:X}')
        end = fn.address + fn.size
        for st in r.strings:
            if any(fn.address <= src < end for src in st.referenced_by):
                print(f'STRING 0x{st.address:08X}: {st.value!r}')
        print(fn.assembly)

print('\n=== DATA / STRINGS 0x0055AAF0..0x0055AB60 ===')
for st in r.strings:
    if 0x0055AAF0 <= st.address < 0x0055AB60:
        print(f'STRING 0x{st.address:08X}: {st.value!r} refs={st.referenced_by}')
for ref in r.references:
    if 0x0055AAF0 <= ref.target_address < 0x0055AB60:
        print(
            f'REF 0x{ref.source_address:08X} {ref.source_function or "<unknown>"} '
            f'-> 0x{ref.target_address:08X} ({ref.kind})'
        )

print('\n=== func_0010C9C8 CALLERS, COMPACT ===')
target=0x0010C9C8
for ref in r.references:
    if ref.kind == 'call' and ref.target_address == target:
        print(f'0x{ref.source_address:08X} {ref.source_function or "<unknown>"}')
