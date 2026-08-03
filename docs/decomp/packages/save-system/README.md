# Save System Decompilation Package

## Status

**Task 9 — Checkpoint 9A: static owner and entry-point candidates**

This package currently records exact-binary static evidence only. It does not yet satisfy the Class A functional-reconstruction gate.

## Locked source

- Revision: `ULUS10066-v1.00`
- Module: `BOOT.BIN`
- SHA-256: `906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9`
- Format: plain ELF32 little-endian MIPS/PSP executable
- Relevant loadable mapping: ELF virtual address to stored file offset uses a `0x100` bias for the guarded text and read-only-data regions in this exact binary

The machine-readable evidence is stored at:

```text
analysis/save/save-system-static-candidates.json
```

The artifact and its exact byte guards are parsed and verified by:

```text
src/fnr3_re/save.py
```

## Probable owner

`BOOT.BIN` is the probable owner of the high-level original save interface because the exact executable contains:

- profile and career front-end references;
- the `DATA.BIN` payload filename;
- multiple `PSP/SAVEDATA` path formats;
- a corruption callback label;
- direct references from executable text to those strings;
- `IoFileMgrForUser` and `sceUtility` import-stub sections.

This is not yet a confirmed exclusive ownership claim. Runtime call-path evidence must still determine whether a PRX module receives delegated serializer or storage work.

## Static candidates

| Role | ELF virtual address | Confidence | Current bounded conclusion |
|---|---:|---|---|
| Profile save controller | `0x0042C614` | Candidate | Six-state profile-oriented controller that installs `DATA.BIN`; load and save directions remain unresolved. |
| Savedata directory enumerator | `0x004C62B8` | Probable | Formats the savedata root and uses file-manager imports in an open/iterate/close pattern. |
| Savedata operation state machine | `0x004C8838` | Candidate | Operates on savedata paths and object-owned buffers through explicit states; operation meanings remain unresolved. |
| Corrupt-file callback | `0x003412CC` | Probable | Enters the labeled corruption callback path; error-code and recovery contracts remain unresolved. |

Every region is guarded by its exact size and SHA-256. String bytes and each selected 16-byte cross-reference region are also guarded.

## Explicitly unresolved

Checkpoint 9A makes no semantic claim about:

- checksum algorithm;
- profile slot count;
- serializer or deserializer boundaries;
- block headers or version fields;
- compression or obfuscation;
- write ordering;
- interrupted-write recovery;
- maximum payload size or unused capacity;
- exclusive ownership across `BOOT.BIN` and PRX modules.

No candidate above may be promoted to confirmed from decompiler output or strings alone.

## Checkpoint 9A acceptance

Checkpoint 9A is complete only when:

1. The normalized artifact passes its schema tests.
2. A changed or unrelated binary is rejected before any region is trusted.
3. The exact reference `BOOT.BIN`, when supplied through `FNR3_BOOT_BIN`, matches every string, xref, and entry-point guard.
4. The full repository tests, Ruff, and strict mypy pass.

## Next checkpoint

Checkpoint 9B will answer one separate evidence question: identify the serializer/deserializer call-path boundaries and data-buffer contract without yet assigning profile, career, checksum, or slot-field semantics.
