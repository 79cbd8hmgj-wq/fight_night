# Task 9E Runtime Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reconstruct a deterministic Fight Night Round 3 runtime image from the committed extracted payload, prepare real PPSSPP save/state inputs, and run the existing Task 9E successful-versus-corrupted capture without requiring the 1.1 GB retail ISO.

**Architecture:** Add a Fight Night-specific runtime preparation layer in front of the already-merged Task 9E adapter. A committed allowlist manifest identity-locks repository payload files, `pycdlib==1.21.0` masters a deterministic temporary ISO, runtime provenance keeps retail identity separate from reconstructed-image identity, and each Task 9E control launches the verified PPSSPP bundle with its own `--memstick` root. Bootstrap uses the verified bundle's own `PPSSPPSDL` and `bin/Xvfb`, debugger-injected PSP controls, the locked `load_commit_entry` breakpoint, and PPSSPP's normal F2 save-state action; it never synthesizes save bytes or the `.ppst` format.

**Tech Stack:** Python 3.11+, `pycdlib==1.21.0`, standard-library hashing/JSON/subprocess/tempfile/ctypes, existing `PpssppDebuggerClient`, verified PPSSPP bundle revision `fa50bb1976065c4f8b1b47af227d367fe9771555`, pytest, Ruff, strict mypy.

**Spec:** `docs/superpowers/specs/2026-08-27-task-9e-runtime-recovery-design.md`

## Global Constraints

- Canonical revision remains `ULUS10066-v1.00`.
- Retail ISO SHA-256 remains `b11da5afe208d9791eecd9f6a44d0f57946f7d9de165b7d8dd22f5ee740f4ee2`; reconstructed images must never be labeled as this retail hash unless they actually match it.
- Locked `BOOT.BIN` SHA-256 remains `906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9`.
- PPSSPP bundle verification remains mandatory and uses the existing pinned profile.
- The runtime builder may create only local temporary/runtime artifacts; ISO, save, `.ppst`, screenshots, raw debugger transcripts, and raw memory must not be committed.
- Repository runtime-image mode must use an explicit committed allowlist; it must not infer payload membership at capture time by scanning the repository.
- Every successful/corrupted control must use a distinct verified PPSSPP memstick root.
- `analysis/save/checkpoint-9e-runtime-capture-plan.json` and `analysis/save/save-payload-lifetime.json` remain authoritative and unchanged during this implementation.
- A skipped live test is not runtime evidence.
- If committed extracted coverage is incomplete, report the exact missing allowlisted paths; do not fall back to requiring the whole retail ISO.
- Bootstrap must create savedata through Fight Night and `.ppst` through PPSSPP itself. It must never construct either binary format directly.

## File Structure

- Create `src/fnr3_re/psp_sfo.py` — deterministic PARAM.SFO writer for locked string metadata.
- Create `src/fnr3_re/runtime_image.py` — payload-manifest parser/verifier, deterministic ISO mastering, and runtime-image report.
- Create `src/fnr3_re/runtime_bootstrap.py` — isolated memstick, Xvfb/PPSSPPSDL bootstrap session, controlled input, F2 savestate trigger, and bootstrap report.
- Create `config/runtime/ulus10066-repository-payload.json` — reviewed repository payload allowlist and destination mapping.
- Create `tools/generate_runtime_payload_manifest.py` — one-time deterministic manifest generator used to produce/review the committed allowlist; runtime code never calls it.
- Modify `src/fnr3_re/ppsspp_debugger.py` — add bounded game-status, timed-run, and controller-input methods needed by bootstrap automation.
- Modify `src/fnr3_re/save_runtime_9e.py` — runtime-source/provenance types and bootstrap identity validation.
- Modify `src/fnr3_re/save_runtime_9e_capture.py` — accept reconstructed runtime provenance and launch each control with explicit `--memstick` routing.
- Modify `src/fnr3_re/save_runtime_9e_evidence.py` — record normalized runtime-source provenance without local absolute paths.
- Modify `src/fnr3_re/cli.py` — add `prepare-fnr3-runtime`, `bootstrap-save-9e`, and repository-runtime options for `capture-save-9e`.
- Modify `pyproject.toml` — add the exact `pycdlib==1.21.0` runtime dependency supplied in the source set.
- Create/modify focused unit and integration tests listed below.

---

### Task 1: Deterministic PARAM.SFO Writer and Runtime Dependency

**Files:**
- Create: `src/fnr3_re/psp_sfo.py`
- Modify: `pyproject.toml`
- Test: `tests/unit/test_psp_sfo.py`

**Interfaces:**
- Consumes: `ReferenceRevision` from `fnr3_re.revision`.
- Produces: `build_runtime_param_sfo(revision: ReferenceRevision) -> bytes`.
- Produces: `build_param_sfo_strings(values: Mapping[str, str]) -> bytes`.

- [ ] **Step 1: Write failing deterministic SFO tests**

