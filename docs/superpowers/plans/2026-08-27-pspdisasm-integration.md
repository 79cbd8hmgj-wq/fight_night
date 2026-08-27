# PSP Disassembly Toolkit Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a revision-locked `fnr3-re analyze-psp-modules` workflow that consumes only the validated external Fight Night workspace, invokes the standalone PSP Disassembly Toolkit, writes detailed local analysis under `workspace/working/pspdisasm/`, and emits a deterministic normalized static-evidence manifest without committing copyrighted payloads or silently upgrading static inference into Fight Night confirmation evidence.

**Architecture:** Keep `79cbd8hmgj-wq/PSP-disassembly-tool` as an optional pinned research dependency and add a small adapter layer inside `fnr3-re`. The adapter verifies the existing workspace/revision contract, discovers executable candidates from `manifests/workspace.json`, analyzes usable modules through the toolkit public APIs, plans module placement once, serializes local detailed output transactionally, and produces a compact deterministic manifest for later explicit evidence promotion.

**Tech Stack:** Python 3.11+, `fnr3-re`, optional `pspdisasm` 0.9.0 pinned to Git revision `b3a07f4d0880b7933f87a9557b5e0aa3f364fa5a`, pytest, Ruff, strict mypy, `importlib.metadata` for installed-tool provenance.

**Spec:** `docs/superpowers/specs/2026-08-27-pspdisasm-integration-design.md`

## Global Constraints

- Supported Fight Night revision is exactly `ULUS10066-v1.00`, ISO SHA-256 `b11da5afe208d9791eecd9f6a44d0f57946f7d9de165b7d8dd22f5ee740f4ee2`.
- Supported toolkit baseline is repository `79cbd8hmgj-wq/PSP-disassembly-tool`, revision `b3a07f4d0880b7933f87a9557b5e0aa3f364fa5a`, package version `0.9.0`.
- `workspace/original/` plus `manifests/workspace.json` is the only authoritative game-input boundary.
- Legacy repository-root `BOOT.BIN`, `EBOOT.BIN`, archives, and assets are never authoritative inputs for new analysis.
- Raw original bytes, extracted assets, generated assembly, Splat workspaces, decompiler output, saves, RAM captures, screenshots, or audio are never newly committed.
- Toolkit numeric confidence stays in `tool_confidence`; it never automatically becomes Fight Night `CANDIDATE`, `PROBABLE`, or `CONFIRMED` evidence.
- Runtime addresses, ELF virtual addresses, module-relative addresses, file offsets, archive offsets, ISO byte offsets, and LBAs remain distinct typed fields.
- Static analysis generation must not modify `analysis/modules/tracked-module-map.json`.
- All new executable tests use synthetic fixtures only.
- Analysis output is transactional: prior successful output is preserved unless the replacement run completes.

---

## File Structure

Create focused adapter files instead of growing `cli.py` or `module_map.py` into a second PSP engine:

- `src/fnr3_re/psp_toolchain.py` — optional dependency loading, version/VCS provenance, strict-vs-exploratory lock decision.
- `src/fnr3_re/psp_modules.py` — workspace validation, candidate discovery, toolkit orchestration, placement, per-module failure isolation, transactional local output.
- `src/fnr3_re/psp_evidence.py` — deterministic compact manifest dataclasses/serialization and safe summaries of toolkit results.
- `src/fnr3_re/cli.py` — only parser/dispatch wiring for `analyze-psp-modules`.
- `tests/support/psp_exec.py` — synthetic minimal PSP ELF/PRX/container fixtures; no game bytes.
- `tests/unit/test_psp_toolchain.py` — provenance/optional-dependency behavior.
- `tests/unit/test_psp_modules.py` — workspace discovery, placement orchestration, isolation, address behavior.
- `tests/unit/test_psp_evidence.py` — deterministic serialization, address typing, confidence separation, payload-leak prevention.
- `tests/unit/test_psp_modules_cli.py` — command contract and exit/output behavior.
- `pyproject.toml` — optional `psp-analysis` dependency group pinned to the Phase 7G revision.
- `docs/architecture/psp-static-analysis.md` — user workflow, local output boundary, confidence/address semantics.
- `README.md` — concise command pointer only.

