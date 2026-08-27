# PSP Disassembly Toolkit Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a revision-locked `fnr3-re analyze-psp-modules` workflow that consumes only the validated external Fight Night workspace, invokes the standalone PSP Disassembly Toolkit, writes detailed local analysis under `workspace/working/pspdisasm/`, and emits deterministic normalized static evidence without committing copyrighted payloads or promoting static inference into Fight Night confirmation evidence.

**Architecture:** `fight_night` remains game-specific and evidence-first. `PSP-disassembly-tool` remains a separate optional dependency pinned to its Phase 7G merge commit. A small adapter verifies the existing workspace/revision contract, discovers executable candidates from `manifests/workspace.json`, analyzes usable modules through toolkit public APIs, plans placement once, links modules on the same relocated address model, writes local output transactionally, and emits a compact manifest for explicit later evidence promotion.

**Tech Stack:** Python 3.11+, `fnr3-re`, optional `pspdisasm` 0.9.0 at Git revision `b3a07f4d0880b7933f87a9557b5e0aa3f364fa5a`, pytest, Ruff, strict mypy, `importlib.metadata`.

**Spec:** `docs/superpowers/specs/2026-08-27-pspdisasm-integration-design.md`

## Global Constraints

- Supported Fight Night revision is exactly `ULUS10066-v1.00` with ISO SHA-256 `b11da5afe208d9791eecd9f6a44d0f57946f7d9de165b7d8dd22f5ee740f4ee2` and ISO size `1137737728`.
- Supported toolkit baseline is `79cbd8hmgj-wq/PSP-disassembly-tool`, revision `b3a07f4d0880b7933f87a9557b5e0aa3f364fa5a`, package version `0.9.0`.
- `workspace/original/` plus `workspace/manifests/workspace.json` is the only authoritative game input.
- Legacy repository-root `BOOT.BIN`, `EBOOT.BIN`, archives, and assets are never authoritative inputs for this command.
- New tests use only synthetic executable/container bytes.
- Detailed generated analysis remains local under `workspace/working/pspdisasm/`.
- `analysis/modules/tracked-module-map.json` is not modified by analysis generation.
- Toolkit numeric confidence is serialized as `tool_confidence`; it is never converted automatically into Fight Night `CANDIDATE`, `PROBABLE`, or `CONFIRMED`.
- Every address-bearing normalized record states its address type explicitly.
- Prior successful output is preserved unless the replacement run completes successfully.

## File Map

- Create `src/fnr3_re/psp_toolchain.py`: optional dependency loading and provenance lock.
- Create `src/fnr3_re/psp_modules.py`: verified-workspace discovery, orchestration, placement, linking, failure isolation, transactional local output.
- Create `src/fnr3_re/psp_evidence.py`: compact deterministic evidence serialization.
- Modify `src/fnr3_re/cli.py`: parser and dispatch only.
- Create `tests/support/psp_exec.py`: synthetic ELF/PRX/`~PSP` builders.
- Create `tests/unit/test_psp_toolchain.py`.
- Create `tests/unit/test_psp_modules.py`.
- Create `tests/unit/test_psp_evidence.py`.
- Create `tests/unit/test_psp_modules_cli.py`.
- Modify `pyproject.toml`.
- Create `docs/architecture/psp-static-analysis.md`.
- Modify `README.md` minimally.

---

### Task 1: Optional pinned toolchain and provenance

**Files:**
- Create: `src/fnr3_re/psp_toolchain.py`
- Modify: `pyproject.toml`
- Test: `tests/unit/test_psp_toolchain.py`

**Interfaces:**
- `PspToolchainError(RuntimeError)`
- `PspToolchainInfo(module: object, repository: str, expected_revision: str, observed_revision: str | None, package_version: str, revision_locked: bool)`
- `load_psp_toolchain(*, allow_unpinned: bool) -> PspToolchainInfo`

- [ ] **Step 1: Write failing provenance tests**