```python
from fnr3_re.psp_sfo import build_runtime_param_sfo
from fnr3_re.revision import ReferenceRevision, parse_param_sfo


def _revision() -> ReferenceRevision:
    return ReferenceRevision(
        revision_id="ULUS10066-v1.00",
        disc_id="ULUS10066",
        disc_version="1.00",
        title="EA SPORTS™ FIGHT NIGHT Round 3",
        psp_system_version="2.60",
        iso_size=1137737728,
        iso_sha256="b11da5afe208d9791eecd9f6a44d0f57946f7d9de165b7d8dd22f5ee740f4ee2",
    )


def test_runtime_param_sfo_round_trips_locked_identity() -> None:
    payload = build_runtime_param_sfo(_revision())
    parsed = parse_param_sfo(payload)
    assert parsed["DISC_ID"] == "ULUS10066"
    assert parsed["DISC_VERSION"] == "1.00"
    assert parsed["TITLE"] == "EA SPORTS™ FIGHT NIGHT Round 3"
    assert parsed["PSP_SYSTEM_VER"] == "2.60"


def test_runtime_param_sfo_is_byte_deterministic() -> None:
    assert build_runtime_param_sfo(_revision()) == build_runtime_param_sfo(_revision())
```

- [ ] **Step 2: Verify RED**

Run `pytest tests/unit/test_psp_sfo.py -v`.

Expected: collection/import failure because `fnr3_re.psp_sfo` does not exist.

- [ ] **Step 3: Implement the production SFO writer**

Use the already-tested fixture format from `tests/support/psp_iso.py`, but production code lives in `src/fnr3_re/psp_sfo.py`. Keep insertion order fixed:

```python
_RUNTIME_KEYS = ("DISC_ID", "DISC_VERSION", "PSP_SYSTEM_VER", "TITLE")


def build_runtime_param_sfo(revision: ReferenceRevision) -> bytes:
    return build_param_sfo_strings(
        {
            "DISC_ID": revision.disc_id,
            "DISC_VERSION": revision.disc_version,
            "PSP_SYSTEM_VER": revision.psp_system_version,
            "TITLE": revision.title,
        }
    )
```

`build_param_sfo_strings()` emits PSF version `0x00000101`, string type `0x0204`, 4-byte-aligned data, and rejects empty keys, embedded NULs, and non-string values.

- [ ] **Step 4: Pin the supplied pycdlib version**

Change `pyproject.toml`:

```toml
[project]
dependencies = [
  "pycdlib==1.21.0",
]
```

- [ ] **Step 5: Verify Task 1 GREEN**

```bash
pytest tests/unit/test_psp_sfo.py tests/unit/test_revision.py -v
ruff check src/fnr3_re/psp_sfo.py tests/unit/test_psp_sfo.py
mypy src/fnr3_re/psp_sfo.py tests/unit/test_psp_sfo.py
```

Expected: all pass.

- [ ] **Step 6: Commit Task 1**

```bash
git add pyproject.toml src/fnr3_re/psp_sfo.py tests/unit/test_psp_sfo.py
git commit -m "feat: add deterministic PSP runtime SFO writer"
```

---

### Task 2: Repository Payload Allowlist and Validation

**Files:**
- Create: `src/fnr3_re/runtime_image.py`
- Create: `tools/generate_runtime_payload_manifest.py`
- Create: `config/runtime/ulus10066-repository-payload.json`
- Test: `tests/unit/test_runtime_image_manifest.py`
- Test: `tests/integration/test_repository_runtime_payload.py`

**Interfaces:**
- Produces `RuntimePayloadEntry`, `RuntimePayloadManifest`, `VerifiedRuntimePayloadEntry`.
- Produces `load_runtime_payload_manifest(path: Path) -> RuntimePayloadManifest`.
- Produces `verify_runtime_payload(repository_root: Path, manifest: RuntimePayloadManifest) -> tuple[VerifiedRuntimePayloadEntry, ...]`.

- [ ] **Step 1: Write RED manifest tests**

```python
from pathlib import Path

import pytest

from fnr3_re.runtime_image import RuntimeImageError, load_runtime_payload_manifest


def test_payload_manifest_rejects_duplicate_destinations(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text(
        '{"schema_version":1,"revision_id":"ULUS10066-v1.00",'
        '"entries":['
        '{"source":"BOOT.BIN","destination":"PSP_GAME/SYSDIR/BOOT.BIN",'
        '"size":1,"git_blob_sha1":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","role":"executable"},'
        '{"source":"EBOOT.BIN","destination":"PSP_GAME/SYSDIR/BOOT.BIN",'
        '"size":1,"git_blob_sha1":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","role":"executable"}'
        ']}'
    )
    with pytest.raises(RuntimeImageError, match="duplicate destination"):
        load_runtime_payload_manifest(path)
```

Add tests for absolute/traversal paths, malformed SHA-1, nonpositive sizes, unknown roles, duplicate sources, and revision mismatch.

- [ ] **Step 2: Verify RED**

Run `pytest tests/unit/test_runtime_image_manifest.py -v`.

Expected: import/name failure for the new API.

- [ ] **Step 3: Implement strict types and verifier**

