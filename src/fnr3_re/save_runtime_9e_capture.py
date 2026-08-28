from __future__ import annotations

import contextlib
import hashlib
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .evidence import Address, AddressType
from .iso import verify_workspace
from .manifests import load_workspace_manifest
from .ppsspp_bundle import DebuggerBundleIdentity, DebuggerBundleProfile, verify_ppsspp_bundle
from .ppsspp_debugger import PpssppDebuggerClient
from .revision import ReferenceRevision, hash_file
from .save_runtime_9e import (
    PayloadLifetimeContract,
    SavedataInventoryEntry,
    Task9EBreakpoint,
    Task9ELiveGlobal,
    Task9EPlan,
    Task9EPlanError,
    Task9ERuntimeSource,
    hash_savedata_slot,
)

_REGISTER_CAPTURE_NAMES = frozenset(
    {
        "pc",
        "ra",
        "sp",
        "a0",
        "a1",
        "a2",
        "a3",
        "v0",
        "v1",
        "t9",
    }
)
_CALLBACK_REGISTER_NAMES = ("pc", "ra", "sp", "a0", "a1", "v0", "v1", "t9")


class _DebuggerClient(Protocol):
    def add_exec_breakpoint(self, address: int) -> None: ...

    def remove_exec_breakpoint(self, address: int) -> None: ...

    def resume(self) -> int: ...

    def wait_for_event(
        self,
        event: str,
        *,
        timeout_seconds: float | None = None,
    ) -> dict[str, object]: ...

    def get_registers(self) -> dict[str, int]: ...

    def read_memory(self, address: int, size: int) -> bytes: ...

    def backtrace(self) -> tuple[int, ...]: ...

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class RuntimeMemoryObservation:
    id: str
    address: Address
    size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class RuntimeBreakpointObservation:
    breakpoint_id: str
    address: Address
    registers: tuple[tuple[str, int], ...]
    scalar_values: tuple[tuple[str, int], ...]
    backtrace: tuple[Address, ...]
    memory_hashes: tuple[RuntimeMemoryObservation, ...]
    uncaptured: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RuntimeCallbackObservation:
    target: Address
    registers: tuple[tuple[str, int], ...]
    backtrace: tuple[Address, ...]


@dataclass(frozen=True, slots=True)
class RuntimeControlCapture:
    control_id: str
    valid: bool
    iso_sha256: str
    state_sha256: str
    savedata_inventory: tuple[SavedataInventoryEntry, ...]
    bundle: DebuggerBundleIdentity
    observations: tuple[RuntimeBreakpointObservation, ...]
    callback: RuntimeCallbackObservation | None
    runtime_source: Task9ERuntimeSource
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Task9ECaptureInputs:
    workspace: Path
    bundle_root: Path
    iso: Path
    state: Path
    savedata_slot: Path
    plan: Task9EPlan
    payload_contract: PayloadLifetimeContract
    revision: ReferenceRevision
    control_id: str
    bundle_profile: DebuggerBundleProfile
    runtime_source: Task9ERuntimeSource | None = None
    memstick_root: Path | None = None
    timeout_seconds: float = 3.0


def _validate_input_file(path: Path, label: str) -> None:
    if path.is_symlink():
        raise Task9EPlanError(f"{label} must not be a symlink")
    if not path.exists() or not path.is_file():
        raise Task9EPlanError(f"{label} file does not exist")


def _validate_memstick(inputs: Task9ECaptureInputs) -> Path:
    memstick_root = inputs.memstick_root
    if memstick_root is None:
        raise Task9EPlanError("capture requires an explicit memstick root")
    if memstick_root.is_symlink():
        raise Task9EPlanError("memstick root must not be a symlink")
    if not memstick_root.exists() or not memstick_root.is_dir():
        raise Task9EPlanError("memstick root directory does not exist")

    expected_slot = memstick_root / "PSP" / "SAVEDATA" / inputs.savedata_slot.name
    for component in (
        memstick_root / "PSP",
        memstick_root / "PSP" / "SAVEDATA",
        expected_slot,
    ):
        if component.is_symlink():
            raise Task9EPlanError("memstick savedata path must not contain symlinks")
    try:
        expected_resolved = expected_slot.resolve(strict=True)
        supplied_resolved = inputs.savedata_slot.resolve(strict=True)
    except OSError as exc:
        raise Task9EPlanError("memstick savedata slot does not exist") from exc
    if expected_resolved != supplied_resolved:
        raise Task9EPlanError("supplied savedata slot is not inside the explicit memstick root")
    if not expected_resolved.is_dir():
        raise Task9EPlanError("memstick savedata slot must be a directory")
    return memstick_root