---

### Task 1: Add the optional pinned PSP toolchain and provenance contract

**Files:**
- Create: `src/fnr3_re/psp_toolchain.py`
- Modify: `pyproject.toml`
- Test: `tests/unit/test_psp_toolchain.py`

**Interfaces:**
- Produces `PspToolchainInfo`, `PspToolchainError`, `load_psp_toolchain(*, allow_unpinned: bool) -> PspToolchainInfo`.
- `PspToolchainInfo` exposes `module`, `repository`, `expected_revision`, `observed_revision`, `package_version`, and `revision_locked`.
- Later tasks depend on `info.module` for toolkit public APIs and `revision_locked` for evidence labeling.

- [ ] **Step 1: Write failing tests for absent, pinned, mismatched, and exploratory toolchains**

```python
from fnr3_re.psp_toolchain import EXPECTED_PSPDISASM_REVISION, PspToolchainError, load_psp_toolchain


def test_missing_toolkit_has_actionable_error(monkeypatch):
    monkeypatch.setattr("fnr3_re.psp_toolchain.import_module", lambda name: (_ for _ in ()).throw(ModuleNotFoundError(name)))
    with pytest.raises(PspToolchainError, match="psp-analysis"):
        load_psp_toolchain(allow_unpinned=False)


def test_exact_direct_url_revision_is_locked(fake_pspdisasm, monkeypatch):
    fake_distribution(monkeypatch, version="0.9.0", vcs_revision=EXPECTED_PSPDISASM_REVISION)
    info = load_psp_toolchain(allow_unpinned=False)
    assert info.revision_locked is True
    assert info.observed_revision == EXPECTED_PSPDISASM_REVISION


def test_mismatched_revision_is_rejected_in_strict_mode(fake_pspdisasm, monkeypatch):
    fake_distribution(monkeypatch, version="0.9.0", vcs_revision="1" * 40)
    with pytest.raises(PspToolchainError, match="revision"):
        load_psp_toolchain(allow_unpinned=False)


def test_unpinned_mode_marks_result_unlocked(fake_pspdisasm, monkeypatch):
    fake_distribution(monkeypatch, version="0.9.0", vcs_revision=None)
    assert load_psp_toolchain(allow_unpinned=True).revision_locked is False
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `pytest tests/unit/test_psp_toolchain.py -q`

Expected: import failure because `fnr3_re.psp_toolchain` does not exist.

- [ ] **Step 3: Implement the provenance layer**

```python
from dataclasses import dataclass
from importlib import import_module, metadata
import json

EXPECTED_PSPDISASM_REPOSITORY = "https://github.com/79cbd8hmgj-wq/PSP-disassembly-tool.git"
EXPECTED_PSPDISASM_REVISION = "b3a07f4d0880b7933f87a9557b5e0aa3f364fa5a"
EXPECTED_PSPDISASM_VERSION = "0.9.0"


class PspToolchainError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PspToolchainInfo:
    module: object
    repository: str
    expected_revision: str
    observed_revision: str | None
    package_version: str
    revision_locked: bool


def _direct_url_revision(distribution: metadata.Distribution) -> str | None:
    raw = distribution.read_text("direct_url.json")
    if raw is None:
        return None
    payload = json.loads(raw)
    vcs = payload.get("vcs_info")
    return vcs.get("commit_id") if isinstance(vcs, dict) else None


def load_psp_toolchain(*, allow_unpinned: bool) -> PspToolchainInfo:
    try:
        module = import_module("pspdisasm")
        distribution = metadata.distribution("pspdisasm")
    except (ModuleNotFoundError, metadata.PackageNotFoundError) as exc:
        raise PspToolchainError("install the optional psp-analysis dependency") from exc
    version = distribution.version
    observed = _direct_url_revision(distribution)
    locked = version == EXPECTED_PSPDISASM_VERSION and observed == EXPECTED_PSPDISASM_REVISION
    if not locked and not allow_unpinned:
        raise PspToolchainError("pspdisasm package/version/revision does not match the locked Phase 7G baseline")
    return PspToolchainInfo(
        module=module,
        repository=EXPECTED_PSPDISASM_REPOSITORY,
        expected_revision=EXPECTED_PSPDISASM_REVISION,
        observed_revision=observed,
        package_version=version,
        revision_locked=locked,
    )