```python
import pytest
from fnr3_re.psp_toolchain import EXPECTED_PSPDISASM_REVISION, PspToolchainError, load_psp_toolchain


def test_missing_toolkit_is_actionable(monkeypatch):
    def missing(name: str) -> object:
        raise ModuleNotFoundError(name)
    monkeypatch.setattr("fnr3_re.psp_toolchain.import_module", missing)
    with pytest.raises(PspToolchainError, match="psp-analysis"):
        load_psp_toolchain(allow_unpinned=False)


def test_exact_revision_is_locked(fake_pspdisasm, monkeypatch):
    install_fake_distribution(monkeypatch, version="0.9.0", commit_id=EXPECTED_PSPDISASM_REVISION)
    info = load_psp_toolchain(allow_unpinned=False)
    assert info.revision_locked is True
    assert info.observed_revision == EXPECTED_PSPDISASM_REVISION


def test_unpinned_install_requires_explicit_override(fake_pspdisasm, monkeypatch):
    install_fake_distribution(monkeypatch, version="0.9.0", commit_id=None)
    with pytest.raises(PspToolchainError, match="locked Phase 7G baseline"):
        load_psp_toolchain(allow_unpinned=False)
    assert load_psp_toolchain(allow_unpinned=True).revision_locked is False
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/unit/test_psp_toolchain.py -q`

Expected: import error because `fnr3_re.psp_toolchain` does not exist.

- [ ] **Step 3: Implement provenance loading**

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
    vcs_info = payload.get("vcs_info")
    if not isinstance(vcs_info, dict):
        return None
    commit_id = vcs_info.get("commit_id")
    return commit_id if isinstance(commit_id, str) else None


def load_psp_toolchain(*, allow_unpinned: bool) -> PspToolchainInfo:
    try:
        module = import_module("pspdisasm")
        distribution = metadata.distribution("pspdisasm")
    except (ModuleNotFoundError, metadata.PackageNotFoundError) as exc:
        raise PspToolchainError("install fnr3-re with the psp-analysis extra") from exc
    observed = _direct_url_revision(distribution)
    locked = distribution.version == EXPECTED_PSPDISASM_VERSION and observed == EXPECTED_PSPDISASM_REVISION
    if not locked and not allow_unpinned:
        raise PspToolchainError("pspdisasm does not match the locked Phase 7G baseline")
    return PspToolchainInfo(module, EXPECTED_PSPDISASM_REPOSITORY, EXPECTED_PSPDISASM_REVISION, observed, distribution.version, locked)
```

Add this optional dependency without changing the existing `dev` group:

```toml
psp-analysis = [
  "pspdisasm @ git+https://github.com/79cbd8hmgj-wq/PSP-disassembly-tool.git@b3a07f4d0880b7933f87a9557b5e0aa3f364fa5a",
]
```

- [ ] **Step 4: Verify GREEN and commit**

```bash
pytest tests/unit/test_psp_toolchain.py -q
ruff check src/fnr3_re/psp_toolchain.py tests/unit/test_psp_toolchain.py
mypy src/fnr3_re/psp_toolchain.py tests/unit/test_psp_toolchain.py
git add pyproject.toml src/fnr3_re/psp_toolchain.py tests/unit/test_psp_toolchain.py
git commit -m "Add pinned PSP analysis toolchain"
```

---

### Task 2: Synthetic executable fixtures and authoritative candidate discovery

**Files:**
- Create: `tests/support/psp_exec.py`
- Create: `src/fnr3_re/psp_modules.py`
- Test: `tests/unit/test_psp_modules.py`

**Interfaces:**
- `PspModuleAnalysisError(RuntimeError)`
- `PspModuleCandidate(workspace_path: str, local_path: Path, sha256: str, size: int, iso_lba: int, iso_byte_offset: int, classification: str, is_boot: bool)`
- `discover_psp_module_candidates(workspace: Path) -> tuple[PspModuleCandidate, ...]`

- [ ] **Step 1: Create concrete synthetic ELF/container helpers**

```python
import struct


