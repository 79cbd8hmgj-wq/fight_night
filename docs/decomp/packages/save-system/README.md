# Save System Decompilation Package

## Status

**Task 9 — Checkpoints 9A through 9D complete**

This package now records exact-binary static ownership evidence, the PSP savedata utility boundary, save/load dispatch directions, and the payload envelope's lifetime and size contract. It does not yet satisfy the Class A functional-reconstruction gate because per-field serialization, post-load validation, integrity logic, slot structure, recovery, and migration boundaries remain unresolved.

## Locked source

- Revision: `ULUS10066-v1.00`
- Module: `BOOT.BIN`
- SHA-256: `906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9`
- Format: plain ELF32 little-endian MIPS/PSP executable
- Relevant mapping: ELF virtual address to stored file offset uses the exact load-segment mappings from the ELF program headers

Machine-readable evidence:

```text
analysis/save/save-system-static-candidates.json
analysis/save/save-utility-buffer-contract.json
analysis/save/save-payload-direction-map.json
analysis/save/save-payload-lifetime.json
```

Parsers and exact-byte verifiers:

```text
src/fnr3_re/save.py
src/fnr3_re/save_utility.py
src/fnr3_re/save_payload.py
src/fnr3_re/save_payload_lifetime.py
```

## Checkpoint 9A — probable owner and static entry points

`BOOT.BIN` is the probable owner of the high-level original save interface because the exact executable contains profile and career front-end references, the `DATA.BIN` payload filename, PSP savedata path formats, a corruption callback label, direct string references, and the relevant file-manager and utility imports.

This is not a confirmed exclusive ownership claim. Lower-level delegation and PRX participation remain subject to later evidence.

| Role | ELF virtual address | Confidence | Bounded conclusion |
|---|---:|---|---|
| Profile save controller | `0x0042C614` | Candidate | Six-state profile-oriented controller that installs `DATA.BIN`. |
| Savedata directory enumerator | `0x004C62B8` | Probable | Formats the savedata root and uses file-manager imports in an open/iterate/close pattern. |
| Savedata operation state machine | `0x004C8838` | Candidate | Operates on savedata paths and object-owned buffers through explicit states. |
| Corrupt-file callback | `0x003412CC` | Probable | Enters the labeled corruption callback path. |

## Checkpoint 9B — savedata utility and payload boundary

Two `BOOT.BIN` save controllers construct the same `0x600`-byte PSP savedata parameter block in the global profile/save workspace at offset `0x12A54`.

The parameter block is not the serialized Fight Night profile or career payload. The game payload is separately owned and crosses the operating-system utility boundary through:

| Parameter offset | Bounded meaning | Confidence |
|---:|---|---|
| `0x30` | Savedata utility mode | Probable |
| `0x64` | Payload filename, populated as `DATA.BIN` | Probable |
| `0x74` | Game-payload buffer pointer | Probable |
| `0x78` | Game-payload buffer capacity | Probable |
| `0x7C` | Utility data byte count | Probable |
| `0x80` | SFO title area | Probable |
| `0x180` | SFO detail area | Probable |
| `0x5DC` | Secure-save key area | Probable |

The two save-direction controllers are:

| Role | Address | Modes | Confidence |
|---|---:|---:|---|
| List-save controller | `0x0042C834` | `5` | Probable |
| Autosave-or-save controller | `0x0042CF8C` | `1`, `3` | Probable |

Checkpoint 9C corrected the earlier interpretation of the second branch. The exact instruction stream preloads mode `1`, not mode `0`; the controller therefore selects AUTOSAVE or SAVE rather than AUTOLOAD or SAVE.

### PSP utility boundary

The guarded `sceUtility` import descriptor names the library, declares 20 stubs, references the NID table at `0x004F7404`, and references the stub table at `0x004F6B14`.

The observed controller calls the stub at `0x004F6B4C`, whose guarded NID is `0x50C4CD57`. The `0x600`-byte layout and mode fields are consistent with the PSP savedata initialization interface. The exact imported function name remains probable pending independent symbol or runtime confirmation.

## Checkpoint 9C — payload callback owner and direction map

PSP relocation analysis resolves the copied callback table to runtime address:

```text
0x005C3A18
```

The initializer at `0x0033F5E0` constructs the table, and the copier at `0x004282BC` transfers nineteen eight-byte entries into the runtime table. Both are in `BOOT.BIN`, making `BOOT.BIN` the probable owner of this payload-dispatch layer.

### Dispatch entries

| Entry | Target | Direction | Bounded role | Confidence |
|---:|---:|---|---|---|
| `+0x38` | `0x00340DC8` | Save | Save-envelope provider | Probable |
| `+0x40` | `0x00340F00` | Load | Load-envelope provider | Probable |
| `+0x44` | `0x00340F64` | Load | Loaded-body commit handoff | Probable |

### Utility-mode direction map

