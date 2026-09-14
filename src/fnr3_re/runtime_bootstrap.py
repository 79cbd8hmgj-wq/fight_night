from __future__ import annotations

import contextlib
import ctypes
import ctypes.util
import hashlib
import json
import os
import shutil
import subprocess
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Protocol, cast

from .ppsspp_bundle import (
    FNR3_DEBUGGER_BUNDLE_PROFILE,
    DebuggerBundleProfile,
    verify_ppsspp_bundle,
)
from .ppsspp_debugger import PpssppDebuggerClient, PpssppDebuggerError
from .revision import hash_file
from .save_runtime_9e import (
    SavedataInventoryEntry,
    Task9EPlan,
    Task9ERuntimeSource,
    hash_savedata_slot,
)

_RUNTIME_ISO_NAME = "fight-night-runtime.iso"
_BOOTSTRAP_REPORT_RELATIVE = PurePosixPath("bootstrap/task-9e-bootstrap.json")
_LOCAL_RELATIVE = PurePosixPath("bootstrap/local")
_MEMSTICK_RELATIVE = PurePosixPath("bootstrap/local/memstick")
_STATE_RELATIVE = PurePosixPath("bootstrap/local/task9e.ppst")
_ALLOWED_BUTTONS = frozenset(
    {
        "up",
        "down",
        "left",
        "right",
        "cross",
        "circle",
        "square",
        "triangle",
        "start",
        "select",
        "l",
        "r",
    }
)


class RuntimeBootstrapError(RuntimeError):
    """Raised when a real PPSSPP bootstrap cannot be established safely."""


@dataclass(frozen=True, slots=True)
class BootstrapInputEvent:
    delay_us: int
    button: str
    duration_frames: int = 1

    def __post_init__(self) -> None:
        if (
            not isinstance(self.delay_us, int)
            or isinstance(self.delay_us, bool)
            or self.delay_us <= 0
        ):
            raise RuntimeBootstrapError("input event delay_us must be a positive integer")
        if self.button not in _ALLOWED_BUTTONS:
            raise RuntimeBootstrapError(f"unsupported bootstrap button: {self.button!r}")
        if (
            not isinstance(self.duration_frames, int)
            or isinstance(self.duration_frames, bool)
            or self.duration_frames <= 0
        ):
            raise RuntimeBootstrapError(
                "input event duration_frames must be a positive integer"
            )


@dataclass(frozen=True, slots=True)
class BootstrapInputTrace:
    trace_id: str
    events: tuple[BootstrapInputEvent, ...]
    sha256: str

    def __post_init__(self) -> None:
        if not self.trace_id:
            raise RuntimeBootstrapError("input trace_id must be non-empty")
        if not self.events:
            raise RuntimeBootstrapError("input trace must contain at least one event")
        if len(self.sha256) != 64 or any(
            character not in "0123456789abcdef" for character in self.sha256
        ):
            raise RuntimeBootstrapError("input trace sha256 must be lowercase SHA-256")