def build_minimal_mips_elf(*, file_type: int = 0xFFA0, alignments: tuple[int, ...] = (0x10,)) -> bytes:
    phoff = 0x34
    phentsize = 0x20
    payload = bytearray(0x400)
    payload[:16] = b"\x7fELF\x01\x01\x01" + b"\x00" * 9
    struct.pack_into("<HHIIIIIHHHHHH", payload, 16, file_type, 8, 1, 0, phoff, 0, 0, 0x34, phentsize, len(alignments), 0x28, 0, 0)
    for index, alignment in enumerate(alignments):
        offset = 0x100 + index * 0x80
        vaddr = index * 0x8000
        struct.pack_into("<IIIIIIII", payload, phoff + index * phentsize, 1, offset, vaddr, vaddr, 0x20, 0x40, 5, alignment)
        payload[offset:offset + 4] = b"\x00\x00\x00\x00"
    return bytes(payload)


def build_encrypted_psp_container() -> bytes:
    payload = bytearray(0x150)
    payload[:4] = b"~PSP"
    payload[0x0A:0x0C] = (1).to_bytes(2, "little")
    payload[0x0C:0x10] = b"TEST"
    return bytes(payload)
```

- [ ] **Step 2: Write failing discovery and revision-lock tests**

```python
def test_discovery_uses_manifest_paths_only(tmp_path):
    workspace = make_workspace(tmp_path, {
        "PSP_GAME/SYSDIR/BOOT.BIN": build_minimal_mips_elf(),
        "PSP_GAME/USRDIR/NET.PRX": build_minimal_mips_elf(),
        "PSP_GAME/USRDIR/NOTE.TXT": b"plain text",
    })
    found = discover_psp_module_candidates(workspace)
    assert [item.workspace_path for item in found] == ["PSP_GAME/SYSDIR/BOOT.BIN", "PSP_GAME/USRDIR/NET.PRX"]


def test_wrong_reference_hash_is_rejected(tmp_path):
    workspace = make_workspace(tmp_path, {"PSP_GAME/SYSDIR/BOOT.BIN": build_minimal_mips_elf()})
    replace_workspace_manifest_iso_hash(workspace, "0" * 64)
    with pytest.raises(PspModuleAnalysisError, match="ULUS10066-v1.00"):
        discover_psp_module_candidates(workspace)
```

- [ ] **Step 3: Verify RED**

Run: `pytest tests/unit/test_psp_modules.py -q`

Expected: missing `fnr3_re.psp_modules`.

- [ ] **Step 4: Implement verified-workspace discovery**

```python
FNR3_REVISION_ID = "ULUS10066-v1.00"
FNR3_ISO_SHA256 = "b11da5afe208d9791eecd9f6a44d0f57946f7d9de165b7d8dd22f5ee740f4ee2"
FNR3_ISO_SIZE = 1137737728


def discover_psp_module_candidates(workspace: Path) -> tuple[PspModuleCandidate, ...]:
    result = verify_workspace(workspace)
    if not result.valid:
        raise PspModuleAnalysisError("workspace verification failed: " + "; ".join(result.diagnostics))
    manifest = load_workspace_manifest(workspace / "manifests" / "workspace.json")
    if (manifest.revision_id, manifest.source_iso_sha256, manifest.source_iso_size) != (FNR3_REVISION_ID, FNR3_ISO_SHA256, FNR3_ISO_SIZE):
        raise PspModuleAnalysisError("workspace is not the locked ULUS10066-v1.00 reference")
    found: list[PspModuleCandidate] = []
    for entry in manifest.files:
        upper = entry.path.upper()
        declared = upper in {"PSP_GAME/SYSDIR/BOOT.BIN", "PSP_GAME/SYSDIR/EBOOT.BIN"} or upper.endswith(".PRX")
        local = workspace / "original" / Path(entry.path)
        signature = local.read_bytes()[:4]
        recognized = signature in {b"\x7fELF", b"~PSP"}
        if declared or recognized:
            found.append(PspModuleCandidate(entry.path, local, entry.sha256, entry.size, entry.lba, entry.offset, entry.classification, upper == "PSP_GAME/SYSDIR/BOOT.BIN"))
    return tuple(sorted(found, key=lambda item: (not item.is_boot, item.workspace_path.casefold())))
