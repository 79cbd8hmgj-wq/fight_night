# PPSSPP Task 9E Runtime Adapter Design

Date: 2026-08-27
Status: Approved in chat; written-spec review pending
Branch: `task-9e-ppsspp-runtime-adapter`

## Purpose

Integrate the verified Fight Night Round 3 PPSSPP debugger bundle with the existing `fnr3-re` runtime-capture harness so Checkpoint 9E can collect controlled, normalized live evidence from the exact ULUS10066-v1.00 game revision.

The adapter must not replace the generic PPSSPP harness, copy PPSSPP binaries into the repository, or promote emulator observations directly into semantic conclusions. It connects one verified external debugger bundle to the existing capture/evidence model and executes the already-prepared Task 9E successful-load and corrupted-copy controls.

## Source artifacts and locked identities

### Fight Night reference revision

The runtime adapter accepts only the locked Fight Night Round 3 PSP reference unless an explicitly separate future exploratory mode is designed:

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

The adapter verifies these identities from files inside the extracted external bundle. The 214 MB archive, unpacked PPSSPP binaries, assets, runtime directory, memstick, save states, and save data are never committed to this repository.

## Existing repository boundaries

The repository already provides:

1. A generic deterministic PPSSPP harness in `src/fnr3_re/ppsspp.py` with emulator probing, capture plans, transactional capture bundles, memory snapshots/diffs, breakpoint journals, hash guards, and capture verification.
2. A documented runtime-capture architecture that intentionally leaves transport-specific debugger automation external until the selected PPSSPP build has been confirmed.
3. `analysis/save/checkpoint-9e-runtime-capture-plan.json`, which already defines the exact Task 9E addresses, globals, breakpoints, successful-load control, corrupted-copy control, and evidence boundary.
4. Static PSP analysis integrated through the standalone PSP Disassembly Toolkit.

This change fills only the missing live debugger transport and Task 9E orchestration layer.

## Goals

The implementation must:

- verify the exact external debugger bundle before launch;
- verify the exact ULUS10066-v1.00 ISO before runtime capture;
- use only the bundle's local WebSocket endpoint and reject non-loopback debugger hosts;
- preserve the existing generic PPSSPP capture/evidence models;
- consume the existing Task 9E capture plan instead of duplicating its addresses in source code;
- launch the exact bundle with an explicit compatible `.ppst` state for evidence capture;
- support bundle diagnostics without a state, but never classify a no-state diagnostic launch as Task 9E evidence;
- collect successful-load and corrupted-copy captures through the same breakpoint protocol;
- resolve the dynamic load follow-up callback at runtime;
- record bounded register values and memory-region hashes needed by the prepared plan;
- identify the first observed divergence between the successful and corrupted controls;
- write raw runtime artifacts only to the external workspace/capture directory;
- emit a deterministic normalized evidence artifact suitable for repository promotion after researcher review;
- keep runtime observations distinct from static-toolkit placement confidence and from semantic interpretation.

## Non-goals

This phase does not:

- decompile new functions merely because they were hit at runtime;
- assign persistent save-field meanings;
- claim checksum, encryption, obfuscation, slot, corruption, or recovery semantics unless directly supported by the captured controls;
- automate arbitrary gameplay scenarios beyond Task 9E;
- make PPSSPP save states authoritative over clean-boot controls;
- add emulator binaries, ISO data, save data, save states, screenshots, raw memory dumps, or raw debugger transcripts to Git;
- replace the standalone PSP Disassembly Toolkit or the generic PPSSPP harness.

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

The generic harness remains below this adapter. The Task 9E adapter owns bundle-specific verification, WebSocket event sequencing, capture-plan interpretation, and successful/corrupted comparison semantics only.

## Components

### 1. Debugger bundle verifier

Add a focused bundle-verification module, expected under `src/fnr3_re/ppsspp_bundle.py` or an equivalently narrow file.

It returns a typed immutable bundle identity containing at least:

- resolved bundle root;
- resolved PPSSPP revision;
- `PPSSPPSDL`, `PPSSPPHeadless`, and Xvfb sizes/hashes;
- required launcher/client/config paths;
- default debugger host/port;
- verification status and diagnostics.

Verification requires:

- required files are regular files beneath the bundle root;
- no required path is a symlink or escapes the bundle root;
- the revision file exactly matches the locked revision;
- binary hashes exactly match the locked hashes;
- `ppsspp-debug.ini` enables remote debugger startup, restricts the debugger to local access, and declares the expected default port;
- launcher/client files exist and are not silently substituted from `$PATH`;
- malformed or missing verification data causes a hard failure.

The repository does not trust `BUNDLE-VERIFICATION.txt` alone; it recomputes the locked binary hashes itself.

### 2. Bundle WebSocket transport