```python
@dataclass(frozen=True, slots=True)
class RuntimePayloadEntry:
    source: PurePosixPath
    destination: PurePosixPath
    size: int
    git_blob_sha1: str
    role: str
    sha256: str | None = None


@dataclass(frozen=True, slots=True)
class RuntimePayloadManifest:
    schema_version: int
    revision_id: str
    entries: tuple[RuntimePayloadEntry, ...]
    sha256: str


@dataclass(frozen=True, slots=True)
class VerifiedRuntimePayloadEntry:
    source_path: Path
    destination: PurePosixPath
    size: int
    sha256: str
    role: str
```

`verify_runtime_payload()` resolves sources under `repository_root`, rejects symlinks/escapes, checks size, hashes SHA-256, checks optional committed SHA-256, and runs `git hash-object --no-filters <file>` to require the committed `git_blob_sha1`. Failure to execute `git` is a hard error.

- [ ] **Step 4: Implement the one-time manifest generator**

`tools/generate_runtime_payload_manifest.py` is not imported by runtime code. It uses an explicit legacy game-root allowlist and maps:

```text
BOOT.BIN                    -> PSP_GAME/SYSDIR/BOOT.BIN
EBOOT.BIN                   -> PSP_GAME/SYSDIR/EBOOT.BIN
UPDATE/*                    -> PSP_GAME/SYSDIR/UPDATE/*
approved legacy game roots  -> PSP_GAME/USRDIR/<same relative path>
```

It writes sorted-key JSON containing `source`, `destination`, `size`, `git_blob_sha1`, optional independently known `sha256`, and `role`.

Invocation:

```bash
python tools/generate_runtime_payload_manifest.py . config/runtime/ulus10066-repository-payload.json
```

- [ ] **Step 5: Generate and review the committed allowlist**

```bash
python -m json.tool config/runtime/ulus10066-repository-payload.json >/dev/null
python - <<'PY'
import json
p=json.load(open('config/runtime/ulus10066-repository-payload.json'))
assert p['revision_id'] == 'ULUS10066-v1.00'
assert any(e['destination']=='PSP_GAME/SYSDIR/BOOT.BIN' for e in p['entries'])
assert any(e['destination'].startswith('PSP_GAME/USRDIR/') for e in p['entries'])
PY
```

Review the diff and require no `src/`, `tests/`, `docs/`, `.github/`, `analysis/`, `config/`, or `tools/` payload source.

- [ ] **Step 6: Add repository integration verification**

```python
def test_committed_runtime_payload_manifest_matches_repository() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest = load_runtime_payload_manifest(
        root / "config/runtime/ulus10066-repository-payload.json"
    )
    entries = verify_runtime_payload(root, manifest)
    boot = next(e for e in entries if str(e.destination) == "PSP_GAME/SYSDIR/BOOT.BIN")
    assert boot.sha256 == "906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9"
```

- [ ] **Step 7: Verify Task 2 GREEN**

```bash
pytest tests/unit/test_runtime_image_manifest.py tests/integration/test_repository_runtime_payload.py -v
ruff check src/fnr3_re/runtime_image.py tools/generate_runtime_payload_manifest.py tests/unit/test_runtime_image_manifest.py tests/integration/test_repository_runtime_payload.py
mypy src/fnr3_re/runtime_image.py tests/unit/test_runtime_image_manifest.py
```

If missing extracted coverage is found, print the exact missing source paths and stop; do not request the retail ISO.

- [ ] **Step 8: Commit Task 2**

```bash
git add src/fnr3_re/runtime_image.py tools/generate_runtime_payload_manifest.py config/runtime/ulus10066-repository-payload.json tests/unit/test_runtime_image_manifest.py tests/integration/test_repository_runtime_payload.py
git commit -m "feat: lock Fight Night repository runtime payload"
```

---

### Task 3: Deterministic Runtime ISO and Provenance Report

**Files:**
- Modify: `src/fnr3_re/runtime_image.py`
- Test: `tests/unit/test_runtime_image_builder.py`
- Test: `tests/integration/test_repository_runtime_image.py`

**Interfaces:**
- Produces `RuntimeImageFileReport`, `RuntimeImageReport`.
- Produces `prepare_runtime_image(repository_root: Path, output_root: Path, manifest: RuntimePayloadManifest, revision: ReferenceRevision, *, force: bool = False) -> RuntimeImageReport`.
- Writes `<output_root>/fight-night-runtime.iso` and `<output_root>/runtime-image.json` as one transactional replacement.

- [ ] **Step 1: Write RED deterministic-build tests**

Create a synthetic repo with BOOT/EBOOT and nested USRDIR files. Build twice:

```python
report_a = prepare_runtime_image(repo, tmp_path / "a", manifest, revision)
report_b = prepare_runtime_image(repo, tmp_path / "b", manifest, revision)
assert report_a.runtime_iso_sha256 == report_b.runtime_iso_sha256
assert (tmp_path / "a/fight-night-runtime.iso").read_bytes() == (
    tmp_path / "b/fight-night-runtime.iso"
).read_bytes()
```