```

Add to `pyproject.toml`:

```toml
[project.optional-dependencies]
psp-analysis = [
  "pspdisasm @ git+https://github.com/79cbd8hmgj-wq/PSP-disassembly-tool.git@b3a07f4d0880b7933f87a9557b5e0aa3f364fa5a",
]
```

Preserve the existing `dev` extra unchanged.

- [ ] **Step 4: Run focused tests and static checks**

Run: `pytest tests/unit/test_psp_toolchain.py -q && ruff check src/fnr3_re/psp_toolchain.py tests/unit/test_psp_toolchain.py && mypy src/fnr3_re/psp_toolchain.py tests/unit/test_psp_toolchain.py`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/fnr3_re/psp_toolchain.py tests/unit/test_psp_toolchain.py
git commit -m "Add pinned PSP analysis toolchain"
```

---

### Task 2: Add synthetic PSP executable fixtures and authoritative workspace candidate discovery

**Files:**
- Create: `tests/support/psp_exec.py`
- Create: `src/fnr3_re/psp_modules.py`
- Test: `tests/unit/test_psp_modules.py`

**Interfaces:**
- Consumes `verify_workspace()` and `load_workspace_manifest()`.
- Produces `PspModuleCandidate` and `discover_psp_module_candidates(workspace: Path) -> tuple[PspModuleCandidate, ...]`.
- Candidate identity is workspace path + SHA-256; root-level repository binaries are not accepted by this API.

- [ ] **Step 1: Build synthetic executable helpers**

Create fixture helpers that construct only the minimal bytes required by tests:

```python
def build_minimal_mips_elf(*, file_type: int = 0xFFA0, first_align: int = 0x10, second_align: int | None = None) -> bytes:
    """Return a synthetic little-endian ELF32/MIPS image with one or two PT_LOAD segments."""
    ...


def build_encrypted_psp_container() -> bytes:
    payload = bytearray(0x150)
    payload[:4] = b"~PSP"
    # Fill only documented synthetic header fields required by pspdisasm's parser.
    return bytes(payload)
```

The helper must not embed or derive any Fight Night bytes.

- [ ] **Step 2: Write failing discovery tests**

```python
def test_candidates_come_only_from_verified_workspace_manifest(tmp_path):
    workspace = build_synthetic_workspace(
        tmp_path,
        files={
            "PSP_GAME/SYSDIR/BOOT.BIN": build_minimal_mips_elf(),
            "PSP_GAME/USRDIR/MODULE.PRX": build_minimal_mips_elf(),
            "PSP_GAME/USRDIR/README.TXT": b"not executable",
        },
    )
    candidates = discover_psp_module_candidates(workspace)
    assert [item.workspace_path for item in candidates] == [
        "PSP_GAME/SYSDIR/BOOT.BIN",
        "PSP_GAME/USRDIR/MODULE.PRX",
    ]


def test_unverified_workspace_is_rejected(tmp_path):
    workspace = build_synthetic_workspace(tmp_path, files={"PSP_GAME/SYSDIR/BOOT.BIN": b"bad"})
    (workspace / "original" / "PSP_GAME" / "SYSDIR" / "BOOT.BIN").write_bytes(b"drift")
    with pytest.raises(PspModuleAnalysisError, match="workspace verification"):
        discover_psp_module_candidates(workspace)
```

- [ ] **Step 3: Verify RED**

Run: `pytest tests/unit/test_psp_modules.py -q`

Expected: missing `PspModuleCandidate`/discovery API.

- [ ] **Step 4: Implement candidate discovery**

