from __future__ import annotations

import json
from pathlib import Path

import pytest

from fnr3_re.cli import main


def test_validate_image_cli_reports_missing_image(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = Path(__file__).resolve().parents[2]
    config = root / "config" / "revisions" / "ulus10066-v1.00.json"

    code = main(
        [
            "validate-image",
            str(tmp_path / "missing.iso"),
            "--revision-config",
            str(config),
            "--json",
        ]
    )

    assert code == 1
    output = json.loads(capsys.readouterr().out)
    assert output["valid"] is False
    assert output["diagnostics"] == ["image file does not exist"]
