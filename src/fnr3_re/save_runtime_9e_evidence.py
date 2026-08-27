from __future__ import annotations

import json
import os
import shutil
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .evidence import Address
from .ppsspp_debugger import PpssppDebuggerClient
from .save_runtime_9e import (
    SaveMutation,
    SavedataInventoryEntry,
    Task9EPlan,
    Task9EPlanError,
)
from .save_runtime_9e_capture import (
    RuntimeBreakpointObservation,
    RuntimeControlCapture,
    RuntimeMemoryObservation,
    Task9ECaptureInputs,
    capture_task9e_control,
)

_EVIDENCE_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class Task9EFirstDivergence:
    fact: str
    observation_id: str | None
    field: str | None
    control_a: str | int | bool | None
    control_b: str | int | bool | None

    def to_mapping(self) -> dict[str, object]:
        return {
            "control_a": self.control_a,
            "control_b": self.control_b,
            "fact": self.fact,
            "field": self.field,
            "observation_id": self.observation_id,
        }


@dataclass(frozen=True, slots=True)
class Task9ERuntimeEvidence:
    revision_id: str
    iso_sha256: str
    boot_sha256: str
    state_sha256: str
    successful: RuntimeControlCapture
    corrupted: RuntimeControlCapture
    mutation: SaveMutation
    first_divergence: Task9EFirstDivergence | None
    runtime_observed: tuple[str, ...]
    static_correlated: tuple[str, ...]
    semantic_interpretation: tuple[str, ...]
    confirmed: tuple[str, ...]
    not_confirmed: tuple[str, ...]
    warnings: tuple[str, ...]
    schema_version: int = _EVIDENCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != _EVIDENCE_SCHEMA_VERSION:
            raise Task9EPlanError(
                f"unsupported Task 9E runtime evidence schema: {self.schema_version}"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "boot_sha256": self.boot_sha256,
            "bundle": _bundle_mapping(self.successful),
            "confirmed": list(self.confirmed),
            "corrupted": _control_mapping(self.corrupted),
            "first_divergence": (
                None
                if self.first_divergence is None
                else self.first_divergence.to_mapping()
            ),
            "iso_sha256": self.iso_sha256,
            "mutation": _mutation_mapping(self.mutation),
            "not_confirmed": list(self.not_confirmed),
            "revision_id": self.revision_id,
            "runtime_observed": list(self.runtime_observed),
            "schema_version": self.schema_version,
            "semantic_interpretation": list(self.semantic_interpretation),
            "state_sha256": self.state_sha256,
            "static_correlated": list(self.static_correlated),
            "successful": _control_mapping(self.successful),
            "warnings": list(self.warnings),
        }

    def to_json(self) -> str:
        return _json(self.to_mapping())


def _json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _address_mapping(address: Address) -> dict[str, object]:
    return {
        "address_type": address.address_type.value,
        "value": address.value,
    }


def _inventory_mapping(
    inventory: tuple[SavedataInventoryEntry, ...],
) -> list[dict[str, object]]:
    return [
        {
            "relative_path": entry.relative_path,
            "sha256": entry.sha256,
            "size": entry.size,
        }
        for entry in inventory
    ]


def _memory_mapping(observation: RuntimeMemoryObservation) -> dict[str, object]:
    return {
        "address": _address_mapping(observation.address),
        "id": observation.id,
        "sha256": observation.sha256,
        "size": observation.size,
    }


def _breakpoint_mapping(
    observation: RuntimeBreakpointObservation,
) -> dict[str, object]:
    return {
        "address": _address_mapping(observation.address),
        "backtrace": [_address_mapping(address) for address in observation.backtrace],
        "breakpoint_id": observation.breakpoint_id,
        "memory_hashes": [
            _memory_mapping(memory) for memory in observation.memory_hashes
        ],
        "registers": [[name, value] for name, value in observation.registers],
        "scalar_values": [[name, value] for name, value in observation.scalar_values],
        "uncaptured": list(observation.uncaptured),
    }


def _callback_mapping(control: RuntimeControlCapture) -> dict[str, object] | None:
    callback = control.callback
    if callback is None:
        return None
    return {
        "backtrace": [_address_mapping(address) for address in callback.backtrace],
        "registers": [[name, value] for name, value in callback.registers],
        "target": _address_mapping(callback.target),
    }