@dataclass(frozen=True, slots=True)
class Task9EBootstrapReport:
    schema_version: int
    revision_id: str
    runtime_iso_sha256: str
    payload_manifest_sha256: str
    bundle_revision: str
    bundle_sdl_sha256: str
    savedata_slot_name: str
    savedata_inventory_sha256: str
    state_sha256: str
    input_trace_sha256: str
    state_relative_path: str
    memstick_relative_path: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "bundle_revision": self.bundle_revision,
            "bundle_sdl_sha256": self.bundle_sdl_sha256,
            "input_trace_sha256": self.input_trace_sha256,
            "memstick_relative_path": self.memstick_relative_path,
            "payload_manifest_sha256": self.payload_manifest_sha256,
            "revision_id": self.revision_id,
            "runtime_iso_sha256": self.runtime_iso_sha256,
            "savedata_inventory_sha256": self.savedata_inventory_sha256,
            "savedata_slot_name": self.savedata_slot_name,
            "schema_version": self.schema_version,
            "state_relative_path": self.state_relative_path,
            "state_sha256": self.state_sha256,
        }

    def to_json(self) -> str:
        return (
            json.dumps(
                self.to_mapping(),
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n"
        )


class _BootstrapDebugger(Protocol):
    def game_status(self) -> dict[str, object]: ...

    def add_exec_breakpoint(self, address: int) -> None: ...

    def remove_exec_breakpoint(self, address: int) -> None: ...

    def run_until_time(self, relative_us: int) -> int: ...

    def press_button(self, button: str, *, duration_frames: int = 1) -> None: ...

    def resume(self) -> int: ...

    def wait_for_event(
        self,
        event: str,
        *,
        timeout_seconds: float | None = None,
    ) -> dict[str, object]: ...

    def close(self) -> None: ...


class _HostKeyInjector(Protocol):
    def press_f2(self, display_name: str) -> None: ...


class _XWindowAttributes(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("width", ctypes.c_int),
        ("height", ctypes.c_int),
        ("border_width", ctypes.c_int),
        ("depth", ctypes.c_int),
        ("visual", ctypes.c_void_p),
        ("root", ctypes.c_ulong),
        ("class_", ctypes.c_int),
        ("bit_gravity", ctypes.c_int),
        ("win_gravity", ctypes.c_int),
        ("backing_store", ctypes.c_int),
        ("backing_planes", ctypes.c_ulong),
        ("backing_pixel", ctypes.c_ulong),
        ("save_under", ctypes.c_int),
        ("colormap", ctypes.c_ulong),
        ("map_installed", ctypes.c_int),
        ("map_state", ctypes.c_int),
        ("all_event_masks", ctypes.c_long),
        ("your_event_mask", ctypes.c_long),
        ("do_not_propagate_mask", ctypes.c_long),
        ("override_redirect", ctypes.c_int),
        ("screen", ctypes.c_void_p),
    ]


class _X11HostKeyInjector:
    _MAP_IS_VIEWABLE = 2
    _REVERT_TO_PARENT = 2

    def press_f2(self, display_name: str) -> None:
        x11_name = ctypes.util.find_library("X11")
        xtst_name = ctypes.util.find_library("Xtst")
        if x11_name is None or xtst_name is None:
            raise RuntimeBootstrapError("X11/XTEST libraries are required for PPSSPP F2")
        try:
            x11 = ctypes.CDLL(x11_name)
            xtst = ctypes.CDLL(xtst_name)
        except OSError as exc:
            raise RuntimeBootstrapError(f"unable to load X11/XTEST libraries: {exc}") from exc
        self._configure_x11(x11, xtst)

        display = x11.XOpenDisplay(display_name.encode("utf-8"))
        if not display:
            raise RuntimeBootstrapError(f"unable to open X display {display_name}")
        try:
            root = int(x11.XDefaultRootWindow(display))
            window = self._find_ppsspp_window(x11, display, root)
            if window is None:
                raise RuntimeBootstrapError("unable to find a mapped PPSSPP X11 window")
            keysym = int(x11.XStringToKeysym(b"F2"))
            if keysym == 0:
                raise RuntimeBootstrapError("X11 could not resolve the F2 keysym")
            keycode = int(x11.XKeysymToKeycode(display, keysym))
            if keycode == 0:
                raise RuntimeBootstrapError("X11 could not resolve the F2 keycode")
            x11.XSetInputFocus(display, window, self._REVERT_TO_PARENT, 0)
            if not xtst.XTestFakeKeyEvent(display, keycode, 1, 0):
                raise RuntimeBootstrapError("XTEST failed to inject F2 key-down")
            if not xtst.XTestFakeKeyEvent(display, keycode, 0, 0):
                raise RuntimeBootstrapError("XTEST failed to inject F2 key-up")
            x11.XFlush(display)
        finally:
            x11.XCloseDisplay(display)

    @staticmethod
    def _configure_x11(x11: Any, xtst: Any) -> None:
        x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        x11.XOpenDisplay.restype = ctypes.c_void_p
        x11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
        x11.XDefaultRootWindow.restype = ctypes.c_ulong
        x11.XQueryTree.argtypes = [
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.POINTER(ctypes.c_ulong)),
            ctypes.POINTER(ctypes.c_uint),
        ]
        x11.XQueryTree.restype = ctypes.c_int
        x11.XFetchName.argtypes = [
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_char_p),
        ]
        x11.XFetchName.restype = ctypes.c_int
        x11.XGetWindowAttributes.argtypes = [
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.POINTER(_XWindowAttributes),
        ]
        x11.XGetWindowAttributes.restype = ctypes.c_int
        x11.XSetInputFocus.argtypes = [
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.c_int,
            ctypes.c_ulong,
        ]
        x11.XSetInputFocus.restype = ctypes.c_int
        x11.XStringToKeysym.argtypes = [ctypes.c_char_p]
        x11.XStringToKeysym.restype = ctypes.c_ulong
        x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        x11.XKeysymToKeycode.restype = ctypes.c_ubyte
        x11.XFlush.argtypes = [ctypes.c_void_p]
        x11.XFlush.restype = ctypes.c_int
        x11.XFree.argtypes = [ctypes.c_void_p]
        x11.XFree.restype = ctypes.c_int
        x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
        x11.XCloseDisplay.restype = ctypes.c_int
        xtst.XTestFakeKeyEvent.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_int,
            ctypes.c_ulong,
        ]
        xtst.XTestFakeKeyEvent.restype = ctypes.c_int

    def _find_ppsspp_window(
        self,
        x11: Any,
        display: Any,
        root: int,
    ) -> int | None:
        root_return = ctypes.c_ulong()
        parent_return = ctypes.c_ulong()
        children = ctypes.POINTER(ctypes.c_ulong)()
        child_count = ctypes.c_uint()
        if not x11.XQueryTree(
            display,
            root,
            ctypes.byref(root_return),
            ctypes.byref(parent_return),
            ctypes.byref(children),
            ctypes.byref(child_count),
        ):
            raise RuntimeBootstrapError("XQueryTree failed while locating PPSSPP")
        try:
            for index in range(child_count.value):
                window = int(children[index])
                attributes = _XWindowAttributes()
                if not x11.XGetWindowAttributes(display, window, ctypes.byref(attributes)):
                    continue
                if attributes.map_state != self._MAP_IS_VIEWABLE:
                    continue
                name = ctypes.c_char_p()
                if not x11.XFetchName(display, window, ctypes.byref(name)) or not name.value:
                    continue
                try:
                    title = name.value.decode("utf-8", errors="replace")
                finally:
                    x11.XFree(ctypes.cast(name, ctypes.c_void_p))
                if "ppsspp" in title.casefold():
                    return window
        finally:
            if children:
                x11.XFree(ctypes.cast(children, ctypes.c_void_p))
        return None


