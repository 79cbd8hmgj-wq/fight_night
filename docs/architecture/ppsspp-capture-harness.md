# PPSSPP Runtime Capture Harness

## Purpose

The PPSSPP harness makes emulator-side reverse-engineering captures deterministic, attributable, and verifiable. It records exact executable identities, exact ISO/state/save identities, controlled capture conditions, normalized runtime observations, process outcome, and transactionally installed evidence.

The generic harness remains transport-neutral. Checkpoint 9E adds a separate identity-locked PPSSPP WebSocket adapter for one bounded save-system experiment.

## Generic emulator discovery and probe

`discover_ppsspp()` resolves an executable in this order:

1. Explicit path supplied by the caller.
2. `PPSSPP_EXECUTABLE` from the selected environment.
3. Known headless or SDL executable names on the selected search path.

The selected path must be a regular executable file. `probe_ppsspp()` then records:

- resolved executable path;
- executable size and SHA-256;
- exact `--version` output and return code;
- exact `--help` output, hash, and return code;
- capability references found in the executable name or help output.

A probe is evidence about one exact binary. A generic capture refuses to run if that executable's hash changes afterward.

## Controlled input traces

`InputTrace` records a canonical, hash-stable sequence of PSP controller states. Each event contains:

- frame number;
- sorted, unique button names;
- signed analog X and Y values.

Frames must be strictly increasing. Unknown buttons, duplicate buttons, invalid analog values, and noncanonical ordering are rejected. The trace SHA-256 is embedded in the scenario and checked when the capture plan is constructed.

The trace format records intended deterministic input. Delivery to PPSSPP remains adapter-specific.

## Generic capture plans

A `CapturePlan` binds together:

- exact emulator probe;
- controlled scenario metadata;
- exact input trace;
- explicit process arguments;
- explicit environment additions;
- finite timeout;
- expected artifact paths;
- destination capture directory.

The only argument placeholders expanded by the generic runner are:

- `{iso}` — absolute path to the verified rebuilt ISO;
- `{capture}` — absolute path to the transaction's temporary capture directory.

Unresolved placeholders and NUL bytes are rejected. The generic harness does not invent PPSSPP flags.

## Generic transactional capture bundle

`run_capture()` verifies the current emulator and ISO hashes before launch. It writes into a temporary directory and atomically replaces the requested destination only after the process result and artifact inventory have been recorded.

A generic bundle contains:

```text
capture-plan.json
input-trace.json
stdout.log
stderr.log
capture-result.json
<declared capture artifacts>
```

The result records plan, emulator, and ISO hashes; return code or timeout; stdout/stderr hashes; declared artifact presence, size, and hash; missing required artifacts; and overall validity.

`verify_capture_bundle()` independently checks required files, log hashes, artifact paths, sizes, and hashes. It rejects symlinks and path traversal.

## Memory snapshots and comparisons

`MemorySnapshot` binds raw bytes to:

- snapshot ID;
- source revision;
- module;
- typed address.

`compare_memory()` supports aligned comparisons as unsigned bytes, little-endian halfwords, little-endian words, or little-endian single-precision floats.

Before/after comparisons require matching revision, module, base address, and size. When no initial snapshot exists, values are labeled `unknown_initial` rather than treated as changed or inferred.

## Breakpoint journal

`BreakpointJournal` stores normalized evidence for each breakpoint or watchpoint hit:

- typed breakpoint address;
- execute/read/write access classification;
- width and hit count;
- typed program counter;
- register values;
- reconstructed call stack;
- relevant bounded memory snapshots;
- bounded researcher note;
- exact emulator hash and source revision.

Raw debugger transcripts remain local. Only normalized evidence should be committed.

## Checkpoint 9E runtime adapter

Checkpoint 9E is not a generic PPSSPP launch. It consumes the committed experiment definition in:

```text
analysis/save/checkpoint-9e-runtime-capture-plan.json
analysis/save/save-payload-lifetime.json
```

The JSON artifacts are authoritative for the fixed runtime breakpoint sequence, live globals, control IDs, and save-payload dimensions. Production code loads and validates those artifacts rather than duplicating their addresses or body offsets as constants.

### Required external inputs

A Task 9E run requires all of the following:

- verified Fight Night Round 3 workspace for `ULUS10066-v1.00`;
- exact reference ISO;
- verified identity-locked PPSSPP debugger bundle;
- explicit `.ppst` state;
- explicit savedata **slot directory**, not the broad `PSP/SAVEDATA` parent.

The ISO, state, and save remain external to the repository.

### Launch guard

Before launching PPSSPP, the adapter:

1. verifies the workspace and workspace manifest;
2. confirms the manifest revision, ISO size, and ISO SHA-256 against the locked reference revision;
3. verifies and hashes the supplied ISO;
4. verifies and hashes the supplied `.ppst` state;
5. inventories the supplied savedata slot with sorted relative paths, sizes, and SHA-256 hashes;
6. verifies the external PPSSPP bundle revision, binary hashes, and local debugger configuration.

