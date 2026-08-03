from __future__ import annotations

import json
from pathlib import Path

import pytest

from fnr3_re.cli import main


def test_validate_package_cli_returns_nonzero_and_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    package = tmp_path / "missing"
    code = main(["validate-package", str(package), "--json"])
    assert code == 1
    output = capsys.readouterr().out
    parsed = json.loads(output)
    assert parsed["valid"] is False
    assert parsed["package"] == str(package)


def test_validate_registry_cli_accepts_task1_registry(
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = Path(__file__).resolve().parents[2]
    registry = root / "config" / "subsystem_registry.json"
    code = main(["validate-registry", str(registry), "--json"])
    assert code == 0
    output = capsys.readouterr().out
    assert json.loads(output)["valid"] is True