Also read `PSP_GAME/PARAM.SFO` and `PSP_GAME/SYSDIR/BOOT.BIN` back through the existing ISO reader.

- [ ] **Step 2: Verify RED**

Run `pytest tests/unit/test_runtime_image_builder.py -v`.

Expected: missing runtime builder/report API.

- [ ] **Step 3: Implement deterministic pycdlib mastering**

```python
iso.new(
    interchange_level=3,
    joliet=3,
    sys_ident="PSP GAME",
    vol_ident="FNR3_ULUS10066_RUNTIME",
    app_ident_str="fnr3-re runtime recovery",
)
```

Create directories parent-before-child. Add Task 1 `PARAM.SFO` plus verified payload. Primary ISO paths are uppercase and files receive `;1`; Joliet paths retain manifest spelling.

Pin pycdlib's internal timestamps through one private version-guarded context:

```python
@contextmanager
def _fixed_pycdlib_time() -> Iterator[None]:
    fixed = 946684800.0
    with (
        mock.patch("pycdlib.headervd.time.time", return_value=fixed),
        mock.patch("pycdlib.pycdlib.time.time", return_value=fixed),
    ):
        yield
```

The two-build byte-equality test is the guard against dependency drift.

- [ ] **Step 4: Implement runtime report**

```python
@dataclass(frozen=True, slots=True)
class RuntimeImageReport:
    schema_version: int
    revision_id: str
    source_mode: str
    retail_iso_sha256: str
    payload_manifest_sha256: str
    boot_sha256: str
    eboot_sha256: str
    generated_metadata: tuple[tuple[str, str], ...]
    runtime_iso_size: int
    runtime_iso_sha256: str
    deterministic: bool
    files: tuple[RuntimeImageFileReport, ...]
```

`source_mode` is exactly `repository_runtime_image`. Hash the actual ISO after writing; never substitute the retail hash.

- [ ] **Step 5: Make output rollback-safe**

Build in a sibling temporary directory, validate/hash all files and report, then replace the destination. Reject symlink output components. `force=False` refuses an existing destination without mutation.

- [ ] **Step 6: Add repository integration build**

Build the committed payload into `tmp_path`; never upload the ISO as an artifact. Require locked revision/BOOT provenance and a non-empty actual runtime hash. Do not require equality with the retail ISO hash.

- [ ] **Step 7: Verify Task 3 GREEN**

```bash
pytest tests/unit/test_runtime_image_builder.py tests/integration/test_repository_runtime_image.py -v
ruff check src/fnr3_re/runtime_image.py tests/unit/test_runtime_image_builder.py tests/integration/test_repository_runtime_image.py
mypy src/fnr3_re/runtime_image.py tests/unit/test_runtime_image_builder.py
```

- [ ] **Step 8: Commit Task 3**

```bash
git add src/fnr3_re/runtime_image.py tests/unit/test_runtime_image_builder.py tests/integration/test_repository_runtime_image.py
git commit -m "feat: build deterministic Fight Night runtime image"
```

---

### Task 4: Runtime Provenance and Per-Control Memstick Routing

**Files:**
- Modify: `src/fnr3_re/save_runtime_9e.py`
- Modify: `src/fnr3_re/save_runtime_9e_capture.py`
- Modify: `src/fnr3_re/save_runtime_9e_evidence.py`
- Test: `tests/unit/test_save_runtime_9e_capture.py`
- Test: `tests/unit/test_save_runtime_9e_evidence.py`
- Create: `tests/unit/test_save_runtime_9e_provenance.py`

**Interfaces:**
- Produces `Task9ERuntimeSource`.
- Extends `Task9ECaptureInputs` with `runtime_source: Task9ERuntimeSource` and `memstick_root: Path`.

- [ ] **Step 1: Write RED provenance tests**

```python
source = Task9ERuntimeSource.repository_image(
    revision_id="ULUS10066-v1.00",
    retail_iso_sha256=LOCKED_RETAIL_SHA,
    runtime_iso_sha256="1" * 64,
    payload_manifest_sha256="2" * 64,
    boot_sha256=LOCKED_BOOT_SHA,
)
assert source.source_mode == "repository_runtime_image"
assert source.runtime_iso_sha256 != source.retail_iso_sha256
```

Reject wrong revision, wrong BOOT hash, malformed hashes, and report/provenance mismatch.

- [ ] **Step 2: Verify RED**

Run `pytest tests/unit/test_save_runtime_9e_provenance.py -v`.

- [ ] **Step 3: Implement runtime-source validation**

```python
@dataclass(frozen=True, slots=True)
class Task9ERuntimeSource:
    source_mode: str
    revision_id: str
    retail_iso_sha256: str
    runtime_iso_sha256: str
    payload_manifest_sha256: str | None
    boot_sha256: str
```

Provide `retail_iso(...)` and `repository_image(...)` constructors.

Repository-mode preflight requires actual ISO hash == runtime provenance hash, retail provenance == revision hash, and BOOT provenance == Task 9E plan BOOT hash. Retail mode keeps the current exact retail size/hash checks.

