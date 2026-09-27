from pathlib import Path

from pspdisasm.disassembler import disassemble_file


result = disassemble_file(Path('BOOT.BIN'))
by_name = {fn.name: fn for fn in result.functions}
targets = {
    0x00185374: 'field_0B_helper',
    0x001853F0: 'field_0D_hi_byte',
    0x00185434: 'field_0D_lo_byte',
    0x00185468: 'field_0E_lo_nibble',
    0x0018549C: 'field_0E_mid_nibble',
    0x001854DC: 'field_0E_hi_nibble',
    0x00185B30: 'boxer_field_helper_185B30',
    0x00185170: 'boxer_field_helper_185170',
    0x00185520: 'rating_slot_helper',
}

callers: dict[str, set[int]] = {}
for ref in result.references:
    if ref.kind == 'call' and ref.target_address in targets and ref.source_function:
        callers.setdefault(ref.source_function, set()).add(ref.target_address)

for name in sorted(callers, key=lambda n: by_name[n].address if n in by_name else 0):
    fn = by_name.get(name)
    if fn is None:
        continue
    print(
        f'\n=== CALLER {fn.name} @ 0x{fn.address:08X} size=0x{fn.size:X} '
        f'targets={[targets[t] for t in sorted(callers[name])]} ==='
    )
    fn_end = fn.address + fn.size
    refs = [
        st for st in result.strings
        if any(fn.address <= src < fn_end for src in st.referenced_by)
    ]
    if refs:
        print('STRINGS:')
        for st in refs:
            print(f'  0x{st.address:08X}: {st.value!r}')
    print(fn.assembly)


BIO_STRINGS = {
    "ViewBoxerBio",
    "strBoxerFirstName",
    "strBoxerLastName",
    "strBoxerRecord",
    "strRivalFirstName",
    "strRivalLastName",
    "iTitleBeltsWon",
    "iTitleBeltsLost",
    "strNickName",
    "strHomeTown",
    "strStance",
    "strStyle",
    "iAge",
}

print("\n=== BOXER BIO NATIVE/OUTPUT STRING XREFS ===")
bio_functions: set[str] = set()
for st in result.strings:
    if st.value not in BIO_STRINGS:
        continue
    print(
        f"STRING 0x{st.address:08X} {st.value!r} "
        f"refs={[f'0x{x:08X}' for x in st.referenced_by]}"
    )
    for src in st.referenced_by:
        owner = next(
            (
                fn
                for fn in result.functions
                if fn.address <= src < fn.address + fn.size
            ),
            None,
        )
        if owner is not None:
            bio_functions.add(owner.name)

for name in sorted(
    bio_functions,
    key=lambda n: by_name[n].address if n in by_name else 0,
):
    fn = by_name.get(name)
    if fn is None:
        continue
    print(f"\n=== BIO XREF FUNCTION {fn.name} @ 0x{fn.address:08X} size=0x{fn.size:X} ===")
    print(fn.assembly)
