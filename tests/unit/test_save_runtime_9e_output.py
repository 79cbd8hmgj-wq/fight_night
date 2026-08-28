from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from fnr3_re.evidence import Address, AddressType
from fnr3_re.ppsspp_bundle import DebuggerBundleIdentity
from fnr3_re.save_runtime_9e import (
    RuntimeBreakpointObservation,
    RuntimeCallbackObservation,
    RuntimeControlCapture,
    SavedataInventoryEntry,
    SaveMutation,
    Task9EBreakpoint,
    Task9ELiveGlobal,
    Task9EPlan,
    Task9EPlanError,
    Task9ERuntimeEvidence,
    Task9ERuntimeSource,
    compare_task9e_controls,
    write_task9e_runtime_evidence,
)

_BOOT_SHA256 = "906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9"
_ISO_SHA256 = "a" * 64


def _runtime(value: int) -> Address:
    return Address(AddressType.RUNTIME, value)


def _runtime_source() -> Task9ERuntimeSource:
    return Task9ERuntimeSource.retail_iso(
        revision_id="ULUS10066-v1.00",
        retail_iso_sha256=_ISO_SHA256,
        boot_sha256=_BOOT_SHA256,
    )


def _bundle(tmp_path: Path) -> DebuggerBundleIdentity:
    root = tmp_path / "bundle"
    return DebuggerBundleIdentity(
        root=root,
        revision="fixture-revision",
        sdl_path=root / "PPSSPPSDL",
        sdl_sha256="1" * 64,
        headless_path=root / "PPSSPPHeadless",
        headless_sha256="2" * 64,
        xvfb_path=root / "bin" / "Xvfb",
        xvfb_sha256="3" * 64,
        launcher_path=root / "launch-debug.sh",
        client_path=root / "ppsspp_ws.py",
        config_path=root / "ppsspp-debug.ini",
        host="127.0.0.1",
        port=56244,
    )