def _control_mapping(control: RuntimeControlCapture) -> dict[str, object]:
    return {
        "callback": _callback_mapping(control),
        "control_id": control.control_id,
        "diagnostics": list(control.diagnostics),
        "iso_sha256": control.iso_sha256,
        "observations": [
            _breakpoint_mapping(observation) for observation in control.observations
        ],
        "savedata_inventory": _inventory_mapping(control.savedata_inventory),
        "state_sha256": control.state_sha256,
        "valid": control.valid,
    }


def _bundle_mapping(control: RuntimeControlCapture) -> dict[str, object]:
    bundle = control.bundle
    return {
        "headless_sha256": bundle.headless_sha256,
        "revision": bundle.revision,
        "sdl_sha256": bundle.sdl_sha256,
        "xvfb_sha256": bundle.xvfb_sha256,
    }


def _mutation_mapping(mutation: SaveMutation) -> dict[str, object]:
    return {
        "mutated_inventory": _inventory_mapping(mutation.mutated_inventory),
        "mutated_sha256": mutation.mutated_sha256,
        "offset": mutation.offset,
        "original_byte": mutation.original_byte,
        "relative_path": mutation.relative_path,
        "replacement_byte": mutation.replacement_byte,
        "source_inventory": _inventory_mapping(mutation.source_inventory),
        "source_sha256": mutation.source_sha256,
    }


def _bundle_key(control: RuntimeControlCapture) -> tuple[str, str, str, str]:
    bundle = control.bundle
    return (
        bundle.revision,
        bundle.sdl_sha256,
        bundle.headless_sha256,
        bundle.xvfb_sha256,
    )


def _validate_control_pair(
    success: RuntimeControlCapture,
    corrupted: RuntimeControlCapture,
    plan: Task9EPlan,
    mutation: SaveMutation,
) -> None:
    if success.control_id != "successful_load":
        raise Task9EPlanError("successful control has the wrong control_id")
    if corrupted.control_id != "corrupted_copy_control":
        raise Task9EPlanError("corrupted control has the wrong control_id")
    if not success.valid or not corrupted.valid:
        raise Task9EPlanError("both Task 9E controls must be valid before comparison")
    if success.iso_sha256 != corrupted.iso_sha256:
        raise Task9EPlanError("Task 9E controls use different ISO identities")
    if success.state_sha256 != corrupted.state_sha256:
        raise Task9EPlanError("Task 9E controls use different state identities")
    if _bundle_key(success) != _bundle_key(corrupted):
        raise Task9EPlanError("Task 9E controls use different debugger bundle identities")
    if success.savedata_inventory != mutation.source_inventory:
        raise Task9EPlanError("successful control inventory does not match mutation source")
    if corrupted.savedata_inventory != mutation.mutated_inventory:
        raise Task9EPlanError("corrupted control inventory does not match mutation output")

    expected = tuple((item.id, item.address.value) for item in plan.breakpoints)
    for label, control in (("successful", success), ("corrupted", corrupted)):
        observed = tuple(
            (item.breakpoint_id, item.address.value) for item in control.observations
        )
        if observed != expected:
            raise Task9EPlanError(
                f"{label} control observation sequence does not match Task 9E plan"
            )


def _sequence_divergence(
    success: RuntimeControlCapture,
    corrupted: RuntimeControlCapture,
) -> Task9EFirstDivergence | None:
    left = tuple(
        (item.breakpoint_id, item.address.value) for item in success.observations
    )
    right = tuple(
        (item.breakpoint_id, item.address.value) for item in corrupted.observations
    )
    if left == right:
        return None
    limit = max(len(left), len(right))
    for index in range(limit):
        left_item = left[index] if index < len(left) else None
        right_item = right[index] if index < len(right) else None
        if left_item == right_item:
            continue
        observation_id = None
        if left_item is not None:
            observation_id = left_item[0]
        elif right_item is not None:
            observation_id = right_item[0]
        return Task9EFirstDivergence(
            fact="breakpoint_sequence",
            observation_id=observation_id,
            field=None,
            control_a=None if left_item is None else f"{left_item[0]}@0x{left_item[1]:08X}",
            control_b=None if right_item is None else f"{right_item[0]}@0x{right_item[1]:08X}",
        )
    return None


def _callback_divergence(
    success: RuntimeControlCapture,
    corrupted: RuntimeControlCapture,
) -> Task9EFirstDivergence | None:
    left = None if success.callback is None else success.callback.target.value
    right = None if corrupted.callback is None else corrupted.callback.target.value
    if left == right:
        return None
    return Task9EFirstDivergence(
        fact="callback_target",
        observation_id="before_followup_call",
        field="target",
        control_a=left,
        control_b=right,
    )


