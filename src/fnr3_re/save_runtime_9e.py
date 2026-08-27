from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from .evidence import Address, AddressType

_LOCKED_REVISION = "ULUS10066-v1.00"
_LOCKED_BOOT_SHA256 = "906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9"
_LOCKED_MAPPING_RULE = "ppsspp_absolute = 0x08804000 + elf_virtual"
_REQUIRED_BREAKPOINT_IDS = (
    "load_commit_entry",
    "before_body_copy",
    "before_followup_pointer_load",
    "before_followup_call",
    "after_followup_return",
)
_REQUIRED_LIVE_GLOBAL_IDS = (
    "followup_callback_pointer",
    "savedata_workspace",
    "registered_destination_pointer",
    "registered_destination_size",
    "active_body_size_global",
)
_REQUIRED_CONTROL_IDS = ("successful_load", "corrupted_copy_control")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class Task9EPlanError(ValueError):
    """Raised when committed Task 9E evidence does not match the locked contract."""


@dataclass(frozen=True, slots=True)
class Task9EBreakpoint:
    id: str
    address: Address
    capture: tuple[str, ...]
    action: str | None = None


@dataclass(frozen=True, slots=True)
class Task9ELiveGlobal:
    id: str
    address: Address
    size: int | None = None


@dataclass(frozen=True, slots=True)
class Task9EPlan:
    revision_id: str
    boot_sha256: str
    mapping_rule: str
    breakpoints: tuple[Task9EBreakpoint, ...]
    live_globals: tuple[Task9ELiveGlobal, ...]
    required_control_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PayloadLifetimeContract:
    source_revision: str
    boot_sha256: str
    total_size: int
    envelope_header_size: int
    active_body_size_offset: int
    body_offset: int
    body_capacity: int


def _load_object(path: Path) -> Mapping[str, Any]:
    try:
        decoded: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Task9EPlanError(f"unable to load Task 9E evidence: {exc}") from exc
    if not isinstance(decoded, Mapping):
        raise Task9EPlanError("Task 9E evidence root must be a JSON object")
    return cast(Mapping[str, Any], decoded)


