from __future__ import annotations

import hashlib
import json
import stat
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import pytest

from fnr3_re.manifests import (
    ManifestDirectory,
    ManifestFile,
    WorkspaceManifest,
    classify_iso_path,
)
from fnr3_re.psp_modules import (
    PspModuleAnalysisError,
    PspModuleCandidate,
    analyze_psp_modules,
    discover_psp_module_candidates,
)
from fnr3_re.psp_toolchain import PspToolchainInfo
from tests.support.psp_exec import build_minimal_mips_elf

FNR3_ISO_SHA256 = "b11da5afe208d9791eecd9f6a44d0f57946f7d9de165b7d8dd22f5ee740f4ee2"
TOOLKIT_REVISION = "b3a07f4d0880b7933f87a9557b5e0aa3f364fa5a"


def _make_workspace(tmp_path: Path, files: dict[str, bytes]) -> Path:
    workspace = tmp_path / "workspace"
    original = workspace / "original"
    working = workspace / "working"
    modified = workspace / "modified"
    manifests = workspace / "manifests"
    original.mkdir(parents=True)
    working.mkdir()
    modified.mkdir()
    manifests.mkdir()

    manifest_files: list[ManifestFile] = []
    for order, (path, payload) in enumerate(files.items()):
        destination = original / Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        destination.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        manifest_files.append(
            ManifestFile(
                path=path,
                lba=100 + order,
                offset=(100 + order) * 2048,
                size=len(payload),
                sha256=hashlib.sha256(payload).hexdigest(),
                order=order,
                classification=classify_iso_path(path),
            )
        )

    manifest = WorkspaceManifest(
        revision_id="ULUS10066-v1.00",
        source_iso_size=1137737728,
        source_iso_sha256=FNR3_ISO_SHA256,
        volume_id="FNR3TEST",
        sector_size=2048,
        volume_sectors=555536,
        directories=(
            ManifestDirectory(path=".", lba=20, offset=40960, size=2048, order=0),
        ),
        files=tuple(manifest_files),
    )
    (manifests / "workspace.json").write_text(manifest.to_json(), encoding="utf-8")
    return workspace


def test_discovery_uses_verified_manifest_paths_and_content(tmp_path: Path) -> None:
    workspace = _make_workspace(
        tmp_path,
        {
            "PSP_GAME/SYSDIR/BOOT.BIN": build_minimal_mips_elf(),
            "PSP_GAME/USRDIR/NET.PRX": build_minimal_mips_elf(),
            "PSP_GAME/USRDIR/OTHER.BIN": build_minimal_mips_elf(),
            "PSP_GAME/USRDIR/NOTE.TXT": b"plain text",
        },
    )

    found = discover_psp_module_candidates(workspace)

    assert [item.workspace_path for item in found] == [
        "PSP_GAME/SYSDIR/BOOT.BIN",
        "PSP_GAME/USRDIR/NET.PRX",
        "PSP_GAME/USRDIR/OTHER.BIN",
    ]
    assert found[0].is_boot is True
    assert found[0].iso_lba == 100
    assert found[0].iso_byte_offset == 100 * 2048


def test_workspace_hash_drift_is_rejected_before_discovery(tmp_path: Path) -> None:
    workspace = _make_workspace(
        tmp_path,
        {"PSP_GAME/SYSDIR/BOOT.BIN": build_minimal_mips_elf()},
    )
    boot = workspace / "original" / "PSP_GAME" / "SYSDIR" / "BOOT.BIN"
    boot.chmod(stat.S_IRUSR | stat.S_IWUSR)
    boot.write_bytes(b"drift")
    boot.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    with pytest.raises(PspModuleAnalysisError, match="workspace verification failed"):
        discover_psp_module_candidates(workspace)


def test_wrong_reference_revision_is_rejected(tmp_path: Path) -> None:
    workspace = _make_workspace(
        tmp_path,
        {"PSP_GAME/SYSDIR/BOOT.BIN": build_minimal_mips_elf()},
    )
    manifest_path = workspace / "manifests" / "workspace.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["source_iso_sha256"] = "0" * 64
    manifest_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(PspModuleAnalysisError, match=r"ULUS10066-v1\.00"):
        discover_psp_module_candidates(workspace)


def test_symbolic_link_in_original_is_rejected(tmp_path: Path) -> None:
    workspace = _make_workspace(
        tmp_path,
        {"PSP_GAME/SYSDIR/BOOT.BIN": build_minimal_mips_elf()},
    )
    outside = tmp_path / "outside.bin"
    outside.write_bytes(build_minimal_mips_elf())
    link = workspace / "original" / "PSP_GAME" / "USRDIR" / "ESCAPE.PRX"
    link.parent.mkdir(parents=True)
    link.symlink_to(outside)

    with pytest.raises(PspModuleAnalysisError, match="workspace verification failed"):
        discover_psp_module_candidates(workspace)


@dataclass(slots=True)
class _FakeModel:
    needs_decryption: bool = False


@dataclass(slots=True)
class _FakePlacementInput:
    path: str
    is_boot: bool
    model: _FakeModel


@dataclass(slots=True)
class _FakePlacement:
    path: str
    load_address: int
    placement_kind: str
    requires_relocation: bool
    alignment: int = 0x10


@dataclass(slots=True)
class _FakeDisassembly:
    source_name: str


@dataclass(slots=True)
class _FakeAdvanced:
    source_name: str