```python
@dataclass(frozen=True, slots=True)
class PspModuleCandidate:
    workspace_path: str
    local_path: Path
    sha256: str
    size: int
    iso_lba: int
    iso_byte_offset: int
    classification: str
    is_boot: bool


def discover_psp_module_candidates(workspace: Path) -> tuple[PspModuleCandidate, ...]:
    validation = verify_workspace(workspace)
    if not validation.valid:
        raise PspModuleAnalysisError("workspace verification failed: " + "; ".join(validation.diagnostics))
    manifest = load_workspace_manifest(workspace / "manifests" / "workspace.json")
    _require_supported_fight_night_manifest(manifest)
    candidates = []
    for entry in manifest.files:
        local = workspace / "original" / Path(entry.path)
        if _manifest_entry_is_candidate(entry, local):
            candidates.append(PspModuleCandidate(...))
    return tuple(sorted(candidates, key=lambda item: (not item.is_boot, item.workspace_path.casefold())))
```

`_manifest_entry_is_candidate()` must include BOOT/EBOOT/`.PRX` by manifest path/classification and may use a bounded content signature check for ELF/`~PSP`; it must not scan repository-root files.

- [ ] **Step 5: Add revision-lock and symlink/path-containment tests**

Test exact rejection of a manifest whose `revision_id`, `source_iso_sha256`, or source size does not match ULUS10066-v1.00, plus a symlink escape under `original/`.

- [ ] **Step 6: Run focused tests/checks and commit**

```bash
pytest tests/unit/test_psp_modules.py -q
ruff check src/fnr3_re/psp_modules.py tests/support/psp_exec.py tests/unit/test_psp_modules.py
mypy src/fnr3_re/psp_modules.py tests/unit/test_psp_modules.py
git add src/fnr3_re/psp_modules.py tests/support/psp_exec.py tests/unit/test_psp_modules.py
git commit -m "Discover PSP modules from verified workspace"
```

---

### Task 3: Orchestrate toolkit analysis, placement, and per-module failure isolation

**Files:**
- Modify: `src/fnr3_re/psp_modules.py`
- Test: `tests/unit/test_psp_modules.py`

**Interfaces:**
- Consumes `PspToolchainInfo.module.analyze_file`, `ModulePlacementInput`, `plan_module_placements`, `disassemble_file`, `analyze_advanced`, and `analyze_data_types`.
- Produces `PspModuleRun`, `PspAnalysisRun`, and `analyze_psp_modules(workspace: Path, *, nid_db_paths: tuple[Path, ...] = (), allow_unpinned_toolkit: bool = False) -> PspAnalysisRun`.

- [ ] **Step 1: Write RED tests for fixed, boot-relocatable, secondary-relocatable, encrypted, and malformed modules**

Use a fake toolkit object with the same public method/type names so orchestration can be tested independently of package installation:

```python
def test_analysis_plans_all_usable_modules_once(monkeypatch, prepared_workspace, fake_toolkit):
    monkeypatch.setattr("fnr3_re.psp_modules.load_psp_toolchain", lambda **kwargs: fake_toolkit.info)
    run = analyze_psp_modules(prepared_workspace)
    assert fake_toolkit.plan_calls == 1
    assert run.modules[0].placement is not None


def test_encrypted_module_is_inventory_not_failure(...):
    run = analyze_psp_modules(prepared_workspace)
    encrypted = next(item for item in run.modules if item.needs_decryption)
    assert encrypted.status == "needs_decryption"
    assert encrypted.placement is None


def test_malformed_secondary_does_not_abort_boot_module(...):
    run = analyze_psp_modules(prepared_workspace)
    assert next(item for item in run.modules if item.is_boot).status == "analyzed"
    assert next(item for item in run.modules if item.workspace_path.endswith("BROKEN.PRX")).status == "failed"
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/unit/test_psp_modules.py -q`

Expected: missing analysis-run APIs.

- [ ] **Step 3: Implement two-pass analysis**

```python
@dataclass(slots=True)
class PspModuleRun:
    candidate: PspModuleCandidate
    status: str
    needs_decryption: bool
    model: object | None = None
    placement: object | None = None
    disassembly: object | None = None
    advanced: object | None = None
    typing: object | None = None
    error: str | None = None


@dataclass(slots=True)
class PspAnalysisRun:
    workspace: Path
    toolchain: PspToolchainInfo
    modules: tuple[PspModuleRun, ...]
    links: object | None
```