def _mapping(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise Task9EPlanError(f"{key} must be an object")
    return cast(Mapping[str, Any], value)


def _list(payload: Mapping[str, Any], key: str) -> list[Any]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise Task9EPlanError(f"{key} must be an array")
    return value


def _string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise Task9EPlanError(f"{key} must be a non-empty string")
    return value


def _integer(payload: Mapping[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise Task9EPlanError(f"{key} must be an integer")
    return value


def _sha256(payload: Mapping[str, Any], key: str) -> str:
    value = _string(payload, key)
    if _SHA256_RE.fullmatch(value) is None:
        raise Task9EPlanError(f"{key} must be a lowercase SHA-256 digest")
    return value


def _runtime_address(value: object, label: str) -> Address:
    if not isinstance(value, str):
        raise Task9EPlanError(f"{label} runtime address must be a hexadecimal string")
    try:
        parsed = int(value, 16)
    except ValueError as exc:
        raise Task9EPlanError(f"{label} has an invalid runtime address") from exc
    if not value.lower().startswith("0x") or parsed < 0:
        raise Task9EPlanError(f"{label} has an invalid runtime address")
    return Address(AddressType.RUNTIME, parsed)


def _string_tuple(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise Task9EPlanError(f"{label} must be a non-empty string array")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise Task9EPlanError(f"{label} must contain non-empty strings")
    return tuple(cast(list[str], value))


def _validate_plan_identity(payload: Mapping[str, Any]) -> tuple[str, str, str]:
    if _integer(payload, "schema_version") != 1:
        raise Task9EPlanError("unsupported Task 9E plan schema_version")
    if _integer(payload, "task") != 9:
        raise Task9EPlanError("Task 9E plan must declare task 9")
    if _string(payload, "checkpoint") != "9E":
        raise Task9EPlanError("Task 9E plan must declare checkpoint 9E")

    source = _mapping(payload, "source_revision")
    revision_id = _string(source, "id")
    module = _string(source, "module")
    boot_sha256 = _sha256(source, "sha256")
    if revision_id != _LOCKED_REVISION or module != "BOOT.BIN":
        raise Task9EPlanError("Task 9E plan revision/module identity does not match the lock")
    if boot_sha256 != _LOCKED_BOOT_SHA256:
        raise Task9EPlanError("Task 9E plan BOOT.BIN hash does not match the lock")

    mapping_rule = _string(_mapping(payload, "address_mapping"), "mapping_rule")
    if mapping_rule != _LOCKED_MAPPING_RULE:
        raise Task9EPlanError("Task 9E address mapping rule does not match the confirmed rule")
    return revision_id, boot_sha256, mapping_rule


def _load_breakpoints(payload: Mapping[str, Any]) -> tuple[Task9EBreakpoint, ...]:
    raw_breakpoints = _list(payload, "breakpoints")
    breakpoints: list[Task9EBreakpoint] = []
    for index, raw in enumerate(raw_breakpoints):
        if not isinstance(raw, Mapping):
            raise Task9EPlanError(f"breakpoints[{index}] must be an object")
        item = cast(Mapping[str, Any], raw)
        breakpoint_id = _string(item, "id")
        address = _runtime_address(item.get("address"), f"breakpoint {breakpoint_id}")
        capture = _string_tuple(item.get("capture"), f"breakpoint {breakpoint_id} capture")
        raw_action = item.get("action")
        if raw_action is not None and (
            not isinstance(raw_action, str) or not raw_action.strip()
        ):
            raise Task9EPlanError(f"breakpoint {breakpoint_id} action must be text")
        action = raw_action
        breakpoints.append(Task9EBreakpoint(breakpoint_id, address, capture, action))

    observed_ids = tuple(item.id for item in breakpoints)
    if observed_ids != _REQUIRED_BREAKPOINT_IDS:
        raise Task9EPlanError(
            "Task 9E breakpoint sequence does not match the required capture sequence"
        )
    return tuple(breakpoints)


def _load_live_globals(payload: Mapping[str, Any]) -> tuple[Task9ELiveGlobal, ...]:
    raw_globals = _mapping(payload, "live_globals")
    if tuple(raw_globals.keys()) != _REQUIRED_LIVE_GLOBAL_IDS:
        raise Task9EPlanError("Task 9E live-global set/order does not match the required contract")

    globals_: list[Task9ELiveGlobal] = []
    for global_id in _REQUIRED_LIVE_GLOBAL_IDS:
        raw = raw_globals.get(global_id)
        if not isinstance(raw, Mapping):
            raise Task9EPlanError(f"live global {global_id} must be an object")
        item = cast(Mapping[str, Any], raw)
        address = _runtime_address(item.get("ppsspp_address"), f"live global {global_id}")
        raw_size = item.get("size")
        size: int | None = None
        if raw_size is not None:
            if not isinstance(raw_size, str):
                raise Task9EPlanError(f"live global {global_id} size must be hexadecimal")
            try:
                size = int(raw_size, 16)
            except ValueError as exc:
                raise Task9EPlanError(f"live global {global_id} has invalid size") from exc
            if size <= 0:
                raise Task9EPlanError(f"live global {global_id} size must be positive")
        globals_.append(Task9ELiveGlobal(global_id, address, size))
    return tuple(globals_)


def _load_control_ids(payload: Mapping[str, Any]) -> tuple[str, ...]:
    raw_controls = _list(payload, "required_captures")
    control_ids: list[str] = []
    for index, raw in enumerate(raw_controls):
        if not isinstance(raw, Mapping):
            raise Task9EPlanError(f"required_captures[{index}] must be an object")
        item = cast(Mapping[str, Any], raw)
        control_ids.append(_string(item, "id"))
        _string(item, "precondition")
        _string_tuple(item.get("required_outputs"), f"required capture {control_ids[-1]} outputs")
    result = tuple(control_ids)
    if result != _REQUIRED_CONTROL_IDS:
        raise Task9EPlanError("Task 9E required controls do not match the approved experiment")
    return result


def load_task9e_plan(path: Path) -> Task9EPlan:
    payload = _load_object(path)
    revision_id, boot_sha256, mapping_rule = _validate_plan_identity(payload)
    return Task9EPlan(
        revision_id=revision_id,
        boot_sha256=boot_sha256,
        mapping_rule=mapping_rule,
        breakpoints=_load_breakpoints(payload),
        live_globals=_load_live_globals(payload),
        required_control_ids=_load_control_ids(payload),
    )


def load_payload_lifetime_contract(path: Path) -> PayloadLifetimeContract:
    payload = _load_object(path)
    if _integer(payload, "schema_version") != 1:
        raise Task9EPlanError("unsupported payload-lifetime schema_version")
    source_revision = _string(payload, "source_revision")
    boot_sha256 = _sha256(payload, "boot_sha256")
    if source_revision != _LOCKED_REVISION:
        raise Task9EPlanError("payload-lifetime revision does not match the Task 9E lock")
    if boot_sha256 != _LOCKED_BOOT_SHA256:
        raise Task9EPlanError("payload-lifetime BOOT.BIN hash does not match the Task 9E lock")

    workspace = _mapping(payload, "workspace")
    total_size = _integer(workspace, "total_size")
    envelope_header_size = _integer(workspace, "envelope_header_size")
    active_body_size_offset = _integer(workspace, "active_body_size_offset")
    body_offset = _integer(workspace, "body_offset")
    body_capacity = _integer(workspace, "body_capacity")
    if min(
        total_size,
        envelope_header_size,
        body_offset,
        body_capacity,
    ) <= 0 or active_body_size_offset < 0:
        raise Task9EPlanError("payload-lifetime body dimensions must be positive and bounded")
    if body_offset != envelope_header_size:
        raise Task9EPlanError("payload-lifetime body offset must equal envelope header size")
    if body_offset + body_capacity != total_size:
        raise Task9EPlanError("payload-lifetime body capacity does not fill the fixed envelope")
    if active_body_size_offset + 4 > envelope_header_size:
        raise Task9EPlanError("payload-lifetime active body size field escapes the envelope header")

    return PayloadLifetimeContract(
        source_revision=source_revision,
        boot_sha256=boot_sha256,
        total_size=total_size,
        envelope_header_size=envelope_header_size,
        active_body_size_offset=active_body_size_offset,
        body_offset=body_offset,
        body_capacity=body_capacity,
    )
