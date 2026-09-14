# Resource Loaders Decompilation Package

## Status

**Task 10 -- corpus-wide static pass (second PR #31 commit). Loaders traced for `preload/db.viv` (all 10 xdb tables), `contract/contracts.viv` (all 3 .fnc members), and a second, distinct data-driven registry mechanism found this pass covering 9 boxer-appearance-family archives. `preload/tables.viv`, `preload/boxerpre.viv`, `scripts/scripts.viv`, and `preload/bootpreloads.viv` remain enumerated and RefPack-verified but not yet traced to a loader function -- see `analysis/resources/static-discovery-backlog.json` for named next steps on each.**

This pass also expanded from the original 7 target archives to a corpus-wide inventory (428 top-level files classified; see `analysis/resources/corpus-resource-index.json`), proved a second compression codec (`.zlb`, zlib-based, `src/fnr3_re/zlb.py`), and reassembled/hash-verified/enumerated `actors.viv` (1657 members).

This package records how the game's EA BIG/VIV archives and their RefPack-compressed members are opened, looked up, and handed to per-table loading code inside `BOOT.BIN`. It reuses the Task 5 archive/RefPack codecs unmodified (`docs/architecture/resource-codecs.md`) and does not re-prove container or compression format -- it moves inward to the functions that actually call those codecs at runtime.

No PPSSPP execution, debugger session, save state, breakpoint, or gameplay experiment was performed for this package. Every claim below is derived from static disassembly of a hash-verified `BOOT.BIN` sample plus deterministic decoding of the tracked archive samples.

## Locked source

- Revision: `ULUS10066-v1.00`
- Module: `BOOT.BIN`
- SHA-256: `906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9`
- Format: plain ELF32 little-endian MIPS/PSP executable
- Address mapping: exact ELF virtual addresses (no relocated/runtime placement was used or needed for this package)

Repository-root `BOOT.BIN` is legacy/non-authoritative as a workspace input; it is used here only because its hash matches the tracked golden fixture (`analysis/modules/tracked-module-map.json`) and the locked revision, following the same precedent the Task 9 save-system package already established. No verified `<workspace>/original/` was available in this session.

Machine-readable evidence:

```text
analysis/resources/corpus-resource-index.json      (new this pass: corpus-wide inventory)
analysis/resources/loader-hierarchy.json           (new this pass: loader architecture as a tree)
analysis/resources/resource-loader-map.json
analysis/resources/xdb-schema-evidence.json
analysis/resources/static-resolution-matrix.json
analysis/resources/runtime-minimum-backlog.json    (empty this pass)
analysis/resources/static-discovery-backlog.json   (new this pass)
```

Codec and parser code reused/added:

```text
src/fnr3_re/ea_archive.py   (Task 5, unmodified)
src/fnr3_re/refpack.py      (Task 5, unmodified)
src/fnr3_re/xdb.py          (the proven shared xdb table header only)
src/fnr3_re/zlb.py          (new this pass: the proven .zlb codec, a second compression format distinct from RefPack)
```

## Archive enumeration and RefPack coverage

The 7 archives named as Task 10/11 primary targets were parsed with the existing `parse_ea_archive`/`decompress_refpack` codecs (repository-root historical samples; the caveat above applies). Result: 511 total members across all 7 archives, of which 335 are RefPack-compressed. **All 335 decode cleanly** -- exact declared-size match, zero trailing bytes after the stop command, and a self-consistent decode/encode round trip through the existing codec (`decompress_refpack(compress_refpack(decoded)) == decoded` for every member). The 176 non-RefPack members are exact-match negatives (no `10 FB`/`90 FB` signature), not decode failures: the entirety of `scripts/scrptpal.viv` (167 members) and 9 of `preload/bootpreloads.viv`'s 80 members store their content uncompressed.

Full per-archive member lists, sizes, and RefPack status are in `analysis/resources/xdb-schema-evidence.json`'s `sibling_archives_investigated` section; the exact byte-perfect proof this claim rests on is the codec's own existing decode/encode contract (`docs/architecture/resource-codecs.md`), not a new format this package invented.

## The `preload/db.viv` dispatcher

`func_001AD694` (`BOOT.BIN`, ELF virtual `0x001AD694`) is a single bitmask-driven dispatcher: its first argument selects, one bit per table, which of `preload/db.viv`'s 10 `xdbNNNN.adf` members to open this call. The bit-to-table mapping (bit `0x001` = `xdbboxr.adf` through bit `0x200` = `xdbcutpn.adf`) was proven two independent ways -- once from the extracted string table's own address for each table name, and once from the `lui`/`addiu` `%hi`/`%lo` operand pair immediately preceding each table's trampoline call inside the dispatcher -- and the two extractions agree exactly for all 10 tables.

Every requested table follows the identical three-hop shape:

```text
func_001AD694 (dispatcher, tests one bitmask bit)
  -> func_0033B58C (shared: find archive member by name, returns opaque handle)
  -> <table-specific trampoline, 0x30 bytes / 12 instructions, identical shape for all 10 tables>
       -> <table-specific singleton accessor, e.g. func_00186408 for xdbboxr.adf>
       -> func_001A0C74 (shared: generic per-table loader, reused verbatim by all 10 tables)
```

`func_001A0C74` reads a decode/extract function pointer out of the archive-member handle's own sub-object (a vtable-like `{length: i16 @ +0x20, funcptr: u32 @ +0x24}` pair) and invokes it, then stores the result pointer and a size value into the caller-supplied table singleton. This single shared function is why all 10 xdb tables can be documented once instead of ten times -- see `analysis/resources/resource-loader-map.json` for the full per-table address table.

## `contract/contracts.viv`

Each of the 3 `.fnc` members is referenced from a distinct function (`cutman.fnc` from `func_001A023C`, `fights.fnc` from `func_001A3D48`, `trainer.fnc` from `func_001B9334`), unlike the shared-dispatcher shape above. None of the three referencing functions were traced further in this pass beyond locating the string xref.

## A second, data-driven registry mechanism

This pass found a completely different resource-dispatch mechanism from `func_001AD694`'s bitmask dispatcher: a 9-entry, 16-byte-stride array at ELF virtual `0x567D60`, each entry `{name_ptr, word1, word2, word3}`, listing `misc.viv` (referenced but absent from the currently-tracked corpus), `boxersh.viv`, `actors.viv`, `cboxshr.viv`, `boxerpre.viv`, `allhair.viv`, `boxmisc.viv`, `boxmisc2.viv`, and `tables.viv`. **This table's own string references were missed entirely by this project's automated string/xref extraction** -- they were found only by a direct raw-byte search of `BOOT.BIN`, cross-checked against (but not taken on the authority of) a pre-existing, pre-evidence-standard exploratory audit already on disk. The practical lesson, recorded in `analysis/resources/resource-loader-map.json`'s `discovery_methodology_note`: absence from the automated extraction does not prove a resource is unreferenced. See `analysis/resources/loader-hierarchy.json` for the full architecture as a tree.

## Not yet traced

`preload/tables.viv`'s and `preload/bootpreloads.viv`'s own dispatch logic (the registry table above lists `tables.viv` but its consuming function was not located); `scripts/scripts.viv` has one xref (inside `func_000852BC`); **`scripts/scrptpal.viv` has zero string references anywhere in `BOOT.BIN`'s extracted string table** -- deferred to program-05/06 static analysis, out of Task 10/11 scope (see `analysis/resources/static-resolution-matrix.json`).

## Verification

```text
11 unit tests (tests/unit/test_xdb.py: 4, tests/unit/test_zlb.py: 7) -- pass
Full repository test suite -- see PR for the run recorded at merge time
Ruff and strict mypy -- clean
```

## Explicitly unresolved (see `analysis/resources/static-resolution-matrix.json` and `static-discovery-backlog.json`)

Every open question from this pass is STATIC_PENDING with a named next avenue, not RUNTIME_BLOCKED -- see `analysis/resources/static-discovery-backlog.json` for the full list, including: the consumer of the 9-entry registry table; loaders for `preload/tables.viv` and `preload/bootpreloads.viv`'s dispatch; and whether `scripts/scrptpal.viv` is opened by any code path reachable from `BOOT.BIN` at all.

## Next checkpoint

**Trace the pointer at ELF virtual `0x6DE908` (a raw pointer to the registry table's base address, found in a data region) to the function that actually walks the 9-entry table, and locate the loader/dispatch function for `preload/tables.viv`.**
