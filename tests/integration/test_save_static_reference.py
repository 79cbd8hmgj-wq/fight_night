from __future__ import annotations

import os
from pathlib import Path

import pytest

from fnr3_re.save import load_save_static_map, verify_save_static_map

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "analysis/save/save-system-static-candidates.json"


@pytest.mark.skipif(
    "FNR3_BOOT_BIN" not in os.environ,
    reason="FNR3_BOOT_BIN is not configured",
)
def test_exact_boot_matches_all_static_save_evidence_guards() -> None:
    boot = Path(os.environ["FNR3_BOOT_BIN"])
    save_map = load_save_static_map(ARTIFACT)

    verification = verify_save_static_map(boot, save_map)

    assert verification.valid
    assert verification.diagnostics == ()
    assert verification.checked_string_references == len(save_map.string_references)
    assert verification.checked_xrefs == sum(
        len(reference.xrefs) for reference in save_map.string_references
    )
    assert verification.checked_entry_points == len(save_map.entry_points)


def test_static_save_verifier_rejects_tampered_boot(tmp_path: Path) -> None:
    save_map = load_save_static_map(ARTIFACT)
    tampered = tmp_path / "BOOT.BIN"
    tampered.write_bytes(b"not-the-reference-binary")

    verification = verify_save_static_map(tampered, save_map)

    assert not verification.valid
    assert verification.checked_string_references == 0
    assert verification.checked_xrefs == 0
    assert verification.checked_entry_points == 0
    assert verification.diagnostics == ("BOOT.BIN sha256 mismatch",)