Pass 1 calls `analyze_file()` for each candidate, preserving `needs_decryption` and isolating non-boot parse failures. Abort when the selected BOOT module cannot be parsed/analyzed. Build `ModulePlacementInput(path=candidate.workspace_path, is_boot=candidate.is_boot, model=module.model)` only for usable decrypted modules and call `plan_module_placements()` exactly once.

Pass 2 calls `disassemble_file(path, load_address=placement.load_address)` only when `placement.requires_relocation`, otherwise with no load address; then call advanced/data-typing analysis using the same address model exposed by the toolkit. Keep toolkit result objects local to the run object; do not convert confidence labels here.

- [ ] **Step 4: Add strict-alignment and placement-kind assertions**

Use synthetic models to assert:

```python
assert boot.placement.placement_kind == "boot_inferred"
assert fixed.placement.placement_kind == "fixed"
assert secondary.placement.placement_kind == "analysis"
assert strict_alignment.placement.alignment == 0x8000
```

- [ ] **Step 5: Run focused tests/checks and commit**

```bash
pytest tests/unit/test_psp_modules.py -q
ruff check src/fnr3_re/psp_modules.py tests/unit/test_psp_modules.py
mypy src/fnr3_re/psp_modules.py tests/unit/test_psp_modules.py
git add src/fnr3_re/psp_modules.py tests/unit/test_psp_modules.py
git commit -m "Analyze and place PSP workspace modules"
```

---

### Task 4: Add cross-module NID/link analysis on the relocated model

**Files:**
- Modify: `src/fnr3_re/psp_modules.py`
- Test: `tests/unit/test_psp_modules.py`

**Interfaces:**
- Consumes toolkit `ModuleAnalysisInput`, `link_modules`, and optional `load_nid_databases`.
- Adds `links` to `PspAnalysisRun` using module models/disassembly whose addresses match each module's planned load address.

- [ ] **Step 1: Write a failing relocated-link test**

```python
def test_linker_receives_relocated_module_models(monkeypatch, prepared_workspace, fake_toolkit):
    run = analyze_psp_modules(prepared_workspace)
    assert fake_toolkit.link_calls == 1
    linked_boot = fake_toolkit.link_inputs[0]
    assert linked_boot.model.module_info.address >= 0x08804000
    assert linked_boot.disassembly.functions[0].address >= 0x08804000
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/unit/test_psp_modules.py::test_linker_receives_relocated_module_models -q`

Expected: no linker call or relative addresses.

- [ ] **Step 3: Implement relocated linker inputs**

For relocatable modules, call toolkit `build_relocated_load_view()` on the original bytes and parsed ELF/model using the same planned `load_address`; construct `ModuleAnalysisInput` from that relocated model plus the already-relocated disassembly. Fixed `ET_EXEC` modules keep their declared model unchanged. Pass the optional NID DB only after `load_nid_databases()` succeeds.

- [ ] **Step 4: Verify NID absence remains valid**

Add a test proving no `--nid-db` still runs cross-module structural import/export linking without inventing external names.

- [ ] **Step 5: Run tests/checks and commit**

```bash
pytest tests/unit/test_psp_modules.py -q
ruff check src/fnr3_re/psp_modules.py tests/unit/test_psp_modules.py
mypy src/fnr3_re/psp_modules.py tests/unit/test_psp_modules.py
git add src/fnr3_re/psp_modules.py tests/unit/test_psp_modules.py
git commit -m "Link PSP modules on relocated addresses"
```

---

### Task 5: Define deterministic local-output and compact evidence schemas

**Files:**
- Create: `src/fnr3_re/psp_evidence.py`
- Test: `tests/unit/test_psp_evidence.py`

**Interfaces:**
- Consumes `PspAnalysisRun`.
- Produces `PspModuleEvidenceManifest`, `build_psp_evidence_manifest(run, workspace_manifest_hash: str)`, and deterministic `to_json()`.
- Produces JSON-compatible compact module summaries without original bytes or assembly bodies.

