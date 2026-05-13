# .bin Format Groups

Grouping dimensions: size bucket, first four header bytes, parent folder, string style, and classification.

## <8MB | header 7e 50 53 50 | parent (repo root)
- `EBOOT.BIN` — 7271008 bytes, entropy 7.9998, class: structured, PSP executable container

## <8MB | header 7e 50 53 50 | parent UPDATE
- `UPDATE/EBOOT.BIN` — 3951712 bytes, entropy 7.9998, class: structured, PSP executable container, system/update

## <8MB | header 7f 45 4c 46 | parent (repo root)
- `BOOT.BIN` — 7270664 bytes, entropy 5.7567, class: structured, ELF executable

## >=8MB | header 50 53 41 52 | parent UPDATE
- `UPDATE/DATA.BIN` — 14809632 bytes, entropy 7.9998, class: structured, PSP update PSAR package, system/update

## Family conclusions
- Animation `.bin`: none found.
- Script/palette `.bin`: none found.
- Database/table-like `.bin`: none found among loose/extracted `.bin`; all files classify as PSP system/executable containers.
- UI/support `.bin`: none found as separate `.bin` assets. `BOOT.BIN`/`EBOOT.BIN` contain UI/game strings as executable resources.
- Unknown binary blobs: none; all four files have recognizable PSP/ELF/PSAR headers.

## Record-structure analysis
### `BOOT.BIN`
Executable/container file; record-width signals below are mechanical only and not evidence of data rows:
- width 4: 1817666 rows if forced; first-dword monotonic pairs 50/63, zero first dwords 39/64

### `EBOOT.BIN`
No table-like fixed-record signal identified; header/classification indicates executable or system package.

### `UPDATE/DATA.BIN`
No table-like fixed-record signal identified; header/classification indicates executable or system package.

### `UPDATE/EBOOT.BIN`
No table-like fixed-record signal identified; header/classification indicates executable or system package.

## Decompression successes
No zlib/gzip/raw-deflate decompression from offset 0 succeeded.
