from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_PATH = ROOT / "analysis" / "reference" / "ulus10066-intake-validation.json"
REVISION_PATH = ROOT / "config" / "revisions" / "ulus10066-v1.00.json"


def load_object(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_intake_evidence_matches_locked_revision() -> None:
    evidence = load_object(EVIDENCE_PATH)
    revision = load_object(REVISION_PATH)
    identity = cast(dict[str, Any], evidence["observed_identity"])

    assert evidence["status"] == "confirmed"
    assert identity == {
        "disc_id": revision["disc_id"],
        "disc_version": revision["disc_version"],
        "iso_sha256": revision["iso_sha256"],
        "iso_size": revision["iso_size"],
        "psp_system_version": revision["psp_system_version"],
        "title": revision["title"],
    }


def test_intake_evidence_records_complete_reference_inventory() -> None:
    evidence = load_object(EVIDENCE_PATH)
    inventory = cast(dict[str, Any], evidence["filesystem_inventory"])
    members = cast(list[dict[str, Any]], evidence["archive_members"])

    assert evidence["source_archive"] == "FightNightRound3(USA).7z"
    assert members[0] == {
        "name": "Fight Night Round 3 (USA).iso",
        "size": 1_137_737_728,
    }
    assert inventory == {"directories": 71, "files": 653, "prx_modules": 6}
