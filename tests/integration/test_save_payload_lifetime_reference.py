from __future__ import annotations

import os
from pathlib import Path

import pytest

from fnr3_re.save_payload_lifetime import (
    load_save_payload_lifetime_map,
    verify_save_payload_lifetime_map,
)

_ROOT = Path(__file__).resolve().parents[2]
_ARTIFACT = _ROOT / "analysis/save/save-payload-lifetime.json"


def test_exact_boot_matches_payload_lifetime_guards() -> None:
    configured = os.environ.get("FNR3_BOOT_BIN")
    if not configured:
        pytest.skip("FNR3_BOOT_BIN is not configured")

    payload_map = load_save_payload_lifetime_map(_ARTIFACT)
    result = verify_save_payload_lifetime_map(Path(configured), payload_map)

    assert result.valid, result.diagnostics
    assert result.checked_regions == 10
    assert result.workspace_inside_bss