def load_bootstrap_input_trace(path: Path) -> BootstrapInputTrace:
    if path.is_symlink():
        raise RuntimeBootstrapError("bootstrap input trace must not be a symlink")
    try:
        raw = path.read_bytes()
        decoded: object = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeBootstrapError(f"unable to load bootstrap input trace: {exc}") from exc
    if not isinstance(decoded, Mapping):
        raise RuntimeBootstrapError("bootstrap input trace root must be an object")
    payload = cast(Mapping[str, object], decoded)
    expected_keys = {"schema_version", "trace_id", "events"}
    if set(payload) != expected_keys:
        raise RuntimeBootstrapError("bootstrap input trace root keys do not match schema")
    if payload.get("schema_version") != 1:
        raise RuntimeBootstrapError("unsupported bootstrap input trace schema_version")
    trace_id = payload.get("trace_id")
    if not isinstance(trace_id, str) or not trace_id:
        raise RuntimeBootstrapError("bootstrap input trace_id must be non-empty")
    raw_events = payload.get("events")
    if not isinstance(raw_events, list) or not raw_events:
        raise RuntimeBootstrapError("bootstrap input trace events must be non-empty")

    events: list[BootstrapInputEvent] = []
    for index, raw_event in enumerate(raw_events):
        if not isinstance(raw_event, Mapping):
            raise RuntimeBootstrapError(f"bootstrap input event {index} must be an object")
        event = cast(Mapping[str, object], raw_event)
        if set(event) != {"delay_us", "button", "duration_frames"}:
            raise RuntimeBootstrapError(f"bootstrap input event {index} keys do not match schema")
        delay_us = event.get("delay_us")
        button = event.get("button")
        duration_frames = event.get("duration_frames")
        if not isinstance(delay_us, int) or isinstance(delay_us, bool):
            raise RuntimeBootstrapError(f"bootstrap input event {index} has invalid delay_us")
        if not isinstance(button, str):
            raise RuntimeBootstrapError(f"bootstrap input event {index} has invalid button")
        if not isinstance(duration_frames, int) or isinstance(duration_frames, bool):
            raise RuntimeBootstrapError(
                f"bootstrap input event {index} has invalid duration_frames"
            )
        events.append(BootstrapInputEvent(delay_us, button, duration_frames))

    return BootstrapInputTrace(
        trace_id=trace_id,
        events=tuple(events),
        sha256=hashlib.sha256(raw).hexdigest(),
    )