Only after all preflight checks pass does the adapter launch the verified bundle-local executable wrapper:

```bash
launch-debug.sh ISO --state STATE.ppst --port PORT
```

The adapter never invokes `ppsspp_ws.py` as a Python library. The repository's own `PpssppDebuggerClient` implements and tests the required WebSocket protocol subset independently.

### Breakpoint state machine

The adapter installs the fixed execution breakpoints loaded from the Task 9E plan. Each `cpu.stepping` event must report an execution hit at the next expected address; missing, repeated, or out-of-order fixed hits invalidate the control.

At each fixed observation, only requested registers, scalars, backtrace context, and bounded memory hashes are collected.

At `before_followup_call`, the adapter derives the actual callback target from the observed call register, installs a temporary execution breakpoint at that runtime address, records callback-entry registers/backtrace, removes the temporary breakpoint, and continues to the planned return observation.

The dynamic callback is recorded as an observed runtime address. Checkpoint 9E does not assign it a semantic function name merely because it was reached.

Temporary and fixed breakpoints, debugger connections, and PPSSPP processes are cleaned up in `finally` paths.

### Dual controls

Task 9E runs two controls with the same locked ISO, state identity, bundle identity, and plan:

1. `successful_load` — the untouched source savedata slot;
2. `corrupted_copy_control` — a temporary copied slot with one deterministic bit-flip applied to the first nonzero byte in the validated active body.

The source slot is inventoried before and after preparation and must not change. The corrupted copy must differ by exactly one byte at the recorded offset.

### Normalized evidence

The two controls are compared in deterministic order:

1. breakpoint sequence;
2. dynamic callback target;
3. selected register/scalar values at matching observations;
4. bounded memory hashes;
5. control outcome/error route.

The first unequal fact is recorded as structured `first_divergence` evidence. If every captured fact is identical, `first_divergence` is null and the evidence records a warning that no divergence was observed.

Normalized evidence separates:

- `runtime_observed`;
- `static_correlated`;
- `semantic_interpretation`;
- `confirmed`;
- `not_confirmed`;
- `warnings`.

This prevents a runtime observation from silently becoming a semantic claim.

Raw save bytes, `data_hex`, broad memory dumps, screenshot paths, raw transcript bodies, and assembly bodies are intentionally excluded.

### Transactional output

A successful run installs the capture tree and manifest as a rollback-safe pair:

```text
workspace/working/runtime/task-9e/<capture-id>/
  successful/control.json
  corrupted/control.json
  comparison.json
  local-diagnostics/
workspace/manifests/task-9e-runtime-evidence.json
```

Serialization occurs before installation. Symlinked output components are rejected. If either capture-tree or manifest installation fails, any previously valid pair is restored.

## CLI

The supported Task 9E entry point is:

```bash
fnr3-re capture-save-9e WORKSPACE \
  --bundle BUNDLE \
  --iso ISO \
  --state STATE.ppst \
  --savedata-slot SLOT \
  [--plan analysis/save/checkpoint-9e-runtime-capture-plan.json] \
  [--payload-lifetime analysis/save/save-payload-lifetime.json] \
  [--capture-id ID] \
  [--json]
```

`--state` is required. Human output contains only validity, capture ID, observed callback target if present, first-divergence summary, and evidence path. JSON output contains the same normalized summary fields.

## Environment-gated live verification

The repository includes a live integration test that is skipped unless all four environment variables are present:

```text
FNR3_REFERENCE_ISO
FNR3_PPSSPP_BUNDLE
FNR3_TASK9E_STATE
FNR3_TASK9E_SAVEDATA_SLOT
```

Ordinary CI therefore tests the adapter without requiring or uploading copyrighted/runtime material. A skipped live test does **not** count as observed Fight Night runtime evidence.

## Required controlled scenarios

The wider reverse-engineering program should maintain reproducible saves or states for at least:

- exhibition fighter selection;
- opening bell;
- low stamina;
- stunned fighter;
- knockdown sequence;
- end of round;
- judges' decision;
- career hub;
- training selection;
- weight change;
- title fight;
- created-boxer save/load.

Each research checkpoint should answer one bounded evidence question.

## Current boundary

The generic capture harness, direct PPSSPP WebSocket client, Task 9E plan/payload loaders, deterministic corrupted-save control, breakpoint orchestration, dual-control comparison, normalized evidence writer, CLI, and environment-gated live test are implemented and unit-tested.

The adapter implementation alone does **not** claim that a real Task 9E Fight Night capture has been observed. That claim requires an explicitly provisioned run with the exact ISO, verified bundle, `.ppst` state, and savedata slot, followed by review of the produced normalized evidence.
