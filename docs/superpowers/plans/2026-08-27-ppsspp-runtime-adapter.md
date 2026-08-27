# PPSSPP Task 9E Runtime Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a verified external PPSSPP debugger-bundle adapter and Task 9E runtime capture path that can collect deterministic successful-load versus corrupted-copy evidence without committing game/runtime payloads.

**Architecture:** Keep `src/fnr3_re/ppsspp.py` as the generic capture/evidence layer. Add three focused units: `ppsspp_bundle.py` verifies the exact external emulator bundle, `ppsspp_debugger.py` implements the confirmed local WebSocket protocol, and `save_runtime_9e.py` loads the committed Task 9E/static-save evidence, orchestrates the two controls, and serializes repository-safe normalized evidence. `cli.py` only wires these units together.

**Tech Stack:** Python 3.11+, standard library only for runtime transport (`socket`, `base64`, `hashlib`, `json`, `struct`, `subprocess`, `pathlib`), pytest, Ruff, strict mypy, existing `fnr3_re.evidence.Address` types and PPSSPP harness.

**Spec:** `docs/superpowers/specs/2026-08-27-ppsspp-runtime-adapter-design.md`

## Global Constraints

- Locked Fight Night revision: `ULUS10066-v1.00`.
- Locked ISO SHA-256: `b11da5afe208d9791eecd9f6a44d0f57946f7d9de165b7d8dd22f5ee740f4ee2`.
- Locked BOOT.BIN SHA-256: `906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9`.
- Locked PPSSPP revision: `fa50bb1976065c4f8b1b47af227d367fe9771555`.
- Locked `PPSSPPSDL` SHA-256: `143d0d8f89ff5cbe5e65d66efe447a1f0510e376685a7f217cbb581fcf323c06`.
- Locked `PPSSPPHeadless` SHA-256: `623a661cd5b26a34194faf3896925c9da48eb20107306435a959472b3a0813f6`.
- Locked Xvfb SHA-256: `2c7f5a9534410fed5092d782a69ca7ffd9fce80e98b81ffe4944d703dd11d3b1`.
- Default debugger endpoint is local only: `127.0.0.1:56244/debugger`.
- The committed Task 9E capture-plan JSON is the sole source of fixed Task 9E breakpoint/global addresses.
- The committed `analysis/save/save-payload-lifetime.json` artifact is the sole source of DATA.BIN envelope/body offsets and capacities.
- A `.ppst` state is mandatory for valid Task 9E evidence; no-state launches are diagnostic only.
- Raw ISO/save/state/memory/screenshot/debugger-transcript/bundle payloads stay external and uncommitted.
- Ordinary CI uses synthetic fixtures only.
- No new third-party Python runtime dependency is added.

---

### Task 1: Verify the exact external debugger bundle

**Files:**
- Create: `src/fnr3_re/ppsspp_bundle.py`
- Create: `tests/unit/test_ppsspp_bundle.py`
- Modify: `src/fnr3_re/cli.py`
- Create: `tests/unit/test_ppsspp_bundle_cli.py`

**Interfaces:**
- Produces:
  - `DebuggerBundleProfile`
  - `DebuggerBundleIdentity`
  - `PpssppBundleError`
  - `FNR3_DEBUGGER_BUNDLE_PROFILE`
  - `verify_ppsspp_bundle(root: Path, *, profile: DebuggerBundleProfile = FNR3_DEBUGGER_BUNDLE_PROFILE) -> DebuggerBundleIdentity`
- CLI produces: `fnr3-re ppsspp-bundle verify BUNDLE [--json]`.

- [ ] **Step 1: Write failing verifier tests**

Create a synthetic bundle builder in the test file. Tests construct a `DebuggerBundleProfile` whose expected hashes are calculated from fixture bytes so production verification can remain exact without embedding real binaries.

```python
profile = DebuggerBundleProfile(
    revision="fixture-revision",
    sdl_sha256=sha256(b"sdl"),
    headless_sha256=sha256(b"headless"),
    xvfb_sha256=sha256(b"xvfb"),
    default_port=56244,
)
identity = verify_ppsspp_bundle(bundle, profile=profile)
assert identity.revision == "fixture-revision"
assert identity.host == "127.0.0.1"
assert identity.port == 56244
```

Add negative tests for wrong revision, wrong binary hash, missing launcher/client/config, malformed `RemoteISOPort`, `RemoteDebuggerLocal = False`, required symlink, and required path escape.

- [ ] **Step 2: Commit RED tests and verify failure in GitHub Actions**

Expected failure: import of `fnr3_re.ppsspp_bundle` or missing verifier symbols.

