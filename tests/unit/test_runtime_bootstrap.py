from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from fnr3_re.evidence import Address, AddressType
from fnr3_re.ppsspp_bundle import DebuggerBundleProfile, PpssppBundleError
from fnr3_re.runtime_bootstrap import (
    BootstrapInputEvent,
    BootstrapInputTrace,
    RuntimeBootstrapError,
    load_bootstrap_input_trace,
    prepare_task9e_bootstrap,
)
from fnr3_re.save_runtime_9e import (
    Task9EBreakpoint,
    Task9ELiveGlobal,
    Task9EPlan,
    Task9ERuntimeSource,
)

_BOOT_SHA256 = "906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9"
_RETAIL_SHA256 = "9" * 64
_MANIFEST_SHA256 = "8" * 64


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
            Task9EBreakpoint("load_commit_entry", _runtime(0x08B44F64), ("pc",)),
            Task9EBreakpoint("before_body_copy", _runtime(0x08B44FC0), ("pc",)),
            Task9EBreakpoint(
                "before_followup_pointer_load",
                _runtime(0x08B45008),
                ("pc",),
            ),
            Task9EBreakpoint("before_followup_call", _runtime(0x08B45020), ("pc",)),
            Task9EBreakpoint("after_followup_return", _runtime(0x08B45028), ("pc",)),
        ),
        live_globals=(
            Task9ELiveGlobal("followup_callback_pointer", _runtime(0x08DBEF10)),
            Task9ELiveGlobal("savedata_workspace", _runtime(0x08DBEE58), 0x17838),
            Task9ELiveGlobal("registered_destination_pointer", _runtime(0x08DBEF18)),
            Task9ELiveGlobal("registered_destination_size", _runtime(0x08DBEF1C)),
            Task9ELiveGlobal("active_body_size_global", _runtime(0x08DBEF20)),
        ),
        required_control_ids=("successful_load", "corrupted_copy_control"),
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
        "fixture-revision\n",
        encoding="utf-8",
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


def _runtime_root(tmp_path: Path) -> tuple[Path, Task9ERuntimeSource]:
    root = tmp_path / "runtime"
    root.mkdir()
    payload = b"runtime iso fixture"
    (root / "fight-night-runtime.iso").write_bytes(payload)
    source = Task9ERuntimeSource.repository_image(
        revision_id="ULUS10066-v1.00",
        retail_iso_sha256=_RETAIL_SHA256,
        runtime_iso_sha256=_sha256(payload),
        payload_manifest_sha256=_MANIFEST_SHA256,
        boot_sha256=_BOOT_SHA256,
    )
    return root, source


def _trace() -> BootstrapInputTrace:
    events = (BootstrapInputEvent(delay_us=250_000, button="cross", duration_frames=2),)
    payload = {
        "schema_version": 1,
        "trace_id": "fixture-trace",
        "events": [
            {"delay_us": 250_000, "button": "cross", "duration_frames": 2}
        ],
    }
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    return BootstrapInputTrace(
        trace_id="fixture-trace",
        events=events,
        sha256=_sha256(encoded),
    )


class FakeProcess:
    def __init__(self, argv: list[str]) -> None:
        self.argv = argv
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