def _register_divergence(
    success: RuntimeControlCapture,
    corrupted: RuntimeControlCapture,
) -> Task9EFirstDivergence | None:
    for left, right in zip(success.observations, corrupted.observations, strict=True):
        left_registers = dict(left.registers)
        right_registers = dict(right.registers)
        ordered_names = tuple(
            dict.fromkeys(
                [name for name, _value in left.registers]
                + [name for name, _value in right.registers]
            )
        )
        for name in ordered_names:
            left_value = left_registers.get(name)
            right_value = right_registers.get(name)
            if left_value != right_value:
                return Task9EFirstDivergence(
                    fact="register_value",
                    observation_id=left.breakpoint_id,
                    field=name,
                    control_a=left_value,
                    control_b=right_value,
                )

        left_scalars = dict(left.scalar_values)
        right_scalars = dict(right.scalar_values)
        ordered_scalars = tuple(
            dict.fromkeys(
                [name for name, _value in left.scalar_values]
                + [name for name, _value in right.scalar_values]
            )
        )
        for name in ordered_scalars:
            left_value = left_scalars.get(name)
            right_value = right_scalars.get(name)
            if left_value != right_value:
                return Task9EFirstDivergence(
                    fact="scalar_value",
                    observation_id=left.breakpoint_id,
                    field=name,
                    control_a=left_value,
                    control_b=right_value,
                )
    return None


def _memory_divergence(
    success: RuntimeControlCapture,
    corrupted: RuntimeControlCapture,
) -> Task9EFirstDivergence | None:
    for left, right in zip(success.observations, corrupted.observations, strict=True):
        left_memory = {item.id: item for item in left.memory_hashes}
        right_memory = {item.id: item for item in right.memory_hashes}
        ordered_ids = tuple(
            dict.fromkeys(
                [item.id for item in left.memory_hashes]
                + [item.id for item in right.memory_hashes]
            )
        )
        for memory_id in ordered_ids:
            left_item = left_memory.get(memory_id)
            right_item = right_memory.get(memory_id)
            left_value = None if left_item is None else left_item.sha256
            right_value = None if right_item is None else right_item.sha256
            if left_value != right_value:
                return Task9EFirstDivergence(
                    fact="memory_hash",
                    observation_id=left.breakpoint_id,
                    field=memory_id,
                    control_a=left_value,
                    control_b=right_value,
                )
            if left_item is not None and right_item is not None:
                left_shape = (left_item.address.value, left_item.size)
                right_shape = (right_item.address.value, right_item.size)
                if left_shape != right_shape:
                    return Task9EFirstDivergence(
                        fact="memory_region",
                        observation_id=left.breakpoint_id,
                        field=memory_id,
                        control_a=f"0x{left_shape[0]:08X}+{left_shape[1]}",
                        control_b=f"0x{right_shape[0]:08X}+{right_shape[1]}",
                    )
    return None


def _outcome_divergence(
    success: RuntimeControlCapture,
    corrupted: RuntimeControlCapture,
) -> Task9EFirstDivergence | None:
    if success.valid != corrupted.valid:
        return Task9EFirstDivergence(
            fact="control_outcome",
            observation_id=None,
            field="valid",
            control_a=success.valid,
            control_b=corrupted.valid,
        )
    if success.diagnostics != corrupted.diagnostics:
        return Task9EFirstDivergence(
            fact="error_route",
            observation_id=None,
            field="diagnostics",
            control_a=" | ".join(success.diagnostics),
            control_b=" | ".join(corrupted.diagnostics),
        )
    return None


def _first_divergence(
    success: RuntimeControlCapture,
    corrupted: RuntimeControlCapture,
) -> Task9EFirstDivergence | None:
    for comparator in (
        _sequence_divergence,
        _callback_divergence,
        _register_divergence,
        _memory_divergence,
        _outcome_divergence,
    ):
        divergence = comparator(success, corrupted)
        if divergence is not None:
            return divergence
    return None


def _capture_warnings(
    success: RuntimeControlCapture,
    corrupted: RuntimeControlCapture,
    first_divergence: Task9EFirstDivergence | None,
) -> tuple[str, ...]:
    warnings: list[str] = []
    for control in (success, corrupted):
        for observation in control.observations:
            for token in observation.uncaptured:
                warnings.append(
                    f"{control.control_id}:{observation.breakpoint_id} did not normalize {token}."
                )
    if first_divergence is None:
        warnings.append("No divergence was observed through the captured Task 9E facts.")
    return tuple(warnings)


