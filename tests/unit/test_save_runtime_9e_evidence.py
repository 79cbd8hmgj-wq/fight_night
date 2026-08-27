from __future__ import annotations

import json
from pathlib import Path

from fnr3_re.evidence import Address, AddressType
from fnr3_re.ppsspp_bundle import DebuggerBundleIdentity
from fnr3_re.save_runtime_9e import (
    RuntimeBreakpointObservation,
    RuntimeCallbackObservation,
    RuntimeControlCapture,
    RuntimeMemoryObservation,
    SaveMutation,
    SavedataInventoryEntry,
    Task9EBreakpoint,
    Task9ELiveGlobal,
    Task9EPlan,
    Task9ERuntimeEvidence,
    compare_task9e_controls,
)

_BOOT_SHA256 = "906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9"
_ISO_SHA256 = "a" * 64
_STATE_SHA256 = "b" * 64
_SOURCE_DATA_SHA256 = "c" * 64
_MUTATED_DATA_SHA256 = "d" * 64
_MEMORY_A_SHA256 = "e" * 64
_MEMORY_B_SHA256 = "f" * 64


def _runtime(value: int) -> Address:
    return Address(AddressType.RUNTIME, value)


def _bundle(tmp_path: Path) -> DebuggerBundleIdentity:
    return DebuggerBundleIdentity(
        root=tmp_path / "bundle",
        revision="fixture-revision",
        sdl_path=tmp_path / "bundle" / "PPSSPPSDL",
        sdl_sha256="1" * 64,
        headless_path=tmp_path / "bundle" / "PPSSPPHeadless",
        headless_sha256="2" * 64,
        xvfb_path=tmp_path / "bundle" / "bin" / "Xvfb",
        xvfb_sha256="3" * 64,
        launcher_path=tmp_path / "bundle" / "launch-debug.sh",
        client_path=tmp_path / "bundle" / "ppsspp_ws.py",
        config_path=tmp_path / "bundle" / "ppsspp-debug.ini",
        host="127.0.0.1",
        port=56244,
    )


def _plan() -> Task9EPlan:
    return Task9EPlan(
        revision_id="ULUS10066-v1.00",
        boot_sha256=_BOOT_SHA256,
        mapping_rule="ppsspp_absolute = 0x08804000 + elf_virtual",
        breakpoints=(
            Task9EBreakpoint("load_commit_entry", _runtime(0x1000), ("pc", "a0")),
            Task9EBreakpoint(
                "before_body_copy",
                _runtime(0x1010),
                ("a0", "workspace_active_body_size"),
            ),
            Task9EBreakpoint(
                "before_followup_pointer_load",
                _runtime(0x1020),
                ("a0", "destination_body_hash"),
            ),
            Task9EBreakpoint(
                "before_followup_call",
                _runtime(0x1030),
                ("t9_or_call_register", "ra"),
            ),
            Task9EBreakpoint(
                "after_followup_return",
                _runtime(0x1040),
                ("v0", "caller_pc"),
            ),
        ),
        live_globals=(
            Task9ELiveGlobal("followup_callback_pointer", _runtime(0x2000)),
            Task9ELiveGlobal("savedata_workspace", _runtime(0x2100), 20),
            Task9ELiveGlobal("registered_destination_pointer", _runtime(0x2200)),
            Task9ELiveGlobal("registered_destination_size", _runtime(0x2204)),
            Task9ELiveGlobal("active_body_size_global", _runtime(0x2208)),
        ),
        required_control_ids=("successful_load", "corrupted_copy_control"),
    )


def _inventory(sha256: str) -> tuple[SavedataInventoryEntry, ...]:
    return (
        SavedataInventoryEntry("DATA.BIN", 20, sha256),
        SavedataInventoryEntry("PARAM.SFO", 12, "4" * 64),
    )


def _observation(
    breakpoint_id: str,
    address: int,
    *,
    registers: tuple[tuple[str, int], ...],
    memory_sha256: str | None = None,
) -> RuntimeBreakpointObservation:
    memory_hashes: tuple[RuntimeMemoryObservation, ...] = ()
    if memory_sha256 is not None:
        memory_hashes = (
            RuntimeMemoryObservation(
                id="destination_body",
                address=_runtime(0x4000),
                size=4,
                sha256=memory_sha256,
            ),
        )
    return RuntimeBreakpointObservation(
        breakpoint_id=breakpoint_id,
        address=_runtime(address),
        registers=registers,
        scalar_values=(),
        backtrace=(),
        memory_hashes=memory_hashes,
    )


def _capture(
    tmp_path: Path,
    control_id: str,
    *,
    callback_target: int = 0x3000,
    before_call_t9: int = 0x3000,
    memory_sha256: str = _MEMORY_A_SHA256,
) -> RuntimeControlCapture:
    inventory_sha = (
        _SOURCE_DATA_SHA256
        if control_id == "successful_load"
        else _MUTATED_DATA_SHA256
    )
    return RuntimeControlCapture(
        control_id=control_id,
        valid=True,
        iso_sha256=_ISO_SHA256,
        state_sha256=_STATE_SHA256,
        savedata_inventory=_inventory(inventory_sha),
        bundle=_bundle(tmp_path),
        observations=(
            _observation("load_commit_entry", 0x1000, registers=(("pc", 0x1000), ("a0", 1))),
            _observation("before_body_copy", 0x1010, registers=(("a0", 1),)),
            _observation(
                "before_followup_pointer_load",
                0x1020,
                registers=(("a0", 1),),
                memory_sha256=memory_sha256,
            ),
            _observation(
                "before_followup_call",
                0x1030,
                registers=(("t9", before_call_t9), ("ra", 0x1040)),
            ),
            _observation("after_followup_return", 0x1040, registers=(("v0", 0),)),
        ),
        callback=RuntimeCallbackObservation(
            target=_runtime(callback_target),
            registers=(("pc", callback_target), ("a0", 1)),
            backtrace=(_runtime(callback_target), _runtime(0x1038)),
        ),
    )


