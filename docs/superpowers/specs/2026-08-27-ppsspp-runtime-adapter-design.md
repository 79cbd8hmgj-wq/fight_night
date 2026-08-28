# PPSSPP Task 9E Runtime Adapter Design

Date: 2026-08-27
Status: Approved in chat; written-spec review pending
Branch: `task-9e-ppsspp-runtime-adapter`

## Purpose

Integrate the verified Fight Night Round 3 PPSSPP debugger bundle with the existing `fnr3-re` runtime-capture harness so Checkpoint 9E can collect controlled, normalized live evidence from the exact ULUS10066-v1.00 game revision.

The adapter must not replace the generic PPSSPP harness, copy PPSSPP binaries into the repository, or promote emulator observations directly into semantic conclusions. It connects one verified external debugger bundle to the existing capture/evidence model and executes the already-prepared Task 9E successful-load and corrupted-copy controls.

## Source artifacts and locked identities

### Fight Night reference revision

The runtime adapter accepts only the locked Fight Night Round 3 PSP reference:

- revision: `ULUS10066-v1.00`
- reference ISO SHA-256: `b11da5afe208d9791eecd9f6a44d0f57946f7d9de165b7d8dd22f5ee740f4ee2`
- BOOT.BIN SHA-256 used by Task 9E: `906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9`

The existing validated external workspace remains authoritative for revision identity and static evidence.

### Verified debugger bundle

The external debugger bundle supplied for this phase is locked to:

- PPSSPP revision: `fa50bb1976065c4f8b1b47af227d367fe9771555`
- `PPSSPPSDL` SHA-256: `143d0d8f89ff5cbe5e65d66efe447a1f0510e376685a7f217cbb581fcf323c06`
- `PPSSPPHeadless` SHA-256: `623a661cd5b26a34194faf3896925c9da48eb20107306435a959472b3a0813f6`
- Xvfb SHA-256: `2c7f5a9534410fed5092d782a69ca7ffd9fce80e98b81ffe4944d703dd11d3b1`
- debugger endpoint: `ws://127.0.0.1:56244/debugger` by default
- debugger transport: bundle-local standard-library `ppsspp_ws.py`
- launch transport: bundle-local `launch-debug.sh`
- debugger startup configuration: `ppsspp-debug.ini` with local-only remote debugging

The adapter verifies these identities from files inside the extracted external bundle. The archive, unpacked PPSSPP binaries, assets, runtime directory, memstick, save states, and save data are never committed to this repository.

## Existing repository boundaries

The repository already provides:

1. A generic deterministic PPSSPP harness in `src/fnr3_re/ppsspp.py` with emulator probing, capture plans, transactional capture bundles, memory snapshots/diffs, breakpoint journals, hash guards, and capture verification.
2. A documented runtime-capture architecture that intentionally leaves transport-specific debugger automation external until the selected PPSSPP build has been confirmed.
3. `analysis/save/checkpoint-9e-runtime-capture-plan.json`, which defines the Task 9E runtime addresses, globals, breakpoint sequence, successful-load control, corrupted-copy control, and evidence boundary.
4. `analysis/save/save-payload-lifetime.json`, which is authoritative for the statically established `DATA.BIN` envelope/body layout used to constrain the corruption experiment.
5. Static PSP analysis integrated through the standalone PSP Disassembly Toolkit.

This change fills only the missing live debugger transport and Task 9E orchestration layer.

## Goals

The implementation must:

- verify the exact external debugger bundle before launch;
- verify the exact ULUS10066-v1.00 ISO before runtime capture;
- use only a loopback debugger endpoint;
- preserve the existing generic PPSSPP capture/evidence models;
- consume existing checkpoint artifacts instead of duplicating runtime addresses or save-body layout constants in production code;
- launch the exact bundle with an explicit compatible `.ppst` state for evidence capture;
- support bundle diagnostics without a state while never classifying a no-state launch as Task 9E evidence;
- collect successful-load and corrupted-copy captures through the same breakpoint protocol;
- resolve the dynamic load follow-up callback at runtime;
- record only the bounded registers/globals/memory hashes required by the checkpoint plan;
- identify the first observed divergence between successful and corrupted controls;
- keep raw runtime material external;
- emit deterministic normalized evidence suitable for later repository promotion after review;
- keep runtime observations distinct from static correlation and semantic interpretation.