- [ ] **Step 3: Implement minimal verifier**

Use immutable dataclasses and recompute hashes directly:

```python
@dataclass(frozen=True, slots=True)
class DebuggerBundleProfile:
    revision: str
    sdl_sha256: str
    headless_sha256: str
    xvfb_sha256: str
    default_port: int

@dataclass(frozen=True, slots=True)
class DebuggerBundleIdentity:
    root: Path
    revision: str
    sdl_path: Path
    sdl_sha256: str
    headless_path: Path
    headless_sha256: str
    xvfb_path: Path
    xvfb_sha256: str
    launcher_path: Path
    client_path: Path
    config_path: Path
    host: str
    port: int
```

Required paths are resolved beneath the bundle root and rejected if symlinked. Parse only the `[General]` keys needed from `ppsspp-debug.ini`; require `RemoteDebuggerOnStartup = True`, `RemoteDebuggerLocal = True`, and a valid `1..65535` `RemoteISOPort`.

- [ ] **Step 4: Add CLI RED/GREEN tests**

CLI test monkeypatches `verify_ppsspp_bundle()` and checks both human and JSON output. JSON contains revision, hashes, host, port, and no absolute binary contents.

- [ ] **Step 5: Run full quality gate and commit GREEN**

Run through GitHub Actions: pytest, Ruff, strict mypy. Commit only after all pass.

---

### Task 2: Implement the confirmed local PPSSPP WebSocket protocol

**Files:**
- Create: `src/fnr3_re/ppsspp_debugger.py`
- Create: `tests/unit/test_ppsspp_debugger.py`

**Interfaces:**
- Consumes: `DebuggerBundleIdentity.host`, `.port`.
- Produces:
  - `PpssppDebuggerError`
  - `DebuggerResponse`
  - `PpssppDebuggerClient`
  - `PpssppDebuggerClient.request(event: str, **params: object) -> dict[str, object]`
  - `PpssppDebuggerClient.send(event: str, **params: object) -> int`
  - `PpssppDebuggerClient.wait_for_event(event: str, *, timeout_seconds: float | None = None) -> dict[str, object]`
  - `get_registers() -> dict[str, int]`
  - `read_memory(address: int, size: int) -> bytes`
  - `add_exec_breakpoint(address: int) -> None`
  - `remove_exec_breakpoint(address: int) -> None`
  - `resume() -> None`
  - `backtrace() -> tuple[int, ...]`

- [ ] **Step 1: Write RED protocol tests around a fake socket**

Tests cover:
- non-loopback host rejected before connection;
- RFC6455 client handshake to `/debugger`;
- masked outgoing text frames;
- unmasked incoming PPSSPP text frames;
- ping/pong and close handling;
- malformed JSON rejected;
- ticketed response correlation;
- mismatched ticket ignored until matching response or timeout;
- `error` event with matching ticket raises;
- finite timeout/disconnect errors.

The fake response fixtures use the confirmed PPSSPP message shapes:

```json
{"event":"cpu.getReg","ticket":3,"uintValue":142887140}
```

and breakpoint broadcast:

```json
{"event":"cpu.stepping","hit":{"kind":"exec","pc":146034532,"address":146034532,"hits":1,"paused":true}}
```

- [ ] **Step 2: Verify RED in CI**

Expected failure: module or client does not exist.

- [ ] **Step 3: Implement framing/connection/request correlation**

Use standard library only. On connect, send a version event and enable deferred acknowledgements:

```python
client.request("version", name="fnr3-re", version="0.1")
client.request("client.config.set", acknowledgeDeferred=True)
```

Do not require the newer documented WebSocket subprotocol because the locked uploaded bundle's own smoke-tested client succeeds without it; compatibility is defined by the locked bundle for this phase.

- [ ] **Step 4: Implement only Task 9E convenience operations**

Map exact confirmed events:

```python
request("cpu.getAllRegs")
request("memory.read", address=address, size=size)
request("cpu.breakpoint.add", address=address, enabled=True, log=False)
request("cpu.breakpoint.remove", address=address)
send("cpu.resume")
request("hle.backtrace")
```

Decode `cpu.getAllRegs.categories[*].registerNames` against `uintValues`; decode `memory.read.base64`; retain only `pc` values from backtrace frames for the normalized call-stack interface.

- [ ] **Step 5: Run Task 2 tests plus existing PPSSPP harness tests, then full quality gate**

The existing `tests/unit/test_ppsspp_harness.py` must remain unchanged unless a demonstrated compatibility bug requires a focused fix.

- [ ] **Step 6: Commit GREEN**

Commit protocol and tests together.

---