def _mutation() -> SaveMutation:
    return SaveMutation(
        relative_path="DATA.BIN",
        offset=9,
        original_byte=0x10,
        replacement_byte=0x11,
        source_sha256=_SOURCE_DATA_SHA256,
        mutated_sha256=_MUTATED_DATA_SHA256,
        source_inventory=_inventory(_SOURCE_DATA_SHA256),
        mutated_inventory=_inventory(_MUTATED_DATA_SHA256),
    )


def test_comparison_serialization_is_deterministic_and_repository_safe(tmp_path: Path) -> None:
    success = _capture(tmp_path, "successful_load")
    corrupted = _capture(
        tmp_path,
        "corrupted_copy_control",
        memory_sha256=_MEMORY_B_SHA256,
    )

    evidence = compare_task9e_controls(
        success,
        corrupted,
        plan=_plan(),
        mutation=_mutation(),
    )

    assert isinstance(evidence, Task9ERuntimeEvidence)
    encoded = evidence.to_json()
    assert encoded == evidence.to_json()
    decoded = json.loads(encoded)

    assert decoded["schema_version"] == 1
    assert decoded["revision_id"] == "ULUS10066-v1.00"
    assert decoded["iso_sha256"] == _ISO_SHA256
    assert decoded["boot_sha256"] == _BOOT_SHA256
    assert decoded["state_sha256"] == _STATE_SHA256
    assert decoded["bundle"] == {
        "headless_sha256": "2" * 64,
        "revision": "fixture-revision",
        "sdl_sha256": "1" * 64,
        "xvfb_sha256": "3" * 64,
    }
    assert decoded["successful"]["control_id"] == "successful_load"
    assert decoded["successful"]["valid"] is True
    assert decoded["corrupted"]["control_id"] == "corrupted_copy_control"
    assert decoded["corrupted"]["valid"] is True
    assert decoded["successful"]["savedata_inventory"][0]["sha256"] == _SOURCE_DATA_SHA256
    assert decoded["corrupted"]["savedata_inventory"][0]["sha256"] == _MUTATED_DATA_SHA256

    before_call = decoded["successful"]["observations"][3]
    assert before_call["address"] == {"address_type": "runtime", "value": 0x1030}
    assert before_call["registers"] == [["t9", 0x3000], ["ra", 0x1040]]
    assert decoded["successful"]["callback"]["target"] == {
        "address_type": "runtime",
        "value": 0x3000,
    }
    memory = decoded["successful"]["observations"][2]["memory_hashes"][0]
    assert memory == {
        "address": {"address_type": "runtime", "value": 0x4000},
        "id": "destination_body",
        "sha256": _MEMORY_A_SHA256,
        "size": 4,
    }
    assert decoded["mutation"]["offset"] == 9
    assert decoded["mutation"]["original_byte"] == 0x10
    assert decoded["mutation"]["replacement_byte"] == 0x11
    assert decoded["mutation"]["source_sha256"] == _SOURCE_DATA_SHA256
    assert decoded["mutation"]["mutated_sha256"] == _MUTATED_DATA_SHA256
    assert decoded["first_divergence"] == {
        "control_a": _MEMORY_A_SHA256,
        "control_b": _MEMORY_B_SHA256,
        "fact": "memory_hash",
        "field": "destination_body",
        "observation_id": "before_followup_pointer_load",
    }

    for section in (
        "runtime_observed",
        "static_correlated",
        "semantic_interpretation",
        "confirmed",
        "not_confirmed",
        "warnings",
    ):
        assert section in decoded

    lowered = encoded.casefold()
    for forbidden in (
        "data_hex",
        "screenshot",
        "transcript",
        "assembly_body",
        "raw_memory",
        "raw_save",
    ):
        assert forbidden not in lowered
    assert str(tmp_path) not in encoded


def test_first_divergence_precedence_prefers_callback_before_registers(tmp_path: Path) -> None:
    success = _capture(tmp_path, "successful_load")
    corrupted = _capture(
        tmp_path,
        "corrupted_copy_control",
        callback_target=0x3333,
        before_call_t9=0x4444,
        memory_sha256=_MEMORY_B_SHA256,
    )

    evidence = compare_task9e_controls(
        success,
        corrupted,
        plan=_plan(),
        mutation=_mutation(),
    )

    assert evidence.first_divergence is not None
    assert evidence.first_divergence.fact == "callback_target"
    assert evidence.first_divergence.control_a == 0x3000
    assert evidence.first_divergence.control_b == 0x3333


def test_identical_captured_facts_produce_no_divergence_warning(tmp_path: Path) -> None:
    success = _capture(tmp_path, "successful_load")
    corrupted = _capture(tmp_path, "corrupted_copy_control")

    evidence = compare_task9e_controls(
        success,
        corrupted,
        plan=_plan(),
        mutation=_mutation(),
    )

    assert evidence.first_divergence is None
    assert any("no divergence" in warning.casefold() for warning in evidence.warnings)
