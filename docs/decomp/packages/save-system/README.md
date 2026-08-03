# Save System Decompilation Package

## Status

**Task 9 — Checkpoints 9A and 9B complete**

This package now records exact-binary static ownership evidence and the PSP savedata utility-buffer boundary. It does not yet satisfy the Class A functional-reconstruction gate because serializer direction, payload format, integrity logic, slot structure, and runtime ownership remain unresolved.

## Locked source

- Revision: `ULUS10066-v1.00`
- Module: `BOOT.BIN`
- SHA-256: `906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9`
- Format: plain ELF32 little-endian MIPS/PSP executable
- Relevant mapping: ELF virtual address to stored file offset uses a `0x100` bias for the guarded text and read-only-data regions in this exact binary

Machine-readable evidence:

```text
analysis/save/save-system-static-candidates.json
analysis/save/save-utility-buffer-contract.json
```

Parsers and exact-byte verifiers:

```text
src/fnr3_re/save.py
src/fnr3_re/save_utility.py
```

## Checkpoint 9A — probable owner and static entry points

`BOOT.BIN` is the probable owner of the high-level original save interface because the exact executable contains:

- profile and career front-end references;
- the `DATA.BIN` payload filename;
- multiple `PSP/SAVEDATA` path formats;
- a corruption callback label;
- direct references from executable text to those strings;
- `IoFileMgrForUser` and `sceUtility` import-stub sections.

This is not yet a confirmed exclusive ownership claim. Runtime call-path evidence must still determine whether a PRX module or another object receives delegated serializer or storage work.

### Static candidates

| Role | ELF virtual address | Confidence | Bounded conclusion |
|---|---:|---|---|
| Profile save controller | `0x0042C614` | Candidate | Six-state profile-oriented controller that installs `DATA.BIN`; operation directions remain unresolved. |
| Savedata directory enumerator | `0x004C62B8` | Probable | Formats the savedata root and uses file-manager imports in an open/iterate/close pattern. |
| Savedata operation state machine | `0x004C8838` | Candidate | Operates on savedata paths and object-owned buffers through explicit states; operation meanings remain unresolved. |
| Corrupt-file callback | `0x003412CC` | Probable | Enters the labeled corruption callback path; error-code and recovery contracts remain unresolved. |

Every region is guarded by its exact size and SHA-256. String bytes and selected 16-byte cross-reference regions are also guarded.

## Checkpoint 9B — savedata utility and payload boundary

Two adjacent `BOOT.BIN` controllers construct the same `0x600`-byte PSP savedata parameter block in the global profile/save workspace at offset `0x12A54`.

The parameter block is not the serialized Fight Night profile or career payload. The game payload is separately allocated or owned and crosses the operating-system utility boundary through these fields:

| Parameter offset | Bounded meaning | Confidence |
|---:|---|---|
| `0x30` | Savedata utility mode | Probable |
| `0x64` | Payload filename, populated as `DATA.BIN` | Probable |
| `0x74` | Game-payload buffer pointer | Probable |
| `0x78` | Game-payload buffer capacity | Probable |
| `0x7C` | Active payload byte count | Probable |
| `0x80` | SFO title area | Probable |
| `0x180` | SFO detail area | Probable |
| `0x5DC` | Secure-save key area | Probable |

### Controller sites

| Role | Address | Observed modes | Confidence |
|---|---:|---:|---|
| List-save controller | `0x0042C834` | `5` | Probable |
| Save-or-autoload controller | `0x0042CF8C` | `0`, `3` | Probable |

Both controllers invoke the same indirect callback-table slot before calling the savedata utility. Each callback receives references associated with the payload pointer and capacity fields.

The callback sites are:

| Role | Address | Confidence |
|---|---:|---|
| List-save payload provider | `0x0042C888` | Candidate |
| Save-or-autoload payload provider | `0x0042CFDC` | Candidate |

These sites establish the game-payload handoff boundary. They do not establish whether the callback serializes into the buffer, prepares a load target, validates loaded bytes, or delegates to another owner.

### PSP utility boundary

The guarded `sceUtility` import descriptor names the library, declares 20 stubs, references the NID table at `0x004F7404`, and references the stub table at `0x004F6B14`.

The observed controller calls the stub at:

```text
0x004F6B4C
```

Its guarded NID is:

```text
0x50C4CD57
```

The `0x600`-byte argument layout and observed mode fields are consistent with the PSP savedata initialization interface. The exact imported function name remains probable until runtime or independently authoritative symbol evidence is attached.

## Exact verification

The repository tests verify:

1. The normalized artifacts satisfy strict typed schemas.
2. A changed or unrelated `BOOT.BIN` is rejected before region evidence is trusted.
3. The tracked exact `BOOT.BIN` matches every guarded string, xref, controller, callback, import descriptor, NID table, and utility stub region.
4. Static-only candidates cannot be promoted to `CONFIRMED` by the artifact model.
5. Payload flow direction remains explicitly unresolved.

Checkpoint 9B verification completed with:

```text
168 passed
4 expected reference-ISO skips
Ruff passed
Strict mypy passed
```

## Explicitly unresolved

The completed checkpoints make no confirmed semantic claim about:

- payload-provider callback target or owner;
- serializer writer set;
- deserializer reader set;
- runtime direction of each upstream branch;
- payload allocation and release lifetime;
- post-load active-size behavior;
- checksum algorithm;
- encryption or obfuscation;
- profile-slot count;
- profile and career block boundaries;
- block headers or version fields;
- write ordering;
- interrupted-write recovery;
- maximum payload size or unused capacity;
- PRX delegation below the utility boundary;
- exclusive ownership across `BOOT.BIN` and PRX modules.

No field, callback, or candidate may be promoted beyond its recorded confidence without executable or controlled runtime evidence.

## Next checkpoint

Checkpoint 9C will resolve the indirect payload-provider callback target and owner, then distinguish serializer and deserializer directions without assigning persistent profile, career, checksum, or slot-field meanings prematurely.