- [ ] **Step 4: Route each control to an explicit memstick**

Preflight requires a non-symlink `memstick_root` containing the supplied slot at `PSP/SAVEDATA/<slot-name>`. Launch:

```python
argv = [
    str(bundle.launcher_path),
    str(inputs.iso),
    "--memstick",
    str(inputs.memstick_root),
    "--state",
    str(inputs.state),
    "--port",
    str(bundle.port),
]
```

Tests must prove successful and corrupted controls receive different memstick roots.

- [ ] **Step 5: Normalize provenance in evidence**

`RuntimeControlCapture` gains `runtime_source`. Committed evidence records source mode, retail provenance hash, runtime ISO hash, payload-manifest hash, and save inventory identity, never absolute memstick paths.

- [ ] **Step 6: Verify Task 4 GREEN**

```bash
pytest tests/unit/test_save_runtime_9e_capture.py tests/unit/test_save_runtime_9e_evidence.py tests/unit/test_save_runtime_9e_provenance.py -v
ruff check src/fnr3_re/save_runtime_9e.py src/fnr3_re/save_runtime_9e_capture.py src/fnr3_re/save_runtime_9e_evidence.py tests/unit/test_save_runtime_9e_capture.py tests/unit/test_save_runtime_9e_evidence.py tests/unit/test_save_runtime_9e_provenance.py
mypy src/fnr3_re/save_runtime_9e.py src/fnr3_re/save_runtime_9e_capture.py src/fnr3_re/save_runtime_9e_evidence.py tests/unit/test_save_runtime_9e_provenance.py
```

- [ ] **Step 7: Commit Task 4**

```bash
git add src/fnr3_re/save_runtime_9e.py src/fnr3_re/save_runtime_9e_capture.py src/fnr3_re/save_runtime_9e_evidence.py tests/unit/test_save_runtime_9e_capture.py tests/unit/test_save_runtime_9e_evidence.py tests/unit/test_save_runtime_9e_provenance.py
git commit -m "fix: route Task 9E controls through isolated memsticks"
```

---

### Task 5: PPSSPP Input Automation and Real Save/State Bootstrap

**Files:**
- Modify: `src/fnr3_re/ppsspp_debugger.py`
- Create: `src/fnr3_re/runtime_bootstrap.py`
- Test: `tests/unit/test_ppsspp_debugger.py`
- Create: `tests/unit/test_runtime_bootstrap.py`

**Interfaces:**
- Extends `PpssppDebuggerClient` with `game_status()`, `run_until_time(relative_us: int)`, `press_button(button: str, *, duration_frames: int = 1)`, and `set_analog(x: float, y: float)`.
- Produces `BootstrapInputEvent`, `BootstrapInputTrace`, `Task9EBootstrapReport`.
- Produces `prepare_task9e_bootstrap(...) -> Task9EBootstrapReport`.

- [ ] **Step 1: Add RED debugger request tests**

```python
client.press_button("cross", duration_frames=2)
# input.buttons.press button=cross duration=2
client.set_analog(0.5, -0.25)
# input.analog.send x=0.5 y=-0.25 stick=left
client.run_until_time(500_000)
# cpu.runUntilTime relativeUs=500000
```

Reject unsupported buttons, nonpositive durations, and analog values outside `[-1.0, 1.0]`.

- [ ] **Step 2: Verify debugger RED**

Run `pytest tests/unit/test_ppsspp_debugger.py -v`.

- [ ] **Step 3: Implement debugger methods**

`press_button()` uses `request("input.buttons.press", button=button, duration=duration_frames)`. `set_analog()` uses `request("input.analog.send", x=x, y=y, stick="left")`. `run_until_time()` uses `send("cpu.runUntilTime", relativeUs=relative_us)`.

- [ ] **Step 4: Write RED bootstrap-session tests**

Use fake process/X11/debugger adapters. Assert bootstrap:

1. verifies bundle before launch;
2. launches bundle `bin/Xvfb` and `PPSSPPSDL`, not an unverified system emulator;
3. passes `--memstick <bootstrap-root>` and `--config=<bundle>/ppsspp-debug.ini`;
4. executes an explicit input trace;
5. sets an execution breakpoint at the plan's `load_commit_entry` (`0x08B44F64` loaded from the plan, not duplicated as a production constant);
6. waits for that real breakpoint before savestate creation;
7. discovers a real new Fight Night savedata slot;
8. triggers PPSSPP's F2 save-state action through the X11 adapter;
9. discovers exactly one new `.ppst` under the isolated memstick;
10. writes only hashes/relative runtime-root paths into the bootstrap report.

- [ ] **Step 5: Implement explicit bootstrap trace data**

```python
@dataclass(frozen=True, slots=True)
class BootstrapInputEvent:
    delay_us: int
    button: str
    duration_frames: int = 1


@dataclass(frozen=True, slots=True)
class BootstrapInputTrace:
    trace_id: str
    events: tuple[BootstrapInputEvent, ...]
    sha256: str
```