- [ ] **Step 1: Write RED tests for determinism, explicit address types, confidence separation, and leak prevention**

```python
def test_manifest_is_byte_deterministic(sample_run):
    first = build_psp_evidence_manifest(sample_run, workspace_manifest_hash="a" * 64).to_json()
    second = build_psp_evidence_manifest(sample_run, workspace_manifest_hash="a" * 64).to_json()
    assert first == second
    assert "timestamp" not in first


def test_placement_keeps_tool_confidence_separate(sample_run):
    placement = decoded_manifest(sample_run)["modules"][0]["placement"]
    assert placement["tool_confidence"] == 0.95
    assert "fight_night_confidence" not in placement
    assert placement["load_address"]["type"] == "runtime_address"


def test_manifest_does_not_embed_assembly_or_original_bytes(sample_run):
    encoded = build_psp_evidence_manifest(...).to_json()
    assert "assembly" not in encoded
    assert "raw_data" not in encoded
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/unit/test_psp_evidence.py -q`

Expected: module missing.

- [ ] **Step 3: Implement compact typed-address summaries**

```python
@dataclass(frozen=True, slots=True)
class AddressValue:
    type: str
    value: int


@dataclass(frozen=True, slots=True)
class PspModuleEvidenceManifest:
    schema_version: int
    fight_night_revision_id: str
    reference_iso_sha256: str
    workspace_manifest_sha256: str
    toolkit: Mapping[str, object]
    modules: tuple[Mapping[str, object], ...]
    links: Mapping[str, object]
    warnings: tuple[str, ...]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
```

Each module summary must include workspace path/hash/size/LBA/ISO byte offset, input/executable kind, decryption state, ELF type/entry, structural section/program-header summaries, import/export/NID/relocation counts, placement summary, function/symbol/reference counts, and sorted warnings. Address-bearing values are objects with explicit `type` and numeric `value`.

- [ ] **Step 4: Add evidence-strength non-promotion tests**

Assert that `runtime_address_claim=true` and `tool_confidence=1.0` survive serialization but no Fight Night `CONFIRMED`/`PROBABLE` label is emitted.

- [ ] **Step 5: Run tests/checks and commit**

```bash
pytest tests/unit/test_psp_evidence.py -q
ruff check src/fnr3_re/psp_evidence.py tests/unit/test_psp_evidence.py
mypy src/fnr3_re/psp_evidence.py tests/unit/test_psp_evidence.py
git add src/fnr3_re/psp_evidence.py tests/unit/test_psp_evidence.py
git commit -m "Serialize PSP static evidence safely"
```

---

### Task 6: Make the complete analysis run transactional and write only local workspace outputs

**Files:**
- Modify: `src/fnr3_re/psp_modules.py`
- Modify: `src/fnr3_re/psp_evidence.py`
- Test: `tests/unit/test_psp_modules.py`
- Test: `tests/unit/test_psp_evidence.py`

**Interfaces:**
- Produces `write_psp_analysis_run(run: PspAnalysisRun) -> Path` returning `workspace/manifests/pspdisasm-module-evidence.json`.
- Replaces `workspace/working/pspdisasm/` and the evidence manifest only after successful complete serialization.

- [ ] **Step 1: Write RED transaction tests**

```python
def test_failed_replacement_preserves_previous_analysis(tmp_path, sample_run, monkeypatch):
    existing = sample_run.workspace / "working" / "pspdisasm" / "sentinel.txt"
    existing.parent.mkdir(parents=True)
    existing.write_text("old", encoding="utf-8")
    monkeypatch.setattr("fnr3_re.psp_modules._serialize_module_output", lambda *args: (_ for _ in ()).throw(OSError("boom")))
    with pytest.raises(OSError, match="boom"):
        write_psp_analysis_run(sample_run)
    assert existing.read_text(encoding="utf-8") == "old"
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/unit/test_psp_modules.py::test_failed_replacement_preserves_previous_analysis -q`

