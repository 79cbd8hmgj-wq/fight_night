# EA resource codecs

Task 5 establishes the original-behavior codec boundary required before database, table, script, UI, model, or career resources can be edited.

## RefPack/QFS

The game stores many resources whose logical extension is `.csv`, `.txt`, `.adf`, or `.fnc` as EA RefPack streams beginning with `10 FB`.

Supported reference headers:

```text
10 FB + 24-bit big-endian uncompressed size
90 FB + 32-bit big-endian uncompressed size
```

The decoder is fail-closed. It validates command lengths, literal bounds, prior-output backreferences, declared output size, an explicit stop command, output limits, and trailing bytes. Embedded-stream callers can opt into trailing data and receive the exact number of consumed bytes.

The encoder is deterministic. It uses bounded greedy match selection with stable tie-breaking and emits valid short, medium, long, literal, and stop commands. The project does not require compressed output to match the original encoder byte-for-byte; it requires deterministic decoding equivalence and later rebuilt-game validation.

### Commands

```bash
fnr3-re refpack-decode input.adf decoded.adf
fnr3-re refpack-encode decoded.adf rebuilt.adf
```

Both commands refuse to overwrite an output unless `--force` is supplied.

## BIGF and BIG4 archives

Observed repository samples confirm a shared mixed-endian directory format:

| Offset | Size | Endianness | Meaning |
|---:|---:|---|---|
| `0x00` | 4 | ASCII | `BIGF` or `BIG4` |
| `0x04` | 4 | little | Total archive size |
| `0x08` | 4 | big | Member count |
| `0x0C` | 4 | big | End of directory/header size |

Each member record contains:

```text
big-endian uint32 payload offset
big-endian uint32 payload size
NUL-terminated ASCII path
```

The tracked `components/alpha.big` sample is a four-member `BIGF` archive with 16-byte payload alignment. The tracked `preload/db.viv` sample is a ten-member `BIG4` archive with 64-byte payload alignment. Both parse and no-change rebuild byte-exactly in integration tests.

The parser rejects unsupported magic, inconsistent sizes, malformed names, traversal, duplicate case-insensitive paths, payloads inside the header, out-of-bounds payloads, and overlapping member ranges.

The builder preserves caller-provided order, magic, and alignment. Replacements are guarded by optional expected member SHA-256 values. A no-change rebuild returns the exact original bytes, including original padding.

### Commands

```bash
fnr3-re archive-list preload/db.viv
fnr3-re archive-list preload/db.viv --json
fnr3-re archive-extract preload/db.viv /local/path/db-viv
```

Archive extraction is transactional and writes `archive-manifest.json` containing each member's original order, offset, size, SHA-256, and RefPack status. Use `--force` only to transactionally replace an existing extraction directory.

Guarded archive modification and ISO reinsertion will be exposed through Task 6's rebuild manifest rather than an unguarded command-line replacement interface.

## Evidence boundary

Codec success does not establish the semantic meaning of decoded ADF, FNC, CSV, or script fields. Task 5 proves container and compression behavior only. Later subsystem packages must separately establish schemas, readers, writers, consumers, and runtime behavior before decoded resources receive confirmed semantic labels.

No original member payloads or newly extracted copyrighted files are added by this task.
