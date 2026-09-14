# XDB Schema and Boxer Ownership Decompilation Package

## Status

**Task 11 (static portion only), second pass -- container-level ownership, the shared xdb header format, and (new this pass) direct proof that header word0 is consumed as a genuine per-entry count are static_mapped-grade. Per-record boxer field schema past the newly-found flags array remains open, and is tracked as STATIC_PENDING with named next avenues, not RUNTIME_BLOCKED. Not a Class A complete package.**

This package continues pushing `config/subsystem_registry.json`'s `program-04` ("Boxers") as far as static evidence permits. Per this task's explicit instruction, every question this package previously marked `RUNTIME_BLOCKED` was re-examined for remaining static avenues before any runtime classification was allowed to stand -- none had actually exhausted the corpus/executable dependency graph, so all were reclassified `STATIC_PENDING`. No PPSSPP execution, debugger session, save state, breakpoint, or gameplay experiment was performed.

## Locked source

Same as `docs/decomp/packages/resource-loaders/README.md`: `BOOT.BIN`, SHA-256 `906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9`.

Machine-readable evidence:

```text
analysis/resources/xdbboxr-schema.json         (model_version 2 this pass)
analysis/resources/boxer-ownership-map.json    (schema_version 2 this pass)
analysis/resources/xdb-schema-evidence.json
analysis/resources/static-resolution-matrix.json
analysis/resources/static-discovery-backlog.json
analysis/resources/corpus-resource-index.json
```

Parser code:

```text
src/fnr3_re/xdb.py   (the proven shared xdb table header; see tests/unit/test_xdb.py)
```

## The shared xdb table header, revised

All 10 decoded `xdbNNNN.adf` tables still open with the identical 8-word (32-byte) structure parsed by `src/fnr3_re/xdb.py::parse_xdb_header`. This pass found direct executable evidence changing how two of those words should be understood:

- **word0 is proven, not merely plausible, to be consumed as a genuine per-entry loop count.** `func_001AD268` (ELF virtual `0x001AD268`) reads the boxer singleton's `+0x8` payload pointer, reads word0 from that payload, and uses it directly as the upper bound of a scanning loop. This is a real-code consumption, not an inference from the number 121 "looking like" a plausible boxer count.
- **Payload offset `+0x18` -- previously modeled as a scalar "word6" -- is very likely the start of a packed 2-bit-per-entry array of `word0` entries**, not a reserved field. `func_001AD268` indexes it as `payload+0x18+(index>>2)` and extracts 2 bits per entry. This directly explains why "word6" was zero for every table with `word0 <= 12` (the array fits in under 4 bytes) and non-zero for `xdbboxr.adf` (121 entries -> 31 bytes) and `xdbcutpn.adf`.

Full details: `analysis/resources/xdb-schema-evidence.json`'s `revised_this_pass` and `analysis/resources/boxer-ownership-map.json`'s `header_word0_proof`/`revised_header_model`.

## Boxer ownership chain, extended

```text
xdbboxr.adf (archive member)
  -> func_001863B4  (boxer-specific loader trampoline)
       -> func_00186408  (lazily-initialized singleton accessor -> ELF virtual 0x000080B4)
       -> func_001A0C74  (shared generic per-table loader -> populates +0x0/+0x4/+0x8)
  -> func_001AD268  (reads word0 as a count, scans the +0x18 flags array, repacks into a caller-chosen stride)
       <- called by T_0018E4F4 (stride=1) and func_001AF768 (stride=5 and stride=0x28, twice)
```

All 6 direct callers of the singleton accessor found by a whole-binary search have now been disassembled across both passes. The two left open in the first commit are resolved this pass:

- **`T_0018E4F4`** constructs a small, vtable-bearing object (a fixed pointer at `+0x14`, a sized sub-object at `+0x18`) that queries the boxer singleton via `func_001AD268` with stride 1. No caller of `T_0018E4F4` itself was found in this pass -- it may be reached only through a function pointer/vtable dispatch, or from an unanalyzed module.
- **`func_001AF768`** constructs a much larger object (writes observed to offset `+0x7084`) that queries the boxer singleton **twice**, with two different strides (5 and `0x28`=40), storing each result at `+0x198C`/`+0x198E`, then chains 9 further subsystem-initialization calls. This is the strongest evidence found connecting boxer ownership to a UI/menu-construction routine -- plausibly a roster-select or boxer-list screen -- though which screen, and what the 9 chained subsystems are, were not determined.

