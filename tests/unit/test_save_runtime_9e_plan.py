from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from fnr3_re.evidence import AddressType
from fnr3_re.save_runtime_9e import (
    Task9EPlanError,
    load_payload_lifetime_contract,
    load_task9e_plan,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PLAN_PATH = _REPO_ROOT / "analysis/save/checkpoint-9e-runtime-capture-plan.json"
_LIFETIME_PATH = _REPO_ROOT / "analysis/save/save-payload-lifetime.json"
_EXPECTED_BOOT_SHA256 = (
    "906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9"
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_loads_committed_task9e_capture_plan() -> None:
    plan = load_task9e_plan(_PLAN_PATH)

    assert plan.revision_id == "ULUS10066-v1.00"
    assert plan.boot_sha256 == _EXPECTED_BOOT_SHA256
    assert plan.mapping_rule == "ppsspp_absolute = 0x08804000 + elf_virtual"
    assert [breakpoint.id for breakpoint in plan.breakpoints] == [
        "load_commit_entry",
        "before_body_copy",
        "before_followup_pointer_load",
        "before_followup_call",
        "after_followup_return",
    ]
    assert all(
        breakpoint.address.address_type is AddressType.RUNTIME
        for breakpoint in plan.breakpoints
    )
    assert [live_global.id for live_global in plan.live_globals] == [
        "followup_callback_pointer",
        "savedata_workspace",
        "registered_destination_pointer",
        "registered_destination_size",
        "active_body_size_global",
    ]
    assert all(
        live_global.address.address_type is AddressType.RUNTIME
        for live_global in plan.live_globals
    )
    assert plan.required_control_ids == ("successful_load", "corrupted_copy_control")


def test_task9e_plan_rejects_identity_mapping_and_breakpoint_mutations(tmp_path: Path) -> None:
    base = _load_json(_PLAN_PATH)
    mutations: list[tuple[str, dict[str, Any]]] = []

    wrong_task = deepcopy(base)
    wrong_task["task"] = 8
    mutations.append(("task", wrong_task))

    wrong_checkpoint = deepcopy(base)
    wrong_checkpoint["checkpoint"] = "9D"
    mutations.append(("checkpoint", wrong_checkpoint))

    wrong_revision = deepcopy(base)
    wrong_revision["source_revision"]["id"] = "wrong-revision"
    mutations.append(("revision", wrong_revision))

    wrong_hash = deepcopy(base)
    wrong_hash["source_revision"]["sha256"] = "0" * 64
    mutations.append(("BOOT", wrong_hash))

    wrong_mapping = deepcopy(base)
    wrong_mapping["address_mapping"]["mapping_rule"] = "incorrect"
    mutations.append(("mapping", wrong_mapping))

    missing_breakpoint = deepcopy(base)
    missing_breakpoint["breakpoints"] = missing_breakpoint["breakpoints"][:-1]
    mutations.append(("breakpoint", missing_breakpoint))

    for label, payload in mutations:
        with pytest.raises(Task9EPlanError):
            load_task9e_plan(_write_json(tmp_path / f"{label}.json", payload))


def test_task9e_plan_rejects_non_runtime_fixed_addresses(tmp_path: Path) -> None:
    payload = _load_json(_PLAN_PATH)
    payload["breakpoints"][0]["address"] = "not-an-address"

    with pytest.raises(Task9EPlanError, match="runtime"):
        load_task9e_plan(_write_json(tmp_path / "bad-address.json", payload))


def test_loads_committed_payload_lifetime_contract() -> None:
    contract = load_payload_lifetime_contract(_LIFETIME_PATH)

    assert contract.source_revision == "ULUS10066-v1.00"
    assert contract.boot_sha256 == _EXPECTED_BOOT_SHA256
    assert contract.total_size == 30044
    assert contract.envelope_header_size == 44
    assert contract.active_body_size_offset == 40
    assert contract.body_offset == 44
    assert contract.body_capacity == 30000


def test_payload_lifetime_rejects_inconsistent_body_bounds(tmp_path: Path) -> None:
    payload = _load_json(_LIFETIME_PATH)
    payload["workspace"]["body_offset"] = 45

    with pytest.raises(Task9EPlanError, match="body"):
        load_payload_lifetime_contract(_write_json(tmp_path / "bad-lifetime.json", payload))