def _validate_runtime_root(
    runtime_root: Path,
    plan: Task9EPlan,
    runtime_source: Task9ERuntimeSource,
) -> tuple[Path, Path]:
    if runtime_root.is_symlink():
        raise RuntimeBootstrapError("runtime root must not be a symlink")
    try:
        root = runtime_root.resolve(strict=True)
    except OSError as exc:
        raise RuntimeBootstrapError("runtime root does not exist") from exc
    if not root.is_dir():
        raise RuntimeBootstrapError("runtime root must be a directory")
    if runtime_source.source_mode != "repository_runtime_image":
        raise RuntimeBootstrapError("bootstrap requires repository runtime provenance")
    if runtime_source.revision_id != plan.revision_id:
        raise RuntimeBootstrapError("runtime provenance revision does not match Task 9E plan")
    if runtime_source.boot_sha256 != plan.boot_sha256:
        raise RuntimeBootstrapError("runtime provenance BOOT hash does not match Task 9E plan")
    if runtime_source.payload_manifest_sha256 is None:
        raise RuntimeBootstrapError("repository runtime provenance lacks payload manifest hash")

    runtime_iso = root / _RUNTIME_ISO_NAME
    if runtime_iso.is_symlink() or not runtime_iso.is_file():
        raise RuntimeBootstrapError("runtime ISO is missing or unsafe")
    observed_hash = hash_file(runtime_iso)
    if observed_hash != runtime_source.runtime_iso_sha256:
        raise RuntimeBootstrapError("runtime ISO hash does not match runtime provenance")
    return root, runtime_iso


def _load_entry_address(plan: Task9EPlan) -> int:
    matches = [
        breakpoint.address.value
        for breakpoint in plan.breakpoints
        if breakpoint.id == "load_commit_entry"
    ]
    if len(matches) != 1:
        raise RuntimeBootstrapError("Task 9E plan must define one load_commit_entry")
    return matches[0]


def _choose_display(candidates: tuple[int, ...]) -> tuple[int, str]:
    if not candidates:
        raise RuntimeBootstrapError("at least one X display candidate is required")
    for number in candidates:
        if number < 1:
            continue
        socket_path = Path(f"/tmp/.X11-unix/X{number}")
        lock_path = Path(f"/tmp/.X{number}-lock")
        if not socket_path.exists() and not lock_path.exists():
            return number, f":{number}"
    raise RuntimeBootstrapError("no free X display candidate is available")


def _process_alive(process: Any, label: str) -> None:
    status = process.poll()
    if status is not None:
        raise RuntimeBootstrapError(f"{label} exited before bootstrap completed: {status}")


def _connect_debugger(
    client_factory: Callable[..., Any],
    host: str,
    port: int,
    *,
    timeout_seconds: float,
    poll_interval_seconds: float,
    sleep: Callable[[float], None],
) -> _BootstrapDebugger:
    attempts = max(2, int(timeout_seconds / max(poll_interval_seconds, 0.05)) + 1)
    last_error: Exception | None = None
    for _attempt in range(attempts):
        try:
            return cast(
                _BootstrapDebugger,
                client_factory(host, port, timeout_seconds=timeout_seconds),
            )
        except (PpssppDebuggerError, OSError) as exc:
            last_error = exc
            sleep(poll_interval_seconds)
    raise RuntimeBootstrapError(f"unable to connect to PPSSPP debugger: {last_error}")


