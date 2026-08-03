from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ARTIFACT = Path("analysis/save/save-payload-direction-map.json")
UTILITY_ARTIFACT = Path("analysis/save/save-utility-buffer-contract.json")


def test_save_payload_direction_contract_is_available() -> None:
    script = """
import json
from pathlib import Path
from fnr3_re.save_payload import load_save_payload_direction_map

payload_map = load_save_payload_direction_map(
    Path('analysis/save/save-payload-direction-map.json')
)
print(json.dumps({
    'dispatch_runtime_base': payload_map.dispatch_table.runtime_base.value,
    'entries': [
        [
            entry.entry_offset,
            entry.target.value,
            entry.direction,
            entry.role,
        ]
        for entry in payload_map.dispatch_table.entries
    ],
    'controllers': [
        [
            site.role,
            list(site.mode_values),
            site.direction,
            site.callback_entry_offset,
        ]
        for site in payload_map.controller_sites
    ],
}, sort_keys=True))
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "controllers": [
            ["list_save_controller", [5], "save", 56],
            ["autosave_or_save_controller", [1, 3], "save", 56],
            ["autoload_or_load_controller", [0, 2], "load", 64],
            ["list_load_controller", [4], "load", 64],
            ["delete_controller", [6, 7], "non_payload", None],
        ],
        "dispatch_runtime_base": 0x005C3A18,
        "entries": [
            [56, 0x00340DC8, "save", "save_payload_workspace_provider"],
            [64, 0x00340F00, "load", "load_payload_workspace_provider"],
            [68, 0x00340F64, "load", "load_payload_commit_handler"],
        ],
    }


def test_adjacent_controller_modes_are_autosave_and_save() -> None:
    payload = json.loads(UTILITY_ARTIFACT.read_text(encoding="utf-8"))
    sites = {site["role"]: site for site in payload["controller_sites"]}

    assert "autosave_or_save_controller" in sites
    assert sites["autosave_or_save_controller"]["mode_values"] == [1, 3]
    observations = " ".join(sites["autosave_or_save_controller"]["observations"])
    assert "AUTOSAVE" in observations
    assert "AUTOLOAD" not in observations
