from __future__ import annotations

from pathlib import Path
from types import ModuleType

import pytest

from fnr3_re.psp_modules import PspAnalysisRun, write_psp_analysis_run
from fnr3_re.psp_toolchain import PspToolchainInfo

TOOLKIT_REVISION = "b3a07f4d0880b7933f87a9557b5e0aa3f364fa5a"


def _sample_run(workspace: Path) -> PspAnalysisRun:
    return PspAnalysisRun(
        workspace=workspace,
        toolchain=PspToolchainInfo(
            module=ModuleType("fake_pspdisasm"),
            repository="https://github.com/79cbd8hmgj-wq/PSP-disassembly-tool.git",
            expected_revision=TOOLKIT_REVISION,
            observed_revision=TOOLKIT_REVISION,
            package_version="0.9.0",
            revision_locked=True,
        ),
        modules=(),
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
