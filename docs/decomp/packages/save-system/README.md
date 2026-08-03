# Save System Decompilation Package

## Status

**Task 9 — Checkpoints 9A through 9D complete; Checkpoint 9E runtime-blocked**

The package records exact-binary ownership candidates, the PSP savedata utility boundary, save/load dispatch directions, and the payload envelope's lifetime and size contract. It does not satisfy the Class A functional-reconstruction gate because the remaining load validation, integrity, slot, corruption, recovery, and migration semantics require controlled live PPSSPP evidence.

No further save-system semantic claim may be promoted from static interpretation alone.

## Locked source

- Revision: `ULUS10066-v1.00`
- Module: `BOOT.BIN`
- SHA-256: `906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9`
- Format: plain ELF32 little-endian MIPS/PSP executable
- Address mapping: exact ELF load-segment mappings

Machine-readable evidence:

```text
analysis/save/save-system-static-candidates.json
analysis/save/save-utility-buffer-contract.json
analysis/save/save-payload-direction-map.json
analysis/save/save-payload-lifetime.json
analysis/save/task-status.json
```

Parsers and exact-byte verifiers:

```text
src/fnr3_re/save.py
src/fnr3_re/save_utility.py
src/fnr3_re/save_payload.py
src/fnr3_re/save_payload_lifetime.py
```

## Checkpoint 9A — probable owner and entry points

`BOOT.BIN` is the probable high-level save-interface owner. It contains the relevant profile/career strings, `DATA.BIN`, PSP savedata path formats, corruption-path label, file-manager imports, and savedata utility imports.

| Role | ELF virtual address | Confidence |
|---|---:|---|
| Profile save controller | `0x0042C614` | Candidate |
| Savedata directory enumerator | `0x004C62B8` | Probable |
| Savedata operation state machine | `0x004C8838` | Candidate |
| Corrupt-file callback | `0x003412CC` | Probable |

This is not an exclusive module-ownership claim.

## Checkpoint 9B — savedata utility boundary

Two save controllers construct the same `0x600`-byte PSP savedata parameter block. The operating-system block is separate from Fight Night's serialized payload.

| Parameter offset | Bounded meaning |
|---:|---|
| `0x30` | Savedata utility mode |
| `0x64` | Payload filename (`DATA.BIN`) |
| `0x74` | Payload buffer pointer |
| `0x78` | Payload buffer capacity |
| `0x7C` | Utility data byte count |
| `0x80` | SFO title area |
| `0x180` | SFO detail area |
| `0x5DC` | Secure-save key area |

Save controllers:

| Role | Address | Modes |
|---|---:|---:|
| List-save controller | `0x0042C834` | `5` |
| Autosave-or-save controller | `0x0042CF8C` | `1`, `3` |

The guarded `sceUtility` import descriptor declares twenty stubs. The observed controller uses the stub at `0x004F6B4C`, guarded by NID `0x50C4CD57`. Its exact imported function name remains probable pending runtime or symbol confirmation.

## Checkpoint 9C — payload dispatch and direction

The copied dispatch table resolves to runtime address `0x005C3A18`. The initializer at `0x0033F5E0` and copier at `0x004282BC` are both in `BOOT.BIN`.

| Entry | Target | Direction | Bounded role |
|---:|---:|---|---|
| `+0x38` | `0x00340DC8` | Save | Save-envelope provider |
| `+0x40` | `0x00340F00` | Load | Load-envelope provider |
| `+0x44` | `0x00340F64` | Load | Loaded-body commit handoff |

Utility modes:

```text
Save:        1 AUTOSAVE, 3 SAVE, 5 LISTSAVE
Load:        0 AUTOLOAD, 2 LOAD, 4 LISTLOAD
Non-payload: 6 and 7 delete operations
```

The load-commit handler invokes a follow-up callback whose exact target, ownership, validation role, and error propagation remain unresolved.

## Checkpoint 9D — payload envelope and lifetime

PSP relocations place the fixed workspace at runtime `0x005BAF10` inside the exact `BOOT.BIN` `.bss` range `0x005923C0–0x005C7964`.

```text
Envelope total:         0x755C bytes (30044)
Envelope header:        0x002C bytes (44)
Serialized body offset: 0x002C
Body capacity:          0x7530 bytes (30000)
Active body-size field: envelope +0x28
```

### Save

The body serializer boundary at `0x0034526C` receives capacity `0x7530` and returns a dynamic body length. The save provider at `0x00340DC8` stores that length at `+0x28`, clears the complete body capacity, copies the active body to `+0x2C`, and returns the fixed `0x755C` envelope to the PSP utility. Unused capacity is deterministic zero padding.

### Load

The provider at `0x00340F00` clears the full `0x755C` envelope. The commit handler at `0x00340F64` reads the body length at `+0x28`, records it in the registered-size global, copies exactly that many bytes from `+0x2C`, and invokes the unresolved follow-up callback.

### Lifetime

The envelope is static module BSS with module-load-to-module-unload lifetime. It has no heap allocation or release. Registered external source/destination buffers use globals at `0x005C250C` and `0x005C2510`; the clear function at `0x003401D0` zeros them, while the setter at `0x0034025C` borrows caller-provided pointer and size values until reset or replacement.

## Verification through 9D

```text
172 passed
6 expected environment-gated skips
Ruff passed
Strict mypy passed
10/10 exact BOOT.BIN regions matched
Workspace confirmed inside exact .bss bounds
```

## Checkpoint 9E runtime prerequisite

Checkpoint 9E will not begin until all of the following are available:

1. Exact `ULUS10066-v1.00` game image.
2. A `.ppst` state created by the distributed pinned PPSSPP debugger bundle.
3. Visible confirmation that the state is immediately before or during a save/load operation.
4. Associated `memstick/PSP/SAVEDATA` directory when available.
5. Controlled successful-load and corrupted-copy captures.

The repository already contains a separate Task 8 PPSSPP debugger-bundle builder on `main`; Task 9 does not duplicate that infrastructure.

Useful state positions include:

- immediately before SAVE or AUTOSAVE confirmation;
- immediately before LOAD or AUTOLOAD confirmation;
- immediately after a successful load, before leaving the profile/career menu;
- immediately before confirming a deliberately corrupted copied save.

## Explicitly unresolved

- real-save active body lengths;
- allocator and ultimate owner of registered external buffers;
- per-field serializer and deserializer sets;
- load-commit follow-up callback target and owner;
- post-load validation and error propagation;
- checksum or integrity algorithm;
- encryption or obfuscation;
- profile-slot count;
- profile and career block boundaries;
- headers and version fields;
- write ordering and interrupted-write recovery;
- migration feasibility;
- PRX delegation below the `BOOT.BIN` handoff;
- exclusive ownership across all modules.

## Next checkpoint

**9E — using a matching PPSSPP state, resolve the load-commit follow-up callback and post-load validation/error propagation without assigning persistent field meanings.**
