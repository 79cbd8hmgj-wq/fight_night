# XDB Schema and Boxer Ownership Decompilation Package

## Status

**Task 11 (static portion only) -- container-level ownership and the shared xdb header format are static_mapped-grade; per-record boxer field schema remains open. Not a Class A complete package: the decompilation gate's field-level, lifecycle, and consumer-inventory requirements are not all satisfied.**

This package pushes `config/subsystem_registry.json`'s `program-04` ("Boxers") blocking unknown -- previously the single line "field schema pending" -- as far as static evidence permits: from "we don't know how the boxer database is loaded or owned" to "we know exactly how it is loaded, owned, and singleton-stored, and we know precisely which specific per-record questions remain and why static analysis cannot answer them." No PPSSPP execution, debugger session, save state, breakpoint, or gameplay experiment was performed.

## Locked source

Same as `docs/decomp/packages/resource-loaders/README.md`: `BOOT.BIN`, SHA-256 `906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9`, repository-root sample used only because its hash matches the tracked golden fixture and locked revision.

Machine-readable evidence:

```text
analysis/resources/xdbboxr-schema.json
analysis/resources/boxer-ownership-map.json
analysis/resources/xdb-schema-evidence.json
analysis/resources/static-resolution-matrix.json
```

Parser code:

```text
src/fnr3_re/xdb.py   (the proven shared xdb table header; see tests/unit/test_xdb.py)
```

## The shared xdb table header

All 10 decoded `xdbNNNN.adf` tables in `preload/db.viv` (compressed sizes 256-8204 bytes, decoded 436-18252 bytes) open with the identical 8-word (32-byte) little-endian structure, parsed by `src/fnr3_re/xdb.py::parse_xdb_header`. Two words are small counts of undetermined meaning; three words are usually (9 of 10 tables) equal to each other and describe a leading section size, with `xdbtrain.adf` proving by exact counter-example that they are not always three redundant copies of one field. Full per-table values are in `analysis/resources/xdb-schema-evidence.json`.

Field names in the parser and in the evidence JSON are deliberately neutral (`word0`, `word1`, `section_size_a/b/c`) rather than semantic, per the repository's evidence discipline: no static consumer of these fields was located that would justify naming them.

## Boxer ownership chain

Tracing forward from `preload/db.viv!xdbboxr.adf` through `BOOT.BIN`'s executable code (full chain and addresses in `analysis/resources/boxer-ownership-map.json`):

```text
xdbboxr.adf (archive member)
  -> func_001863B4  (boxer-specific loader trampoline, 0x30 bytes)
       -> func_00186408  (lazily-initialized singleton accessor)
            -> backing object at ELF virtual 0x000080B4 (func_00007E80 + 0x234)
       -> func_001A0C74  (shared generic per-table loader; see resource-loaders package)
            -> populates the singleton: +0x0 loaded flag, +0x4 size, +0x8 decoded-payload pointer
```

Six functions in the entire 24,576-function `BOOT.BIN` disassembly directly call the singleton accessor (`func_00186408`): the loader trampoline itself, and five consumers. Two of those five were disassembled and interpreted (`func_00186464`, `func_001863E4`, `func_00185114` -- three, not two; see the ownership map for exact roles); two more (`T_0018E4F4`, `func_001AF768`) were identified by the same whole-binary search but not yet disassembled in this pass.

The most concrete fact found: **`func_00186464` masks its index argument to 8 bits** (`andi $s1, $a0, 0xFF` at ELF virtual `0x0018646C`) before using it to walk a linked list from the boxer table singleton via each visited node's `+0x10` field. This directly answers the task's "ID/index width" question for this specific accessor (8 bits, 0-255) -- but whether each visited node is one boxer record or something else (a table-instance registration) is exactly the kind of question static analysis cannot finish alone; see the `RUNTIME_BLOCKED` entries below.

## What remains open: `xdbboxr.adf`'s per-record schema

