# XDB Schema and Boxer Ownership Decompilation Package

## Status

PR #37 substantially advances the XDB model. The generic table ABI is mapped far enough
to distinguish fields from records, locate the row matrix, resolve all four storage
classes, and identify concrete boxer identity/rating fields. Many non-rating semantic
fields remain open, so this is not yet a complete boxer-schema decompilation.

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
        align to 4 bytes
        record matrix: record_count rows * field_count int16 tokens
word2   float pool
word3   int32 pool
word4   byte/string pool
```

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

## Boxer identity fields

Direct decoding plus the native name-composition path now resolves the leading fields:

| Field | Row-relative token | Storage | Meaning |
| --- | ---: | --- | --- |
| `0x00` | `+0x00` | signed int16 | explicit global boxer ID |
| `0x01` | `+0x02` | string pool | last/surname or family display name |
| `0x02` | `+0x04` | string pool | first/given name |
| `0x03` | `+0x06` | string pool | short CRO/resource stem (probable) |

`func_001851CC` reads field 2 and then field 1 while composing the display name,
independently corroborating the first/given-name and surname mapping.

The two physical rows outside the normal SelectBoxer ID ranges are real bonus records:

| Physical row | Global boxer ID | Name | CRO stem |
| ---: | ---: | --- | --- |
| 35 | 74 | Fabolous | `fabo` |
| 36 | 75 | Little Mac | `spun` |

This also proves that global boxer ID is not required to equal physical XDB row index.
The created/custom-boxer SelectBoxer path is separate and emits
`iCustomBoxerID`, `strCustomBoxerName`, and `iCustomBoxerWeightClass` from
session/custom state; rows 35-36 are not created-boxer placeholders.

Field `0x04` is a strong standard-roster/selectability candidate: it is `1` for every
normal stock record 0-34 and `0` for Fabolous/Little Mac. `func_00185D84` reads field 4
and returns whether it is positive; a caller at `0x00278B0C` applies that predicate
across 35 stock boxer IDs. The exact engine label (visible/selectable/unlocked/eligible)
has not yet been promoted to confirmed.

## Weight field and exact division thresholds

`func_0018600C` reads XDB field `0x09` as a signed-int16 boxer weight and maps
that value directly to the SelectBoxer weight-class enum. The recovered mapping is:

| Enum | Division | Weight range |
| ---: | --- | ---: |
| 0 | Heavyweight | 191-280 |
| 1 | Light Heavyweight | 169-190 |
| 2 | Middleweight | 148-168 |
| 3 | Welterweight | 136-147 |
| 4 | Lightweight | 127-135 |
| 5 | Featherweight | <=126 |

Weights `>=281` return `-1`/invalid. `GetSelectBoxerInfo` calls this classifier
at `0x001D7D28` and immediately applies the independently-proven `<6` enum bound.
Retail records corroborate the scale directly: Manny Pacquiao's row stores `125`
and Erik Morales's stores `126` in field `0x09`.

Field `0x09` is therefore the exact boxer-weight field at row-relative token
`+0x12`, and the six retail division thresholds no longer require inference from UI
labels.
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

For record 0, the rating tokens begin at payload offsets `0x58` through `0x68`.
For record `n`, use `0x38 + n*0xF2 + field_id*2`.

## Boxer ID / roster implications

The normal stock SelectBoxer range table exposes IDs 0-34 across six executable-bounded
weight classes. The same base XDB also contains bonus IDs 74 and 75. `func_00186284`
resolves a numeric boxer ID through the registered table-instance chain, subtracting each
table's dynamic record count until it reaches the owning table. Therefore `121` is not a
roster cap and the global ID space is not inherently limited to one 37-row table.
A separate hard cap in save/UI/allocation code is still unproven.

## Remaining work

The next static targets are the exact semantic label of field 4 and the other non-rating
fields: weight/division, stance/handedness, appearance/equipment references, hometown,
career/store state, and remaining created-boxer metadata. The generic accessor ABI is
known, so each concrete reader can now be traced directly to a field ID and storage class.

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