Add a small adapter around the confirmed PPSSPP debugger JSON protocol. It may reuse logic from the bundle's `ppsspp_ws.py`, but repository implementation must be independently testable and must not execute arbitrary bundle Python code as a library.

The transport must:

- connect only to `127.0.0.1`, `::1`, or `localhost` after normalization;
- use `/debugger`;
- support request/response correlation required by the selected PPSSPP protocol;
- expose only the operations Task 9E needs initially;
- use finite connect/read timeouts;
- preserve raw transcripts locally when requested, but exclude them from normalized repository evidence;
- fail closed on malformed JSON, mismatched response identity, disconnects, or unsupported events.

Initial logical operations are expected to cover:

- debugger health/game status;
- CPU pause/resume/status;
- register reads;
- memory reads;
- execution breakpoint create/remove;
- stepping/resume until breakpoint;
- backtrace or caller context when available.

No undocumented event name is accepted into production code without evidence from the pinned debugger interface or a test fixture representing that confirmed interface.

### 3. Bundle launcher

The adapter launches the external bundle through its verified `launch-debug.sh`, not a reimplementation of PPSSPP startup flags.

For Task 9E evidence:

- a `.ppst` state is required;
- the state is hashed before launch;
- the exact ISO is hashed before launch;
- the bundle verifier must pass first;
- the launcher's debugger port is explicit;
- the process uses the bundle's isolated memstick/runtime model;
- debugger health must succeed before capture begins;
- process/stdout/stderr identity is recorded through the existing harness where applicable.

`--allow-no-state` remains permitted only for bundle diagnostics/setup and cannot produce a valid Task 9E checkpoint result.

### 4. Task 9E capture-plan loader

Add a typed loader for `analysis/save/checkpoint-9e-runtime-capture-plan.json`.

It validates:

- schema version;
- task `9`, checkpoint `9E`;
- source revision and BOOT.BIN hash;
- the confirmed address rule `ppsspp_absolute = 0x08804000 + elf_virtual`;
- every required fixed breakpoint and live-global address;
- successful-load and corrupted-copy control definitions.

The runner must read fixed addresses from this artifact. Production source must not contain a second independent list of Task 9E breakpoint addresses.

### 5. Successful-load capture

The successful control must record the existing plan's fixed sequence:

- load-commit entry at `0x08B44F64`;
- before body copy at `0x08B44FAC`;
- before follow-up pointer load at `0x08B44FB4`;
- before follow-up call at `0x08B44FC0`;
- after follow-up return at `0x08B44FC8`.

At each breakpoint, capture only the registers/globals/memory hashes named by the checkpoint plan.

At `before_followup_call`, read the actual callback target from the call register/pointer and install a temporary execution breakpoint at that exact runtime address before allowing the indirect call to execute. Record callback-entry and callback-return context without naming the callback semantically unless the evidence proves identity.

### 6. Corrupted-copy control

The known-good save is immutable.

The adapter creates a scratch copy of the relevant save set outside the repository and performs exactly one controlled mutation inside the `DATA.BIN` active body:

- choose a recorded nonzero byte within the active body;
- preserve total file size;
- record file, byte offset, original byte, replacement byte, original SHA-256, and mutated SHA-256;
- never mutate the source save in place;
- run the same breakpoint sequence as the successful control.

The mutation algorithm must be deterministic given the selected source save and explicit mutation policy. If no eligible nonzero byte exists within the validated active-body range, the corrupted control fails rather than mutating an unverified location.

### 7. Runtime comparison evidence

The normalized comparison artifact records facts, not guessed semantics.

Required fields include:

- schema version;
- Fight Night revision and ISO hash;
- BOOT.BIN hash;
- debugger-bundle revision and binary hashes;
- state hash;
- savedata inventory hashes;
- capture IDs and timestamps only where determinism does not require omission;
- fixed breakpoint identities and typed runtime addresses;
- hit/miss sequence;
- selected register values;
- dynamic follow-up callback runtime target;
- bounded memory region sizes and SHA-256 values;
- successful-control outcome;
- corrupted-control mutation provenance;
- corrupted-control outcome;
- first observed control divergence, if any;
- explicit `confirmed`, `not_confirmed`, and `warnings` sections.

Do not serialize raw save contents, raw memory bytes, screenshots, assembly bodies, debugger transcript bodies, or broad string dumps into repository evidence.

Runtime addresses must be tagged as runtime addresses. ELF virtual addresses, module-relative addresses, ISO offsets, and runtime addresses must never share an untyped integer field.

### 8. Static/runtime evidence bridge

The adapter may correlate a runtime callback target with an existing static function/symbol only when the mapping is mechanically demonstrated through the confirmed `0x08804000` translation and the static module identity matches the locked BOOT.BIN hash.

The evidence format must distinguish:

- `runtime_observed` — directly seen in PPSSPP;
- `static_correlated` — mechanically mapped to existing static evidence;
- `semantic_interpretation` — human/research conclusion requiring separate support.