```

Add tests that `verify_workspace()` catches file-hash drift and symlinks before discovery.

- [ ] **Step 5: Verify GREEN and commit**

```bash
pytest tests/unit/test_psp_modules.py -q
ruff check src/fnr3_re/psp_modules.py tests/support/psp_exec.py tests/unit/test_psp_modules.py
mypy src/fnr3_re/psp_modules.py tests/unit/test_psp_modules.py
git add src/fnr3_re/psp_modules.py tests/support/psp_exec.py tests/unit/test_psp_modules.py
git commit -m "Discover PSP modules from verified workspace"
```

---

### Task 3: Two-pass analysis and placement with failure isolation

**Files:**
- Modify: `src/fnr3_re/psp_modules.py`
- Test: `tests/unit/test_psp_modules.py`

**Interfaces:**
- `PspModuleRun(candidate: PspModuleCandidate, status: str, needs_decryption: bool, model: object | None, placement: object | None, disassembly: object | None, advanced: object | None, typing: object | None, error: str | None)`
- `PspAnalysisRun(workspace: Path, toolchain: PspToolchainInfo, modules: tuple[PspModuleRun, ...], links: object | None)`
- `analyze_psp_modules(workspace: Path, *, nid_db_paths: tuple[Path, ...] = (), allow_unpinned_toolkit: bool = False) -> PspAnalysisRun`

- [ ] **Step 1: Write failing orchestration tests**

```python
def test_planner_is_called_once_for_all_decrypted_modules(monkeypatch, workspace, fake_toolkit_info):
    monkeypatch.setattr("fnr3_re.psp_modules.load_psp_toolchain", lambda allow_unpinned: fake_toolkit_info)
    run = analyze_psp_modules(workspace)
    assert fake_toolkit_info.module.plan_calls == 1
    assert all(item.placement is not None for item in run.modules if item.status == "analyzed")


def test_encrypted_module_is_inventory_not_failure(monkeypatch, workspace_with_encrypted, fake_toolkit_info):
    monkeypatch.setattr("fnr3_re.psp_modules.load_psp_toolchain", lambda allow_unpinned: fake_toolkit_info)
    run = analyze_psp_modules(workspace_with_encrypted)
    encrypted = next(item for item in run.modules if item.needs_decryption)
    assert encrypted.status == "needs_decryption"
    assert encrypted.placement is None


def test_malformed_secondary_does_not_abort_boot(monkeypatch, workspace_with_broken_secondary, fake_toolkit_info):
    monkeypatch.setattr("fnr3_re.psp_modules.load_psp_toolchain", lambda allow_unpinned: fake_toolkit_info)
    run = analyze_psp_modules(workspace_with_broken_secondary)
    assert next(item for item in run.modules if item.candidate.is_boot).status == "analyzed"
    assert next(item for item in run.modules if item.candidate.workspace_path.endswith("BROKEN.PRX")).status == "failed"
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/unit/test_psp_modules.py -q`

Expected: missing run/orchestration APIs.

- [ ] **Step 3: Implement two-pass analysis**

```python
def analyze_psp_modules(workspace: Path, *, nid_db_paths: tuple[Path, ...] = (), allow_unpinned_toolkit: bool = False) -> PspAnalysisRun:
    toolchain = load_psp_toolchain(allow_unpinned=allow_unpinned_toolkit)
    toolkit = toolchain.module
    candidates = discover_psp_module_candidates(workspace)
    runs: list[PspModuleRun] = []
    placement_inputs = []
    for candidate in candidates:
        try:
            model = toolkit.analyze_file(candidate.local_path)
        except Exception as exc:
            if candidate.is_boot:
                raise PspModuleAnalysisError(f"boot module analysis failed: {exc}") from exc
            runs.append(PspModuleRun(candidate, "failed", False, None, None, None, None, None, str(exc)))
            continue
        if model.needs_decryption:
            runs.append(PspModuleRun(candidate, "needs_decryption", True, model, None, None, None, None, None))
            continue
        runs.append(PspModuleRun(candidate, "pending", False, model, None, None, None, None, None))
        placement_inputs.append(toolkit.ModulePlacementInput(path=candidate.workspace_path, is_boot=candidate.is_boot, model=model))
    placements = {item.path: item for item in toolkit.plan_module_placements(placement_inputs)}
    for run in runs:
        if run.status != "pending" or run.model is None:
            continue
        placement = placements[run.candidate.workspace_path]
        load_address = placement.load_address if placement.requires_relocation else None
        run.placement = placement
        run.disassembly = toolkit.disassemble_file(run.candidate.local_path, load_address=load_address)
        run.advanced = toolkit.analyze_advanced(run.disassembly)
        run.typing = toolkit.analyze_data_types(run.disassembly)
        run.status = "analyzed"
    return PspAnalysisRun(workspace, toolchain, tuple(runs), None)
