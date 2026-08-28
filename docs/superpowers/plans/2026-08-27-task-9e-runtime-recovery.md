# Task 9E Runtime Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reconstruct a deterministic Fight Night Round 3 runtime image from the committed extracted payload, prepare isolated PPSSPP save/state inputs, and run the existing Task 9E successful-versus-corrupted capture without requiring the 1.1 GB retail ISO.

**Architecture:** Add a Fight Night-specific runtime preparation layer in front of the already-merged Task 9E adapter. A committed allowlist manifest identity-locks repository payload files, `pycdlib==1.21.0` masters a deterministic temporary ISO, a runtime provenance object keeps retail identity separate from reconstructed-image identity, and each Task 9E control launches the verified PPSSPP bundle with its own `--memstick` root. The existing breakpoint plan and save-payload semantics remain unchanged.

**Tech Stack:** Python 3.11+, `pycdlib==1.21.0`, standard-library hashing/JSON/subprocess/tempfile, existing `PpssppDebuggerClient`, verified PPSSPP bundle revision `fa50bb1976065c4f8b1b47af227d367fe9771555`, pytest, Ruff, strict mypy.

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

## File Structure

- Create `src/fnr3_re/psp_sfo.py` — deterministic PARAM.SFO writer for locked string metadata.
- Create `src/fnr3_re/runtime_image.py` — payload-manifest parser/verifier, deterministic ISO mastering, and runtime-image report.
- Create `src/fnr3_re/runtime_bootstrap.py` — isolated memstick construction, controlled input trace execution, bootstrap save/state discovery, and bootstrap identity report.
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
- Produces: `build_param_sfo_strings(values: Mapping[str, str]) -> bytes` for fixture-level tests only.

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

- [ ] **Step 2: Run the new tests and verify RED**

Run:

```bash
pytest tests/unit/test_psp_sfo.py -v
```

Expected: collection/import failure because `fnr3_re.psp_sfo` does not exist.

- [ ] **Step 3: Implement the production SFO writer**

Use the already-tested fixture format from `tests/support/psp_iso.py`, but place production code in `src/fnr3_re/psp_sfo.py`. Keep insertion order fixed to these four keys:

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

`build_param_sfo_strings()` must emit PSF version `0x00000101`, string type `0x0204`, 4-byte-aligned data, and reject empty keys, embedded NULs, duplicate keys after normalization, and non-string values.

- [ ] **Step 4: Pin the supplied pycdlib version**

Change `pyproject.toml`:

```toml
[project]
dependencies = [
  "pycdlib==1.21.0",
]
```

Do not copy GPL PPSSPP code into the project; pycdlib is used only as the ISO mastering dependency.

- [ ] **Step 5: Verify Task 1 GREEN**

Run:

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
- Produces: `RuntimePayloadEntry`.
- Produces: `RuntimePayloadManifest`.
- Produces: `load_runtime_payload_manifest(path: Path) -> RuntimePayloadManifest`.
- Produces: `verify_runtime_payload(repository_root: Path, manifest: RuntimePayloadManifest) -> tuple[VerifiedRuntimePayloadEntry, ...]`.
- Later tasks consume the verified entries and the manifest SHA-256.

- [ ] **Step 1: Write RED tests for strict manifest parsing**

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

Add companion tests rejecting absolute/traversal paths, symlinks, malformed SHA-1, nonpositive sizes, unknown roles, and revision mismatch.

- [ ] **Step 2: Verify the parser tests fail**

Run:

```bash
pytest tests/unit/test_runtime_image_manifest.py -v
```

Expected: import/name failure for the new manifest API.

- [ ] **Step 3: Implement manifest data types and verifier**

Use these frozen interfaces:

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

`verify_runtime_payload()` must:

1. resolve each source under `repository_root`;
2. reject symlinks and escapes;
3. require exact size;
4. compute SHA-256;
5. require `sha256` where present;
6. use `git hash-object --no-filters <file>` and require the committed `git_blob_sha1`;
7. return entries in manifest order.

If `git` cannot be executed, fail closed with `RuntimeImageError`; do not silently skip blob verification.