A runtime hit is not by itself proof of function purpose.

## CLI

Recommended commands:

```bash
fnr3-re ppsspp-bundle verify /path/to/ppsspp-fnr3-debugger
```

and:

```bash
fnr3-re capture-save-9e \
  /path/to/fnr3-workspace \
  --bundle /path/to/ppsspp-fnr3-debugger \
  --iso /path/to/FightNightRound3.iso \
  --state /path/to/task9-load-boundary.ppst \
  --savedata /path/to/PSP/SAVEDATA
```

Both commands support `--json`.

The capture command should default to a local external capture destination beneath the selected Fight Night workspace, for example:

```text
workspace/working/runtime/task-9e/<capture-id>/
```

A compact normalized candidate evidence file may be written under workspace manifests, for example:

```text
workspace/manifests/task-9e-runtime-evidence.json
```

Promotion into `analysis/save/` is a separate reviewed repository action; live capture must not automatically overwrite committed checkpoint evidence.

## Transaction and failure behavior

Runtime capture is transactional.

- Write to a temporary capture directory.
- Verify bundle, ISO, state, plan, debugger health, and required local inputs before execution.
- Preserve the source savedata and state unchanged.
- On debugger disconnect, timeout, unexpected breakpoint sequence, process exit, missing required capture, or serialization failure, mark the run invalid and retain sufficient local diagnostics without promoting normalized evidence as confirmed.
- Atomically install the completed local capture only after required artifacts are internally consistent.
- Never partially replace a previously valid capture.

A corrupted-control failure must not invalidate an already-complete successful-control capture; the combined comparison remains incomplete until both required controls pass.

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

Repository-safe normalized evidence may contain hashes, addresses, register values, bounded sizes/counts, mutation offsets and byte before/after values, control outcomes, and evidence-backed conclusions.

## Testing strategy

Implementation uses strict TDD.

All ordinary CI tests use synthetic fixtures only. No PPSSPP binary, Fight Night executable, game image, save, state, or memory dump is committed as a fixture.

Required tests include:

### Bundle verification

- exact synthetic locked bundle accepted;
- wrong PPSSPP revision rejected;
- wrong binary hash rejected;
- missing launcher/client/config rejected;
- symlinked required paths rejected;
- debugger configured non-local rejected;
- malformed port rejected.

### Transport

- local loopback connection accepted;
- non-loopback host rejected;
- valid debugger response decoded;
- malformed JSON rejected;
- timeout/disconnect handled deterministically;
- mismatched request/response correlation rejected where the protocol supplies IDs.

### Task 9E plan

- current plan parses;
- wrong task/checkpoint/revision/BOOT hash rejected;
- address-domain fields remain typed;
- missing required breakpoint/control rejected.

### Capture orchestration

- bundle verification occurs before launch;
- ISO/state hashes are checked before launch;
- no-state launch cannot become valid Task 9E evidence;
- fixed breakpoint sequence comes from the plan artifact;
- dynamic callback breakpoint is installed from the observed target;
- unexpected breakpoint order invalidates the capture;
- transaction rollback preserves prior valid output.

### Corrupted control

- source save remains byte-identical;
- scratch mutation occurs inside the validated active-body range;
- exactly one byte changes and size is preserved;
- mutation provenance is deterministic;
- no eligible mutation location fails closed.

### Evidence

- deterministic normalized serialization;
- successful/corrupted controls remain separately attributable;
- first divergence is evidence-derived;
- raw bytes/transcript/screenshots/save data are absent;
- static/runtime/semantic confidence classes are not conflated.

### Environment-gated live test

A live integration test may run only when explicitly configured with the external locked debugger bundle, exact ISO, compatible `.ppst` state, and save data. It is skipped in ordinary CI. Its output remains local.

## Acceptance criteria

This phase is complete when:

1. The exact debugger bundle can be verified independently by `fnr3-re`.
2. The existing generic PPSSPP harness remains intact and its tests continue to pass.
3. The Task 9E plan is the single source of fixed runtime addresses.
4. A synthetic end-to-end successful/corrupted capture passes all unit tests without copyrighted fixtures.
5. The CLI refuses wrong bundle, ISO, state, plan, remote host, and unsafe paths.
6. Local capture output is transactional and independently verifiable.
7. Normalized evidence excludes prohibited raw game/debugger payloads.
8. A real Task 9E run can be performed once the exact ISO, compatible state, and savedata are supplied locally.
9. No runtime observation is promoted to semantic certainty without explicit supporting evidence.

## Follow-on boundary

After this adapter is implemented, the next project action is not a broad new subsystem. It is the actual Checkpoint 9E experiment: run the successful-load control and corrupted-copy control with the verified external inputs, review the normalized evidence, and only then update the committed save-system checkpoint conclusions.