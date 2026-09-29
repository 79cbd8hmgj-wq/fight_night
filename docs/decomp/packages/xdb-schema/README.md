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
| `0x00` | `+0x00` | signed int16 | secondary boxer/resource identity key; exact role unresolved |
| `0x01` | `+0x02` | string pool | last/surname or family display name |
| `0x02` | `+0x04` | string pool | first/given name |
| `0x03` | `+0x06` | string pool | short CRO/resource stem (probable) |

`func_001851CC` reads field 2 and then field 1 while composing the display name,
independently corroborating the first/given-name and surname mapping.

The two physical rows outside the normal SelectBoxer ranges are real bonus records:

| Physical row / selector index | Field-0 secondary ID | Name | CRO stem |
| ---: | ---: | --- | --- |
| 35 | 74 | Fabolous | `fabo` |
| 36 | 75 | Little Mac | `spun` |

A critical correction follows from `func_00186284`: the boxer selector used by the game is a cumulative **record-position index** across registered boxer-table instances. The resolver subtracts each table's dynamic `record_count` and passes the residual index to `func_001AD180`; it never reads xdbboxr field `0x00`. Therefore Fabolous and Little Mac are addressed here as selector indices 35 and 36. Their field-0 values 74/75 are a separate secondary/resource identity number whose exact role is still open.
The created/custom-boxer SelectBoxer path is separate and emits
`iCustomBoxerID`, `strCustomBoxerName`, and `iCustomBoxerWeightClass` from
session/custom state; rows 35-36 are not created-boxer placeholders.

Field `0x04` is now a confirmed **base/default availability flag**. It is `1` for every normal stock record 0-34 and `0` for Fabolous/Little Mac. `func_00185D84` returns `field4 > 0`; the 35-entry stock roster builder uses that predicate directly. `func_001B0FE8` additionally proves that a zero flag is not necessarily permanent: selector index 35 can be enabled by a per-boxer bit in the session/object bitset beginning at `+0x1C4`. `T_001B2648` sets bits in that same bitset using `func_001AF728` (`word = index / 32`, `bit = index % 32`). The executable behavior is confirmed; the most specific user-facing word—unlocked/selectable/available—remains a naming question.

## Replay identity selector

Field `0x05` is now mapped through a concrete event consumer rather than inferred
from its value distribution.

- `func_00185B30` reads boxer field `0x05`.
- `func_0010C9C8` uses it as a bounded 76-entry source selector and returns a
  normalized boxer code. Several alternate-weight records of the same licensed
  fighter normalize to the same result.
- If the direct field-`0x05` mapping has no code, the mapper can fall back through
  field `0x07`'s alias/nickname-linked path.
- `func_0010BB58` runs the mapper for both active boxers and places the two results
  into event-payload offsets `+0x14` and `+0x18`.
- That payload is dispatched through `func_003E5860`. The first-use fallback
  resolves/registers descriptor `D_0055AB38` through `func_003E4A94`.
- `D_0055AB38` is the named event **`Replay`**.

Therefore field `0x05` is a per-boxer source selector for normalized **Replay-event
identity/profile codes**. Earlier wording that treated it as a speech/commentary
identity has been withdrawn: no static evidence presently proves that these codes
are commentary or audio IDs.
## Hometown and nickname references

Two more leading boxer fields are now resolved through their actual foreign-key tables:

| Boxer field | Meaning | Target table | Native path |
| --- | --- | --- | --- |
| `0x06` | hometown key/reference | `xdbhmtwn.adf` | `T_00185FA0` / `T_001860A0` -> `func_001A9020` |
| `0x07` | nickname/alias key/reference | `xdbalias.adf` | `func_00185F34` / `T_00186108` -> `func_00185008` |

`xdbhmtwn.adf` has 63 keyed records and exposes `O_Home_*` localization keys in
field 4. `T_001860A0` resolves boxer field 6 through the hometown table and returns
that field-4 value.

`xdbalias.adf` has 76 keyed records and exposes `ST_Nick_*` localization keys in
field 3. `T_00186108` resolves boxer field 7 through the alias table and returns
that field-3 value.
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

The normal stock SelectBoxer range table exposes selector indices 0-34 across six executable-bounded weight classes. Physical rows 35 and 36 are the Fabolous/Little Mac bonus records. `func_00186284` resolves a numeric selector by walking the registered table-instance chain, subtracting each table's dynamic record count until it reaches the owning table, and then selecting the residual row index. Therefore `121` is not a roster cap, field `0x00` is not the selector index, and the selector space is not inherently limited to one 37-row table. A separate hard cap in save/UI/allocation code is still unproven.

## Remaining work

The next static targets are field `0x00`'s secondary/resource-ID role, physical/biographical fields `0x08`/`0x0A`-`0x0C`, the exact names of the packed `0x0E` traits, remaining handedness/equipment references, career/store state, and created-boxer metadata. Field `0x05`'s Replay-event dataflow is resolved; only the exact authored column name and downstream meaning of the normalized Replay code remain open, and no commentary/audio meaning is assumed.

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