- [ ] **Step 4: Implement the one-time manifest generator**

`tools/generate_runtime_payload_manifest.py` is allowed to inspect the current checkout because its output is reviewed and committed. It must never be imported by production runtime code.

The generator must use an explicit source-root allowlist defined in the tool, not “everything except source files”. It maps:

```text
BOOT.BIN                    -> PSP_GAME/SYSDIR/BOOT.BIN
EBOOT.BIN                   -> PSP_GAME/SYSDIR/EBOOT.BIN
UPDATE/*                    -> PSP_GAME/SYSDIR/UPDATE/*
approved legacy game roots  -> PSP_GAME/USRDIR/<same relative path>
```

The approved legacy roots are derived from the committed extracted-game tree only. The generated JSON includes `source`, `destination`, `size`, `git_blob_sha1`, optional independently-known `sha256`, and `role`.

Invocation:

```bash
python tools/generate_runtime_payload_manifest.py . config/runtime/ulus10066-repository-payload.json
```

- [ ] **Step 5: Generate and review the real manifest**

Run the generator, then explicitly verify:

```bash
python -m json.tool config/runtime/ulus10066-repository-payload.json >/dev/null
python - <<'PY'
import json
p=json.load(open('config/runtime/ulus10066-repository-payload.json'))
print(len(p['entries']))
assert any(e['destination']=='PSP_GAME/SYSDIR/BOOT.BIN' for e in p['entries'])
assert any(e['destination'].startswith('PSP_GAME/USRDIR/') for e in p['entries'])
PY
```

Review the diff to ensure no `src/`, `tests/`, `docs/`, `.github/`, `analysis/`, `config/`, or `tools/` path is included as game payload except the intended `UPDATE/*` source directory.

- [ ] **Step 6: Add repository integration validation**

```python
from pathlib import Path

from fnr3_re.runtime_image import load_runtime_payload_manifest, verify_runtime_payload


def test_committed_runtime_payload_manifest_matches_repository() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest = load_runtime_payload_manifest(
        root / "config/runtime/ulus10066-repository-payload.json"
    )
    entries = verify_runtime_payload(root, manifest)
    assert entries
    boot = next(e for e in entries if str(e.destination) == "PSP_GAME/SYSDIR/BOOT.BIN")
    assert boot.sha256 == "906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9"
```

- [ ] **Step 7: Verify Task 2 GREEN**

Run:

```bash
pytest tests/unit/test_runtime_image_manifest.py tests/integration/test_repository_runtime_payload.py -v
ruff check src/fnr3_re/runtime_image.py tools/generate_runtime_payload_manifest.py tests/unit/test_runtime_image_manifest.py tests/integration/test_repository_runtime_payload.py
mypy src/fnr3_re/runtime_image.py tests/unit/test_runtime_image_manifest.py
```

Expected: all pass. If the integration test identifies missing extracted files, report those exact source paths and stop Task 2; do not request the retail ISO.

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
- Consumes: `RuntimePayloadManifest`, `VerifiedRuntimePayloadEntry`, `ReferenceRevision`.
- Produces: `RuntimeImageReport`.
- Produces: `prepare_runtime_image(repository_root: Path, output_root: Path, manifest: RuntimePayloadManifest, revision: ReferenceRevision, *, force: bool = False) -> RuntimeImageReport`.
- Produces files: `<output_root>/fight-night-runtime.iso` and `<output_root>/runtime-image.json` transactionally.

- [ ] **Step 1: Write RED tests for deterministic ISO construction**

Create a synthetic repository fixture with BOOT/EBOOT plus two nested USRDIR files and a manifest using real git-blob calculations. Assert two independent output roots produce byte-identical ISO/report identities:

```python
report_a = prepare_runtime_image(repo, tmp_path / "a", manifest, revision)
report_b = prepare_runtime_image(repo, tmp_path / "b", manifest, revision)
assert report_a.runtime_iso_sha256 == report_b.runtime_iso_sha256
assert report_a.payload_manifest_sha256 == report_b.payload_manifest_sha256
assert (tmp_path / "a/fight-night-runtime.iso").read_bytes() == (
    tmp_path / "b/fight-night-runtime.iso"
).read_bytes()
```