```

If the actual `analyze_advanced`/`analyze_data_types` signatures at the pinned toolkit revision require additional normalized-model arguments, adapt only the call sites to those exact public signatures; do not add a duplicate analysis implementation.

- [ ] **Step 4: Add placement-policy assertions**

```python
assert boot_run.placement.placement_kind == "boot_inferred"
assert fixed_run.placement.placement_kind == "fixed"
assert secondary_run.placement.placement_kind == "analysis"
assert strict_alignment_run.placement.alignment == 0x8000
```

- [ ] **Step 5: Verify GREEN and commit**

```bash
pytest tests/unit/test_psp_modules.py -q
ruff check src/fnr3_re/psp_modules.py tests/unit/test_psp_modules.py
mypy src/fnr3_re/psp_modules.py tests/unit/test_psp_modules.py
git add src/fnr3_re/psp_modules.py tests/unit/test_psp_modules.py
git commit -m "Analyze and place PSP workspace modules"
```

---

### Task 4: Relocated cross-module linking and optional NID DB

**Files:**
- Modify: `src/fnr3_re/psp_modules.py`
- Test: `tests/unit/test_psp_modules.py`

**Interfaces:**
- Uses toolkit `build_relocated_load_view`, `ModuleAnalysisInput`, `link_modules`, and `load_nid_databases`.
- Stores one game-wide link result in `PspAnalysisRun.links`.

- [ ] **Step 1: Write failing relocated-link test**

```python
def test_link_inputs_share_planned_runtime_addresses(monkeypatch, workspace, fake_toolkit_info):
    monkeypatch.setattr("fnr3_re.psp_modules.load_psp_toolchain", lambda allow_unpinned: fake_toolkit_info)
    run = analyze_psp_modules(workspace)
    assert run.links is not None
    linked = fake_toolkit_info.module.last_link_inputs[0]
    assert linked.model.module_info.address >= 0x08804000
    assert linked.disassembly.functions[0].address >= 0x08804000
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/unit/test_psp_modules.py::test_link_inputs_share_planned_runtime_addresses -q`

- [ ] **Step 3: Build linker inputs from the same placement model**

```python
link_inputs = []
for run in runs:
    if run.status != "analyzed" or run.model is None or run.disassembly is None or run.placement is None:
        continue
    linked_model = run.model
    if run.placement.requires_relocation:
        data = run.candidate.local_path.read_bytes()
        elf = toolkit.parse_elf32(data)
        linked_model = toolkit.build_relocated_load_view(data, elf, run.model, load_address=run.placement.load_address).model
    link_inputs.append(toolkit.ModuleAnalysisInput(path=run.candidate.workspace_path, model=linked_model, disassembly=run.disassembly))
nid_database = toolkit.load_nid_databases(nid_db_paths) if nid_db_paths else None
links = toolkit.link_modules(link_inputs, nid_database=nid_database)
```

Match the pinned toolkit's exact `ModuleAnalysisInput`, `load_nid_databases`, and `link_modules` parameter names during implementation; tests must assert behavior, not private toolkit internals.

- [ ] **Step 4: Verify no-NID mode**

Add a test proving structural import/export linking runs with `nid_db_paths=()` and does not invent external names.

- [ ] **Step 5: Verify GREEN and commit**

```bash
pytest tests/unit/test_psp_modules.py -q
ruff check src/fnr3_re/psp_modules.py tests/unit/test_psp_modules.py
mypy src/fnr3_re/psp_modules.py tests/unit/test_psp_modules.py
git add src/fnr3_re/psp_modules.py tests/unit/test_psp_modules.py
git commit -m "Link PSP modules on relocated addresses"
```

---

### Task 5: Deterministic compact evidence manifest

**Files:**
- Create: `src/fnr3_re/psp_evidence.py`
- Create: `tests/unit/test_psp_evidence.py`

**Interfaces:**
- `AddressValue(type: str, value: int)`
- `PspModuleEvidenceManifest.to_json() -> str`
- `build_psp_evidence_manifest(run: PspAnalysisRun, *, workspace_manifest_sha256: str) -> PspModuleEvidenceManifest`

- [ ] **Step 1: Write failing evidence tests**

```python
def test_manifest_is_deterministic(sample_run):
    first = build_psp_evidence_manifest(sample_run, workspace_manifest_sha256="a" * 64).to_json()
    second = build_psp_evidence_manifest(sample_run, workspace_manifest_sha256="a" * 64).to_json()
    assert first == second
    assert "timestamp" not in first