def _preflight(
    inputs: Task9ECaptureInputs,
) -> tuple[
    str,
    str,
    tuple[SavedataInventoryEntry, ...],
    DebuggerBundleIdentity,
    Task9ERuntimeSource,
    Path,
]:
    if inputs.timeout_seconds <= 0:
        raise Task9EPlanError("capture timeout must be positive")
    if inputs.control_id not in inputs.plan.required_control_ids:
        raise Task9EPlanError(f"unknown Task 9E control: {inputs.control_id}")
    if inputs.revision.revision_id != inputs.plan.revision_id:
        raise Task9EPlanError("capture revision does not match the Task 9E plan")
    if inputs.payload_contract.source_revision != inputs.plan.revision_id:
        raise Task9EPlanError("payload lifetime revision does not match the Task 9E plan")
    if inputs.payload_contract.boot_sha256 != inputs.plan.boot_sha256:
        raise Task9EPlanError("payload lifetime BOOT.BIN hash does not match the Task 9E plan")

    runtime_source = inputs.runtime_source
    if runtime_source is None:
        raise Task9EPlanError("capture requires explicit runtime provenance")
    if runtime_source.revision_id != inputs.revision.revision_id:
        raise Task9EPlanError("runtime provenance revision does not match capture revision")
    if runtime_source.retail_iso_sha256 != inputs.revision.iso_sha256:
        raise Task9EPlanError("runtime provenance retail ISO hash does not match capture revision")
    if runtime_source.boot_sha256 != inputs.plan.boot_sha256:
        raise Task9EPlanError("runtime provenance BOOT hash does not match the Task 9E plan")

    workspace_result = verify_workspace(inputs.workspace)
    if not workspace_result.valid:
        details = "; ".join(workspace_result.diagnostics)
        raise Task9EPlanError(f"workspace verification failed: {details}")
    manifest = load_workspace_manifest(inputs.workspace / "manifests" / "workspace.json")
    if manifest.revision_id != inputs.revision.revision_id:
        raise Task9EPlanError("workspace revision does not match capture revision")
    if manifest.source_iso_size != inputs.revision.iso_size:
        raise Task9EPlanError("workspace ISO size does not match capture revision")
    if manifest.source_iso_sha256 != inputs.revision.iso_sha256:
        raise Task9EPlanError("workspace ISO hash does not match capture revision")

    _validate_input_file(inputs.iso, "ISO")
    iso_sha256 = hash_file(inputs.iso)
    if runtime_source.source_mode == "retail_iso":
        if inputs.iso.stat().st_size != inputs.revision.iso_size:
            raise Task9EPlanError("ISO size does not match the locked revision")
        if iso_sha256 != inputs.revision.iso_sha256:
            raise Task9EPlanError("ISO SHA-256 does not match the locked revision")
    elif iso_sha256 != runtime_source.runtime_iso_sha256:
        raise Task9EPlanError("ISO SHA-256 does not match repository runtime provenance")

    _validate_input_file(inputs.state, "state")
    state_sha256 = hash_file(inputs.state)
    memstick_root = _validate_memstick(inputs)
    savedata_inventory = hash_savedata_slot(inputs.savedata_slot)
    bundle = verify_ppsspp_bundle(inputs.bundle_root, profile=inputs.bundle_profile)
    return (
        iso_sha256,
        state_sha256,
        savedata_inventory,
        bundle,
        runtime_source,
        memstick_root,
    )


def _runtime(value: int) -> Address:
    return Address(AddressType.RUNTIME, value)


def _wait_for_exec_hit(
    client: _DebuggerClient,
    expected: int,
    label: str,
    timeout_seconds: float,
) -> None:
    event = client.wait_for_event("cpu.stepping", timeout_seconds=timeout_seconds)
    hit = event.get("hit")
    if not isinstance(hit, Mapping):
        raise Task9EPlanError(f"{label} breakpoint event is missing hit metadata")
    kind = hit.get("kind")
    address = hit.get("address")
    if kind != "exec" or not isinstance(address, int) or isinstance(address, bool):
        raise Task9EPlanError(f"{label} breakpoint event is not an execution hit")
    if address != expected:
        raise Task9EPlanError(
            f"unexpected breakpoint for {label}: expected 0x{expected:08X}, "
            f"observed 0x{address:08X}"
        )