Also assert `parse_param_sfo(read_iso9660_file(..., "PSP_GAME/PARAM.SFO"))` returns the locked metadata and that `read_iso9660_file(..., "PSP_GAME/SYSDIR/BOOT.BIN")` matches the source bytes.

- [ ] **Step 2: Verify RED**

Run:

```bash
pytest tests/unit/test_runtime_image_builder.py -v
```

Expected: `prepare_runtime_image` / `RuntimeImageReport` missing.

- [ ] **Step 3: Implement deterministic ISO mastering with pycdlib**

Use `pycdlib.PyCdlib()` with:

```python
iso.new(
    interchange_level=3,
    joliet=3,
    sys_ident="PSP GAME",
    vol_ident="FNR3_ULUS10066_RUNTIME",
    app_ident_str="fnr3-re runtime recovery",
)
```

Create directories in parent-before-child sorted order. Add `PARAM.SFO` from Task 1 and all verified payload entries in manifest order. Primary ISO paths are uppercase ISO9660 paths with `;1` on files; Joliet paths retain the manifest destination spelling.

Because pycdlib 1.21.0 internally calls `time.time()`, isolate timestamp determinism in one private context manager pinned to this dependency version:

```python
@contextmanager
def _fixed_pycdlib_time() -> Iterator[None]:
    fixed = 946684800.0  # 2000-01-01T00:00:00Z
    with (
        mock.patch("pycdlib.headervd.time.time", return_value=fixed),
        mock.patch("pycdlib.pycdlib.time.time", return_value=fixed),
    ):
        yield
```

Use it only around `new()`, `add_directory()`, `add_file()` / `add_fp()`, and `write()` calls. The byte-determinism test is the guard against pycdlib internal drift.

- [ ] **Step 4: Implement the normalized report**

Use:

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

`source_mode` must be exactly `"repository_runtime_image"`. The report must serialize sorted-key UTF-8 JSON with a terminal newline. It must never set `runtime_iso_sha256` from the revision config; it must hash the actual newly written image.

- [ ] **Step 5: Make ISO/report installation transactional**

Build in a sibling temporary directory, serialize/hash everything first, then replace `<output_root>` only after validation. Reject symlink output components. Without `force`, existing output fails before mutation. With `force`, a failure while preparing the replacement leaves the prior valid output untouched.

- [ ] **Step 6: Add repository-level build integration test**

The integration test uses the committed allowlist and builds into `tmp_path`; it must not upload or retain the ISO as a CI artifact. Assert:

```python
assert report.revision_id == "ULUS10066-v1.00"
assert report.retail_iso_sha256 == "b11da5afe208d9791eecd9f6a44d0f57946f7d9de165b7d8dd22f5ee740f4ee2"
assert report.boot_sha256 == "906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9"
assert report.runtime_iso_sha256 != ""
assert report.deterministic is True
```

Do **not** assert that the reconstructed runtime hash equals the retail ISO hash.

- [ ] **Step 7: Verify Task 3 GREEN**

Run:

```bash
pytest tests/unit/test_runtime_image_builder.py tests/integration/test_repository_runtime_image.py -v
ruff check src/fnr3_re/runtime_image.py tests/unit/test_runtime_image_builder.py tests/integration/test_repository_runtime_image.py
mypy src/fnr3_re/runtime_image.py tests/unit/test_runtime_image_builder.py
```

Expected: all pass; two synthetic builds have identical bytes.

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
- Produces: `Task9ERuntimeSource`.
- Extends: `Task9ECaptureInputs` with `runtime_source` and `memstick_root`.
- Existing retail mode remains expressible with `source_mode="retail_iso"`.

- [ ] **Step 1: Write RED provenance tests**

Define expectations:

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

Add tests rejecting wrong revision provenance, wrong BOOT hash, malformed hashes, and runtime-image report mismatch.

- [ ] **Step 2: Verify RED**

Run:

```bash
pytest tests/unit/test_save_runtime_9e_provenance.py -v
```