def test_tool_confidence_is_not_fight_night_confirmation(sample_run):
    payload = json.loads(build_psp_evidence_manifest(sample_run, workspace_manifest_sha256="a" * 64).to_json())
    placement = payload["modules"][0]["placement"]
    assert placement["tool_confidence"] == 0.95
    assert placement["load_address"] == {"type": "runtime_address", "value": placement["load_address"]["value"]}
    assert "fight_night_confidence" not in placement


def test_manifest_contains_no_assembly_or_raw_bytes(sample_run):
    encoded = build_psp_evidence_manifest(sample_run, workspace_manifest_sha256="a" * 64).to_json()
    assert '"assembly"' not in encoded
    assert '"raw_data"' not in encoded
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/unit/test_psp_evidence.py -q`

- [ ] **Step 3: Implement typed-address compact serialization**

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

For each module serialize path/hash/size/LBA/ISO offset, executable/decryption state, ELF type/entry where available, compact program/section summaries, import/export/NID/relocation counts, placement kind/load address/original image base/image size/alignment/`tool_confidence`/`runtime_address_claim`/evidence, function/symbol/reference counts, and sorted warnings. Do not serialize function assembly bodies, raw bytes, or decompiler text.

- [ ] **Step 4: Verify GREEN and commit**

```bash
pytest tests/unit/test_psp_evidence.py -q
ruff check src/fnr3_re/psp_evidence.py tests/unit/test_psp_evidence.py
mypy src/fnr3_re/psp_evidence.py tests/unit/test_psp_evidence.py
git add src/fnr3_re/psp_evidence.py tests/unit/test_psp_evidence.py
git commit -m "Serialize PSP static evidence safely"
```

---

### Task 6: Transactional local output writer

**Files:**
- Modify: `src/fnr3_re/psp_modules.py`
- Modify: `src/fnr3_re/psp_evidence.py`
- Test: `tests/unit/test_psp_modules.py`
- Test: `tests/unit/test_psp_evidence.py`

**Interfaces:**
- `write_psp_analysis_run(run: PspAnalysisRun) -> Path`
- Replaces `working/pspdisasm/` and `manifests/pspdisasm-module-evidence.json` only after all temporary output is complete.

- [ ] **Step 1: Write failing transaction test**

```python
def test_failed_write_preserves_previous_output(tmp_path, sample_run, monkeypatch):
    existing = sample_run.workspace / "working" / "pspdisasm" / "sentinel.txt"
    existing.parent.mkdir(parents=True)
    existing.write_text("old", encoding="utf-8")
    def fail_write(run, destination):
        raise OSError("synthetic write failure")
    monkeypatch.setattr("fnr3_re.psp_modules._write_run_tree", fail_write)
    with pytest.raises(OSError, match="synthetic write failure"):
        write_psp_analysis_run(sample_run)
    assert existing.read_text(encoding="utf-8") == "old"
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/unit/test_psp_modules.py::test_failed_write_preserves_previous_output -q`

- [ ] **Step 3: Implement sibling-temp replacement**

```python
def write_psp_analysis_run(run: PspAnalysisRun) -> Path:
    working_target = run.workspace / "working" / "pspdisasm"
    manifest_target = run.workspace / "manifests" / "pspdisasm-module-evidence.json"
    token = uuid4().hex
    working_temp = working_target.with_name(f".{working_target.name}.tmp-{token}")
    manifest_temp = manifest_target.with_name(f".{manifest_target.name}.tmp-{token}")
    try:
        _write_run_tree(run, working_temp)
        manifest = build_psp_evidence_manifest(run, workspace_manifest_sha256=_hash_file(run.workspace / "manifests" / "workspace.json"))
        manifest_temp.write_text(manifest.to_json(), encoding="utf-8")
        _replace_directory(working_temp, working_target)
        manifest_temp.replace(manifest_target)
        return manifest_target
    finally:
        _remove_path(working_temp)
        manifest_temp.unlink(missing_ok=True)
