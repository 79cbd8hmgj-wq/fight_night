# XDB Schema and Boxer Ownership Decompilation Package

## Status

Follow-up PR #37 substantially advances the XDB model. The generic table ABI is now
statically mapped far enough to distinguish fields from records, locate the row matrix,
and resolve all four storage classes. `xdbboxr.adf`'s SelectBoxer rating block is mapped
to exact field IDs and row-relative byte offsets. Many non-rating semantic fields remain
open, so this package is not yet a complete boxer-schema decompilation.

Locked retail source remains `BOOT.BIN` SHA-256
`906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9`.
The ULES00270 review/debug BOOT.BIN is used only as a cross-build static reference;
no executable bytes are tracked.

## Corrected XDB layout

The old 8-word/32-byte-header interpretation is superseded. The executable proves a
24-byte fixed header followed by a packed field-type table and row-major token matrix:

```text
+0x00  u32 field_count
+0x04  u32 record_count
+0x08  u32 float_pool_offset
+0x0C  u32 int32_pool_offset
+0x10  u32 string_pool_offset
+0x14  u32 reserved/unknown
+0x18  packed 2-bit field types (4 fields/byte, MSB-first)
NaN
NaN
NaN
NaN
NaN
NaN

Executable proof:

- `func_001AD21C` returns header word1 as the table record count.
- `func_001AD180` bounds a row index by word1 and computes the row pointer using
  `field_count * 2` bytes per row.
- `func_001ACCAC` bounds a field index by word0 and reads its 2-bit storage type.
- `func_001ACD40` resolves type 0/1/2/3 as inline signed-int16 / string-byte-pool /
  int32-pool / float32-pool respectively.
- `func_001AD268` iterates the word0 field descriptors and classifies their storage
  types; its caller-selected strides are output-shape parameters, not boxer-record strides.

The matrix-start formula derived from `func_001AD180` lands immediately after the
aligned type table in all ten tracked XDB resources.

## xdbboxr.adf

For the tracked retail table:

```text
field_count      = 121
record_count     = 37
type-map offset  = 0x18
type-map bytes   = 31
row-matrix start = 0x38
row stride       = 0xF2 (242 bytes)
row-matrix end   = 0x2334 (9012)
string pool      = 0x2334..0x25E8 (692 bytes)
```

This corrects the earlier interpretation that 121 was a boxer-record count. It is the
number of fields/columns. The base table has 37 rows and the generic accessor reads that
count dynamically.

## SelectBoxer rating fields

`UpdateSelectBoxerInfo` at `0x001D53F0` reaches the table through
`func_00185114 -> func_0018553C -> func_001ACD40`. The rating block is:

| UI field | XDB field ID | Row-relative token | Storage |
| --- | ---: | ---: | --- |
| Power component A | `0x10` | `+0x20` | signed int16 |
| Power component B | `0x11` | `+0x22` | signed int16 |
| Speed | `0x12` | `+0x24` | signed int16 |
| Agility | `0x13` | `+0x26` | signed int16 |
| Stamina | `0x14` | `+0x28` | signed int16 |
| Chin | `0x15` | `+0x2A` | signed int16 |
| Heart | `0x16` | `+0x2C` | signed int16 |
| Cuts | `0x17` | `+0x2E` | signed int16 |
| Body | `0x18` | `+0x30` | signed int16 |

`iPower` is the average of the two power components. `iOverall` is computed through
`func_001D50F4`; no direct raw Overall field is asserted.

For record 0, the rating tokens therefore begin at payload offsets `0x58` through
`0x68`. For record `n`, use `0x38 + n*0xF2 + field_id*2`.

## Boxer ID / roster implications

The stock SelectBoxer range table exposes IDs 0-34 across six executable-bounded weight
classes. The base XDB contains 37 rows, leaving rows 35-36 semantically unresolved.
`func_00186284` resolves a boxer ID through the registered table-instance chain and
subtracts each table's dynamic record count until it reaches the owning table. Therefore
`121` is not a roster cap and the global ID space is not inherently limited to one
37-row table. A separate hard cap in save/UI/allocation code is still unproven.

## Remaining work

The next static targets are the non-rating field IDs: identity/name, weight/division,
stance/handedness, appearance/equipment references, hometown, career/store state, and
created-boxer metadata. The generic accessor ABI is now known, so each concrete reader can
be traced directly to a field ID and storage class instead of inferring structure from raw
bytes.

Machine-readable evidence:

```text
analysis/resources/xdbboxr-schema.json
analysis/resources/xdb-schema-evidence.json
analysis/resources/boxer-ownership-map.json
analysis/resources/debug-build-aip-dispatch.json
```

Parser/reference code:

```text
src/fnr3_re/xdb.py
tests/unit/test_xdb.py
```