Expected: missing `Task9ERuntimeSource`.

- [ ] **Step 3: Implement runtime-source validation**

Use this public shape:

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

Provide classmethods `retail_iso(...)` and `repository_image(...)` so call sites cannot invent mode strings.

For repository mode, `_preflight()` must replace the current hard requirement `hash(inputs.iso) == revision.iso_sha256` with:

```python
actual_iso_sha256 = hash_file(inputs.iso)
if actual_iso_sha256 != inputs.runtime_source.runtime_iso_sha256:
    raise Task9EPlanError("runtime ISO hash does not match runtime provenance")
if inputs.runtime_source.retail_iso_sha256 != inputs.revision.iso_sha256:
    raise Task9EPlanError("runtime provenance does not match locked retail revision")
if inputs.runtime_source.boot_sha256 != inputs.plan.boot_sha256:
    raise Task9EPlanError("runtime provenance BOOT.BIN does not match Task 9E plan")
```

Retail mode retains the old exact size/hash checks.

- [ ] **Step 4: Add explicit memstick root to each capture**

Extend `Task9ECaptureInputs`:

```python
memstick_root: Path
runtime_source: Task9ERuntimeSource
```

Preflight requires a normal non-symlink directory containing `PSP/SAVEDATA/<slot-name>` equal to `savedata_slot.resolve()`. Reject a slot outside the supplied memstick root.

Launch arguments become:

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

Update launcher-fake tests to assert the successful and corrupted controls receive different `--memstick` values.

- [ ] **Step 5: Record normalized provenance in evidence**

`RuntimeControlCapture` gains `runtime_source`. Evidence JSON includes source mode, retail provenance hash, runtime ISO hash, payload-manifest hash, and normalized memstick identity such as `savedata_inventory_sha256`; it must not serialize the absolute memstick path.

- [ ] **Step 6: Verify Task 4 GREEN**

Run:

```bash
pytest tests/unit/test_save_runtime_9e_capture.py tests/unit/test_save_runtime_9e_evidence.py tests/unit/test_save_runtime_9e_provenance.py -v
ruff check src/fnr3_re/save_runtime_9e.py src/fnr3_re/save_runtime_9e_capture.py src/fnr3_re/save_runtime_9e_evidence.py tests/unit/test_save_runtime_9e_capture.py tests/unit/test_save_runtime_9e_evidence.py tests/unit/test_save_runtime_9e_provenance.py
mypy src/fnr3_re/save_runtime_9e.py src/fnr3_re/save_runtime_9e_capture.py src/fnr3_re/save_runtime_9e_evidence.py tests/unit/test_save_runtime_9e_provenance.py
```

Expected: all pass, including explicit per-control routing assertions.

- [ ] **Step 7: Commit Task 4**

```bash
git add src/fnr3_re/save_runtime_9e.py src/fnr3_re/save_runtime_9e_capture.py src/fnr3_re/save_runtime_9e_evidence.py tests/unit/test_save_runtime_9e_capture.py tests/unit/test_save_runtime_9e_evidence.py tests/unit/test_save_runtime_9e_provenance.py
git commit -m "fix: route Task 9E controls through isolated memsticks"
```

---

### Task 5: PPSSPP Input Automation and Bootstrap Artifacts

**Files:**
- Modify: `src/fnr3_re/ppsspp_debugger.py`
- Create: `src/fnr3_re/runtime_bootstrap.py`
- Test: `tests/unit/test_ppsspp_debugger.py`
- Create: `tests/unit/test_runtime_bootstrap.py`

**Interfaces:**
- Extends `PpssppDebuggerClient` with:
  - `game_status() -> dict[str, object]`
  - `run_until_time(relative_us: int) -> int`
  - `press_button(button: str, *, duration_frames: int = 1) -> None`
  - `set_analog(x: float, y: float) -> None`
- Produces: `BootstrapInputEvent`, `BootstrapInputTrace`, `Task9EBootstrapReport`.
- Produces: `prepare_task9e_bootstrap(...) -> Task9EBootstrapReport`.

- [ ] **Step 1: Add RED debugger method tests**