def _global_map(plan: Task9EPlan) -> dict[str, Task9ELiveGlobal]:
    return {item.id: item for item in plan.live_globals}


def _select_registers(
    client: _DebuggerClient,
    breakpoint: Task9EBreakpoint,
) -> tuple[tuple[str, int], ...]:
    requested = [name for name in breakpoint.capture if name in _REGISTER_CAPTURE_NAMES]
    if "t9_or_call_register" in breakpoint.capture:
        requested.append("t9")
    if not requested:
        return ()
    registers = client.get_registers()
    selected: list[tuple[str, int]] = []
    for name in requested:
        if name not in registers:
            raise Task9EPlanError(
                f"required register {name} missing at breakpoint {breakpoint.id}"
            )
        selected.append((name, registers[name]))
    return tuple(selected)


def _read_u32(client: _DebuggerClient, address: int) -> int:
    return int.from_bytes(client.read_memory(address, 4), "little")


def _hash_region(
    client: _DebuggerClient,
    region_id: str,
    address: int,
    size: int,
) -> RuntimeMemoryObservation:
    if address < 0 or size <= 0:
        raise Task9EPlanError(f"invalid bounded memory region: {region_id}")
    data = client.read_memory(address, size)
    return RuntimeMemoryObservation(
        id=region_id,
        address=_runtime(address),
        size=size,
        sha256=hashlib.sha256(data).hexdigest(),
    )


def _capture_memory(
    client: _DebuggerClient,
    breakpoint: Task9EBreakpoint,
    globals_by_id: dict[str, Task9ELiveGlobal],
    contract: PayloadLifetimeContract,
) -> tuple[
    tuple[tuple[str, int], ...],
    tuple[RuntimeMemoryObservation, ...],
    tuple[str, ...],
]:
    scalars: list[tuple[str, int]] = []
    regions: list[RuntimeMemoryObservation] = []
    uncaptured: list[str] = []

    scalar_globals = {
        "callback_pointer": "followup_callback_pointer",
        "registered_destination_pointer": "registered_destination_pointer",
        "registered_destination_size": "registered_destination_size",
        "active_body_size_global": "active_body_size_global",
    }
    for token, global_id in scalar_globals.items():
        if token not in breakpoint.capture:
            continue
        address = globals_by_id[global_id].address.value
        scalars.append((token, _read_u32(client, address)))

    workspace = globals_by_id["savedata_workspace"]
    if workspace.size is not None and workspace.size < contract.total_size:
        raise Task9EPlanError("savedata workspace is smaller than the payload lifetime contract")
    if "workspace_header" in breakpoint.capture:
        regions.append(
            _hash_region(
                client,
                "workspace_header",
                workspace.address.value,
                contract.envelope_header_size,
            )
        )
    if "workspace_active_body_size" in breakpoint.capture:
        size_address = workspace.address.value + contract.active_body_size_offset
        scalars.append(("workspace_active_body_size", _read_u32(client, size_address)))

    if "destination_body_hash" in breakpoint.capture:
        destination = _read_u32(
            client,
            globals_by_id["registered_destination_pointer"].address.value,
        )
        registered_size = _read_u32(
            client,
            globals_by_id["registered_destination_size"].address.value,
        )
        active_size = _read_u32(
            client,
            globals_by_id["active_body_size_global"].address.value,
        )
        if destination == 0:
            raise Task9EPlanError("destination body pointer is null")
        if active_size <= 0 or active_size > contract.body_capacity:
            raise Task9EPlanError("destination active body size is outside the validated capacity")
        if registered_size < active_size:
            raise Task9EPlanError("destination body exceeds the registered destination size")
        regions.append(
            _hash_region(client, "destination_body", destination, active_size)
        )

    for token in breakpoint.capture:
        if token == "error_state_candidates":
            uncaptured.append(token)
    return tuple(scalars), tuple(regions), tuple(uncaptured)


