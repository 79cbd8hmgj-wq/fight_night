from pathlib import Path

from fnr3_re.save_utility import (
    load_save_utility_buffer_contract,
    verify_save_utility_buffer_contract,
)

_ROOT = Path(__file__).resolve().parents[2]
_BOOT = _ROOT / "BOOT.BIN"
_ARTIFACT = _ROOT / "analysis/save/save-utility-buffer-contract.json"


def test_exact_boot_matches_savedata_utility_contract_guards() -> None:
    contract = load_save_utility_buffer_contract(_ARTIFACT)

    verification = verify_save_utility_buffer_contract(_BOOT, contract)

    assert verification.valid
    assert verification.diagnostics == ()
    assert verification.checked_regions == 7


def test_savedata_utility_verifier_rejects_tampered_boot(tmp_path: Path) -> None:
    contract = load_save_utility_buffer_contract(_ARTIFACT)
    tampered = tmp_path / "BOOT.BIN"
    tampered.write_bytes(b"not-the-reference-binary")

    verification = verify_save_utility_buffer_contract(tampered, contract)

    assert not verification.valid
    assert verification.checked_regions == 0
    assert verification.diagnostics == ("BOOT.BIN sha256 mismatch",)