def _wait_for_exec_hit(
    client: _BootstrapDebugger,
    expected: int,
    *,
    timeout_seconds: float,
) -> None:
    event = client.wait_for_event("cpu.stepping", timeout_seconds=timeout_seconds)
    hit = event.get("hit")
    if not isinstance(hit, Mapping):
        raise RuntimeBootstrapError("load-entry stop did not report breakpoint metadata")
    kind = hit.get("kind")
    address = hit.get("address")
    if kind != "exec" or address != expected:
        raise RuntimeBootstrapError("bootstrap stopped at an unexpected breakpoint")


def _ensure_timed_stop_not_load_entry(event: Mapping[str, object], load_entry: int) -> None:
    hit = event.get("hit")
    if not isinstance(hit, Mapping):
        return
    if hit.get("kind") == "exec" and hit.get("address") == load_entry:
        raise RuntimeBootstrapError("bootstrap reached load entry before input trace completed")


def _savedata_names(memstick: Path) -> set[str]:
    root = memstick / "PSP" / "SAVEDATA"
    if root.is_symlink():
        raise RuntimeBootstrapError("savedata root must not be a symlink")
    root.mkdir(parents=True, exist_ok=True)
    result: set[str] = set()
    for path in root.iterdir():
        if path.is_symlink():
            raise RuntimeBootstrapError(f"savedata root contains a symlink: {path.name}")
        if path.is_dir():
            result.add(path.name)
    return result


def _state_files(memstick: Path) -> dict[str, Path]:
    root = memstick / "PSP" / "PPSSPP_STATE"
    if root.is_symlink():
        raise RuntimeBootstrapError("PPSSPP state root must not be a symlink")
    root.mkdir(parents=True, exist_ok=True)
    result: dict[str, Path] = {}
    for path in root.rglob("*.ppst"):
        if path.is_symlink() or not path.is_file():
            raise RuntimeBootstrapError("PPSSPP state tree contains an unsafe state path")
        result[path.relative_to(root).as_posix()] = path
    return result


def _discover_savedata_slot(
    memstick: Path,
    before: set[str],
    revision_id: str,
) -> Path:
    disc_id = revision_id.split("-", 1)[0]
    after = _savedata_names(memstick)
    candidates = sorted(
        name for name in after - before if name.casefold().startswith(disc_id.casefold())
    )
    if len(candidates) != 1:
        raise RuntimeBootstrapError(
            f"expected exactly one new Fight Night savedata slot, observed {len(candidates)}"
        )
    return memstick / "PSP" / "SAVEDATA" / candidates[0]


def _inventory_sha256(inventory: tuple[SavedataInventoryEntry, ...]) -> str:
    normalized = [
        {
            "relative_path": entry.relative_path,
            "sha256": entry.sha256,
            "size": entry.size,
        }
        for entry in inventory
    ]
    encoded = json.dumps(normalized, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _wait_for_new_stable_state(
    memstick: Path,
    before: set[str],
    *,
    timeout_seconds: float,
    poll_interval_seconds: float,
    sleep: Callable[[float], None],
) -> tuple[Path, str]:
    attempts = max(2, int(timeout_seconds / max(poll_interval_seconds, 0.05)) + 1)
    previous: tuple[str, int, str] | None = None
    for _attempt in range(attempts):
        states = _state_files(memstick)
        new_names = sorted(set(states) - before)
        if len(new_names) > 1:
            raise RuntimeBootstrapError("F2 produced more than one new PPSSPP state")
        if len(new_names) == 1:
            name = new_names[0]
            path = states[name]
            size = path.stat().st_size
            digest = hash_file(path)
            current = (name, size, digest)
            if size > 0 and previous == current:
                return path, digest
            previous = current
        sleep(poll_interval_seconds)
    raise RuntimeBootstrapError("PPSSPP did not produce one stable new .ppst state")


def _stop_process(process: Any) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=3.0)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3.0)