def compare_task9e_controls(
    success: RuntimeControlCapture,
    corrupted: RuntimeControlCapture,
    *,
    plan: Task9EPlan,
    mutation: SaveMutation,
) -> Task9ERuntimeEvidence:
    _validate_control_pair(success, corrupted, plan, mutation)
    divergence = _first_divergence(success, corrupted)
    warnings = _capture_warnings(success, corrupted, divergence)

    return Task9ERuntimeEvidence(
        revision_id=plan.revision_id,
        iso_sha256=success.iso_sha256,
        boot_sha256=plan.boot_sha256,
        state_sha256=success.state_sha256,
        successful=success,
        corrupted=corrupted,
        mutation=mutation,
        first_divergence=divergence,
        runtime_observed=(
            "Both controls reached the complete fixed Task 9E breakpoint sequence.",
            "The indirect follow-up callback target was observed at runtime in both controls.",
            "Requested register/scalar values and bounded memory hashes were normalized only.",
        ),
        static_correlated=(),
        semantic_interpretation=(),
        confirmed=(
            "The compared controls share the locked ISO, state, and debugger bundle identities.",
            "The corrupted control uses the recorded deterministic one-byte DATA.BIN mutation.",
        ),
        not_confirmed=(
            "Runtime observation alone does not establish the semantic purpose of the callback.",
            "Checksum, obfuscation, recovery, slot, and field meanings remain unconfirmed unless separately evidenced.",
        ),
        warnings=warnings,
    )


def run_task9e_capture(
    success_inputs: Task9ECaptureInputs,
    corrupted_inputs: Task9ECaptureInputs,
    *,
    mutation: SaveMutation,
    client_factory: Callable[..., Any] = PpssppDebuggerClient,
) -> Task9ERuntimeEvidence:
    if success_inputs.control_id != "successful_load":
        raise Task9EPlanError("success inputs must use successful_load control_id")
    if corrupted_inputs.control_id != "corrupted_copy_control":
        raise Task9EPlanError(
            "corrupted inputs must use corrupted_copy_control control_id"
        )
    if success_inputs.plan != corrupted_inputs.plan:
        raise Task9EPlanError("Task 9E control inputs must use the same capture plan")
    if success_inputs.payload_contract != corrupted_inputs.payload_contract:
        raise Task9EPlanError("Task 9E control inputs must use the same payload contract")

    success = capture_task9e_control(
        success_inputs,
        client_factory=client_factory,
    )
    corrupted = capture_task9e_control(
        corrupted_inputs,
        client_factory=client_factory,
    )
    return compare_task9e_controls(
        success,
        corrupted,
        plan=success_inputs.plan,
        mutation=mutation,
    )


def _assert_regular_directory(path: Path, label: str) -> None:
    if path.is_symlink():
        raise Task9EPlanError(f"{label} must not be a symlink")
    if not path.exists() or not path.is_dir():
        raise Task9EPlanError(f"{label} directory does not exist")


def _ensure_safe_child_directory(parent: Path, child: Path, label: str) -> None:
    _assert_regular_directory(parent, f"{label} parent")
    if child.is_symlink():
        raise Task9EPlanError(f"{label} must not be a symlink")
    if child.exists():
        if not child.is_dir():
            raise Task9EPlanError(f"{label} must be a directory")
    else:
        child.mkdir()