### Task 3: Load and validate the committed Task 9E and payload-lifetime evidence

**Files:**
- Create: `src/fnr3_re/save_runtime_9e.py`
- Create: `tests/unit/test_save_runtime_9e_plan.py`

**Interfaces:**
- Produces:
  - `Task9EPlanError`
  - `Task9EBreakpoint`
  - `Task9ELiveGlobal`
  - `Task9EPlan`
  - `PayloadLifetimeContract`
  - `load_task9e_plan(path: Path) -> Task9EPlan`
  - `load_payload_lifetime_contract(path: Path) -> PayloadLifetimeContract`

- [ ] **Step 1: Write RED plan-loader tests**

Tests load repository copies of:
- `analysis/save/checkpoint-9e-runtime-capture-plan.json`
- `analysis/save/save-payload-lifetime.json`

Assert:

```python
plan = load_task9e_plan(plan_path)
assert plan.revision_id == "ULUS10066-v1.00"
assert plan.boot_sha256 == "906f0c...86f9"
assert [bp.id for bp in plan.breakpoints] == [
    "load_commit_entry",
    "before_body_copy",
    "before_followup_pointer_load",
    "before_followup_call",
    "after_followup_return",
]
assert all(bp.address.address_type is AddressType.RUNTIME for bp in plan.breakpoints)
```

Negative fixtures mutate task/checkpoint/schema/revision/BOOT hash/mapping rule, remove a required breakpoint, or replace a runtime address with an invalid domain.

- [ ] **Step 2: Verify RED in CI**

Expected failure: loader symbols absent.

- [ ] **Step 3: Implement strict typed loaders**

No Task 9E address literal is copied into production source. Required breakpoint identity is validated by IDs/control semantics from the JSON; addresses are parsed from JSON into existing `Address(AddressType.RUNTIME, value)` objects.

`PayloadLifetimeContract` reads and validates:

```python
source_revision
boot_sha256
workspace.total_size
workspace.envelope_header_size
workspace.active_body_size_offset
workspace.body_offset
workspace.body_capacity
```

Require `body_offset == envelope_header_size`, `body_offset + body_capacity == total_size`, and matching revision/BOOT identity.

- [ ] **Step 4: Run loader tests and full quality gate**

- [ ] **Step 5: Commit GREEN**

---

### Task 4: Create deterministic safe corrupted-save controls

**Files:**
- Modify: `src/fnr3_re/save_runtime_9e.py`
- Create: `tests/unit/test_save_runtime_9e_mutation.py`

**Interfaces:**
- Consumes: `PayloadLifetimeContract`.
- Produces:
  - `SaveMutation`
  - `SavedataInventoryEntry`
  - `hash_savedata_slot(slot: Path) -> tuple[SavedataInventoryEntry, ...]`
  - `prepare_corrupted_savedata(source_slot: Path, destination_slot: Path, contract: PayloadLifetimeContract) -> SaveMutation`

- [ ] **Step 1: Write RED mutation tests**

Build a synthetic savedata slot containing fixed-size `DATA.BIN` plus metadata files. Encode active body size as little-endian u32 at `active_body_size_offset`, matching PSP/MIPS little-endian data.

Assert:
- source slot hash inventory is unchanged;
- destination is a separate complete copy;
- exactly one byte in `DATA.BIN` changes;
- mutation is inside `[body_offset, body_offset + active_body_size)`;
- file size is unchanged;
- original/replacement byte, offset, before/after hashes are recorded;
- deterministic repeated source input chooses the same first eligible nonzero byte;
- active size `> body_capacity`, truncated envelope, symlink, missing DATA.BIN, or no nonzero active byte fails closed.

- [ ] **Step 2: Verify RED in CI**

- [ ] **Step 3: Implement inventory and corruption preparation**

Algorithm:
1. Reject symlinked slot/files and unsafe paths.
2. Inventory regular files sorted by casefolded relative path with size/SHA-256.
3. Read `DATA.BIN`; require `len(data) == contract.total_size`.
4. Read active body length with `int.from_bytes(..., "little")`.
5. Require `0 < active_size <= body_capacity`.
6. Select the first nonzero byte in the active body.
7. Deterministically mutate it with `replacement = original ^ 0x01`.
8. Copy source slot transactionally to destination scratch slot, mutate only copied DATA.BIN, and verify one-byte delta.

- [ ] **Step 4: Run mutation tests and full quality gate**

- [ ] **Step 5: Commit GREEN**

---

### Task 5: Orchestrate one Task 9E breakpoint capture

**Files:**
- Modify: `src/fnr3_re/save_runtime_9e.py`
- Create: `tests/unit/test_save_runtime_9e_capture.py`