```

The detailed run tree is exactly:

```text
working/pspdisasm/toolchain.json
working/pspdisasm/modules/<safe-id>/executable.json
working/pspdisasm/modules/<safe-id>/placement.json
working/pspdisasm/modules/<safe-id>/disassembly.json
working/pspdisasm/modules/<safe-id>/advanced.json
working/pspdisasm/modules/<safe-id>/typing.json
working/pspdisasm/links/module_links.json
working/pspdisasm/links/propagated_symbols.json
```

Encrypted/failed modules get inventory/error JSON only. `<safe-id>` is deterministic from normalized workspace path plus the first 12 hex characters of its SHA-256. Reject symlinked output parents and any resolved path outside the workspace.

- [ ] **Step 4: Verify GREEN and commit**

```bash
pytest tests/unit/test_psp_modules.py tests/unit/test_psp_evidence.py -q
ruff check src/fnr3_re/psp_modules.py src/fnr3_re/psp_evidence.py
mypy src/fnr3_re/psp_modules.py src/fnr3_re/psp_evidence.py
git add src/fnr3_re/psp_modules.py src/fnr3_re/psp_evidence.py tests/unit/test_psp_modules.py tests/unit/test_psp_evidence.py
git commit -m "Write PSP analysis transactionally"
```

---

### Task 7: CLI integration

**Files:**
- Modify: `src/fnr3_re/cli.py`
- Create: `tests/unit/test_psp_modules_cli.py`

**Interfaces:**
- `fnr3-re analyze-psp-modules WORKSPACE [--nid-db PATH] [--allow-unpinned-toolkit] [--json]`

- [ ] **Step 1: Write failing CLI tests**

```python
def test_cli_dispatches_psp_analysis(monkeypatch, tmp_path):
    captured: dict[str, object] = {}
    def fake_analyze(workspace: Path, *, nid_db_paths: tuple[Path, ...], allow_unpinned_toolkit: bool):
        captured["workspace"] = workspace
        captured["nid_db_paths"] = nid_db_paths
        captured["allow_unpinned_toolkit"] = allow_unpinned_toolkit
        return object()
    monkeypatch.setattr("fnr3_re.cli.analyze_psp_modules", fake_analyze)
    monkeypatch.setattr("fnr3_re.cli.write_psp_analysis_run", lambda run: tmp_path / "manifests" / "pspdisasm-module-evidence.json")
    assert main(["analyze-psp-modules", str(tmp_path), "--nid-db", "a.csv", "--nid-db", "b.csv"]) == 0
    assert captured["workspace"] == tmp_path
    assert captured["nid_db_paths"] == (Path("a.csv"), Path("b.csv"))
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/unit/test_psp_modules_cli.py -q`

Expected: unknown command.

- [ ] **Step 3: Add parser and dispatch**

```python
psp_parser = subparsers.add_parser("analyze-psp-modules")
psp_parser.add_argument("workspace", type=Path)
psp_parser.add_argument("--nid-db", action="append", type=Path, default=[])
psp_parser.add_argument("--allow-unpinned-toolkit", action="store_true")
psp_parser.add_argument("--json", action="store_true", dest="as_json")
```

Dispatch by calling:

```python
run = analyze_psp_modules(
    args.workspace,
    nid_db_paths=tuple(args.nid_db),
    allow_unpinned_toolkit=args.allow_unpinned_toolkit,
)
evidence_path = write_psp_analysis_run(run)
```

Human output reports analyzed/needs-decryption/failed counts plus evidence path. JSON output reports those counts, `revision_locked`, and evidence path only.

- [ ] **Step 4: Run CLI regressions and commit**

```bash
pytest tests/unit/test_psp_modules_cli.py tests/unit/test_workspace_cli.py tests/unit/test_revision_cli.py -q
ruff check src/fnr3_re/cli.py tests/unit/test_psp_modules_cli.py
mypy src/fnr3_re/cli.py tests/unit/test_psp_modules_cli.py
git add src/fnr3_re/cli.py tests/unit/test_psp_modules_cli.py
git commit -m "Expose PSP module analysis command"
```

---

### Task 8: Documentation and final regression/merge gate

**Files:**
- Create: `docs/architecture/psp-static-analysis.md`
- Modify: `README.md`
- Modify `.gitignore` only if current workspace-ignore coverage is insufficient.

- [ ] **Step 1: Document exact workflow and boundaries**

```bash
python -m pip install -e '.[psp-analysis,dev]'
python tools/build_reference_workspace.py "/path/to/Fight Night Round 3 (USA).iso" /local/fnr3-workspace
fnr3-re analyze-psp-modules /local/fnr3-workspace
fnr3-re analyze-psp-modules /local/fnr3-workspace --nid-db /path/to/psp_nids.csv
```

Document the exact Phase 7G pin, workspace-only input rule, local output paths, evidence manifest path, `--allow-unpinned-toolkit`, explicit address types, static/tool confidence boundary, encrypted-module behavior, and the fact that root-level legacy binaries are not new authoritative inputs.

- [ ] **Step 2: Add a concise README pointer**

Add one Phase I paragraph linking `docs/architecture/psp-static-analysis.md`; do not change unrelated phase language.

- [ ] **Step 3: Run full repository verification**

```bash
pytest -q
ruff check src tests
mypy
```

Expected: all tests pass, no Ruff diagnostics, strict mypy passes.

- [ ] **Step 4: Verify both installation modes**

```bash
python -m pip install -e '.[dev]'
fnr3-re --help
python -m pip install -e '.[psp-analysis,dev]'
python -c 'import pspdisasm; assert pspdisasm.__version__ == "0.9.0"'
```

Expected: base package works without PSP analysis installed; optional install exposes toolkit 0.9.0.

- [ ] **Step 5: Audit copyright/evidence boundaries before PR**

Run:

```bash
git diff main...HEAD --name-only
git diff main...HEAD -- analysis/modules/tracked-module-map.json
git status --short
```

Expected: no new original executable/resource/save/RAM/image/audio payloads; no diff in `analysis/modules/tracked-module-map.json`; clean working tree after commits.

- [ ] **Step 6: Commit documentation**

```bash
git add README.md docs/architecture/psp-static-analysis.md .gitignore
git commit -m "Document PSP static analysis workflow"
```

If `.gitignore` did not require modification, omit it from `git add`.

- [ ] **Step 7: Exact-head PR and post-merge gate**

Open a draft PR from `task-7-pspdisasm-integration`; wait for exact-head CI; review all changed files, review submissions, and inline threads; fix any finding through RED/GREEN; mark ready only when clean; merge using `expected_head_sha`; then verify the post-merge `main` CI result and final pytest count before declaring the integration complete.

---

## Self-Review Results

- **Spec coverage:** Tasks 1–8 cover every approved design requirement: pinned optional dependency, verified workspace/revision boundary, manifest-only discovery, analysis/placement, relocated linking/NIDs, deterministic compact evidence, transactional local output, CLI, documentation, copyright protection, and exact-head/post-merge verification.
- **Placeholder scan:** no `TBD`, `TODO`, ellipsis placeholders, unspecified test requests, or “similar to” shortcuts remain.
- **Type consistency:** `PspToolchainInfo` feeds `PspAnalysisRun.toolchain`; `PspModuleCandidate` feeds `PspModuleRun.candidate`; `PspAnalysisRun` feeds evidence and output writers; CLI consumes only `analyze_psp_modules()` and `write_psp_analysis_run()`.
- **Scope:** this is one adapter subsystem. PSP decryption, game-specific archive parsers, automatic evidence promotion, gameplay changes, and full C reconstruction remain explicit non-goals from the approved spec.
