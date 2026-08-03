from __future__ import annotations

import os
from pathlib import Path

import pytest

from fnr3_re.revision import load_reference_revision, validate_image


def test_local_reference_iso_matches_locked_revision() -> None:
    iso = os.environ.get("FNR3_REFERENCE_ISO")
    if not iso:
        pytest.skip("FNR3_REFERENCE_ISO is not configured")

    root = Path(__file__).resolve().parents[2]
    revision = load_reference_revision(root / "config" / "revisions" / "ulus10066-v1.00.json")
    result = validate_image(Path(iso), revision)

    assert result.valid, result.diagnostics