class FakeDebugger:
    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state
        self.calls: list[tuple[object, ...]] = []
        self.events: list[dict[str, object]] = [
            {"event": "cpu.stepping", "reason": "time"},
            {
                "event": "cpu.stepping",
                "hit": {"kind": "exec", "address": 0x08B44F64},
                "pc": 0x08B44F64,
            },
        ]
        self.closed = False

    def game_status(self) -> dict[str, object]:
        self.calls.append(("game_status",))
        return {"game": "running", "path": "disc0:/PSP_GAME/SYSDIR/EBOOT.BIN"}

    def add_exec_breakpoint(self, address: int) -> None:
        self.calls.append(("add", address))

    def remove_exec_breakpoint(self, address: int) -> None:
        self.calls.append(("remove", address))

    def run_until_time(self, relative_us: int) -> int:
        self.calls.append(("run_until_time", relative_us))
        return 1

    def press_button(self, button: str, *, duration_frames: int = 1) -> None:
        self.calls.append(("press", button, duration_frames))
        memstick = Path(self.state["memstick"])
        slot = memstick / "PSP" / "SAVEDATA" / "ULUS10066PROFILE"
        slot.mkdir(parents=True, exist_ok=True)
        (slot / "DATA.BIN").write_bytes(b"real save fixture")
        (slot / "PARAM.SFO").write_bytes(b"sfo fixture")

    def resume(self) -> int:
        self.calls.append(("resume",))
        return 2

    def wait_for_event(
        self,
        event: str,
        *,
        timeout_seconds: float | None = None,
    ) -> dict[str, object]:
        self.calls.append(("wait", event, timeout_seconds))
        assert event == "cpu.stepping"
        return self.events.pop(0)

    def close(self) -> None:
        self.closed = True
        self.calls.append(("close",))


class FakeHostKeyInjector:
    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state
        self.displays: list[str] = []

    def press_f2(self, display_name: str) -> None:
        self.displays.append(display_name)
        memstick = Path(self.state["memstick"])
        state_root = memstick / "PSP" / "PPSSPP_STATE"
        state_root.mkdir(parents=True, exist_ok=True)
        (state_root / "ULUS10066_1.00_0.ppst").write_bytes(b"ppst fixture")


def test_load_bootstrap_trace_is_exact_and_hashed(tmp_path: Path) -> None:
    path = tmp_path / "trace.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "trace_id": "locked",
                "events": [
                    {
                        "delay_us": 1000,
                        "button": "cross",
                        "duration_frames": 1,
                    }
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    trace = load_bootstrap_input_trace(path)

    assert trace.trace_id == "locked"
    assert trace.events == (
        BootstrapInputEvent(delay_us=1000, button="cross", duration_frames=1),
    )
    assert trace.sha256 == _sha256(path.read_bytes())

    invalid = tmp_path / "invalid.json"
    invalid.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "trace_id": "locked",
                "events": [],
                "unexpected": True,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeBootstrapError, match="keys"):
        load_bootstrap_input_trace(invalid)