The trace is loaded from JSON and validated exactly. During live calibration, debugger/screenshot diagnostics may be used locally to discover the Fight Night menu sequence; only the final button/timing trace is committed.

- [ ] **Step 6: Implement a verified SDL bootstrap session**

`runtime_bootstrap.py` starts a free local X display with:

```text
<bundle>/bin/Xvfb :N -screen 0 960x544x24 -nolisten tcp
```

Then launches:

```text
<bundle>/PPSSPPSDL --config=<bundle>/ppsspp-debug.ini --memstick <memstick-root> <runtime.iso>
```

Set `DISPLAY=:N` only in the child environment. Use the already verified bundle paths from `DebuggerBundleIdentity`; never resolve system `PPSSPPSDL` or system `Xvfb`.

- [ ] **Step 7: Implement the X11 F2 state trigger with standard-library ctypes**

Define a private adapter interface so unit tests do not need X11:

```python
class _HostKeyInjector(Protocol):
    def press_f2(self, display_name: str) -> None: ...
```

Production `_X11HostKeyInjector` loads `libX11` and `libXtst` with `ctypes.util.find_library`, opens the selected display, finds the mapped top-level window whose title contains `PPSSPP`, focuses it, translates keysym `F2` with `XKeysymToKeycode`, sends key-down/key-up through `XTestFakeKeyEvent`, calls `XFlush`, and closes the display. Missing libraries, display, PPSSPP window, or XTEST call failure is a hard `RuntimeBootstrapError`.

This invokes PPSSPP's own `VIRTKEY_SAVE_STATE` path; it does not know or write the `.ppst` format.

- [ ] **Step 8: Implement save/state discovery and bootstrap report**

Before the input trace, inventory `PSP/SAVEDATA` and `PSP/PPSSPP_STATE`. Run the trace until the locked load-entry breakpoint is reached. Require exactly one intended Fight Night savedata slot. Trigger F2 while the CPU is stopped at the breakpoint. Require exactly one new `.ppst` file and wait until its size/hash is stable across two polls.

Copy/rename local bootstrap artifacts into deterministic runtime-root locations:

```text
bootstrap/local/memstick/PSP/SAVEDATA/<slot>/...
bootstrap/local/task9e.ppst
bootstrap/task-9e-bootstrap.json
```

The report contains:

```python
@dataclass(frozen=True, slots=True)
class Task9EBootstrapReport:
    schema_version: int
    revision_id: str
    runtime_iso_sha256: str
    payload_manifest_sha256: str
    bundle_revision: str
    bundle_sdl_sha256: str
    savedata_slot_name: str
    savedata_inventory_sha256: str
    state_sha256: str
    input_trace_sha256: str
    state_relative_path: str
    memstick_relative_path: str
```

Relative paths are resolved only under the runtime root and rejected if they traverse or point through symlinks.

- [ ] **Step 9: Verify Task 5 GREEN**

```bash
pytest tests/unit/test_ppsspp_debugger.py tests/unit/test_runtime_bootstrap.py -v
ruff check src/fnr3_re/ppsspp_debugger.py src/fnr3_re/runtime_bootstrap.py tests/unit/test_ppsspp_debugger.py tests/unit/test_runtime_bootstrap.py
mypy src/fnr3_re/ppsspp_debugger.py src/fnr3_re/runtime_bootstrap.py tests/unit/test_runtime_bootstrap.py
```

- [ ] **Step 10: Commit Task 5**

```bash
git add src/fnr3_re/ppsspp_debugger.py src/fnr3_re/runtime_bootstrap.py tests/unit/test_ppsspp_debugger.py tests/unit/test_runtime_bootstrap.py
git commit -m "feat: bootstrap real Fight Night save and PPSSPP state"
```

---

### Task 6: Repository-Runtime CLI and Dual-Control Capture

**Files:**
- Modify: `src/fnr3_re/cli.py`
- Modify: `tests/unit/test_save_runtime_9e_cli.py`
- Create: `tests/unit/test_runtime_image_cli.py`
- Create: `tests/unit/test_runtime_bootstrap_cli.py`

**Interfaces:**
- `fnr3-re prepare-fnr3-runtime REPOSITORY_ROOT OUTPUT_ROOT --bundle BUNDLE [--payload-manifest ...] [--force] [--json]`.
- `fnr3-re bootstrap-save-9e RUNTIME_ROOT --bundle BUNDLE --trace TRACE.json [--json]`.
- `capture-save-9e` accepts either the existing retail arguments or `--runtime-root RUNTIME_ROOT --bootstrap-report REPORT`.

- [ ] **Step 1: Write RED parser/dispatch tests**

```python
args = build_parser().parse_args([
    "prepare-fnr3-runtime", ".", "/tmp/fnr3-runtime", "--bundle", "/tmp/bundle"
])
assert args.command == "prepare-fnr3-runtime"
```

For `capture-save-9e`, make source modes mutually exclusive:

```text
retail mode:       --iso ISO --state STATE --savedata-slot SLOT
repository mode:   --runtime-root ROOT --bootstrap-report REPORT
```

