from __future__ import annotations

import json
from pathlib import Path

from fnr3_re.module_map import build_repository_module_map

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "analysis" / "modules" / "tracked-module-map.json"


def test_tracked_module_map_artifact_matches_exact_repository_binaries() -> None:
    expected = build_repository_module_map(ROOT).to_json()
    observed = ARTIFACT.read_text(encoding="utf-8")

    assert observed == expected
    decoded = json.loads(observed)
    assert decoded["revision_id"] == "tracked-repository-samples"
    assert [module["path"] for module in decoded["modules"]] == [
        "BOOT.BIN",
        "EBOOT.BIN",
    ]
    assert decoded["modules"][0]["runtime_base"] is None
    assert decoded["modules"][1]["runtime_base"] is None
    assert "runtime load base" in decoded["modules"][0]["unresolved"]
    assert "decrypted ELF correspondence" in decoded["modules"][1]["unresolved"]
