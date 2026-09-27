# XDB Schema and Boxer Ownership Decompilation Package

## Status

**Follow-up PR #37 materially advances this package.** The generic XDB row/field ABI is now recovered: header word0 is `field_count`, word1 is `record_count`, `+0x18` is a packed 2-bit per-field storage-class table, and the row-major signed-16 descriptor matrix is located exactly. For `xdbboxr.adf`, this corrects the old model from "121 possible boxer records" to **121 fields × 37 records**. The SelectBoxer rating block is also mapped to exact signed-int16 record offsets. Most non-rating field semantics remain STATIC_PENDING.
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

## The shared XDB table ABI, resolved

All 10 decoded `xdbNNNN.adf` tables use the same structure. Follow-up disassembly of `func_001AD180`, `func_001ACCAC`, `func_001ACD40`, and `func_001ACE20` resolves it:

- **word0 = field/column count.** `func_001ACCAC` rejects `field_id >= word0`.
- **word1 = record/row count.** `func_001AD180` rejects `record_index >= word1`.
- **`payload+0x18` is a packed 2-bit field-type table**, four fields per byte.
- Type 0 = inline signed int16; type 1 = string; type 2 = int32; type 3 = float32.
- A row-major signed-int16 descriptor matrix has `word1` rows and `word0` fields. Row stride is `word0*2`.
- Matrix start is `section_size_a - align4(word0*word1*2)`.
- `section_size_a`, `section_size_b`, and `section_size_c` are the float32, int32, and string pool bases respectively.

The matrix-start formula lands immediately after the aligned field-type table in **all 10 tracked XDB resources**, giving an independent corpus-wide structural cross-check.

For `xdbboxr.adf` specifically:

```text
field_count       = 121
record_count      = 37
type table        = +0x18, 31 bytes
descriptor matrix = +0x38
record stride     = 0xF2 (242 bytes)
matrix end        = 0x2334
string pool       = 0x2334 .. 0x25E8
```

The previous interpretation of 121 as a boxer/roster count is superseded.
## Boxer ownership chain, extended

```text
xdbboxr.adf (archive member)
  -> func_001863B4  (boxer-specific loader trampoline)
       -> func_00186408  (lazily-initialized singleton accessor -> ELF virtual 0x000080B4)
       -> func_001A0C74  (shared generic per-table loader -> populates +0x0/+0x4/+0x8)
  -> func_001AD268  (reads word0 as field_count, classifies +0x18 field types, repacks schema layout)
       <- called by T_0018E4F4 (stride=1) and func_001AF768 (stride=5 and stride=0x28, twice)
```

All 6 direct callers of the singleton accessor found by a whole-binary search have now been disassembled across both passes. The two left open in the first commit are resolved this pass:

- **`T_0018E4F4`** constructs a small, vtable-bearing object (a fixed pointer at `+0x14`, a sized sub-object at `+0x18`) that queries the boxer singleton via `func_001AD268` with stride 1. No caller of `T_0018E4F4` itself was found in this pass -- it may be reached only through a function pointer/vtable dispatch, or from an unanalyzed module.
- **`func_001AF768`** is the fight-session singleton constructor (corrected by Overhaul Alpha 1), not a roster/UI constructor. It queries the boxer-table schema twice with strides 5 and `0x28`, then initializes the fight-session's dependent subsystems. Its earlier UI/menu interpretation is superseded.

## `xdbboxr.adf` record layout and recovered rating block

The record boundary itself is no longer open. `xdbboxr.adf` contains 37 rows with a `0xF2` descriptor stride.

The real `UpdateSelectBoxerInfo` handler at `0x001D53F0` reaches the generic field binder and provides the rating map. Fields `0x10..0x18` all use type code 0, so each is a direct signed-int16 value in the selected record:

| UI rating | Field ID | Record-relative bytes |
| --- | ---: | ---: |
| Power component A | `0x10` | `+0x20` |
| Power component B | `0x11` | `+0x22` |
| Speed | `0x12` | `+0x24` |
| Agility | `0x13` | `+0x26` |
| Stamina | `0x14` | `+0x28` |
| Chin | `0x15` | `+0x2A` |
| Heart | `0x16` | `+0x2C` |
| Cuts | `0x17` | `+0x2E` |
| Body | `0x18` | `+0x30` |

`iPower` is the signed-integer average of fields `0x10/0x11`. `iOverall` is computed by `func_001D50F4`; no direct raw Overall field is asserted.

For record `r`, a type-0 field `f` is physically located at:

```text
payload + 0x38 + r*0xF2 + f*2
```

For record 0, the recovered rating bytes therefore occupy `0x58..0x68`.

What remains open is **semantic coverage of the other field IDs**: identity/name, division/weight, stance/handedness, appearance/equipment, hometown, career/store flags, created-boxer state, and related fields.
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

Trace the concrete identity/division/appearance/career SelectBoxer and career handlers through the now-recovered generic field binder to assign semantic names to more of the 121 `xdbboxr` field IDs. Separately resolve the two XDB rows outside the 35 stock SelectBoxer IDs.