- [ ] **Step 2: Verify CLI RED**

```bash
pytest tests/unit/test_runtime_image_cli.py tests/unit/test_runtime_bootstrap_cli.py tests/unit/test_save_runtime_9e_cli.py -v
```

- [ ] **Step 3: Implement `prepare-fnr3-runtime`**

```python
revision = load_reference_revision(_DEFAULT_REVISION_CONFIG)
manifest = load_runtime_payload_manifest(args.payload_manifest)
verify_ppsspp_bundle(args.bundle, profile=FNR3_DEBUGGER_BUNDLE_PROFILE)
report = prepare_runtime_image(
    args.repository_root, args.output_root, manifest, revision, force=args.force
)
```

Human output is a one-line revision/runtime-hash/file-count summary; JSON uses the normalized report.

- [ ] **Step 4: Implement `bootstrap-save-9e`**

Load and verify `<runtime-root>/runtime-image.json`, bundle, Task 9E plan, and explicit input trace; call `prepare_task9e_bootstrap()`; write `bootstrap/task-9e-bootstrap.json` transactionally. Raw save/state remain under `bootstrap/local/`.

- [ ] **Step 5: Implement repository-mode `capture-save-9e`**

Load `runtime-image.json` and bootstrap report. Verify runtime ISO hash, state hash, save inventory, bundle identity, revision, payload-manifest hash, and BOOT hash. Resolve only report-relative paths under the runtime root.

Create temporary control roots:

```text
successful-memstick/PSP/SAVEDATA/<slot>/...
corrupted-memstick/PSP/SAVEDATA/<slot>/...
```

Copy the bootstrap save into each. Apply `prepare_corrupted_savedata()` only to the corrupted slot. Pass the same verified `.ppst` and runtime ISO to both controls with their distinct `memstick_root` values.

- [ ] **Step 6: Preserve safe output contracts**

Extend existing tests so CLI/evidence never emit `DATA.BIN`, `data_hex`, `raw_memory`, `transcript`, `.ppst` contents, or absolute memstick/state paths. Error output remains one safe line and exit code 1.

- [ ] **Step 7: Verify Task 6 GREEN**

```bash
pytest tests/unit/test_runtime_image_cli.py tests/unit/test_runtime_bootstrap_cli.py tests/unit/test_save_runtime_9e_cli.py tests/unit/test_save_runtime_9e_capture.py tests/unit/test_save_runtime_9e_evidence.py -v
ruff check src/fnr3_re/cli.py tests/unit/test_runtime_image_cli.py tests/unit/test_runtime_bootstrap_cli.py tests/unit/test_save_runtime_9e_cli.py
mypy src/fnr3_re/cli.py tests/unit/test_runtime_image_cli.py tests/unit/test_runtime_bootstrap_cli.py tests/unit/test_save_runtime_9e_cli.py
```

- [ ] **Step 8: Commit Task 6**

```bash
git add src/fnr3_re/cli.py tests/unit/test_runtime_image_cli.py tests/unit/test_runtime_bootstrap_cli.py tests/unit/test_save_runtime_9e_cli.py
git commit -m "feat: capture Task 9E from reconstructed runtime"
```

---

### Task 7: Live Calibration, Live Gate, Documentation, and Merge

**Files:**
- Create after observed calibration: `config/runtime/task9e-bootstrap-trace.json`
- Modify: `tests/integration/test_task9e_live_capture.py`
- Modify: `docs/architecture/ppsspp-capture-harness.md`
- Modify: `docs/architecture/rebuild-pipeline.md`
- Modify: `README.md`
- Modify only after actual semantic evidence: `analysis/save/task-status.json`

**Interfaces:**
- Live repository-runtime mode no longer requires `FNR3_REFERENCE_ISO`.
- Task 9E semantic status is promoted only after a real successful/corrupted capture completes and normalized evidence is reviewed.

- [ ] **Step 1: Run local runtime-image boot smoke test with the verified bundle**

Build the repository runtime into temporary storage, launch through Task 5 bootstrap session, and require `game.start` / a non-null game path from the debugger. Confirm the locked BOOT hash before launch.

If the game cannot boot, preserve local logs and identify the exact missing/misplaced payload or generated metadata issue. Do not replace the reconstructed image with an unverified ISO.

- [ ] **Step 2: Calibrate the Fight Night input trace against the real game**

Use the debugger's input methods plus local screenshots/logs only as diagnostics. Record the smallest deterministic PSP-button sequence that:

1. clears startup/autosave prompts;
2. reaches a real path that creates a Fight Night save;
3. reaches and triggers the game's load path;
4. stops at the plan-loaded `load_commit_entry` breakpoint.

Write only the observed button/delay sequence to `config/runtime/task9e-bootstrap-trace.json`; do not commit screenshots, saves, or transcripts. Re-run the trace from a fresh memstick and require it to reach the same breakpoint before accepting it.

- [ ] **Step 3: Run bootstrap and require real savedata + `.ppst`**

Run:

```bash
fnr3-re bootstrap-save-9e /local/fnr3-runtime \
  --bundle /local/ppsspp-bundle \
  --trace config/runtime/task9e-bootstrap-trace.json
```

Require a valid Fight Night savedata inventory and non-empty state hash. Verify source memstick files are unchanged after bootstrap finalization.

- [ ] **Step 4: Run the actual Task 9E dual-control capture**

```bash
fnr3-re capture-save-9e /local/fnr3-workspace \
  --bundle /local/ppsspp-bundle \
  --runtime-root /local/fnr3-runtime \
  --bootstrap-report /local/fnr3-runtime/bootstrap/task-9e-bootstrap.json
```

Require both controls valid, fixed breakpoint sequence complete, dynamic callback observed, and successful/corrupted memstick identities distinct. Review `first_divergence` before making any semantic promotion.

- [ ] **Step 5: Update the environment-gated integration test**

Repository mode requires `FNR3_PPSSPP_BUNDLE`; `FNR3_TASK9E_RUNTIME_ROOT` may point to an already prepared runtime. If bootstrap/runtime evidence is not provisioned, skip with an explicit reason. Retail `FNR3_REFERENCE_ISO` mode remains supported.

- [ ] **Step 6: Update documentation**

Document the three identities separately:

```text
retail provenance identity
repository payload-manifest identity
actual reconstructed runtime-ISO identity
```

Document:

```bash
fnr3-re prepare-fnr3-runtime . /local/fnr3-runtime --bundle /local/ppsspp-bundle
fnr3-re bootstrap-save-9e /local/fnr3-runtime --bundle /local/ppsspp-bundle --trace config/runtime/task9e-bootstrap-trace.json
fnr3-re capture-save-9e /local/fnr3-workspace --bundle /local/ppsspp-bundle --runtime-root /local/fnr3-runtime --bootstrap-report /local/fnr3-runtime/bootstrap/task-9e-bootstrap.json
```

State explicitly that reconstructed runtime hash != retail ISO identity and that no game/save/state binaries are added by this work.

- [ ] **Step 7: Run full verification**

```bash
pytest -q
ruff check src tests tools
mypy
```

Also require no diff in:

```text
analysis/save/checkpoint-9e-runtime-capture-plan.json
analysis/save/save-payload-lifetime.json
```

Their pre-work `main` blob SHAs are:

```text
4c5604cf8bfe72d0eae226b3209ade19bf37527f
98d18eec570b7b3b3e953e7a5e653bcc8f35419a
```

- [ ] **Step 8: Audit tracked artifacts**

Require no newly tracked `*.iso`, `*.cso`, `*.ppst`, `PSP/SAVEDATA/**`, RAM dumps, screenshots, or raw runtime logs. The payload manifest may reference historical game files already present on `main`, but this branch adds no new game payload binaries.

- [ ] **Step 9: Update Task 9 status only if live evidence justifies it**

If the real dual-control capture resolves the follow-up callback/validation/error route, update `analysis/save/task-status.json` and related save evidence conservatively from the normalized observations. If live capture does not complete or is ambiguous, leave the existing 9E evidence gate unchanged.

- [ ] **Step 10: Commit final trace/docs/tests/evidence**

Stage only files that actually changed. Example when live evidence succeeds:

```bash
git add config/runtime/task9e-bootstrap-trace.json tests/integration/test_task9e_live_capture.py docs/architecture/ppsspp-capture-harness.md docs/architecture/rebuild-pipeline.md README.md analysis/save/task-status.json analysis/save/
git commit -m "docs: complete reconstructed Task 9E runtime workflow"
```

If semantic status did not change, omit `analysis/save/task-status.json` and any unchanged analysis artifacts.

- [ ] **Step 11: Open PR and exact-head verify**

PR title:

```text
Task 9E: recover runtime from extracted Fight Night payload
```

PR body states: no retail ISO required in repository mode; no new game binaries added; retail/runtime identities remain distinct; `--memstick` routing is fixed; real save/state are produced by Fight Night/PPSSPP; and live semantic evidence is claimed only if Step 4 actually succeeded.

- [ ] **Step 12: Merge only after gates**

Require exact PR-head pytest/Ruff/strict-mypy/PSP-analysis success, review-thread audit, exact-head merge, and post-merge `main` CI success.

---

## Stop Conditions

1. **Payload coverage failure:** report exact missing allowlisted source paths and stop before ISO mastering.
2. **Determinism failure:** fix identical-input ISO byte instability before PPSSPP work.
3. **BOOT mismatch:** stop immediately; do not run PPSSPP.
4. **Bundle mismatch:** stop immediately; do not substitute a different emulator build.
5. **Bootstrap input uncertainty:** keep diagnostics local and calibrate against observed game behavior; do not guess a committed trace.
6. **Savestate trigger failure:** fix Xvfb/X11/PPSSPP F2 delivery; do not synthesize `.ppst`.
7. **Memstick-routing ambiguity:** do not interpret control divergence until distinct `--memstick` roots are proven.
8. **No live evidence:** keep Task 9E semantic status blocked even when runtime-recovery code is green.