| Modes | Direction | Controller behavior |
|---|---|---|
| `1`, `3`, `5` | Save | AUTOSAVE, SAVE, and LISTSAVE paths use dispatch entry `+0x38`. |
| `0`, `2`, `4` | Load | AUTOLOAD, LOAD, and LISTLOAD paths use dispatch entry `+0x40`. |
| `6`, `7` | Non-payload | Delete operations do not use either payload-buffer provider entry. |

The load controllers are statically bounded at:

| Role | Address | Modes | Callback entry |
|---|---:|---:|---:|
| Autoload-or-load controller | `0x004309D8` | `0`, `2` | `+0x40` |
| List-load controller | `0x00430C04` | `4` | `+0x40` |

The delete controller is bounded at `0x00431128` and uses modes `6` or `7` without a payload-provider callback.

## Checkpoint 9D — envelope size, capacity, and lifetime

The savedata workspace is not a transient heap allocation. PSP relocations resolve its static addend `0x00030668` against the second load segment at `0x0058A8A8`, producing runtime address:

```text
0x005BAF10
```

The exact `BOOT.BIN` `.bss` spans `0x005923C0–0x005C7964`, so the complete workspace lies inside module-owned BSS. It exists from module load until module unload and has no heap allocator or release call.

### Fixed `DATA.BIN` envelope

```text
Envelope total:         0x755C bytes (30044)
Envelope header:        0x002C bytes (44)
Serialized body offset: 0x002C
Body capacity:          0x7530 bytes (30000)
Active body-size field: envelope +0x28
```

This distinction is important:

- The PSP utility receives a fixed buffer capacity of `0x755C`.
- Both save controllers also set the utility data byte count to `0x755C`.
- Therefore, `DATA.BIN` is written as a fixed `0x755C`-byte envelope.
- The internal serialized body has a dynamic active length, stored at envelope offset `0x28`.
- The body can occupy at most `0x7530` bytes.

### Save operation

The body serializer boundary at `0x0034526C` receives a maximum capacity of `0x7530` and returns a dynamic encoded-body length.

The save-envelope provider at `0x00340DC8` then:

1. stores the dynamic body length at envelope `+0x28`;
2. clears all `0x7530` body bytes;
3. copies only the active body bytes to envelope `+0x2C`;
4. returns the envelope base and fixed `0x755C` capacity to the PSP utility.

Unused body capacity is therefore deterministic zero padding rather than uninitialized memory.

### Load operation

The load-envelope provider at `0x00340F00` clears the full `0x755C` workspace before the PSP utility fills it.

The load-body commit handler at `0x00340F64` then:

1. reads the dynamic body length from envelope `+0x28`;
2. records that length in the registered-size global;
3. copies exactly that many bytes from envelope `+0x2C` into the registered destination;
4. invokes the still-unresolved post-load callback.

### Borrowed source and destination registrations

The envelope layer uses two globals:

```text
Registered body pointer: 0x005C250C
Registered body size:    0x005C2510
```

The clear function at `0x003401D0` zeros both globals. The setter at `0x0034025C` stores caller-provided pointer and size values without allocating, retaining, or freeing them.

The registered external buffer is therefore borrowed until the next clear or replacement. Its allocator and ultimate owning subsystem remain unresolved and are distinct from the static envelope workspace.

## Verification

Checkpoint 9D followed a test-first sequence:

1. Lifetime and size-contract tests were committed before the model existed.
2. The RED run failed only because `fnr3_re.save_payload_lifetime` was absent.
3. The typed model, normalized artifact, ELF/BSS verifier, and exact-region guards were added.
4. The complete repository suite, Ruff, and strict mypy passed.
5. The uploaded exact `BOOT.BIN` independently matched its whole-file hash, `.bss` bounds, workspace containment, and all ten guarded regions.

Final verification:

```text
172 passed
6 expected environment-gated skips
Ruff passed
Strict mypy passed
10/10 exact BOOT.BIN regions matched
Workspace confirmed inside exact .bss bounds
```

## Explicitly unresolved

The completed checkpoints do not yet establish:

- exact active body length for each real profile and career configuration;
- allocator and ultimate owner of registered external source or destination buffers;
- per-field serializer writer set;
- per-field deserializer reader set;
- load-commit follow-up callback target and owner;
- post-load validation and error propagation;
- checksum algorithm;
- encryption or obfuscation;
- profile-slot count;
- profile and career block boundaries;
- block headers or version fields;
- write ordering;
- interrupted-write recovery;
- PRX delegation below the `BOOT.BIN` handoff boundary;
- exclusive ownership across all modules.

No field, callback, or candidate may be promoted beyond its recorded confidence without executable or controlled runtime evidence.

## Next checkpoint

Checkpoint 9E will answer one evidence question only: resolve the load-commit follow-up callback and post-load validation and error propagation without assigning persistent field meanings.
