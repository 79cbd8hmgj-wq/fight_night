from __future__ import annotations

import hashlib
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from fnr3_re.evidence import Address, AddressType
from fnr3_re.manifests import ManifestDirectory, WorkspaceManifest
from fnr3_re.ppsspp_bundle import DebuggerBundleProfile
from fnr3_re.revision import ReferenceRevision
from fnr3_re.save_runtime_9e import (
    PayloadLifetimeContract,
    RuntimeControlCapture,
    Task9EBreakpoint,
    Task9ECaptureInputs,
    Task9ELiveGlobal,
    Task9EPlan,
    Task9EPlanError,
    capture_task9e_control,
)

_BOOT_SHA256 = "906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _runtime(value: int) -> Address:
    return Address(AddressType.RUNTIME, value)


def _plan() -> Task9EPlan:
    return Task9EPlan(
        revision_id="ULUS10066-v1.00",
        boot_sha256=_BOOT_SHA256,
        mapping_rule="ppsspp_absolute = 0x08804000 + elf_virtual",
        breakpoints=(
            Task9EBreakpoint(
                "load_commit_entry",
                _runtime(0x1000),
                ("pc", "a0", "callback_pointer", "workspace_header"),
            ),
            Task9EBreakpoint(
                "before_body_copy",
                _runtime(0x1010),
                (
                    "a0",
                    "workspace_active_body_size",
                    "registered_destination_pointer",
                    "registered_destination_size",
                ),
            ),
            Task9EBreakpoint(
                "before_followup_pointer_load",
                _runtime(0x1020),
                (
                    "callback_pointer",
                    "a0",
                    "active_body_size_global",
                    "destination_body_hash",
                ),
            ),
            Task9EBreakpoint(
                "before_followup_call",
                _runtime(0x1030),
                ("t9_or_call_register", "a0", "ra", "sp"),
            ),
            Task9EBreakpoint(
                "after_followup_return",
                _runtime(0x1040),
                ("v0", "caller_pc", "destination_body_hash", "error_state_candidates"),
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


def _contract() -> PayloadLifetimeContract:
    return PayloadLifetimeContract(
        source_revision="ULUS10066-v1.00",
        boot_sha256=_BOOT_SHA256,
        total_size=20,
        envelope_header_size=8,
        active_body_size_offset=4,
        body_offset=8,
        body_capacity=12,
    )


def _write_bundle(root: Path) -> DebuggerBundleProfile:
    root.mkdir()
    (root / "bin").mkdir()
    payloads = {
        root / "PPSSPPSDL": b"fixture-sdl",
        root / "PPSSPPHeadless": b"fixture-headless",
        root / "bin" / "Xvfb": b"fixture-xvfb",
        root / "launch-debug.sh": b"#!/bin/sh\nexit 0\n",
        root / "ppsspp_ws.py": b"#!/usr/bin/env python3\n",
    }
    for path, payload in payloads.items():
        path.write_bytes(payload)
        path.chmod(0o755)
    (root / "ppsspp-resolved-revision.txt").write_text(
        "fixture-revision\n", encoding="utf-8"
    )
    (root / "ppsspp-debug.ini").write_text(
        """[General]
RemoteDebuggerOnStartup = True
RemoteDebuggerLocal = True
RemoteISOPort = 56244
""",
        encoding="utf-8",
    )
    return DebuggerBundleProfile(
        revision="fixture-revision",
        sdl_sha256=_sha256(payloads[root / "PPSSPPSDL"]),
        headless_sha256=_sha256(payloads[root / "PPSSPPHeadless"]),
        xvfb_sha256=_sha256(payloads[root / "bin" / "Xvfb"]),
        default_port=56244,
    )


def _write_workspace(root: Path, revision: ReferenceRevision) -> None:
    (root / "original").mkdir(parents=True)
    (root / "working").mkdir()
    (root / "modified").mkdir()
    (root / "manifests").mkdir()
    manifest = WorkspaceManifest(
        revision_id=revision.revision_id,
        source_iso_size=revision.iso_size,
        source_iso_sha256=revision.iso_sha256,
        volume_id="SYNTHETIC",
        sector_size=2048,
        volume_sectors=1,
        directories=(ManifestDirectory(".", 0, 0, 0, 0),),
        files=(),
    )
    (root / "manifests" / "workspace.json").write_text(
        manifest.to_json(), encoding="utf-8"
    )


class FakeProcess:
    def __init__(self) -> None:
        self.terminated = False
        self.killed = False
        self.waited = False

    def poll(self) -> None:
        return None

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True

    def wait(self, timeout: float | None = None) -> int:
        del timeout
        self.waited = True
        return 0


class ScriptedDebugger:
    def __init__(self, hits: list[int]) -> None:
        self.hits = list(hits)
        self.current_hit = 0
        self.calls: list[tuple[str, int | None, int | None]] = []
        self.closed = False
        self.memory_reads: list[tuple[int, int]] = []

    def add_exec_breakpoint(self, address: int) -> None:
        self.calls.append(("add", address, None))

    def remove_exec_breakpoint(self, address: int) -> None:
        self.calls.append(("remove", address, None))

    def resume(self) -> int:
        self.calls.append(("resume", None, None))
        return len(self.calls)

    def wait_for_event(
        self,
        event: str,
        *,
        timeout_seconds: float | None = None,
    ) -> dict[str, object]:
        assert event == "cpu.stepping"
        assert timeout_seconds is not None
        if not self.hits:
            raise RuntimeError("script exhausted")
        self.current_hit = self.hits.pop(0)
        self.calls.append(("hit", self.current_hit, None))
        return {
            "event": "cpu.stepping",
            "pc": self.current_hit,
            "hit": {"kind": "exec", "address": self.current_hit},
        }

    def get_registers(self) -> dict[str, int]:
        self.calls.append(("registers", self.current_hit, None))
        return {
            "pc": self.current_hit,
            "ra": 0x9000,
            "sp": 0xA000,
            "a0": 1,
            "a1": 2,
            "v0": 3,
            "v1": 4,
            "t9": 0x3000,
        }

    def read_memory(self, address: int, size: int) -> bytes:
        self.memory_reads.append((address, size))
        self.calls.append(("memory", address, size))
        if address == 0x2000 and size == 4:
            return (0x3000).to_bytes(4, "little")
        if address == 0x2200 and size == 4:
            return (0x4000).to_bytes(4, "little")
        if address == 0x2204 and size == 4:
            return (12).to_bytes(4, "little")
        if address == 0x2208 and size == 4:
            return (4).to_bytes(4, "little")
        if address == 0x2104 and size == 4:
            return (4).to_bytes(4, "little")
        return bytes(((address + index) & 0xFF) for index in range(size))

    def backtrace(self) -> tuple[int, ...]:
        self.calls.append(("backtrace", self.current_hit, None))
        return (self.current_hit, 0x7777)

    def close(self) -> None:
        self.closed = True
        self.calls.append(("close", None, None))


def _inputs(tmp_path: Path) -> tuple[Task9ECaptureInputs, DebuggerBundleProfile]:
    iso_payload = b"synthetic exact iso"
    iso = tmp_path / "game.iso"
    iso.write_bytes(iso_payload)
    revision = ReferenceRevision(
        revision_id="ULUS10066-v1.00",
        disc_id="ULUS10066",
        disc_version="1.00",
        title="Synthetic",
        psp_system_version="2.60",
        iso_size=len(iso_payload),
        iso_sha256=_sha256(iso_payload),
    )
    workspace = tmp_path / "workspace"
    _write_workspace(workspace, revision)
    state = tmp_path / "capture.ppst"
    state.write_bytes(b"synthetic state")
    slot = tmp_path / "savedata-slot"
    slot.mkdir()
    (slot / "DATA.BIN").write_bytes(b"savedata")
    bundle_root = tmp_path / "bundle"
    profile = _write_bundle(bundle_root)
    return (
        Task9ECaptureInputs(
            workspace=workspace,
            bundle_root=bundle_root,
            iso=iso,
            state=state,
            savedata_slot=slot,
            plan=_plan(),
            payload_contract=_contract(),
            revision=revision,
            control_id="successful_load",
            bundle_profile=profile,
            timeout_seconds=1.0,
        ),
        profile,
    )


def _install_fake_process(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[FakeProcess, list[list[str]]]:
    process = FakeProcess()
    launches: list[list[str]] = []

    def fake_popen(argv: list[str], **kwargs: Any) -> FakeProcess:
        del kwargs
        launches.append(argv)
        return process

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    return process, launches


def test_capture_runs_locked_breakpoint_and_dynamic_callback_sequence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs, _profile = _inputs(tmp_path)
    process, launches = _install_fake_process(monkeypatch)
    debugger = ScriptedDebugger([0x1000, 0x1010, 0x1020, 0x1030, 0x3000, 0x1040])
    factory: Callable[..., ScriptedDebugger] = lambda *args, **kwargs: debugger

    capture = capture_task9e_control(inputs, client_factory=factory)

    assert isinstance(capture, RuntimeControlCapture)
    assert capture.control_id == "successful_load"
    assert capture.valid
    assert capture.iso_sha256 == inputs.revision.iso_sha256
    assert capture.state_sha256 == _sha256(b"synthetic state")
    assert [item.breakpoint_id for item in capture.observations] == [
        "load_commit_entry",
        "before_body_copy",
        "before_followup_pointer_load",
        "before_followup_call",
        "after_followup_return",
    ]
    assert capture.callback is not None
    assert capture.callback.target == _runtime(0x3000)
    assert capture.callback.backtrace == (_runtime(0x3000), _runtime(0x7777))

    assert launches == [
        [
            str(capture.bundle.launcher_path),
            str(inputs.iso),
            "--state",
            str(inputs.state),
            "--port",
            str(capture.bundle.port),
        ]
    ]
    added = [address for action, address, _size in debugger.calls if action == "add"]
    assert added == [0x1000, 0x1010, 0x1020, 0x1030, 0x1040, 0x3000]
    removed = [address for action, address, _size in debugger.calls if action == "remove"]
    assert set(removed) == {0x1000, 0x1010, 0x1020, 0x1030, 0x1040, 0x3000}
    assert debugger.closed
    assert process.terminated
    assert process.waited

    assert all(size <= inputs.payload_contract.body_capacity for _address, size in debugger.memory_reads)
    assert (0x4000, 4) in debugger.memory_reads
    assert (0x2100, inputs.payload_contract.envelope_header_size) in debugger.memory_reads


def test_iso_hash_mismatch_aborts_before_launcher(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs, _profile = _inputs(tmp_path)
    inputs.iso.write_bytes(b"wrong iso")
    _process, launches = _install_fake_process(monkeypatch)

    with pytest.raises(Task9EPlanError, match="ISO"):
        capture_task9e_control(inputs, client_factory=lambda *args, **kwargs: ScriptedDebugger([]))

    assert launches == []


def test_missing_state_aborts_before_launcher(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs, _profile = _inputs(tmp_path)
    inputs.state.unlink()
    _process, launches = _install_fake_process(monkeypatch)

    with pytest.raises(Task9EPlanError, match="state"):
        capture_task9e_control(inputs, client_factory=lambda *args, **kwargs: ScriptedDebugger([]))

    assert launches == []


def test_invalid_bundle_aborts_before_launcher(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs, _profile = _inputs(tmp_path)
    (inputs.bundle_root / "PPSSPPSDL").write_bytes(b"tampered")
    _process, launches = _install_fake_process(monkeypatch)

    with pytest.raises(ValueError, match="hash mismatch"):
        capture_task9e_control(inputs, client_factory=lambda *args, **kwargs: ScriptedDebugger([]))

    assert launches == []


def test_unexpected_breakpoint_order_fails_closed_and_cleans_up(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs, _profile = _inputs(tmp_path)
    process, _launches = _install_fake_process(monkeypatch)
    debugger = ScriptedDebugger([0x1000, 0x1020])

    with pytest.raises(Task9EPlanError, match="breakpoint"):
        capture_task9e_control(
            inputs,
            client_factory=lambda *args, **kwargs: debugger,
        )

    removed = [address for action, address, _size in debugger.calls if action == "remove"]
    assert set(removed) == {0x1000, 0x1010, 0x1020, 0x1030, 0x1040}
    assert debugger.closed
    assert process.terminated
    assert process.waited