def _capture_fixed_observation(
    client: _DebuggerClient,
    breakpoint: Task9EBreakpoint,
    globals_by_id: dict[str, Task9ELiveGlobal],
    contract: PayloadLifetimeContract,
) -> RuntimeBreakpointObservation:
    registers = _select_registers(client, breakpoint)
    scalars, memory_hashes, uncaptured = _capture_memory(
        client, breakpoint, globals_by_id, contract
    )
    backtrace: tuple[Address, ...] = ()
    if "caller_pc" in breakpoint.capture:
        frames = client.backtrace()
        if not frames:
            raise Task9EPlanError(f"missing caller backtrace at breakpoint {breakpoint.id}")
        backtrace = tuple(_runtime(pc) for pc in frames)
        caller = frames[1] if len(frames) > 1 else frames[0]
        scalars = (*scalars, ("caller_pc", caller))
    return RuntimeBreakpointObservation(
        breakpoint_id=breakpoint.id,
        address=breakpoint.address,
        registers=registers,
        scalar_values=scalars,
        backtrace=backtrace,
        memory_hashes=memory_hashes,
        uncaptured=uncaptured,
    )


def _capture_callback(
    client: _DebuggerClient,
    target: int,
) -> RuntimeCallbackObservation:
    registers = client.get_registers()
    selected = tuple(
        (name, registers[name]) for name in _CALLBACK_REGISTER_NAMES if name in registers
    )
    frames = tuple(_runtime(pc) for pc in client.backtrace())
    if not selected or not frames:
        raise Task9EPlanError("dynamic callback entry capture is incomplete")
    return RuntimeCallbackObservation(
        target=_runtime(target),
        registers=selected,
        backtrace=frames,
    )


def _stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=3.0)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3.0)


def capture_task9e_control(
    inputs: Task9ECaptureInputs,
    *,
    client_factory: Callable[..., _DebuggerClient] = PpssppDebuggerClient,
) -> RuntimeControlCapture:
    (
        iso_sha256,
        state_sha256,
        savedata_inventory,
        bundle,
        runtime_source,
        memstick_root,
    ) = _preflight(inputs)
    argv = [
        str(bundle.launcher_path),
        str(inputs.iso),
        "--memstick",
        str(memstick_root),
        "--state",
        str(inputs.state),
        "--port",
        str(bundle.port),
    ]
    process = subprocess.Popen(
        argv,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    client: _DebuggerClient | None = None
    fixed_installed: list[int] = []
    temporary_breakpoint: int | None = None
    observations: list[RuntimeBreakpointObservation] = []
    callback: RuntimeCallbackObservation | None = None
    try:
        client = client_factory(
            bundle.host,
            bundle.port,
            timeout_seconds=inputs.timeout_seconds,
        )
        for breakpoint in inputs.plan.breakpoints:
            client.add_exec_breakpoint(breakpoint.address.value)
            fixed_installed.append(breakpoint.address.value)

        globals_by_id = _global_map(inputs.plan)
        for breakpoint in inputs.plan.breakpoints:
            client.resume()
            _wait_for_exec_hit(
                client,
                breakpoint.address.value,
                breakpoint.id,
                inputs.timeout_seconds,
            )
            observation = _capture_fixed_observation(
                client,
                breakpoint,
                globals_by_id,
                inputs.payload_contract,
            )
            observations.append(observation)

            if breakpoint.id == "before_followup_call":
                registers = dict(observation.registers)
                target = registers.get("t9")
                if target is None or target <= 0:
                    raise Task9EPlanError("dynamic followup callback target is missing or null")
                client.add_exec_breakpoint(target)
                temporary_breakpoint = target
                client.resume()
                _wait_for_exec_hit(
                    client,
                    target,
                    "dynamic callback",
                    inputs.timeout_seconds,
                )
                callback = _capture_callback(client, target)
                client.remove_exec_breakpoint(target)
                temporary_breakpoint = None

        if callback is None:
            raise Task9EPlanError("Task 9E control did not capture the dynamic callback")
        if hash_file(inputs.state) != state_sha256:
            raise Task9EPlanError("state file changed during Task 9E capture")
        if hash_savedata_slot(inputs.savedata_slot) != savedata_inventory:
            raise Task9EPlanError("savedata slot changed during Task 9E capture")

        return RuntimeControlCapture(
            control_id=inputs.control_id,
            valid=True,
            iso_sha256=iso_sha256,
            state_sha256=state_sha256,
            savedata_inventory=savedata_inventory,
            bundle=bundle,
            observations=tuple(observations),
            callback=callback,
            runtime_source=runtime_source,
        )
    finally:
        if client is not None:
            if temporary_breakpoint is not None:
                with contextlib.suppress(Exception):
                    client.remove_exec_breakpoint(temporary_breakpoint)
            for address in reversed(fixed_installed):
                with contextlib.suppress(Exception):
                    client.remove_exec_breakpoint(address)
            with contextlib.suppress(Exception):
                client.close()
        with contextlib.suppress(Exception):
            _stop_process(process)