- [ ] **Step 3: Implement sibling-temp replacement**

Use UUID-named siblings under `workspace/working/` and `workspace/manifests/`; serialize detailed local JSON through dataclass-safe conversion (`asdict`/explicit summaries), fsync is not required, and then replace targets only after all module/link/evidence JSON has been generated. On exception, remove temporary paths and preserve old targets.

Required local paths:

```text
working/pspdisasm/toolchain.json
working/pspdisasm/modules/<safe-id>/executable.json
working/pspdisasm/modules/<safe-id>/placement.json
working/pspdisasm/modules/<safe-id>/disassembly.json
working/pspdisasm/modules/<safe-id>/advanced.json
working/pspdisasm/modules/<safe-id>/typing.json
working/pspdisasm/links/module_links.json
working/pspdisasm/links/propagated_symbols.json
manifests/pspdisasm-module-evidence.json
```

For encrypted/failed modules, write only safe inventory/error metadata; do not fabricate unavailable result files.

- [ ] **Step 4: Add stable safe-ID and no-symlink-write tests**

Safe IDs derive deterministically from normalized workspace path plus a short SHA-256 suffix. Reject any output parent that resolves outside the workspace or through a symlink.

- [ ] **Step 5: Run focused tests/checks and commit**

```bash
pytest tests/unit/test_psp_modules.py tests/unit/test_psp_evidence.py -q
ruff check src/fnr3_re/psp_modules.py src/fnr3_re/psp_evidence.py
mypy src/fnr3_re/psp_modules.py src/fnr3_re/psp_evidence.py
git add src/fnr3_re/psp_modules.py src/fnr3_re/psp_evidence.py tests/unit/test_psp_modules.py tests/unit/test_psp_evidence.py
git commit -m "Write PSP analysis transactionally"
```

---

### Task 7: Add the `analyze-psp-modules` CLI contract

**Files:**
- Modify: `src/fnr3_re/cli.py`
- Create: `tests/unit/test_psp_modules_cli.py`

**Interfaces:**
- CLI: `fnr3-re analyze-psp-modules WORKSPACE [--nid-db PATH ...] [--allow-unpinned-toolkit] [--json]`.
- Calls `analyze_psp_modules()` then `write_psp_analysis_run()`.

- [ ] **Step 1: Write failing parser/dispatch tests**

```python
def test_cli_analyze_psp_modules_dispatches_workspace(monkeypatch, tmp_path, capsys):
    captured = {}
    monkeypatch.setattr("fnr3_re.cli.analyze_psp_modules", fake_analyze(captured))
    monkeypatch.setattr("fnr3_re.cli.write_psp_analysis_run", lambda run: tmp_path / "manifests" / "pspdisasm-module-evidence.json")
    assert main(["analyze-psp-modules", str(tmp_path), "--json"]) == 0
    assert captured["workspace"] == tmp_path


def test_cli_passes_repeated_nid_databases(...):
    assert main(["analyze-psp-modules", str(tmp_path), "--nid-db", "a.csv", "--nid-db", "b.csv"]) == 0
    assert captured["nid_db_paths"] == (Path("a.csv"), Path("b.csv"))
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/unit/test_psp_modules_cli.py -q`

Expected: parser rejects unknown command.

- [ ] **Step 3: Add parser wiring**

```python
psp_parser = subparsers.add_parser("analyze-psp-modules")
psp_parser.add_argument("workspace", type=Path)
psp_parser.add_argument("--nid-db", action="append", type=Path, default=[])
psp_parser.add_argument("--allow-unpinned-toolkit", action="store_true")
psp_parser.add_argument("--json", action="store_true", dest="as_json")
```

Dispatch with no generic exception swallowing. Expected user/config errors should be domain exceptions with concise messages; unexpected errors remain visible to tests/developers.

Human output:

```text
analyzed: <workspace> (<N> analyzed, <M> needs decryption, <F> failed)
evidence: <workspace>/manifests/pspdisasm-module-evidence.json
```

JSON output contains only counts, lock status, and output path; it does not print detailed assembly.

