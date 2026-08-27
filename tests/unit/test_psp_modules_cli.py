from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import fnr3_re.cli as cli


def _fake_run(*, revision_locked: bool = True) -> object:
    return SimpleNamespace(
        modules=(
            SimpleNamespace(status="analyzed"),
            SimpleNamespace(status="needs_decryption"),
            SimpleNamespace(status="failed"),
        ),
        toolchain=SimpleNamespace(revision_locked=revision_locked),
    )


def test_cli_dispatches_psp_analysis_with_nid_databases(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}
    evidence = tmp_path / "manifests" / "pspdisasm-module-evidence.json"

    def fake_analyze(
        workspace: Path,
        *,
        nid_db_paths: tuple[Path, ...],
        allow_unpinned_toolkit: bool,
    ) -> object:
        captured["workspace"] = workspace
        captured["nid_db_paths"] = nid_db_paths
        captured["allow_unpinned_toolkit"] = allow_unpinned_toolkit
        return _fake_run()

    monkeypatch.setattr(cli, "analyze_psp_modules", fake_analyze, raising=False)
    monkeypatch.setattr(cli, "write_psp_analysis_run", lambda run: evidence, raising=False)

    result = cli.main(
        [
            "analyze-psp-modules",
            str(tmp_path),
            "--nid-db",
            "a.csv",
            "--nid-db",
            "b.csv",
        ]
    )

    assert result == 0
    assert captured == {
        "workspace": tmp_path,
        "nid_db_paths": (Path("a.csv"), Path("b.csv")),
        "allow_unpinned_toolkit": False,
    }
    output = capsys.readouterr().out
    assert "analyzed=1" in output
    assert "needs-decryption=1" in output
    assert "failed=1" in output
    assert str(evidence) in output


def test_cli_json_summary_reports_revision_lock_and_override(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}
    evidence = tmp_path / "manifests" / "pspdisasm-module-evidence.json"

    def fake_analyze(
        workspace: Path,
        *,
        nid_db_paths: tuple[Path, ...],
        allow_unpinned_toolkit: bool,
    ) -> object:
        captured["allow_unpinned_toolkit"] = allow_unpinned_toolkit
        return _fake_run(revision_locked=False)

    monkeypatch.setattr(cli, "analyze_psp_modules", fake_analyze, raising=False)
    monkeypatch.setattr(cli, "write_psp_analysis_run", lambda run: evidence, raising=False)

    result = cli.main(
        [
            "analyze-psp-modules",
            str(tmp_path),
            "--allow-unpinned-toolkit",
            "--json",
        ]
    )

    assert result == 0
    assert captured["allow_unpinned_toolkit"] is True
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "analyzed": 1,
        "evidence_path": str(evidence),
        "failed": 1,
        "needs_decryption": 1,
        "revision_locked": False,
    }
