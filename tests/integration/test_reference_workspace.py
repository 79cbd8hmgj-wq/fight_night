from __future__ import annotations

import os
from pathlib import Path

import pytest

from fnr3_re.iso import build_workspace, verify_workspace
from fnr3_re.revision import load_reference_revision

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_CONFIG = ROOT / "config" / "revisions" / "ulus10066-v1.00.json"


@pytest.mark.skipif(
    "FNR3_REFERENCE_ISO" not in os.environ,
    reason="FNR3_REFERENCE_ISO is not configured",
)
def test_reference_workspace_is_complete_and_deterministic(tmp_path: Path) -> None:
    image = Path(os.environ["FNR3_REFERENCE_ISO"])
    revision = load_reference_revision(REFERENCE_CONFIG)
    first_path = tmp_path / "first"
    second_path = tmp_path / "second"

    first = build_workspace(image, first_path, revision)
    second = build_workspace(image, second_path, revision)

    assert len(first.files) == 653
    assert len(first.directories) == 71
    assert first.to_json() == second.to_json()
    assert verify_workspace(first_path).valid
    assert verify_workspace(second_path).valid
