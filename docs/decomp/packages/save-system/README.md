# Save System Decompilation Package

## Status

**Task 9 — Checkpoints 9A, 9B, and 9C complete**

This package now records exact-binary static ownership evidence, the PSP savedata utility-buffer boundary, and the original save/load payload dispatch directions. It does not yet satisfy the Class A functional-reconstruction gate because payload lifetime, exact serialized size, per-field serialization, integrity logic, slot structure, recovery, and migration boundaries remain unresolved.

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
analysis/save/save-payload-direction-map.json
```

Parsers and exact-byte verifiers:

```text
src/fnr3_re/save.py
src/fnr3_re/save_utility.py
src/fnr3_re/save_payload.py
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
| `0x7C` | Active payload byte count | Probable |
| `0x80` | SFO title area | Probable |
| `0x180` | SFO detail area | Probable |
| `0x5DC` | Secure-save key area | Probable |

The two save-direction controllers are:

| Role | Address | Modes | Confidence |
|---|---:|---:|---|
| List-save controller | `0x0042C834` | `5` | Probable |
| Autosave-or-save controller | `0x0042CF8C` | `1`, `3` | Probable |

Checkpoint 9C corrected the earlier interpretation of the second branch. The exact instruction stream preloads mode `1`, not mode `0`; the controller therefore selects AUTOSAVE or SAVE rather than AUTOLOAD or SAVE.

The generic 9B artifact keeps its aggregate `flow_direction` field unresolved because it defines the reusable operating-system buffer contract. Direction-specific behavior is normalized separately in the 9C artifact.

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
| `+0x38` | `0x00340DC8` | Save | Save-payload workspace provider | Probable |
| `+0x40` | `0x00340F00` | Load | Load-buffer workspace provider | Probable |
| `+0x44` | `0x00340F64` | Load | Loaded-payload commit/deserializer handoff | Probable |

The save provider clears a `0x7530`-byte workspace, copies the current persistent source into it, and returns payload pointers and sizes to the utility parameter block.

The load provider clears a `0x755C`-byte input workspace and returns its pointer and capacity. The load-commit handler copies loaded workspace data back into the persistent destination and invokes a follow-up callback. That follow-up target and the per-field deserializer remain unresolved.

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

## Verification

Checkpoint 9C followed a test-first implementation sequence:

1. New direction-map tests were committed before the model or artifact existed.
2. The RED run failed for the missing `fnr3_re.save_payload` module and the stale AUTOLOAD interpretation while all prior tests remained green.
3. The minimal typed model, exact evidence artifact, and integration guard were added.
4. The stale 9B mode interpretation was corrected without changing the generic utility-buffer contract.
5. The complete repository suite, Ruff, and strict mypy passed.

Final verification:

```text
170 passed
5 expected environment-gated skips
Ruff passed
Strict mypy passed
10/10 exact BOOT.BIN regions matched
```

The exact reference binary was also checked directly against all ten 9C region hashes: initializer, copier, three dispatch targets, and five controller regions.

## Explicitly unresolved

The completed checkpoints do not yet establish:

- payload allocation and release lifetime;
- exact active serialized payload size;
- maximum capacity and unused space;
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

Checkpoint 9D will answer one evidence question only: identify payload allocation and release lifetime and determine the exact serialized payload size and capacity boundaries without assigning profile or career field semantics.
