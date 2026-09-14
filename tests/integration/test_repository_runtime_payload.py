from __future__ import annotations

from pathlib import Path

from fnr3_re.runtime_image import load_runtime_payload_manifest, verify_runtime_payload

_LOCKED_BOOT_SHA256 = "906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9"


def test_committed_runtime_payload_manifest_matches_repository() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest = load_runtime_payload_manifest(
        root / "config/runtime/ulus10066-repository-payload.json"
    )

    entries = verify_runtime_payload(root, manifest)

    assert entries
    assert manifest.revision_id == "ULUS10066-v1.00"
    boot = next(
        entry
        for entry in entries
        if entry.destination.as_posix() == "PSP_GAME/SYSDIR/BOOT.BIN"
    )
    eboot = next(
        entry
        for entry in entries
        if entry.destination.as_posix() == "PSP_GAME/SYSDIR/EBOOT.BIN"
    )
    assert boot.sha256 == _LOCKED_BOOT_SHA256
    assert boot.size == 7_270_664
    assert eboot.size == 7_271_008
    assert any(entry.destination.as_posix().startswith("PSP_GAME/USRDIR/") for entry in entries)
    assert not any(
        entry.source_path.relative_to(root).parts[0]
        in {".github", "analysis", "config", "docs", "src", "tests", "tools"}
        for entry in entries
    )
