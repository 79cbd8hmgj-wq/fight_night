# Career Mode 2.0 — C2EX v2 Legacy Persistence

C2EX v2 extends the already-merged Career Mode 2.0 save extension without
changing any byte in the stock 0x5674-byte active body.

## Compatibility

C2EX v1 is preserved as a readable historical format.

- v1 header: unchanged 16-byte C2EX header;
- v1 payload: unchanged 36-byte development block;
- v1 total size: 52 bytes.

C2EX v2 keeps that same 36-byte development payload as its prefix, then adds a
4-byte ledger header and zero or more fixed 16-byte legacy-fight records.

New writes use v2. Existing v1 blocks remain readable and are upgraded to v2
on the next Career 2.0 save.

## v2 layout

The common C2EX header remains:

| Offset | Size | Meaning |
|---:|---:|---|
| 0x00 | 4 | magic C2EX |
| 0x04 | 2 | schema version |
| 0x06 | 2 | flags |
| 0x08 | 4 | payload length |
| 0x0C | 4 | CRC32 of payload |

The v2 payload is:

| Payload offset | Size | Meaning |
|---:|---:|---|
| 0x00 | 36 | exact v1 amateur-development payload |
| 0x24 | 2 | legacy fight count |
| 0x26 | 2 | legacy entry size, currently 16 |
| 0x28 | 16 * count | ordered legacy fight entries |

The entry-size field is checked on load. Unknown sizes fail closed instead of
being guessed.

## Capacity

The proven stock tail has 0x1EBC / 7,868 bytes available.

After the 16-byte C2EX header, 36-byte development prefix and 4-byte ledger
header, v2 can store **488** complete 16-byte fight entries while remaining
inside that proven tail.

This is deliberately derived from the actual save-tail limit rather than from
an arbitrary career-fight cap.

## Migration behavior

Three save states are now distinct:

1. retail-only save: no C2EX block;
2. C2EX v1: development data only;
3. C2EX v2: development data plus the persistent legacy ledger.

Retail-only migration still requires explicit Career 2.0 development defaults.
C2EX v1 does not require those defaults; it is a schema upgrade. Loading v1
produces an empty legacy ledger, and the next save writes a v2 block.

## Preservation rule

Updating amateur-development state must not erase historical legacy data.

The save orchestration therefore:

1. loads the existing C2EX block when present;
2. preserves its legacy ledger;
3. replaces the development state;
4. writes one fresh v2 block after the unchanged stock prefix.

An explicit write API is also available when the caller intentionally supplies
a replacement ledger.

## Fail-closed rules

The v2 decoder rejects:

- unknown versions or flags;
- CRC mismatches;
- body lengths inconsistent with the header;
- ledger entry sizes other than 16;
- ledger counts inconsistent with payload length;
- ledger counts above proven save-tail capacity;
- malformed individual ledger rows;
- nonzero bytes after the declared C2EX block.

Zero padding after a valid block remains accepted because the retail save path
clears unused body capacity.

## PSP integration boundary

This work defines the binary schema and host-side migration contract. It does
not by itself patch the retail PSP serializer.

The eventual serializer hook still has to:

- append the C2EX block after the two stock chunks on save;
- detect v1/v2 after the stock restore on load;
- preserve the stock 0x5674-byte prefix exactly;
- capture and append one legacy-fight entry at the proven post-fight boundary.