## Non-goals

This phase does not:

- decompile new functions merely because they were hit at runtime;
- assign persistent save-field meanings;
- claim checksum, encryption, obfuscation, slot, corruption, or recovery semantics without direct controlled evidence;
- automate arbitrary gameplay scenarios beyond Task 9E;
- make PPSSPP save states authoritative over clean-boot controls;
- add emulator binaries, ISO data, save data, save states, screenshots, raw memory dumps, or raw debugger transcripts to Git;
- replace the standalone PSP Disassembly Toolkit or generic PPSSPP harness.

## Architecture

```text
exact ULUS10066-v1.00 ISO       verified external PPSSPP bundle
            |                              |
            v                              v
  validated Fight Night workspace   bundle verifier
            |                              |
            +---------------+--------------+
                            v
                   Task 9E runtime adapter
                            |
                 local WebSocket debugger
                            |
               +------------+------------+
               v                         v
        successful-load run      corrupted-copy run
               |                         |
               +------------+------------+
                            v
             normalized runtime comparison evidence
                            |
                   researcher review gate
                            |
             repository-safe checkpoint artifact
```

The generic harness remains below this adapter. The Task 9E adapter owns bundle-specific verification, WebSocket event sequencing, checkpoint-artifact interpretation, and successful/corrupted comparison only.

## Components

### 1. Debugger bundle verifier

Add a focused bundle-verification module, expected under `src/fnr3_re/ppsspp_bundle.py` or an equivalently narrow file.

It returns a typed immutable bundle identity containing at least:

- resolved bundle root;
- resolved PPSSPP revision;
- locked executable sizes/hashes;
- verified launcher/client/config paths;
- default debugger host/port;
- verification status and diagnostics.

Verification requires:

- required files are regular files beneath the bundle root;
- no required path is a symlink or escapes the bundle root;
- `ppsspp-resolved-revision.txt` exactly matches the locked revision;
- PPSSPP/Xvfb hashes are recomputed and match the locked values;
- `ppsspp-debug.ini` enables debugger startup, restricts access to local connections, and declares a valid port;
- launcher/client/config files are bundle-local and not substituted from `$PATH`;
- malformed or missing verification data causes a hard failure.

`BUNDLE-VERIFICATION.txt` is supporting metadata, not the trust root.

### 2. Bundle WebSocket transport

Add a small independently testable adapter around the confirmed local PPSSPP debugger JSON WebSocket protocol. Do not import and execute arbitrary code from the external bundle as a Python library.

The transport must:

- connect only to normalized loopback hosts (`127.0.0.1`, `::1`, or `localhost`);
- use `/debugger`;
- use finite connect/read timeouts;
- expose only operations needed by Task 9E initially;
- preserve optional raw transcripts locally but exclude transcript bodies from normalized evidence;
- fail closed on malformed JSON, protocol mismatch, disconnect, timeout, or unsupported operation.

Initial logical operations are expected to cover:

- debugger health/game status;
- CPU pause/resume/status;
- register reads;
- memory reads;
- execution breakpoint create/remove;
- stepping or resume-to-breakpoint;
- backtrace/caller context where confirmed by the pinned debugger interface.

No undocumented debugger event name enters production code without direct evidence for this pinned PPSSPP revision.

### 3. Bundle launcher

The adapter launches through the verified bundle-local `launch-debug.sh`; it does not recreate PPSSPP startup behavior from assumptions.

For Task 9E evidence:

- a `.ppst` state is required;
- state and ISO are hashed before launch;
- bundle verification passes before launch;
- debugger port is explicit;
- the bundle's isolated memstick/runtime layout is used;
- debugger health must succeed before capture begins;
- process/log identity is recorded through the existing harness where applicable.

`--allow-no-state` is diagnostic/setup only and cannot produce a valid Task 9E result.

### 4. Task 9E checkpoint-artifact loader

Add typed loaders for:

- `analysis/save/checkpoint-9e-runtime-capture-plan.json`;
- `analysis/save/save-payload-lifetime.json` for the already-established `DATA.BIN` envelope/body bounds.

The Task 9E plan loader validates:

- schema version;
- task `9`, checkpoint `9E`;
- source revision and BOOT.BIN hash;
- confirmed address rule `ppsspp_absolute = 0x08804000 + elf_virtual`;
- every required fixed breakpoint and live-global address;
- successful-load and corrupted-copy definitions.