def _validate_output_layout(workspace: Path, capture_root: Path) -> tuple[Path, Path]:
    if workspace.is_symlink():
        raise Task9EPlanError("workspace must not be a symlink")
    if not workspace.exists() or not workspace.is_dir():
        raise Task9EPlanError("workspace directory does not exist")

    working = workspace / "working"
    manifests = workspace / "manifests"
    _assert_regular_directory(working, "working")
    _assert_regular_directory(manifests, "manifests")

    runtime = working / "runtime"
    _ensure_safe_child_directory(working, runtime, "working/runtime")
    task_root = runtime / "task-9e"
    _ensure_safe_child_directory(runtime, task_root, "Task 9E runtime root")

    if capture_root.parent != task_root:
        raise Task9EPlanError(
            "capture root must be a direct child of working/runtime/task-9e"
        )
    if not capture_root.name or capture_root.name in {".", ".."}:
        raise Task9EPlanError("capture root requires a normal capture id")
    if capture_root.is_symlink():
        raise Task9EPlanError("capture root must not be a symlink")
    if capture_root.exists() and not capture_root.is_dir():
        raise Task9EPlanError("capture root must be a directory when it exists")

    workspace_resolved = workspace.resolve()
    capture_resolved = capture_root.resolve(strict=False)
    manifest_target = manifests / "task-9e-runtime-evidence.json"
    manifest_resolved = manifest_target.resolve(strict=False)
    for target, label in (
        (capture_resolved, "capture root"),
        (manifest_resolved, "runtime evidence manifest"),
    ):
        try:
            target.relative_to(workspace_resolved)
        except ValueError as exc:
            raise Task9EPlanError(f"{label} escapes workspace") from exc

    if manifest_target.is_symlink():
        raise Task9EPlanError("runtime evidence manifest must not be a symlink")
    if manifest_target.exists() and not manifest_target.is_file():
        raise Task9EPlanError("runtime evidence manifest must be a regular file")
    return task_root, manifest_target


def _remove_if_present(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path)


def _replace_output_pair(
    capture_temp: Path,
    capture_target: Path,
    manifest_temp: Path,
    manifest_target: Path,
    *,
    token: str,
) -> None:
    capture_backup = capture_target.with_name(f".{capture_target.name}.bak-{token}")
    manifest_backup = manifest_target.with_name(f".{manifest_target.name}.bak-{token}")
    capture_backed_up = False
    manifest_backed_up = False
    capture_installed = False
    manifest_installed = False

    try:
        if capture_target.exists():
            os.replace(capture_target, capture_backup)
            capture_backed_up = True
        if manifest_target.exists():
            os.replace(manifest_target, manifest_backup)
            manifest_backed_up = True

        os.replace(capture_temp, capture_target)
        capture_installed = True
        os.replace(manifest_temp, manifest_target)
        manifest_installed = True
    except Exception:
        if capture_installed:
            _remove_if_present(capture_target)
        if manifest_installed:
            _remove_if_present(manifest_target)
        if capture_backed_up and capture_backup.exists():
            os.replace(capture_backup, capture_target)
            capture_backed_up = False
        if manifest_backed_up and manifest_backup.exists():
            os.replace(manifest_backup, manifest_target)
            manifest_backed_up = False
        raise
    finally:
        if capture_backed_up:
            _remove_if_present(capture_backup)
        if manifest_backed_up:
            _remove_if_present(manifest_backup)


def write_task9e_runtime_evidence(
    workspace: Path,
    evidence: Task9ERuntimeEvidence,
    capture_root: Path,
) -> Path:
    task_root, manifest_target = _validate_output_layout(workspace, capture_root)

    comparison_json = evidence.to_json()
    successful_json = _json(_control_mapping(evidence.successful))
    corrupted_json = _json(_control_mapping(evidence.corrupted))

    token = uuid.uuid4().hex
    capture_temp = task_root / f".{capture_root.name}.task9e-{token}"
    manifest_temp = manifest_target.with_name(
        f".{manifest_target.name}.task9e-{token}"
    )
    capture_backup = capture_root.with_name(f".{capture_root.name}.bak-{token}")
    manifest_backup = manifest_target.with_name(f".{manifest_target.name}.bak-{token}")
    for path in (capture_temp, manifest_temp, capture_backup, manifest_backup):
        if path.exists() or path.is_symlink():
            raise Task9EPlanError(f"transaction path already exists: {path.name}")

    try:
        (capture_temp / "successful").mkdir(parents=True)
        (capture_temp / "corrupted").mkdir()
        (capture_temp / "local-diagnostics").mkdir()
        (capture_temp / "successful" / "control.json").write_text(
            successful_json,
            encoding="utf-8",
        )
        (capture_temp / "corrupted" / "control.json").write_text(
            corrupted_json,
            encoding="utf-8",
        )
        (capture_temp / "comparison.json").write_text(
            comparison_json,
            encoding="utf-8",
        )
        manifest_temp.write_text(comparison_json, encoding="utf-8")

        _replace_output_pair(
            capture_temp,
            capture_root,
            manifest_temp,
            manifest_target,
            token=token,
        )
    except Exception:
        _remove_if_present(capture_temp)
        _remove_if_present(manifest_temp)
        raise

    return manifest_target