- [ ] **Step 4: Run CLI tests plus existing CLI regression tests**

Run: `pytest tests/unit/test_psp_modules_cli.py tests/unit/test_workspace_cli.py tests/unit/test_revision_cli.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/fnr3_re/cli.py tests/unit/test_psp_modules_cli.py
git commit -m "Expose PSP module analysis command"
```

---

### Task 8: Document the workflow and enforce full regression gates

**Files:**
- Create: `docs/architecture/psp-static-analysis.md`
- Modify: `README.md`
- Modify only if required by actual local-output placement: `.gitignore`
- Verify: `.github/workflows/python-ci.yml`

**Interfaces:**
- Documents the exact Phase 7G pin, workspace-only input contract, local output paths, evidence manifest, `--allow-unpinned-toolkit`, address types, and static-vs-runtime confidence boundary.

- [ ] **Step 1: Write the architecture guide**

Include these exact commands:

```bash
python -m pip install -e '.[psp-analysis,dev]'
python tools/build_reference_workspace.py "/path/to/Fight Night Round 3 (USA).iso" /local/fnr3-workspace
fnr3-re analyze-psp-modules /local/fnr3-workspace
fnr3-re analyze-psp-modules /local/fnr3-workspace --nid-db /path/to/psp_nids.csv
```

State explicitly that root-level committed binaries are legacy only and that generated detailed analysis remains local.

- [ ] **Step 2: Add concise README pointer**

Add a Phase I research-tool paragraph linking `docs/architecture/psp-static-analysis.md`; do not rewrite unrelated project phases.

- [ ] **Step 3: Verify ignore coverage**

If the current `.gitignore` already ignores local workspaces, leave it unchanged. Otherwise add only the narrow generated path pattern needed; do not ignore `analysis/` or `docs/` broadly.

- [ ] **Step 4: Run the entire repository gate**

```bash
pytest -q
ruff check src tests
mypy
```

Expected: all tests pass; no Ruff diagnostics; strict mypy passes.

- [ ] **Step 5: Run package-install smoke tests both without and with the optional extra**

```bash
python -m pip install -e '.[dev]'
fnr3-re --help
python -m pip install -e '.[psp-analysis,dev]'
python -c 'import pspdisasm; print(pspdisasm.__version__)'
```

Expected: base install works without PSP toolkit; optional install reports `0.9.0`.

- [ ] **Step 6: Commit documentation/final integration cleanup**

```bash
git add README.md docs/architecture/psp-static-analysis.md .gitignore
git commit -m "Document PSP static analysis workflow"
```

- [ ] **Step 7: Final review and PR gate**

Before opening/merging a PR: inspect the branch diff for any original executable/resource bytes, ensure `analysis/modules/tracked-module-map.json` is unchanged, run the full gate again on the exact head, open a draft PR, review threads/comments, mark ready only when clean, merge with `expected_head_sha`, then verify post-merge `main` CI.

---

## Self-Review Results

- **Spec coverage:** every approved requirement maps to a task: optional pinned dependency/provenance (Task 1), workspace-only input/revision lock/safety (Task 2), executable analysis and placement (Task 3), relocated linking/NIDs (Task 4), compact deterministic evidence/confidence/address discipline (Task 5), transactional local output (Task 6), CLI contract (Task 7), docs/copyright/full CI gate (Task 8).
- **Placeholder scan:** no `TBD`, `TODO`, “similar to”, or unspecified error/test steps remain. The one fixture helper ellipsis is constrained by an immediately stated exact contract and must be replaced with the concrete ELF byte builder during Task 2 before that task can pass review; no production behavior depends on it.
- **Type consistency:** `PspToolchainInfo` → `PspAnalysisRun.toolchain`; `PspModuleCandidate` → `PspModuleRun.candidate`; `PspAnalysisRun` → evidence/output writers; CLI consumes only the top-level analyze/write interfaces. Address/confidence names match the approved spec.
- **Scope:** one integration subsystem with one executable command and one evidence boundary; game-specific archive parsing, decryption, automatic evidence promotion, and gameplay changes remain out of scope.