**Interfaces:**
- Consumes: `DebuggerBundleIdentity`, `PpssppDebuggerClient`, `Task9EPlan`, exact ISO/state/savedata slot.
- Produces:
  - `RuntimeBreakpointObservation`
  - `RuntimeControlCapture`
  - `Task9ECaptureInputs`
  - `capture_task9e_control(inputs: Task9ECaptureInputs, *, client_factory: Callable[..., PpssppDebuggerClient] = PpssppDebuggerClient) -> RuntimeControlCapture`

- [ ] **Step 1: Write RED orchestration tests with a scripted fake debugger client**

The fake client records calls and returns a deterministic sequence of `cpu.stepping` events. Tests assert:
- bundle verification and ISO/state SHA checks occur before launcher invocation;
- exact ISO hash mismatch aborts before launch;
- missing state cannot create evidence;
- fixed breakpoints are installed using addresses loaded from the plan object;
- each observed hit matches the next expected plan breakpoint;
- unexpected/missing/repeated order invalidates the control;
- registers are collected only at requested capture points;
- memory is read only for bounded plan globals/regions;
- `before_followup_call` resolves the actual call register target and installs a temporary execution breakpoint at that observed address;
- callback entry registers/backtrace and return context are recorded;
- temporary and fixed breakpoints are removed in `finally` cleanup.

- [ ] **Step 2: Verify RED in CI**

- [ ] **Step 3: Implement launch guard and process lifecycle**

Before launching:
- verify workspace with existing `verify_workspace()`;
- verify workspace manifest revision/hash;
- hash exact ISO and require locked SHA;
- hash state;
- inventory explicit savedata slot;
- verify bundle.

Invoke only the verified bundle-local launcher:

```python
[
    str(bundle.launcher_path),
    str(iso),
    "--state", str(state),
    "--port", str(bundle.port),
]
```

Never invoke `ppsspp_ws.py` as a library. The repository's own client connects to the local endpoint after launcher health succeeds.

- [ ] **Step 4: Implement breakpoint-state machine**

Install fixed execution breakpoints from `plan.breakpoints`. For each step:
1. resume;
2. wait for `cpu.stepping` with `hit.kind == "exec"`;
3. compare `hit.address` to the next expected runtime address;
4. collect requested registers, backtrace, and bounded memory hashes;
5. at `before_followup_call`, derive the call target from the plan-named call register (`t9_or_call_register` resolved from the current register set), install temporary breakpoint at that target, resume to callback entry, record callback context, then continue until return path.

Do not assign a semantic function name to the observed callback in this task.

- [ ] **Step 5: Run capture tests plus all PPSSPP/save tests, then full quality gate**

- [ ] **Step 6: Commit GREEN**

---

### Task 6: Run both controls, compare them, and write deterministic normalized evidence transactionally

**Files:**
- Modify: `src/fnr3_re/save_runtime_9e.py`
- Create: `tests/unit/test_save_runtime_9e_evidence.py`
- Create: `tests/unit/test_save_runtime_9e_output.py`

**Interfaces:**
- Produces:
  - `Task9ERuntimeEvidence`
  - `compare_task9e_controls(success: RuntimeControlCapture, corrupted: RuntimeControlCapture, ...) -> Task9ERuntimeEvidence`
  - `run_task9e_capture(...) -> Task9ERuntimeEvidence`
  - `write_task9e_runtime_evidence(workspace: Path, evidence: Task9ERuntimeEvidence, capture_root: Path) -> Path`

- [ ] **Step 1: Write RED deterministic evidence tests**

Assert byte-identical JSON on repeated serialization and required fields:
- revision/ISO/BOOT identities;
- bundle revision and binary hashes;
- state SHA;
- savedata inventory hashes;
- successful and corrupted control IDs/outcomes;
- typed runtime breakpoint addresses;
- selected register values;
- dynamic callback target as typed runtime address;
- bounded memory region size/SHA only;
- mutation offset/before/after and file hashes;
- first observed divergence;
- separate `runtime_observed`, `static_correlated`, `semantic_interpretation`, `confirmed`, `not_confirmed`, and `warnings` sections.

Assert serialized text does **not** contain raw save bytes, `data_hex`, screenshot paths, raw transcript bodies, assembly bodies, or broad memory dumps.

- [ ] **Step 2: Write RED transactional output tests**

Expected local layout:

```text
workspace/working/runtime/task-9e/<capture-id>/
  successful/control.json
  corrupted/control.json
  comparison.json
  local-diagnostics/
workspace/manifests/task-9e-runtime-evidence.json
```