def _safe_bootstrap_targets(root: Path) -> tuple[Path, Path, Path]:
    bootstrap = root / "bootstrap"
    if bootstrap.is_symlink():
        raise RuntimeBootstrapError("bootstrap output path must not be a symlink")
    bootstrap.mkdir(exist_ok=True)
    local = root.joinpath(*_LOCAL_RELATIVE.parts)
    report = root.joinpath(*_BOOTSTRAP_REPORT_RELATIVE.parts)
    for target, label in ((local, "bootstrap local output"), (report, "bootstrap report")):
        if target.is_symlink():
            raise RuntimeBootstrapError(f"{label} must not be a symlink")
        if target.exists():
            raise RuntimeBootstrapError(f"{label} already exists")
        resolved = target.resolve(strict=False)
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise RuntimeBootstrapError(f"{label} escapes runtime root") from exc
    return bootstrap, local, report


def _finalize_bootstrap(
    root: Path,
    bootstrap: Path,
    source_memstick: Path,
    source_state: Path,
    report: Task9EBootstrapReport,
    savedata_inventory: tuple[SavedataInventoryEntry, ...],
    state_sha256: str,
) -> None:
    token = uuid.uuid4().hex
    local_temp = bootstrap / f".local.task9e-{token}"
    report_temp = bootstrap / f".task-9e-bootstrap.json.task9e-{token}"
    local_target = root.joinpath(*_LOCAL_RELATIVE.parts)
    report_target = root.joinpath(*_BOOTSTRAP_REPORT_RELATIVE.parts)
    try:
        local_temp.mkdir()
        shutil.copytree(source_memstick, local_temp / "memstick")
        shutil.copy2(source_state, local_temp / "task9e.ppst")
        if hash_savedata_slot(
            source_memstick / "PSP" / "SAVEDATA" / report.savedata_slot_name
        ) != savedata_inventory:
            raise RuntimeBootstrapError("source savedata changed during bootstrap finalization")
        if hash_file(source_state) != state_sha256:
            raise RuntimeBootstrapError("source PPSSPP state changed during bootstrap finalization")
        report_temp.write_text(report.to_json(), encoding="utf-8")
        os.replace(local_temp, local_target)
        try:
            os.replace(report_temp, report_target)
        except Exception:
            shutil.rmtree(local_target, ignore_errors=True)
            raise
    finally:
        shutil.rmtree(local_temp, ignore_errors=True)
        with contextlib.suppress(OSError):
            report_temp.unlink()