The payload-lifetime loader supplies the valid `DATA.BIN` body range/capacity for mutation. Production source must not contain a second independent list of fixed Task 9E addresses or duplicated save-body layout constants.

### 5. Successful-load capture

The successful control executes the fixed breakpoint sequence defined by the Task 9E plan, currently corresponding to:

- load-commit entry;
- before body copy;
- before follow-up pointer load;
- before follow-up call;
- after follow-up return.

The runner uses the addresses from the plan artifact at runtime rather than hard-coded source constants.

At each breakpoint, capture only the registers/globals/memory hashes requested by the plan.

At `before_followup_call`, read the actual callback target from the observed call register/pointer and install a temporary execution breakpoint at that exact runtime target before permitting the indirect call. Record callback-entry and callback-return context without assigning function purpose beyond demonstrated evidence.

### 6. Corrupted-copy control

The known-good save slot is immutable.

The CLI requires a **specific savedata slot directory** containing the successful control's `DATA.BIN`; it does not ambiguously select among all directories under `PSP/SAVEDATA`.

The adapter:

1. validates and hashes the source slot inventory;
2. loads the established `DATA.BIN` body bounds from `save-payload-lifetime.json`;
3. copies the entire slot to a scratch location outside the repository;
4. mutates exactly one eligible nonzero byte inside the validated active-body range;
5. preserves `DATA.BIN` total file size;
6. records relative file path, byte offset, original byte, replacement byte, source hash, mutated hash, and slot inventory hashes;
7. never mutates the source slot in place;
8. runs the same breakpoint protocol as the successful control.

The mutation policy must be deterministic. If the runtime/static evidence cannot establish a safe active-body range or there is no eligible nonzero byte within it, the corrupted control fails closed.

### 7. Runtime comparison evidence

The normalized comparison artifact records facts rather than guessed semantics.

Required fields include:

- schema version;
- Fight Night revision and ISO hash;
- BOOT.BIN hash;
- debugger-bundle revision and binary hashes;
- state hash;
- source and scratch savedata inventory hashes;
- breakpoint identities and typed runtime addresses;
- hit/miss sequence;
- selected register values;
- dynamic follow-up callback runtime target;
- bounded memory region sizes and hashes;
- successful-control outcome;
- corrupted-control mutation provenance and outcome;
- first observed control divergence, if any;
- explicit `confirmed`, `not_confirmed`, and `warnings` sections.

Do not serialize raw save contents, raw memory bytes, screenshots, assembly bodies, debugger transcript bodies, or broad string dumps into repository evidence.

Runtime addresses, ELF virtual addresses, module-relative addresses, and ISO offsets must remain explicitly typed domains.

### 8. Static/runtime evidence bridge

A runtime callback target may correlate with existing static evidence only when:

- the runtime-to-ELF mapping is mechanically demonstrated by the confirmed `0x08804000` rule;
- the static module identity matches the locked BOOT.BIN hash.

Evidence must distinguish:

- `runtime_observed` — directly seen in PPSSPP;
- `static_correlated` — mechanically mapped to existing static evidence;
- `semantic_interpretation` — a separate conclusion requiring supporting evidence.

A runtime hit does not itself prove function purpose.

## CLI

Recommended commands:

```bash
fnr3-re ppsspp-bundle verify /path/to/ppsspp-fnr3-debugger
```

```bash
fnr3-re capture-save-9e \
  /path/to/fnr3-workspace \
  --bundle /path/to/ppsspp-fnr3-debugger \
  --iso /path/to/FightNightRound3.iso \
  --state /path/to/task9-load-boundary.ppst \
  --savedata-slot /path/to/PSP/SAVEDATA/EXACT_SLOT
```

Both commands support `--json`.

The capture command defaults to a local external destination under the selected workspace, for example:

```text
workspace/working/runtime/task-9e/<capture-id>/
```

A compact normalized candidate evidence file may be written under workspace manifests:

```text
workspace/manifests/task-9e-runtime-evidence.json
```

Promotion into `analysis/save/` is a separate reviewed repository action. Live capture never automatically overwrites committed checkpoint evidence.

## Transaction and failure behavior

Runtime capture is transactional.