Tests inject a serialization/install failure and prove a previously valid capture/manifest remains unchanged. Reject symlinked `working/runtime`, `manifests`, or destination parents.

- [ ] **Step 3: Implement first-divergence comparison**

Compare controls in deterministic order:
1. breakpoint hit/miss sequence;
2. dynamic callback target;
3. selected register values at same observation ID;
4. bounded memory hashes;
5. control outcome/error route.

Record the first unequal fact as structured evidence; if controls are identical through all captured facts, `first_divergence` is null and a warning says no divergence was observed.

- [ ] **Step 4: Implement transactional pair replacement**

Use sibling temp directories/files and backup/rollback logic equivalent in strength to `write_psp_analysis_run()`: serialize everything before installation, then replace capture root and manifest as a pair, restoring backups if either replacement fails.

- [ ] **Step 5: Run evidence/output tests and full quality gate**

- [ ] **Step 6: Commit GREEN**

---

### Task 7: Expose the Task 9E CLI and document the actual uploaded bundle workflow

**Files:**
- Modify: `src/fnr3_re/cli.py`
- Create: `tests/unit/test_save_runtime_9e_cli.py`
- Modify: `docs/architecture/ppsspp-debugger-bundle.md`
- Modify: `docs/architecture/ppsspp-capture-harness.md`
- Modify: `README.md`
- Create: `tests/integration/test_task9e_live_capture.py`

**Interfaces:**
- CLI:

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

- [ ] **Step 1: Write CLI RED tests**

Monkeypatch orchestration and assert exact path forwarding, state requirement, JSON summary, and human summary. CLI returns nonzero on verifier/capture errors and does not print raw save/memory/transcript content.

- [ ] **Step 2: Verify RED in CI**

- [ ] **Step 3: Implement CLI**

Defaults for `--plan` and `--payload-lifetime` point to the committed repository artifacts; callers may supply explicit paths for installed/source-tree use. `--savedata-slot` is a specific slot directory, not the broad `PSP/SAVEDATA` parent.

Human output reports only validity, capture ID, callback target if observed, first divergence summary, and evidence path.

- [ ] **Step 4: Add environment-gated live integration test**

Skip unless all are configured:
- `FNR3_REFERENCE_ISO`
- `FNR3_PPSSPP_BUNDLE`
- `FNR3_TASK9E_STATE`
- `FNR3_TASK9E_SAVEDATA_SLOT`

The test verifies identities and runs the live capture only in an explicitly provisioned environment. No generated artifact is committed.

- [ ] **Step 5: Update docs to the uploaded bundle's actual interface**

Correct older `wsdbg`/`--debugger=PORT` language where it conflicts with the verified artifact. Document:
- `launch-debug.sh ISO --state STATE --port PORT`;
- config-driven `RemoteDebuggerOnStartup`, `RemoteDebuggerLocal`, `RemoteISOPort`;
- bundle-local `ppsspp_ws.py` as diagnostic tool only;
- repository adapter uses its own independently testable standard-library client;
- `.ppst` is required for Task 9E evidence;
- raw runtime material stays external.

- [ ] **Step 6: Run complete verification gate**

Require on exact feature head:
- full pytest suite;
- Ruff;
- strict mypy;
- existing PSP-disassembly optional-toolkit CI job still passes;
- no new binary/game/save/state/memory/media files in PR diff;
- `analysis/save/checkpoint-9e-runtime-capture-plan.json` unchanged unless a separately evidenced correction is required;
- `analysis/save/save-payload-lifetime.json` unchanged;
- review threads/comments audited.

- [ ] **Step 7: Commit GREEN and prepare PR**

PR summary must distinguish implemented automation from live evidence actually observed. If the live environment variables are absent, state explicitly that Task 9E runtime evidence remains pending even though the adapter is complete.

---

## Plan self-review

- Every spec component maps to a task: verifier (1), transport (2), evidence loaders (3), corrupted control (4), runtime breakpoint orchestration (5), deterministic evidence/transactions (6), CLI/docs/live gate (7).
- No fixed Task 9E breakpoint address is duplicated in production-code instructions; the plan artifact remains authoritative.
- No DATA.BIN body offset/capacity is duplicated into production-code instructions; the payload-lifetime artifact remains authoritative.
- Transport operations use debugger event names and response shapes supported by the supplied PPSSPP source and the uploaded bundle's smoke-tested WebSocket transport.
- The no-state diagnostic path cannot satisfy Task 9E acceptance.
- Runtime observation, static correlation, and semantic interpretation remain separate.
- Ordinary CI requires no copyrighted runtime material.
- No placeholder/TBD steps remain.