def test_bootstrap_uses_verified_bundle_trace_breakpoint_and_f2(tmp_path: Path) -> None:
    runtime_root, runtime_source = _runtime_root(tmp_path)
    bundle_root = tmp_path / "bundle"
    profile = _write_bundle(bundle_root)
    state: dict[str, Any] = {}
    launches: list[tuple[list[str], dict[str, str]]] = []
    processes: list[FakeProcess] = []

    def popen_factory(argv: list[str], **kwargs: Any) -> FakeProcess:
        env = kwargs.get("env")
        assert isinstance(env, dict)
        launches.append((list(argv), dict(env)))
        process = FakeProcess(list(argv))
        processes.append(process)
        if "--memstick" in argv:
            state["memstick"] = argv[argv.index("--memstick") + 1]
        return process

    debugger = FakeDebugger(state)
    injector = FakeHostKeyInjector(state)

    report = prepare_task9e_bootstrap(
        runtime_root,
        bundle_root,
        _trace(),
        _plan(),
        runtime_source,
        bundle_profile=profile,
        popen_factory=popen_factory,
        client_factory=lambda *args, **kwargs: debugger,
        host_key_injector=injector,
        display_candidates=(93,),
        timeout_seconds=1.0,
        poll_interval_seconds=0.0,
        sleep=lambda _seconds: None,
    )

    assert len(launches) == 2
    xvfb_argv, xvfb_env = launches[0]
    assert xvfb_argv == [
        str(bundle_root.resolve() / "bin" / "Xvfb"),
        ":93",
        "-screen",
        "0",
        "960x544x24",
        "-nolisten",
        "tcp",
    ]
    assert "DISPLAY" not in xvfb_env

    sdl_argv, sdl_env = launches[1]
    assert sdl_argv[0] == str(bundle_root.resolve() / "PPSSPPSDL")
    assert sdl_argv[1] == f"--config={bundle_root.resolve() / 'ppsspp-debug.ini'}"
    assert sdl_argv[2] == "--memstick"
    assert Path(sdl_argv[3]).name == "memstick"
    assert sdl_argv[4] == str(runtime_root / "fight-night-runtime.iso")
    assert sdl_env["DISPLAY"] == ":93"

    assert ("game_status",) in debugger.calls
    assert ("add", 0x08B44F64) in debugger.calls
    assert ("run_until_time", 250_000) in debugger.calls
    assert ("press", "cross", 2) in debugger.calls
    assert ("resume",) in debugger.calls
    assert ("remove", 0x08B44F64) in debugger.calls
    assert injector.displays == [":93"]
    assert debugger.closed
    assert all(process.terminated and process.waited for process in processes)

    assert report.schema_version == 1
    assert report.revision_id == "ULUS10066-v1.00"
    assert report.runtime_iso_sha256 == runtime_source.runtime_iso_sha256
    assert report.payload_manifest_sha256 == _MANIFEST_SHA256
    assert report.bundle_revision == "fixture-revision"
    assert report.bundle_sdl_sha256 == profile.sdl_sha256
    assert report.savedata_slot_name == "ULUS10066PROFILE"
    assert len(report.savedata_inventory_sha256) == 64
    assert report.state_sha256 == _sha256(b"ppst fixture")
    assert report.input_trace_sha256 == _trace().sha256
    assert report.state_relative_path == "bootstrap/local/task9e.ppst"
    assert report.memstick_relative_path == "bootstrap/local/memstick"

    final_memstick = runtime_root / report.memstick_relative_path
    assert (final_memstick / "PSP/SAVEDATA/ULUS10066PROFILE/DATA.BIN").read_bytes() == (
        b"real save fixture"
    )
    assert (runtime_root / report.state_relative_path).read_bytes() == b"ppst fixture"
    report_path = runtime_root / "bootstrap/task-9e-bootstrap.json"
    assert json.loads(report_path.read_text(encoding="utf-8"))["state_sha256"] == (
        report.state_sha256
    )
    encoded = report.to_json()
    assert str(tmp_path) not in encoded
    assert "ppst fixture" not in encoded
    assert "real save fixture" not in encoded


def test_bundle_failure_aborts_before_any_process_launch(tmp_path: Path) -> None:
    runtime_root, runtime_source = _runtime_root(tmp_path)
    bundle_root = tmp_path / "bundle"
    profile = _write_bundle(bundle_root)
    (bundle_root / "PPSSPPSDL").write_bytes(b"tampered")
    launches: list[list[str]] = []

    with pytest.raises(PpssppBundleError, match="hash mismatch"):
        prepare_task9e_bootstrap(
            runtime_root,
            bundle_root,
            _trace(),
            _plan(),
            runtime_source,
            bundle_profile=profile,
            popen_factory=lambda argv, **kwargs: launches.append(list(argv)),
            display_candidates=(93,),
        )

    assert launches == []


def test_runtime_hash_mismatch_aborts_before_launch(tmp_path: Path) -> None:
    runtime_root, runtime_source = _runtime_root(tmp_path)
    bundle_root = tmp_path / "bundle"
    profile = _write_bundle(bundle_root)
    (runtime_root / "fight-night-runtime.iso").write_bytes(b"tampered runtime")
    launches: list[list[str]] = []

    with pytest.raises(RuntimeBootstrapError, match="runtime ISO"):
        prepare_task9e_bootstrap(
            runtime_root,
            bundle_root,
            _trace(),
            _plan(),
            runtime_source,
            bundle_profile=profile,
            popen_factory=lambda argv, **kwargs: launches.append(list(argv)),
            display_candidates=(93,),
        )

    assert launches == []