class _FakeToolkit(ModuleType):
    ModulePlacementInput: type[_FakePlacementInput]

    def __init__(self) -> None:
        super().__init__("fake_pspdisasm")
        self.ModulePlacementInput = _FakePlacementInput
        self.plan_calls = 0
        self.disassembly_loads: dict[str, int | None] = {}

    def analyze_file(self, path: Path) -> _FakeModel:
        if "BROKEN" in path.name:
            raise ValueError("synthetic parse failure")
        return _FakeModel(needs_decryption="ENCRYPTED" in path.name)

    def plan_module_placements(
        self,
        inputs: list[_FakePlacementInput],
    ) -> list[_FakePlacement]:
        self.plan_calls += 1
        placements: list[_FakePlacement] = []
        for index, item in enumerate(inputs):
            if item.is_boot:
                placements.append(
                    _FakePlacement(item.path, 0x08804000, "boot_inferred", True)
                )
            elif "FIXED" in item.path:
                placements.append(
                    _FakePlacement(item.path, 0x08900000, "fixed", False)
                )
            else:
                alignment = 0x8000 if "STRICT" in item.path else 0x10
                placements.append(
                    _FakePlacement(
                        item.path,
                        0x08810000 + index * 0x10000,
                        "analysis",
                        True,
                        alignment,
                    )
                )
        return placements

    def disassemble_file(
        self,
        path: Path,
        *,
        load_address: int | None = None,
    ) -> _FakeDisassembly:
        self.disassembly_loads[path.name] = load_address
        return _FakeDisassembly(str(path))

    def analyze_advanced(
        self,
        model: _FakeModel,
        disassembly: _FakeDisassembly,
    ) -> _FakeAdvanced:
        return _FakeAdvanced(disassembly.source_name)


def _candidate(tmp_path: Path, name: str, *, is_boot: bool = False) -> PspModuleCandidate:
    path = tmp_path / name
    path.write_bytes(b"fixture")
    return PspModuleCandidate(
        workspace_path=(
            "PSP_GAME/SYSDIR/BOOT.BIN"
            if is_boot
            else f"PSP_GAME/USRDIR/{name}"
        ),
        local_path=path,
        sha256=hashlib.sha256(b"fixture").hexdigest(),
        size=7,
        iso_lba=200,
        iso_byte_offset=200 * 2048,
        classification="executable",
        is_boot=is_boot,
    )


def _install_fake_analysis(
    monkeypatch: pytest.MonkeyPatch,
    candidates: tuple[PspModuleCandidate, ...],
) -> _FakeToolkit:
    toolkit = _FakeToolkit()
    info = PspToolchainInfo(
        module=toolkit,
        repository="https://github.com/79cbd8hmgj-wq/PSP-disassembly-tool.git",
        expected_revision=TOOLKIT_REVISION,
        observed_revision=TOOLKIT_REVISION,
        package_version="0.9.0",
        revision_locked=True,
    )
    monkeypatch.setattr(
        "fnr3_re.psp_modules.discover_psp_module_candidates",
        lambda workspace: candidates,
    )
    monkeypatch.setattr(
        "fnr3_re.psp_modules.load_psp_toolchain",
        lambda *, allow_unpinned: info,
    )
    return toolkit


def test_analysis_plans_all_usable_modules_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidates = (
        _candidate(tmp_path, "BOOT.BIN", is_boot=True),
        _candidate(tmp_path, "FIXED.PRX"),
        _candidate(tmp_path, "STRICT.PRX"),
    )
    toolkit = _install_fake_analysis(monkeypatch, candidates)

    run = analyze_psp_modules(tmp_path)

    assert toolkit.plan_calls == 1
    analyzed = [item for item in run.modules if item.status == "analyzed"]
    assert len(analyzed) == 3
    assert analyzed[0].placement.placement_kind == "boot_inferred"
    assert analyzed[1].placement.placement_kind == "fixed"
    assert analyzed[2].placement.alignment == 0x8000
    assert toolkit.disassembly_loads["BOOT.BIN"] == 0x08804000
    assert toolkit.disassembly_loads["FIXED.PRX"] is None
    assert toolkit.disassembly_loads["STRICT.PRX"] is not None


def test_encrypted_module_is_inventory_not_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidates = (
        _candidate(tmp_path, "BOOT.BIN", is_boot=True),
        _candidate(tmp_path, "ENCRYPTED.PRX"),
    )
    toolkit = _install_fake_analysis(monkeypatch, candidates)

    run = analyze_psp_modules(tmp_path)

    encrypted = next(item for item in run.modules if item.needs_decryption)
    assert encrypted.status == "needs_decryption"
    assert encrypted.placement is None
    assert "ENCRYPTED.PRX" not in toolkit.disassembly_loads


def test_malformed_secondary_does_not_abort_boot_module(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidates = (
        _candidate(tmp_path, "BOOT.BIN", is_boot=True),
        _candidate(tmp_path, "BROKEN.PRX"),
    )
    _install_fake_analysis(monkeypatch, candidates)

    run = analyze_psp_modules(tmp_path)

    boot = next(item for item in run.modules if item.candidate.is_boot)
    broken = next(item for item in run.modules if item.candidate.workspace_path.endswith("BROKEN.PRX"))
    assert boot.status == "analyzed"
    assert broken.status == "failed"
    assert broken.error == "synthetic parse failure"


def test_boot_analysis_failure_aborts_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    broken_boot = _candidate(tmp_path, "BROKEN_BOOT.BIN", is_boot=True)
    _install_fake_analysis(monkeypatch, (broken_boot,))

    with pytest.raises(PspModuleAnalysisError, match="boot module analysis failed"):
        analyze_psp_modules(tmp_path)