`analysis/resources/xdbboxr-schema.json` is the versioned static model for this table. It contains **zero** semantic field entries (name, rating, weight, division, stance, handedness, appearance, hair, shorts, hometown, career state, rivals, training, store-unlock, created-boxer data) because none were located: dividing the header's leading-section size by either count-like header word does not produce an integer stride for any plausible header size, and the one runtime accessor found (`func_00186464`) walks a linked list rather than doing `index * stride` array arithmetic -- meaning the record boundary is not the simple flat array the header alone would suggest, and the actual per-record field accessor function was not located among the other ~24,000 functions in `BOOT.BIN` in this pass. Every uncertain quantity is kept under a neutral name (`word0`, `word1`, `section_size_a`) rather than a guessed field name, per the evidence standard's explicit prohibition on promoting a claim from "a plausible numeric value" alone.

## Cross-resource relationships found

- `preload/tables.viv`'s boxer-surname `.txt` files (`ali.txt`, `hatton.txt`, `lazcano.txt`, `leonard.txt`, `morales.txt`, `pacquiao.txt`, `robinson.txt`, plus a non-boxer `punchout.txt`) share exact name stems with 8 of `preload/bootpreloads.viv`'s `HK_*.bh` preload descriptors. CANDIDATE only -- no executable code path connecting the two archives was traced.
- `scripts/scripts.viv` and `scripts/scrptpal.viv` hold the identical 167 member names, order, and per-member sizes, but `scripts.viv`'s are RefPack-compressed and `scrptpal.viv`'s are not; a sampled member pair proves the two files share identical framing and most byte positions but differ in specific integer fields -- two distinct, same-shaped parameter sets, not a decompressed duplicate. PROBABLE for the structural claim; the reason two sets exist is `RUNTIME_BLOCKED` and out of this package's boxer/resource-loader scope.
- `preload/boxerpre.viv`'s shared base model/shadow pair plus 8 face-region damage morph targets are structurally consistent with the Medical/damage subsystem's (`program-10`) visualization needs. CANDIDATE only -- no executable code path traced.

## `config/subsystem_registry.json`

`program-04` ("Boxers") was moved from `candidate` to `static_mapped` on the strength of the container-level, dispatcher-level, and singleton-ownership findings above -- the same evidentiary bar `program-03` ("Modules") already met. Its `blocking_unknowns` was narrowed from the single generic line "field schema pending" to the two specific open questions this package could not resolve: `xdbboxr.adf`'s per-record field layout, and the semantic meaning of `func_00186464`'s linked-list index. This is not a claim that `program-04` is complete, functionally reconstructed, or ready for Phase II -- see `docs/architecture/decompilation-gate.md`'s Class A requirements, most of which (readers/writers/callers/callees enumeration, lifecycle coverage, original-behavior tests, replacement boundary) remain unaddressed.

## Verification

```text
4 new unit tests (tests/unit/test_xdb.py) -- pass
Full repository test suite -- see PR for the run recorded at merge time
Ruff and strict mypy -- clean
```

## Explicitly unresolved (see `analysis/resources/static-resolution-matrix.json` and `runtime-minimum-backlog.json`)

- `xdbboxr.adf`'s exact record count, record stride, and per-field offsets/widths/signedness.
- Whether header word0 (121) is a record count and word1 (37) a field count, or something else.
- Whether `func_00186464`'s linked-list walk indexes boxer records or table-instance registrations.
- The two consumer functions identified but not yet disassembled (`T_0018E4F4`, `func_001AF768`).
- Any semantic meaning for `xdbvenue`/`xdbalias`/`xdbevent`/`xdbhmtwn`/`xdbstore`/`xdbpref`/`xdbrivl`/`xdbtrain`/`xdbcutpn` beyond the shared header -- only their own singleton-accessor addresses and shared-loader reuse were confirmed; no per-table field work was attempted for these nine.

## Next checkpoint

**Locate a direct (non-linked-list) accessor into the boxer table singleton's `+0x8` payload pointer, if one exists, before concluding a runtime experiment is required to resolve the record stride.**