- Write to a temporary capture directory.
- Verify bundle, ISO, state, checkpoint artifacts, savedata slot, and debugger health before evidence execution.
- Preserve source savedata and state unchanged.
- On debugger disconnect, timeout, unexpected breakpoint sequence, process exit, missing required capture, or serialization failure, mark the run invalid and retain only local diagnostics.
- Atomically install completed local output only after required artifacts are internally consistent.
- Never partially replace a previously valid capture.

A corrupted-control failure does not invalidate an already-complete successful control; the combined comparison remains incomplete until both controls pass.

## Copyright, privacy, and repository policy

The following remain local and uncommitted:

- game ISO/CSO;
- extracted original executables/assets;
- `.ppst` states;
- `PSP/SAVEDATA` contents;
- mutated save copies;
- raw memory dumps;
- screenshots/video/audio;
- raw debugger transcripts;
- bundle binaries/assets/runtime/memstick directories.

Repository-safe normalized evidence may contain hashes, typed addresses, selected register values, bounded sizes/counts, mutation offset and single-byte before/after values, control outcomes, and evidence-backed conclusions.

## Testing strategy

Implementation uses strict TDD. Ordinary CI uses synthetic fixtures only; no PPSSPP binary, Fight Night executable, ISO, save, state, or memory dump is committed as a fixture.

### Bundle verification

- exact synthetic locked bundle accepted;
- wrong revision rejected;
- wrong binary hash rejected;
- missing launcher/client/config rejected;
- symlinked required path rejected;
- non-local debugger configuration rejected;
- malformed port rejected.

### Transport

- loopback accepted;
- non-loopback rejected;
- valid debugger response decoded;
- malformed JSON rejected;
- timeout/disconnect handled deterministically;
- response/protocol mismatch rejected where the confirmed protocol supplies correlation data.

### Checkpoint artifacts

- current Task 9E plan parses;
- current payload-lifetime artifact parses;
- wrong task/checkpoint/revision/BOOT hash rejected;
- missing required breakpoint/control rejected;
- mutation bounds derive from the artifact rather than production constants;
- address domains remain typed.

### Capture orchestration

- bundle verification occurs before launch;
- ISO/state hashes checked before launch;
- no-state launch cannot become Task 9E evidence;
- fixed breakpoint sequence comes from the plan artifact;
- dynamic callback breakpoint is installed from the observed target;
- unexpected breakpoint order invalidates capture;
- transaction rollback preserves prior valid output.

### Corrupted control

- a specific slot directory is required;
- source slot remains byte-identical;
- full slot is copied to scratch;
- mutation occurs inside validated active-body bounds;
- exactly one `DATA.BIN` byte changes and file size is preserved;
- mutation provenance is deterministic;
- missing/ambiguous `DATA.BIN` or no eligible mutation location fails closed.

### Evidence

- deterministic normalized serialization;
- successful/corrupted controls remain separately attributable;
- first divergence is evidence-derived;
- raw bytes/transcripts/screenshots/save contents are absent;
- static/runtime/semantic confidence classes are not conflated.

### Environment-gated live test

A live integration test may run only when explicitly configured with the external locked debugger bundle, exact ISO, compatible `.ppst` state, and exact savedata slot. It is skipped in ordinary CI and its output remains local.

## Acceptance criteria

This phase is complete when:

1. The exact debugger bundle can be independently verified by `fnr3-re`.
2. The existing generic PPSSPP harness remains intact and its tests continue to pass.
3. Existing checkpoint artifacts are the single source of fixed Task 9E addresses and save-body mutation bounds.
4. A synthetic end-to-end successful/corrupted capture passes without copyrighted fixtures.
5. The CLI refuses wrong bundle, ISO, state, checkpoint artifacts, non-loopback transport, ambiguous savedata inputs, and unsafe paths.
6. Local capture output is transactional and independently verifiable.
7. Normalized evidence excludes prohibited raw game/debugger payloads.
8. A real Task 9E run can be performed once the exact ISO, compatible state, and specific savedata slot are supplied locally.
9. No runtime observation is promoted to semantic certainty without explicit supporting evidence.

## Follow-on boundary

After this adapter is implemented, the next project action is the actual Checkpoint 9E experiment: run the successful-load and corrupted-copy controls with verified external inputs, review the normalized evidence, and only then update the committed save-system checkpoint conclusions.