Use the existing fake WebSocket server and assert exact request payloads:

```python
client.press_button("cross", duration_frames=2)
# server observes:
# {"event":"input.buttons.press","button":"cross","duration":2,"ticket":...}

client.set_analog(0.5, -0.25)
# {"event":"input.analog.send","x":0.5,"y":-0.25,"stick":"left",...}

client.run_until_time(500_000)
# {"event":"cpu.runUntilTime","relativeUs":500000,...}
```

Reject unsupported button names and analog values outside `[-1.0, 1.0]` before sending.

- [ ] **Step 2: Verify debugger RED**

Run:

```bash
pytest tests/unit/test_ppsspp_debugger.py -v
```

Expected: method-not-found failures for new API calls.

- [ ] **Step 3: Implement the debugger methods minimally**

Button mapping must use debugger-native names: `cross`, `circle`, `triangle`, `square`, `up`, `down`, `left`, `right`, `start`, `select`, `home`, `ltrigger`, `rtrigger`, `vol_up`, `vol_down`.

`press_button()` uses `request("input.buttons.press", ...)`; `set_analog()` uses `request("input.analog.send", x=x, y=y, stick="left")`; `run_until_time()` validates positive microseconds and uses `send("cpu.runUntilTime", relativeUs=relative_us)`.

- [ ] **Step 4: Write RED bootstrap tests with a fake launcher/client**

The bootstrap unit test creates a runtime image fixture, isolated memstick root, and fake debugger. It asserts:

1. bundle verification happens before launch;
2. launch receives `--memstick <bootstrap-root>`;
3. the input trace is executed in exact order;
4. a newly created `PSP/SAVEDATA/<slot>` is discovered only after the trace;
5. an existing unrelated save slot is ignored;
6. source/runtime identities appear in `Task9EBootstrapReport`;
7. no save bytes or absolute paths appear in `to_mapping()`.

- [ ] **Step 5: Implement bootstrap input trace types**

Use:

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
```

The trace is explicit data, not hard-coded sleeps scattered through the runner. For each event, use `run_until_time(delay_us)`, wait for `cpu.stepping`, then `press_button()` and resume.

- [ ] **Step 6: Implement bootstrap save discovery first**

`prepare_task9e_bootstrap()` launches the reconstructed runtime with a fresh isolated memstick. It snapshots `PSP/SAVEDATA` before input, runs the supplied trace, then requires exactly one new Fight Night slot directory. It records a hash inventory using the existing `hash_savedata_slot()`.

Do not fabricate `DATA.BIN` or any other save file.

- [ ] **Step 7: Support `.ppst` as an explicit bootstrap output, without blocking cold-boot automation**

The runtime adapter must support two bootstrap completion forms:

```python
@dataclass(frozen=True, slots=True)
class Task9EBootstrapReport:
    revision_id: str
    runtime_iso_sha256: str
    bundle_revision: str
    savedata_slot_name: str
    savedata_inventory_sha256: str
    state_sha256: str | None
    input_trace_sha256: str