## What remains open: `xdbboxr.adf`'s per-record schema

`analysis/resources/xdbboxr-schema.json` (model_version 2) now records the proven record count (121, via word0) and the proven flags-array location (`+0x18`, 2 bits/entry) but still contains **zero** semantic field entries for name/rating/weight/division/stance/handedness/appearance/hair/shorts/hometown/career-state/rivals/training/store-unlock/created-boxer data -- the byte range past the flags array (payload offset ~0x37 through 9704 bytes) was not structurally analyzed this pass, and the meaning of the flags array's own 4 possible values (0/1/2/3) was not determined. See `analysis/resources/static-discovery-backlog.json` for the four concrete next avenues (disassemble `func_0018654C`; analyze the payload tail; cross-check another xdb table's own consumer; disassemble the 9 chained subsystem-init calls).

## Boxer data is not confined to `xdbboxr.adf`

This pass found and enumerated 4 previously-unknown boxer-appearance archives (`boxersh.viv` -- staged damage models and gloves; `cboxshr.viv` -- shorts models; `boxmisc.viv` -- face/damage/equipment geometry including `face_cuts.off`; `boxmisc2.viv` -- headgear-compatible hair morphs) plus 36 `hk_*.viv` hairstyle/legend-boxer archives and the reassembled, hash-verified `actors.viv` (1657 members). All of these are 3D model/geometry resources, confirmed structurally distinct from `xdbboxr.adf`'s own database-record format -- boxer *appearance* is a separate resource family from boxer *database fields*, not a surprising schema split. See `analysis/resources/xdbboxr-schema.json`'s `boxer_data_is_not_confined_to_this_table` and `analysis/resources/boxer-ownership-map.json`'s `cross_resource_relationships`.

## Cross-resource relationships, updated

- `preload/tables.viv`'s boxer-surname `.txt` files, `preload/bootpreloads.viv`'s `HK_*.bh` descriptors, and the repository's 36 `hk_*.viv` archives were cross-verified by direct content inspection this pass (not just filename matching), confirming two distinct kinds: 28 generic hairstyle templates and 8 named-legend-boxer archives whose stems match exactly. Upgraded from `CANDIDATE` to `PROBABLE`.
- `scripts/scripts.viv`/`scripts/scrptpal.viv`'s paired-but-different parameter sets remain `PROBABLE` structurally; the reason two sets exist is explicitly deferred to program-05/06 static analysis (`STATIC_PENDING / deferred`), not `RUNTIME_BLOCKED`.
- New: `boxersh.viv`/`cboxshr.viv`/`boxmisc.viv`/`boxmisc2.viv` are grouped with `boxerpre.viv`/`actors.viv`/`allhair.viv`/`tables.viv` in a single 9-entry data-driven resource registry table found in `BOOT.BIN` -- see `docs/decomp/packages/resource-loaders/README.md`.

## `config/subsystem_registry.json`

No change this pass. `program-04` remains `static_mapped` (set in the prior commit); the evidence gathered this pass strengthens that status further but does not yet justify moving past it -- the decompilation gate's Class A requirements (per-record fields, lifecycle coverage, original-behavior tests, replacement boundary) remain unaddressed.

## Verification

```text
11 unit tests (tests/unit/test_xdb.py: 4, tests/unit/test_zlb.py: 7) -- pass
Full repository test suite -- see PR for the run recorded at merge time
Ruff and strict mypy -- clean
```

## Explicitly unresolved (see `analysis/resources/static-resolution-matrix.json` and `static-discovery-backlog.json`)

Every open question is `STATIC_PENDING` with a named next avenue this pass -- `analysis/resources/runtime-minimum-backlog.json` is empty. See `static-discovery-backlog.json` for the full list, including: `xdbboxr.adf`'s payload tail past the flags array; the meaning of the flags array's 4 values; the node type walked by `func_00186464`'s linked-list index; callers of `func_001AF768`/`T_0018E4F4` and the 9 chained subsystem-init calls; and cross-checking the flags-array model against another xdb table's own consumer.

## Next checkpoint

**Disassemble `func_0018654C` (consumed by both `T_0018E4F4` and `func_001AF768` immediately after `func_001AD268`) to learn what it does with the boxer-table classification result, and structurally analyze `xdbboxr.adf`'s payload bytes past the proven `+0x18` flags array.**
