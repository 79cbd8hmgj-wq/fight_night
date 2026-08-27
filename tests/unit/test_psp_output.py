from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

import pytest

from fnr3_re.psp_modules import (
    PspAnalysisRun,
    PspModuleAnalysisError,
    PspModuleCandidate,
    PspModuleRun,
    write_psp_analysis_run,
)
from fnr3_re.psp_toolchain import PspToolchainInfo

TOOLKIT_REVISION = "b3a07f4d0880b7933f87a9557b5e0aa3f364fa5a"


@dataclass(slots=True)
class _Header:
    file_type: int = 0xFFA0
    entry: int = 0x100


@dataclass(slots=True)
class _Model:
    input_kind: str = "elf"
    executable_kind: str = "prx"
    needs_decryption: bool = False
    elf_header: _Header = field(default_factory=_Header)
    program_headers: list[object] = field(default_factory=list)
    sections: list[object] = field(default_factory=list)
    module_info: object | None = None
    imports: list[object] = field(default_factory=list)
    exports: list[object] = field(default_factory=list)
    relocations: list[object] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class _Placement:
    load_address: int = 0x08804000
    original_image_base: int = 0
    image_size: int = 0x800
    image_end: int = 0x08804800
    alignment: int = 0x1000
    placement_kind: str = "boot_inferred"
    placement_confidence: float = 0.95
    runtime_address_claim: bool = True
    requires_relocation: bool = True
    placement_evidence: list[str] = field(
        default_factory=lambda: ["synthetic placement evidence"]
    )


@dataclass(slots=True)
class _Disassembly:
    functions: list[object] = field(default_factory=list)
    symbols: list[object] = field(default_factory=list)
    references: list[object] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class _Advanced:
    function_confidence: list[object] = field(default_factory=list)
    call_edges: list[object] = field(default_factory=list)
    jump_tables: list[object] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _toolchain() -> PspToolchainInfo:
    return PspToolchainInfo(
        module=ModuleType("fake_pspdisasm"),
        repository="https://github.com/79cbd8hmgj-wq/PSP-disassembly-tool.git",
        expected_revision=TOOLKIT_REVISION,
        observed_revision=TOOLKIT_REVISION,
        package_version="0.9.0",
        revision_locked=True,
    )


def _sample_run(workspace: Path) -> PspAnalysisRun:
    return PspAnalysisRun(
        workspace=workspace,
        toolchain=_toolchain(),
        modules=(),
        links=None,
    )


def _analyzed_run(workspace: Path) -> PspAnalysisRun:
    candidate = PspModuleCandidate(
        workspace_path="PSP_GAME/SYSDIR/BOOT.BIN",
        local_path=workspace / "original" / "PSP_GAME" / "SYSDIR" / "BOOT.BIN",
        sha256="a" * 64,
        size=0x500,
        iso_lba=100,
        iso_byte_offset=100 * 2048,
        classification="executable",
        is_boot=True,
    )
    module = PspModuleRun(
        candidate=candidate,
        status="analyzed",
        needs_decryption=False,
        model=_Model(),
        placement=_Placement(),
        disassembly=_Disassembly(),
        advanced=_Advanced(),
        typing=None,
    )
    return PspAnalysisRun(
        workspace=workspace,
        toolchain=_toolchain(),
        modules=(module,),
        links=None,
    )


def _workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    (workspace / "working" / "pspdisasm").mkdir(parents=True)
    (workspace / "manifests").mkdir()
    (workspace / "manifests" / "workspace.json").write_text(
        '{"synthetic": true}\n',
        encoding="utf-8",
    )
    return workspace


def test_failed_write_preserves_previous_output_and_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _workspace(tmp_path)
    existing = workspace / "working" / "pspdisasm" / "sentinel.txt"
    existing.write_text("old tree", encoding="utf-8")
    evidence = workspace / "manifests" / "pspdisasm-module-evidence.json"
    evidence.write_text("old manifest\n", encoding="utf-8")

    def fail_write(run: PspAnalysisRun, destination: Path) -> None:
        destination.mkdir(parents=True)
        (destination / "partial.txt").write_text("partial", encoding="utf-8")
        raise OSError("synthetic write failure")

    monkeypatch.setattr("fnr3_re.psp_modules._write_run_tree", fail_write)

    with pytest.raises(OSError, match="synthetic write failure"):
        write_psp_analysis_run(_sample_run(workspace))

    assert existing.read_text(encoding="utf-8") == "old tree"
    assert evidence.read_text(encoding="utf-8") == "old manifest\n"
    assert not list((workspace / "working").glob(".pspdisasm.tmp-*"))
    assert not list((workspace / "manifests").glob(".pspdisasm-module-evidence.json.tmp-*"))


def test_successful_write_emits_detailed_tree_and_evidence(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)

    evidence_path = write_psp_analysis_run(_analyzed_run(workspace))

    root = workspace / "working" / "pspdisasm"
    assert evidence_path == workspace / "manifests" / "pspdisasm-module-evidence.json"
    assert evidence_path.is_file()
    assert (root / "toolchain.json").is_file()
    module_dirs = list((root / "modules").iterdir())
    assert len(module_dirs) == 1
    assert {path.name for path in module_dirs[0].iterdir()} == {
        "advanced.json",
        "disassembly.json",
        "executable.json",
        "placement.json",
        "typing.json",
    }
    assert (root / "links" / "module_links.json").is_file()
    assert (root / "links" / "propagated_symbols.json").is_file()


def test_symlinked_output_parent_is_rejected(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    (workspace / "working" / "pspdisasm").rmdir()
    (workspace / "working").rmdir()
    outside = tmp_path / "outside-working"
    outside.mkdir()
    (workspace / "working").symlink_to(outside, target_is_directory=True)

    with pytest.raises(PspModuleAnalysisError, match="symlink"):
        write_psp_analysis_run(_sample_run(workspace))

    assert not (outside / "pspdisasm").exists()