```

If the verified bundle/session produces a `.ppst`, record and validate it. If no state is produced, retain `state_sha256=None` and allow the later capture path to use the same deterministic cold-boot input trace rather than manufacturing a state file. This preserves semantic correctness while avoiding a false requirement for synthesizing PPSSPP’s private savestate format.

The capture implementation added in Task 6 must therefore support either:

- `state: Path` with exact state hash; or
- `state=None` plus the bootstrap trace needed to reach the load path.

- [ ] **Step 8: Verify Task 5 GREEN**

Run:

```bash
pytest tests/unit/test_ppsspp_debugger.py tests/unit/test_runtime_bootstrap.py -v
ruff check src/fnr3_re/ppsspp_debugger.py src/fnr3_re/runtime_bootstrap.py tests/unit/test_ppsspp_debugger.py tests/unit/test_runtime_bootstrap.py
mypy src/fnr3_re/ppsspp_debugger.py src/fnr3_re/runtime_bootstrap.py tests/unit/test_runtime_bootstrap.py
```

Expected: all pass; bootstrap never synthesizes savedata or `.ppst` bytes.

- [ ] **Step 9: Commit Task 5**

```bash
git add src/fnr3_re/ppsspp_debugger.py src/fnr3_re/runtime_bootstrap.py tests/unit/test_ppsspp_debugger.py tests/unit/test_runtime_bootstrap.py
git commit -m "feat: add PPSSPP save bootstrap automation"
```

---

### Task 6: Repository-Runtime CLI and State-or-Cold-Boot Capture

**Files:**
- Modify: `src/fnr3_re/save_runtime_9e.py`
- Modify: `src/fnr3_re/save_runtime_9e_capture.py`
- Modify: `src/fnr3_re/cli.py`
- Modify: `tests/unit/test_save_runtime_9e_cli.py`
- Create: `tests/unit/test_runtime_image_cli.py`
- Create: `tests/unit/test_runtime_bootstrap_cli.py`

**Interfaces:**
- CLI: `fnr3-re prepare-fnr3-runtime REPOSITORY_ROOT OUTPUT_ROOT --bundle BUNDLE [--payload-manifest ...] [--force] [--json]`.
- CLI: `fnr3-re bootstrap-save-9e RUNTIME_ROOT --bundle BUNDLE --trace TRACE.json [--json]`.
- Existing CLI: `capture-save-9e` accepts either retail ISO inputs or `--runtime-root RUNTIME_ROOT` plus bootstrap artifacts.

- [ ] **Step 1: Write RED parser tests**

Assert:

```python
args = build_parser().parse_args([
    "prepare-fnr3-runtime", ".", "/tmp/fnr3-runtime", "--bundle", "/tmp/bundle"
])
assert args.command == "prepare-fnr3-runtime"
```

For capture, enforce mutually exclusive source modes:

```text
retail mode:       --iso ISO --state STATE --savedata-slot SLOT
repository mode:   --runtime-root ROOT --bootstrap-report REPORT
```

`--state` becomes optional only in repository mode when the bootstrap report has `state_sha256=null` and a trace is present.

- [ ] **Step 2: Verify CLI RED**

Run:

```bash
pytest tests/unit/test_runtime_image_cli.py tests/unit/test_runtime_bootstrap_cli.py tests/unit/test_save_runtime_9e_cli.py -v
```

Expected: parser/dispatch failures for new commands/options.

- [ ] **Step 3: Implement `prepare-fnr3-runtime`**

Execution order:

```python
revision = load_reference_revision(_DEFAULT_REVISION_CONFIG)
manifest = load_runtime_payload_manifest(args.payload_manifest)
verify_ppsspp_bundle(args.bundle, profile=FNR3_DEBUGGER_BUNDLE_PROFILE)
report = prepare_runtime_image(args.repository_root, args.output_root, manifest, revision, force=args.force)
```

The bundle check is included because the command prepares a Task 9E runtime root, not a generic ISO mastering utility.

Human output:

```text
runtime: revision=ULUS10066-v1.00 iso=<sha256> files=<count> root=<output-root>
```

JSON contains only normalized report fields and the user-selected output root.

- [ ] **Step 4: Implement `bootstrap-save-9e`**

Load `<runtime-root>/runtime-image.json`, verify the runtime ISO, verify the bundle, load the explicit trace JSON, and call `prepare_task9e_bootstrap()`. Write `<runtime-root>/bootstrap/task-9e-bootstrap.json` transactionally. Raw save/state files stay under `<runtime-root>/bootstrap/local/` and are ignored by Git policy.

- [ ] **Step 5: Add cold-boot path to `capture_task9e_control()`**

Change `Task9ECaptureInputs.state` to `Path | None` and add `bootstrap_trace: BootstrapInputTrace | None`.

Launch arguments:

```python
argv = [str(bundle.launcher_path), str(inputs.iso), "--memstick", str(inputs.memstick_root)]
if inputs.state is not None:
    argv.extend(["--state", str(inputs.state)])