def prepare_task9e_bootstrap(
    runtime_root: Path,
    bundle_root: Path,
    trace: BootstrapInputTrace,
    plan: Task9EPlan,
    runtime_source: Task9ERuntimeSource,
    *,
    bundle_profile: DebuggerBundleProfile = FNR3_DEBUGGER_BUNDLE_PROFILE,
    popen_factory: Callable[..., Any] = subprocess.Popen,
    client_factory: Callable[..., Any] = PpssppDebuggerClient,
    host_key_injector: _HostKeyInjector | None = None,
    display_candidates: tuple[int, ...] = tuple(range(90, 100)),
    timeout_seconds: float = 10.0,
    poll_interval_seconds: float = 0.1,
    sleep: Callable[[float], None] = time.sleep,
) -> Task9EBootstrapReport:
    if timeout_seconds <= 0:
        raise RuntimeBootstrapError("bootstrap timeout must be positive")
    if poll_interval_seconds < 0:
        raise RuntimeBootstrapError("bootstrap poll interval must not be negative")

    bundle = verify_ppsspp_bundle(bundle_root, profile=bundle_profile)
    root, runtime_iso = _validate_runtime_root(runtime_root, plan, runtime_source)
    bootstrap, _local_target, _report_target = _safe_bootstrap_targets(root)
    load_entry = _load_entry_address(plan)
    display_number, display_name = _choose_display(display_candidates)
    del display_number

    session = bootstrap / f".session-{uuid.uuid4().hex}"
    memstick = session / "memstick"
    savedata_root = memstick / "PSP" / "SAVEDATA"
    state_root = memstick / "PSP" / "PPSSPP_STATE"
    savedata_root.mkdir(parents=True)
    state_root.mkdir(parents=True)
    before_savedata = _savedata_names(memstick)
    before_states = set(_state_files(memstick))

    xvfb_env = dict(os.environ)
    xvfb_env.pop("DISPLAY", None)
    sdl_env = dict(os.environ)
    sdl_env["DISPLAY"] = display_name
    xvfb_argv = [
        str(bundle.xvfb_path),
        display_name,
        "-screen",
        "0",
        "960x544x24",
        "-nolisten",
        "tcp",
    ]
    sdl_argv = [
        str(bundle.sdl_path),
        f"--config={bundle.config_path}",
        "--memstick",
        str(memstick),
        str(runtime_iso),
    ]

    xvfb_process: Any | None = None
    sdl_process: Any | None = None
    debugger: _BootstrapDebugger | None = None
    breakpoint_installed = False
    savedata_inventory: tuple[SavedataInventoryEntry, ...] | None = None
    source_state: Path | None = None
    state_sha256: str | None = None
    slot: Path | None = None
    try:
        xvfb_process = popen_factory(
            xvfb_argv,
            env=xvfb_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _process_alive(xvfb_process, "Xvfb")
        sdl_process = popen_factory(
            sdl_argv,
            env=sdl_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _process_alive(sdl_process, "PPSSPPSDL")
        debugger = _connect_debugger(
            client_factory,
            bundle.host,
            bundle.port,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
            sleep=sleep,
        )
        status = debugger.game_status()
        if not status.get("game") or not status.get("path"):
            raise RuntimeBootstrapError("PPSSPP did not report a running game path")

        debugger.add_exec_breakpoint(load_entry)
        breakpoint_installed = True
        for event in trace.events:
            debugger.run_until_time(event.delay_us)
            stop = debugger.wait_for_event(
                "cpu.stepping",
                timeout_seconds=timeout_seconds,
            )
            _ensure_timed_stop_not_load_entry(stop, load_entry)
            debugger.press_button(
                event.button,
                duration_frames=event.duration_frames,
            )

        debugger.resume()
        _wait_for_exec_hit(
            debugger,
            load_entry,
            timeout_seconds=timeout_seconds,
        )
        slot = _discover_savedata_slot(memstick, before_savedata, plan.revision_id)
        savedata_inventory = hash_savedata_slot(slot)
        if not savedata_inventory:
            raise RuntimeBootstrapError("Fight Night savedata slot is empty")

        injector = _X11HostKeyInjector() if host_key_injector is None else host_key_injector
        injector.press_f2(display_name)
        source_state, state_sha256 = _wait_for_new_stable_state(
            memstick,
            before_states,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
            sleep=sleep,
        )
    finally:
        if debugger is not None:
            if breakpoint_installed:
                with contextlib.suppress(Exception):
                    debugger.remove_exec_breakpoint(load_entry)
            with contextlib.suppress(Exception):
                debugger.close()
        if sdl_process is not None:
            with contextlib.suppress(Exception):
                _stop_process(sdl_process)
        if xvfb_process is not None:
            with contextlib.suppress(Exception):
                _stop_process(xvfb_process)

    if slot is None or savedata_inventory is None or source_state is None or state_sha256 is None:
        shutil.rmtree(session, ignore_errors=True)
        raise RuntimeBootstrapError("bootstrap ended without complete save/state evidence")

    payload_manifest_sha256 = runtime_source.payload_manifest_sha256
    if payload_manifest_sha256 is None:
        shutil.rmtree(session, ignore_errors=True)
        raise RuntimeBootstrapError("runtime provenance lost payload manifest identity")
    report = Task9EBootstrapReport(
        schema_version=1,
        revision_id=plan.revision_id,
        runtime_iso_sha256=runtime_source.runtime_iso_sha256,
        payload_manifest_sha256=payload_manifest_sha256,
        bundle_revision=bundle.revision,
        bundle_sdl_sha256=bundle.sdl_sha256,
        savedata_slot_name=slot.name,
        savedata_inventory_sha256=_inventory_sha256(savedata_inventory),
        state_sha256=state_sha256,
        input_trace_sha256=trace.sha256,
        state_relative_path=_STATE_RELATIVE.as_posix(),
        memstick_relative_path=_MEMSTICK_RELATIVE.as_posix(),
    )
    try:
        _finalize_bootstrap(
            root,
            bootstrap,
            memstick,
            source_state,
            report,
            savedata_inventory,
            state_sha256,
        )
    finally:
        shutil.rmtree(session, ignore_errors=True)
    return report