def _plan() -> Task9EPlan:
    ids = (
        "load_commit_entry",
        "before_body_copy",
        "before_followup_pointer_load",
        "before_followup_call",
        "after_followup_return",
    )
    return Task9EPlan(
        revision_id="ULUS10066-v1.00",
        boot_sha256=_BOOT_SHA256,
        mapping_rule="ppsspp_absolute = 0x08804000 + elf_virtual",
        breakpoints=tuple(
            Task9EBreakpoint(item, _runtime(0x1000 + index * 0x10), ("pc",))
            for index, item in enumerate(ids)
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


def _inventory(data_hash: str) -> tuple[SavedataInventoryEntry, ...]:
    return (SavedataInventoryEntry("DATA.BIN", 20, data_hash),)


def _capture(tmp_path: Path, control_id: str, data_hash: str) -> RuntimeControlCapture:
    plan = _plan()
    return RuntimeControlCapture(
        control_id=control_id,
        valid=True,
        iso_sha256=_ISO_SHA256,
        state_sha256="b" * 64,
        savedata_inventory=_inventory(data_hash),
        bundle=_bundle(tmp_path),
        observations=tuple(
            RuntimeBreakpointObservation(
                breakpoint_id=breakpoint.id,
                address=breakpoint.address,
                registers=(("pc", breakpoint.address.value),),
                scalar_values=(),
                backtrace=(),
                memory_hashes=(),
            )
            for breakpoint in plan.breakpoints
        ),
        callback=RuntimeCallbackObservation(
            target=_runtime(0x3000),
            registers=(("pc", 0x3000),),
            backtrace=(_runtime(0x3000),),
        ),
        runtime_source=_runtime_source(),
    )


def _evidence(tmp_path: Path) -> Task9ERuntimeEvidence:
    source_hash = "c" * 64
    mutated_hash = "d" * 64
    success = _capture(tmp_path, "successful_load", source_hash)
    corrupted = _capture(tmp_path, "corrupted_copy_control", mutated_hash)
    mutation = SaveMutation(
        relative_path="DATA.BIN",
        offset=9,
        original_byte=0x10,
        replacement_byte=0x11,
        source_sha256=source_hash,
        mutated_sha256=mutated_hash,
        source_inventory=_inventory(source_hash),
        mutated_inventory=_inventory(mutated_hash),
    )
    return compare_task9e_controls(success, corrupted, plan=_plan(), mutation=mutation)


def _workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    (workspace / "working" / "runtime" / "task-9e").mkdir(parents=True)
    (workspace / "manifests").mkdir()
    return workspace


def test_writes_normalized_pair_and_manifest_layout(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    capture_root = workspace / "working" / "runtime" / "task-9e" / "capture-001"
    evidence = _evidence(tmp_path)

    result = write_task9e_runtime_evidence(workspace, evidence, capture_root)

    manifest = workspace / "manifests" / "task-9e-runtime-evidence.json"
    assert result == manifest
    assert json.loads((capture_root / "successful" / "control.json").read_text())["control_id"] == (
        "successful_load"
    )
    assert json.loads((capture_root / "corrupted" / "control.json").read_text())["control_id"] == (
        "corrupted_copy_control"
    )
    assert (capture_root / "comparison.json").read_text(encoding="utf-8") == evidence.to_json()
    assert manifest.read_text(encoding="utf-8") == evidence.to_json()
    diagnostics = capture_root / "local-diagnostics"
    assert diagnostics.is_dir()
    assert list(diagnostics.iterdir()) == []


def test_pair_install_failure_restores_previous_capture_and_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _workspace(tmp_path)
    capture_root = workspace / "working" / "runtime" / "task-9e" / "capture-001"
    capture_root.mkdir()
    (capture_root / "old-marker.txt").write_text("old capture\n", encoding="utf-8")
    manifest = workspace / "manifests" / "task-9e-runtime-evidence.json"
    manifest.write_text("old manifest\n", encoding="utf-8")
    evidence = _evidence(tmp_path)

    real_replace = os.replace
    failed = False

    def flaky_replace(
        source: str | os.PathLike[str],
        destination: str | os.PathLike[str],
    ) -> None:
        nonlocal failed
        if Path(destination) == manifest and not failed:
            failed = True
            raise OSError("injected manifest install failure")
        real_replace(source, destination)

    monkeypatch.setattr(
        "fnr3_re.save_runtime_9e_evidence.os.replace",
        flaky_replace,
    )

    with pytest.raises(OSError, match="injected manifest install failure"):
        write_task9e_runtime_evidence(workspace, evidence, capture_root)

    assert (capture_root / "old-marker.txt").read_text(encoding="utf-8") == "old capture\n"
    assert manifest.read_text(encoding="utf-8") == "old manifest\n"
    assert not any(
        path.name.startswith(".capture-001.task9e-")
        for path in capture_root.parent.iterdir()
    )


@pytest.mark.parametrize("symlink_target", ["runtime", "manifests", "capture_parent"])
def test_output_rejects_symlinked_destination_components(
    tmp_path: Path,
    symlink_target: str,
) -> None:
    if os.name == "nt":
        pytest.skip("symlink fixture requires Unix-like test permissions")

    workspace = _workspace(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    capture_parent = workspace / "working" / "runtime" / "task-9e"

    if symlink_target == "runtime":
        capture_parent.rmdir()
        runtime = workspace / "working" / "runtime"
        runtime.rmdir()
        runtime.symlink_to(outside, target_is_directory=True)
        capture_root = runtime / "task-9e" / "capture-001"
    elif symlink_target == "manifests":
        manifests = workspace / "manifests"
        manifests.rmdir()
        manifests.symlink_to(outside, target_is_directory=True)
        capture_root = capture_parent / "capture-001"
    else:
        capture_parent.rmdir()
        capture_parent.symlink_to(outside, target_is_directory=True)
        capture_root = capture_parent / "capture-001"

    with pytest.raises(Task9EPlanError, match="symlink"):
        write_task9e_runtime_evidence(workspace, _evidence(tmp_path), capture_root)