argv.extend(["--port", str(bundle.port)])
```

When `state is None`, connect, install all fixed Task 9E breakpoints **before resuming**, then execute the supplied bootstrap trace until the first expected Task 9E breakpoint stops execution. The fixed breakpoint state machine thereafter remains unchanged.

Reject `state=None` with no bootstrap trace.

- [ ] **Step 6: Build per-control memsticks in the CLI**

Inside the existing temporary directory create:

```text
successful-memstick/PSP/SAVEDATA/<slot>/...
corrupted-memstick/PSP/SAVEDATA/<slot>/...
```

Copy the source save into both. Apply `prepare_corrupted_savedata()` only to the corrupted copy. Pass each full memstick root plus its contained slot to its corresponding `Task9ECaptureInputs`.

- [ ] **Step 7: Verify CLI output/raw-artifact exclusion**

Extend the existing checks so no emitted JSON/evidence contains `DATA.BIN`, `data_hex`, `raw_memory`, `transcript`, `.ppst` bytes, or absolute memstick paths.

- [ ] **Step 8: Verify Task 6 GREEN**

Run:

```bash
pytest tests/unit/test_runtime_image_cli.py tests/unit/test_runtime_bootstrap_cli.py tests/unit/test_save_runtime_9e_cli.py tests/unit/test_save_runtime_9e_capture.py tests/unit/test_save_runtime_9e_evidence.py -v
ruff check src/fnr3_re/cli.py src/fnr3_re/save_runtime_9e.py src/fnr3_re/save_runtime_9e_capture.py tests/unit/test_runtime_image_cli.py tests/unit/test_runtime_bootstrap_cli.py tests/unit/test_save_runtime_9e_cli.py
mypy src/fnr3_re/cli.py src/fnr3_re/save_runtime_9e.py src/fnr3_re/save_runtime_9e_capture.py tests/unit/test_runtime_image_cli.py tests/unit/test_runtime_bootstrap_cli.py tests/unit/test_save_runtime_9e_cli.py
```

Expected: all pass.

- [ ] **Step 9: Commit Task 6**

```bash
git add src/fnr3_re/cli.py src/fnr3_re/save_runtime_9e.py src/fnr3_re/save_runtime_9e_capture.py tests/unit/test_runtime_image_cli.py tests/unit/test_runtime_bootstrap_cli.py tests/unit/test_save_runtime_9e_cli.py tests/unit/test_save_runtime_9e_capture.py tests/unit/test_save_runtime_9e_evidence.py
git commit -m "feat: capture Task 9E from reconstructed runtime"
```

---

### Task 7: Live Gate, Documentation, Full Verification, and PR

**Files:**
- Modify: `tests/integration/test_task9e_live_capture.py`
- Modify: `docs/architecture/ppsspp-capture-harness.md`
- Modify: `docs/architecture/rebuild-pipeline.md`
- Modify: `README.md`
- Modify only if required by accurate status: `analysis/save/task-status.json`

**Interfaces:**
- Live gate supports repository-runtime mode without `FNR3_REFERENCE_ISO`.
- No semantic Task 9E status is promoted until a real successful/corrupted capture completes and its normalized evidence is reviewed.

- [ ] **Step 1: Update the environment-gated live integration test**

Repository-runtime live mode requires:

```text
FNR3_PPSSPP_BUNDLE
```

and the committed repository payload. It builds a temporary runtime image. If no identity-matched bootstrap save exists, the test must skip with the explicit reason `Task 9E bootstrap save/state not provisioned` rather than failing or pretending evidence exists.

A separately provisioned bootstrap may be supplied with:

```text
FNR3_TASK9E_BOOTSTRAP_ROOT
```

Retail mode with `FNR3_REFERENCE_ISO` remains supported for backwards compatibility.

- [ ] **Step 2: Add a repository-runtime smoke gate**

Before any semantic capture, verify:

1. runtime image builds;
2. `PSP_GAME/PARAM.SFO` parses to locked identity;
3. `PSP_GAME/SYSDIR/BOOT.BIN` hashes to the locked BOOT hash;
4. PPSSPP bundle verification passes;
5. runtime artifacts are under temporary/output storage, not tracked paths.

This gate may pass without claiming a save/load callback was observed.

- [ ] **Step 3: Update documentation to distinguish three identities**

Document separately:

```text
retail provenance identity
repository payload-manifest identity
actual reconstructed runtime-ISO identity
```

Update Task 9E examples:

```bash
fnr3-re prepare-fnr3-runtime . /local/fnr3-runtime --bundle /local/ppsspp-bundle
fnr3-re bootstrap-save-9e /local/fnr3-runtime --bundle /local/ppsspp-bundle --trace config/runtime/task9e-bootstrap-trace.json
fnr3-re capture-save-9e /local/workspace --bundle /local/ppsspp-bundle --runtime-root /local/fnr3-runtime --bootstrap-report /local/fnr3-runtime/bootstrap/task-9e-bootstrap.json
```

State explicitly that a reconstructed runtime image does not equal the retail ISO, and that this mode is valid for Task 9E because the experiment observes the locked executable/save path rather than UMD sector placement.

- [ ] **Step 4: Run focused full tests**

Run:

```bash
pytest -q
ruff check src tests tools
mypy
```

Expected: full suite passes; the live semantic test is skipped unless real bootstrap/runtime inputs are present.

- [ ] **Step 5: Verify immutable Task 9E plan artifacts**

Compare branch against `main` and require no diff in:

```text
analysis/save/checkpoint-9e-runtime-capture-plan.json
analysis/save/save-payload-lifetime.json
```

Their `main` blob SHAs before this work are:

```text
4c5604cf8bfe72d0eae226b3209ade19bf37527f
98d18eec570b7b3b3e953e7a5e653bcc8f35419a
```

- [ ] **Step 6: Audit tracked files for forbidden runtime artifacts**

Require no newly tracked files matching:

```text
*.iso
*.cso
*.ppst
PSP/SAVEDATA/**
*.dmp
*.raw
*.png
*.jpg
```

unless an image is an existing intentional documentation/test fixture already present on `main`. The new payload manifest may describe copyrighted files already committed historically, but this branch must not add new game payload binaries.

- [ ] **Step 7: Commit final docs/tests**

```bash
git add tests/integration/test_task9e_live_capture.py docs/architecture/ppsspp-capture-harness.md docs/architecture/rebuild-pipeline.md README.md analysis/save/task-status.json
git commit -m "docs: document reconstructed Task 9E runtime workflow"
```

Do not stage `analysis/save/task-status.json` if no live semantic evidence changed its contents.

- [ ] **Step 8: Open PR and run exact-head verification**

PR title:

```text
Task 9E: recover runtime from extracted Fight Night payload
```

PR body must explicitly state:

- no retail ISO is required for repository-runtime mode;
- no new copyrighted runtime binaries are added by this branch;
- retail ISO identity and reconstructed runtime identity remain distinct;
- per-control `--memstick` routing bug is fixed;
- bootstrap/cold-boot support does not itself constitute semantic evidence;
- Task 9E semantic status remains blocked until a real successful/corrupted capture completes.

- [ ] **Step 9: Merge only after verification**

Require exact PR-head CI success for pytest, Ruff, strict mypy, and PSP-analysis integration; audit review threads/comments; merge the exact verified head; then require post-merge `main` CI success before declaring runtime recovery implemented.

---

## Implementation Order and Stop Conditions

Execute Tasks 1–7 in order. The following are hard stop conditions, not reasons to improvise:

1. **Payload coverage failure:** report exact missing allowlisted source paths and stop before ISO mastering.
2. **Determinism failure:** if two identical synthetic builds differ, fix timestamp/layout determinism before continuing.
3. **BOOT mismatch:** stop immediately; do not run PPSSPP.
4. **Bundle mismatch:** stop immediately; do not substitute a different PPSSPP build.
5. **Memstick-routing ambiguity:** do not interpret successful/corrupted divergence until each control is proven to use its own `--memstick` root.
6. **Bootstrap failure:** preserve diagnostics locally and report the exact stage reached; do not fabricate save/state artifacts.
7. **No live evidence:** keep `analysis/save/task-status.json` at the 9E evidence gate even if all runtime-recovery code and CI are green.
