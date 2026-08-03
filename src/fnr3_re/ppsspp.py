from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import struct
import subprocess
import uuid
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath

from .evidence import Address

_ALLOWED_BUTTONS = {
    "CIRCLE",
    "CROSS",
    "DOWN",
    "HOME",
    "L",
    "LEFT",
    "NOTE",
    "R",
    "RIGHT",
    "SELECT",
    "SQUARE",
    "START",
    "TRIANGLE",
    "UP",
    "VOL_DOWN",
    "VOL_UP",
}
_SHA256_HEX_LENGTH = 64
_COPY_CHUNK_SIZE = 1024 * 1024


class PpssppHarnessError(ValueError):
    """Raised when a PPSSPP capture cannot be performed safely."""


@dataclass(frozen=True, slots=True)
class EmulatorProbe:
    executable: Path
    executable_size: int
    executable_sha256: str
    version: str
    version_output: str
    version_return_code: int
    help_output: str
    help_sha256: str
    help_return_code: int
    capabilities: tuple[str, ...]

    def to_mapping(self) -> dict[str, object]:
        return {
            "capabilities": list(self.capabilities),
            "executable": str(self.executable),
            "executable_sha256": self.executable_sha256,
            "executable_size": self.executable_size,
            "help_output": self.help_output,
            "help_return_code": self.help_return_code,
            "help_sha256": self.help_sha256,
            "version": self.version,
            "version_output": self.version_output,
            "version_return_code": self.version_return_code,
        }


@dataclass(frozen=True, slots=True)
class InputEvent:
    frame: int
    buttons: tuple[str, ...]
    analog_x: int = 0
    analog_y: int = 0

    def to_mapping(self) -> dict[str, object]:
        return {
            "analog_x": self.analog_x,
            "analog_y": self.analog_y,
            "buttons": list(self.buttons),
            "frame": self.frame,
        }


@dataclass(frozen=True, slots=True)
class InputTrace:
    trace_id: str
    frames_per_second: int
    events: tuple[InputEvent, ...]
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError(f"unsupported input trace schema: {self.schema_version}")
        if not self.trace_id.strip():
            raise ValueError("input trace id is required")
        if self.frames_per_second <= 0:
            raise ValueError("frames_per_second must be positive")
        previous_frame = -1
        for event in self.events:
            if event.frame < 0:
                raise ValueError("input event frame must be non-negative")
            if event.frame <= previous_frame:
                raise ValueError("input event frames must be strictly increasing")
            previous_frame = event.frame
            if len(event.buttons) != len(set(event.buttons)):
                raise ValueError("input event buttons must not contain duplicates")
            if tuple(sorted(event.buttons)) != event.buttons:
                raise ValueError("input event buttons must be in canonical order")
            unknown = set(event.buttons) - _ALLOWED_BUTTONS
            if unknown:
                raise ValueError(f"unknown PSP input buttons: {sorted(unknown)}")
            if not -128 <= event.analog_x <= 127:
                raise ValueError("analog_x must be between -128 and 127")
            if not -128 <= event.analog_y <= 127:
                raise ValueError("analog_y must be between -128 and 127")

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()

    def to_json(self) -> str:
        return _json(
            {
                "events": [event.to_mapping() for event in self.events],
                "frames_per_second": self.frames_per_second,
                "schema_version": self.schema_version,
                "trace_id": self.trace_id,
            }
        )


@dataclass(frozen=True, slots=True)
class MemorySnapshot:
    snapshot_id: str
    source_revision: str
    module: str
    address: Address
    data: bytes

    def __post_init__(self) -> None:
        for label, value in (
            ("snapshot_id", self.snapshot_id),
            ("source_revision", self.source_revision),
            ("module", self.module),
        ):
            if not value.strip():
                raise ValueError(f"{label} is required")
        if not self.data:
            raise ValueError("memory snapshot data is required")

    def to_mapping(self) -> dict[str, object]:
        return {
            "address": _address_mapping(self.address),
            "data_hex": self.data.hex(),
            "module": self.module,
            "sha256": hashlib.sha256(self.data).hexdigest(),
            "snapshot_id": self.snapshot_id,
            "source_revision": self.source_revision,
        }


class MemoryValueType(StrEnum):
    U8 = "u8"
    U16 = "u16_le"
    U32 = "u32_le"
    F32 = "f32_le"

    @property
    def width(self) -> int:
        return {
            MemoryValueType.U8: 1,
            MemoryValueType.U16: 2,
            MemoryValueType.U32: 4,
            MemoryValueType.F32: 4,
        }[self]


@dataclass(frozen=True, slots=True)
class MemoryChange:
    offset: int
    address: Address
    value_type: MemoryValueType
    before_hex: str | None
    after_hex: str
    before_value: int | float | None
    after_value: int | float
    classification: str

    @property
    def changed(self) -> bool:
        return self.classification == "changed"


@dataclass(frozen=True, slots=True)
class BreakpointEvent:
    sequence: int
    breakpoint: Address
    access: str
    width: int
    hit_count: int
    pc: Address
    registers: tuple[tuple[str, int], ...]
    call_stack: tuple[Address, ...]
    memory: tuple[MemorySnapshot, ...]
    note: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "access": self.access,
            "breakpoint": _address_mapping(self.breakpoint),
            "call_stack": [_address_mapping(address) for address in self.call_stack],
            "hit_count": self.hit_count,
            "memory": [snapshot.to_mapping() for snapshot in self.memory],
            "note": self.note,
            "pc": _address_mapping(self.pc),
            "registers": [[name, value] for name, value in self.registers],
            "sequence": self.sequence,
            "width": self.width,
        }


@dataclass(frozen=True, slots=True)
class BreakpointJournal:
    journal_id: str
    source_revision: str
    emulator_sha256: str
    events: tuple[BreakpointEvent, ...]
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError(f"unsupported breakpoint journal schema: {self.schema_version}")
        if not self.journal_id.strip() or not self.source_revision.strip():
            raise ValueError("breakpoint journal identity is required")
        _validate_sha256(self.emulator_sha256, "emulator_sha256")
        previous_sequence = -1
        for event in self.events:
            if event.sequence <= previous_sequence:
                raise ValueError("breakpoint events must have increasing sequence numbers")
            previous_sequence = event.sequence
            if event.access not in {"execute", "read", "write", "read_write"}:
                raise ValueError(f"unsupported breakpoint access: {event.access}")
            if event.width <= 0:
                raise ValueError("breakpoint width must be positive")
            if event.hit_count <= 0:
                raise ValueError("breakpoint hit_count must be positive")
            register_names = [name for name, _value in event.registers]
            if any(not name.strip() for name in register_names):
                raise ValueError("register names must be non-empty")
            if len(register_names) != len(set(register_names)):
                raise ValueError("register names must be unique per event")

    def to_json(self) -> str:
        return _json(
            {
                "emulator_sha256": self.emulator_sha256,
                "events": [event.to_mapping() for event in self.events],
                "journal_id": self.journal_id,
                "schema_version": self.schema_version,
                "source_revision": self.source_revision,
            }
        )


@dataclass(frozen=True, slots=True)
class CaptureArtifact:
    path: str
    required: bool

    def __post_init__(self) -> None:
        _safe_relative_path(self.path, "capture artifact")

    def to_mapping(self) -> dict[str, object]:
        return {"path": self.path, "required": self.required}


@dataclass(frozen=True, slots=True)
class CaptureScenario:
    scenario_id: str
    source_revision: str
    rebuilt_iso_sha256: str
    mode: str
    fighters: tuple[str, ...]
    round_number: int
    clock_seconds: int
    input_trace_sha256: str
    save_sha256: str | None
    state_sha256: str | None
    notes: tuple[str, ...]

    def __post_init__(self) -> None:
        for label, value in (
            ("scenario_id", self.scenario_id),
            ("source_revision", self.source_revision),
            ("mode", self.mode),
        ):
            if not value.strip():
                raise ValueError(f"{label} is required")
        _validate_sha256(self.rebuilt_iso_sha256, "rebuilt_iso_sha256")
        _validate_sha256(self.input_trace_sha256, "input_trace_sha256")
        if self.save_sha256 is not None:
            _validate_sha256(self.save_sha256, "save_sha256")
        if self.state_sha256 is not None:
            _validate_sha256(self.state_sha256, "state_sha256")
        if not self.fighters or any(not fighter.strip() for fighter in self.fighters):
            raise ValueError("capture fighters are required")
        if self.round_number <= 0:
            raise ValueError("round_number must be positive")
        if self.clock_seconds < 0:
            raise ValueError("clock_seconds must be non-negative")

    def to_mapping(self) -> dict[str, object]:
        return {
            "clock_seconds": self.clock_seconds,
            "fighters": list(self.fighters),
            "input_trace_sha256": self.input_trace_sha256,
            "mode": self.mode,
            "notes": list(self.notes),
            "rebuilt_iso_sha256": self.rebuilt_iso_sha256,
            "round_number": self.round_number,
            "save_sha256": self.save_sha256,
            "scenario_id": self.scenario_id,
            "source_revision": self.source_revision,
            "state_sha256": self.state_sha256,
        }


@dataclass(frozen=True, slots=True)
class CapturePlan:
    plan_id: str
    emulator: EmulatorProbe
    scenario: CaptureScenario
    input_trace: InputTrace
    arguments: tuple[str, ...]
    environment: tuple[tuple[str, str], ...]
    timeout_seconds: float
    expected_artifacts: tuple[CaptureArtifact, ...]
    capture_directory: Path
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError(f"unsupported capture plan schema: {self.schema_version}")
        if not self.plan_id.strip():
            raise ValueError("capture plan id is required")
        if self.scenario.input_trace_sha256 != self.input_trace.sha256:
            raise ValueError("capture scenario input trace hash does not match trace")
        if not self.arguments:
            raise ValueError("capture arguments are required")
        if self.timeout_seconds <= 0 or not math.isfinite(self.timeout_seconds):
            raise ValueError("timeout_seconds must be a finite positive value")
        environment_names = [name for name, _value in self.environment]
        if len(environment_names) != len(set(environment_names)):
            raise ValueError("capture environment names must be unique")
        for name, _value in self.environment:
            if not name or "=" in name or "\x00" in name:
                raise ValueError(f"invalid capture environment name: {name!r}")
        artifact_paths = [artifact.path.casefold() for artifact in self.expected_artifacts]
        if len(artifact_paths) != len(set(artifact_paths)):
            raise ValueError("capture artifact paths must be unique")

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()

    def to_json(self) -> str:
        return _json(
            {
                "arguments": list(self.arguments),
                "capture_directory": str(self.capture_directory),
                "emulator": self.emulator.to_mapping(),
                "environment": [[name, value] for name, value in self.environment],
                "expected_artifacts": [
                    artifact.to_mapping() for artifact in self.expected_artifacts
                ],
                "input_trace_sha256": self.input_trace.sha256,
                "plan_id": self.plan_id,
                "scenario": self.scenario.to_mapping(),
                "schema_version": self.schema_version,
                "timeout_seconds": self.timeout_seconds,
            }
        )


@dataclass(frozen=True, slots=True)
class CapturedArtifact:
    path: str
    required: bool
    present: bool
    size: int | None
    sha256: str | None

    def to_mapping(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CaptureResult:
    plan_sha256: str
    emulator_sha256: str
    iso_sha256: str
    return_code: int | None
    timed_out: bool
    valid: bool
    stdout_sha256: str
    stderr_sha256: str
    artifacts: tuple[CapturedArtifact, ...]
    missing_artifacts: tuple[str, ...]
    schema_version: int = 1

    def to_json(self) -> str:
        return _json(
            {
                "artifacts": [artifact.to_mapping() for artifact in self.artifacts],
                "emulator_sha256": self.emulator_sha256,
                "iso_sha256": self.iso_sha256,
                "missing_artifacts": list(self.missing_artifacts),
                "plan_sha256": self.plan_sha256,
                "return_code": self.return_code,
                "schema_version": self.schema_version,
                "stderr_sha256": self.stderr_sha256,
                "stdout_sha256": self.stdout_sha256,
                "timed_out": self.timed_out,
                "valid": self.valid,
            }
        )


@dataclass(frozen=True, slots=True)
class CaptureBundleVerification:
    capture_directory: Path
    valid: bool
    diagnostics: tuple[str, ...]


def discover_ppsspp(
    *,
    explicit: Path | None = None,
    environment: Mapping[str, str] | None = None,
    search_path: str | None = None,
) -> Path:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit)
    selected_environment = os.environ if environment is None else environment
    configured = selected_environment.get("PPSSPP_EXECUTABLE")
    if configured:
        candidates.append(Path(configured))
    for name in ("PPSSPPHeadless", "PPSSPPSDL", "ppsspp-headless", "ppsspp-sdl"):
        which_result = shutil.which(name, path=search_path)
        if which_result:
            candidates.append(Path(which_result))

    for candidate in candidates:
        candidate_path = candidate.expanduser().resolve()
        if candidate_path.is_file() and os.access(candidate_path, os.X_OK):
            return candidate_path
    raise PpssppHarnessError(
        "PPSSPP executable was not found; set PPSSPP_EXECUTABLE or pass an explicit path"
    )


def probe_ppsspp(executable: Path, *, timeout_seconds: float = 5.0) -> EmulatorProbe:
    resolved = discover_ppsspp(explicit=executable)
    version_code, version_output = _run_probe(
        resolved, "--version", timeout_seconds=timeout_seconds
    )
    help_code, help_output = _run_probe(
        resolved, "--help", timeout_seconds=timeout_seconds
    )
    version = next(
        (line.strip() for line in version_output.splitlines() if line.strip()),
        "unknown",
    )
    searchable = f"{resolved.name}\n{help_output}".lower()
    capabilities: list[str] = []
    if "debugger" in searchable:
        capabilities.append("debugger_reference")
    if "headless" in searchable:
        capabilities.append("headless_frontend")
    if "log" in searchable:
        capabilities.append("logging_reference")
    return EmulatorProbe(
        executable=resolved,
        executable_size=resolved.stat().st_size,
        executable_sha256=_hash_file(resolved),
        version=version,
        version_output=version_output,
        version_return_code=version_code,
        help_output=help_output,
        help_sha256=hashlib.sha256(help_output.encode("utf-8")).hexdigest(),
        help_return_code=help_code,
        capabilities=tuple(sorted(capabilities)),
    )


def compare_memory(
    before: MemorySnapshot | None,
    after: MemorySnapshot,
    value_type: MemoryValueType,
) -> tuple[MemoryChange, ...]:
    if before is not None:
        if before.source_revision != after.source_revision:
            raise ValueError("memory snapshot revisions differ")
        if before.module != after.module:
            raise ValueError("memory snapshot modules differ")
        if before.address != after.address:
            raise ValueError("memory snapshot base addresses differ")
        if len(before.data) != len(after.data):
            raise ValueError("memory snapshot sizes differ")
    width = value_type.width
    changes: list[MemoryChange] = []
    for offset in range(0, len(after.data) - width + 1, width):
        after_bytes = after.data[offset : offset + width]
        before_bytes = None if before is None else before.data[offset : offset + width]
        after_value = _decode_memory_value(after_bytes, value_type)
        before_value = (
            None
            if before_bytes is None
            else _decode_memory_value(before_bytes, value_type)
        )
        classification = (
            "unknown_initial"
            if before_bytes is None
            else "changed"
            if before_bytes != after_bytes
            else "unchanged"
        )
        changes.append(
            MemoryChange(
                offset=offset,
                address=Address(
                    after.address.address_type,
                    after.address.value + offset,
                ),
                value_type=value_type,
                before_hex=None if before_bytes is None else before_bytes.hex(),
                after_hex=after_bytes.hex(),
                before_value=before_value,
                after_value=after_value,
                classification=classification,
            )
        )
    return tuple(changes)


def run_capture(plan: CapturePlan, iso: Path, *, force: bool = False) -> CaptureResult:
    executable = plan.emulator.executable
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise PpssppHarnessError(f"emulator executable is unavailable: {executable}")
    observed_emulator_hash = _hash_file(executable)
    if observed_emulator_hash != plan.emulator.executable_sha256:
        raise PpssppHarnessError(
            "emulator hash mismatch: "
            f"expected {plan.emulator.executable_sha256}, got {observed_emulator_hash}"
        )
    if not iso.is_file():
        raise PpssppHarnessError(f"ISO does not exist: {iso}")
    observed_iso_hash = _hash_file(iso)
    if observed_iso_hash != plan.scenario.rebuilt_iso_sha256:
        raise PpssppHarnessError(
            "ISO hash mismatch: "
            f"expected {plan.scenario.rebuilt_iso_sha256}, got {observed_iso_hash}"
        )

    destination = plan.capture_directory.absolute()
    if destination.exists() and not force:
        raise FileExistsError(f"capture directory already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    temporary = destination.parent / f".{destination.name}.tmp-{token}"
    backup = destination.parent / f".{destination.name}.bak-{token}"

    try:
        temporary.mkdir()
        (temporary / "capture-plan.json").write_text(plan.to_json(), encoding="utf-8")
        (temporary / "input-trace.json").write_text(
            plan.input_trace.to_json(), encoding="utf-8"
        )
        arguments = tuple(
            _expand_capture_argument(argument, iso=iso, capture=temporary)
            for argument in plan.arguments
        )
        command = (str(executable), *arguments)
        environment = dict(os.environ)
        environment.update(dict(plan.environment))
        return_code: int | None
        timed_out = False
        try:
            completed = subprocess.run(
                command,
                cwd=temporary,
                env=environment,
                capture_output=True,
                timeout=plan.timeout_seconds,
                check=False,
            )
            return_code = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
        except subprocess.TimeoutExpired as exc:
            return_code = None
            timed_out = True
            stdout = _timeout_bytes(exc.stdout)
            stderr = _timeout_bytes(exc.stderr)

        (temporary / "stdout.log").write_bytes(stdout)
        (temporary / "stderr.log").write_bytes(stderr)
        captured_artifacts: list[CapturedArtifact] = []
        missing_artifacts: list[str] = []
        for expected in plan.expected_artifacts:
            artifact_path = _capture_path(temporary, expected.path)
            present = artifact_path.is_file() and not artifact_path.is_symlink()
            size = artifact_path.stat().st_size if present else None
            artifact_hash = _hash_file(artifact_path) if present else None
            captured_artifacts.append(
                CapturedArtifact(
                    path=expected.path,
                    required=expected.required,
                    present=present,
                    size=size,
                    sha256=artifact_hash,
                )
            )
            if expected.required and not present:
                missing_artifacts.append(expected.path)

        valid = return_code == 0 and not timed_out and not missing_artifacts
        result = CaptureResult(
            plan_sha256=plan.sha256,
            emulator_sha256=observed_emulator_hash,
            iso_sha256=observed_iso_hash,
            return_code=return_code,
            timed_out=timed_out,
            valid=valid,
            stdout_sha256=hashlib.sha256(stdout).hexdigest(),
            stderr_sha256=hashlib.sha256(stderr).hexdigest(),
            artifacts=tuple(captured_artifacts),
            missing_artifacts=tuple(missing_artifacts),
        )
        (temporary / "capture-result.json").write_text(
            result.to_json(), encoding="utf-8"
        )
        _replace_directory(temporary, destination, backup, force=force)
        return result
    except Exception:
        _remove_path(temporary)
        if backup.exists() and not destination.exists():
            os.replace(backup, destination)
        raise
    finally:
        _remove_path(backup)


def verify_capture_bundle(capture_directory: Path) -> CaptureBundleVerification:
    diagnostics: set[str] = set()
    required_files = (
        "capture-plan.json",
        "capture-result.json",
        "input-trace.json",
        "stdout.log",
        "stderr.log",
    )
    for name in required_files:
        path = capture_directory / name
        if not path.is_file() or path.is_symlink():
            diagnostics.add(f"missing capture file: {name}")
    result_path = capture_directory / "capture-result.json"
    if diagnostics or not result_path.is_file():
        return CaptureBundleVerification(
            capture_directory=capture_directory,
            valid=False,
            diagnostics=tuple(sorted(diagnostics)),
        )
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        diagnostics.add(f"invalid capture result: {exc}")
        return CaptureBundleVerification(
            capture_directory=capture_directory,
            valid=False,
            diagnostics=tuple(sorted(diagnostics)),
        )
    if not isinstance(result, Mapping):
        diagnostics.add("invalid capture result: root must be an object")
        return CaptureBundleVerification(
            capture_directory=capture_directory,
            valid=False,
            diagnostics=tuple(sorted(diagnostics)),
        )

    _verify_bundle_file_hash(
        capture_directory / "stdout.log",
        result.get("stdout_sha256"),
        "stdout.log",
        diagnostics,
    )
    _verify_bundle_file_hash(
        capture_directory / "stderr.log",
        result.get("stderr_sha256"),
        "stderr.log",
        diagnostics,
    )
    artifacts = result.get("artifacts")
    if not isinstance(artifacts, list):
        diagnostics.add("invalid capture result: artifacts must be a list")
    else:
        for item in artifacts:
            if not isinstance(item, Mapping):
                diagnostics.add("invalid capture result: artifact must be an object")
                continue
            path_value = item.get("path")
            if not isinstance(path_value, str):
                diagnostics.add("invalid capture result: artifact path must be a string")
                continue
            try:
                artifact_path = _capture_path(capture_directory, path_value)
            except ValueError as exc:
                diagnostics.add(str(exc))
                continue
            present = item.get("present") is True
            if present:
                if not artifact_path.is_file() or artifact_path.is_symlink():
                    diagnostics.add(f"missing artifact: {path_value}")
                    continue
                expected_size = item.get("size")
                if artifact_path.stat().st_size != expected_size:
                    diagnostics.add(f"artifact size mismatch: {path_value}")
                expected_hash = item.get("sha256")
                if _hash_file(artifact_path) != expected_hash:
                    diagnostics.add(f"artifact hash mismatch: {path_value}")
            elif item.get("required") is True:
                diagnostics.add(f"missing required artifact: {path_value}")

    ordered = tuple(sorted(diagnostics))
    return CaptureBundleVerification(
        capture_directory=capture_directory,
        valid=not ordered,
        diagnostics=ordered,
    )


def _run_probe(executable: Path, flag: str, *, timeout_seconds: float) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            (str(executable), flag),
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            text=True,
        )
    except subprocess.TimeoutExpired as exc:
        raise PpssppHarnessError(f"PPSSPP probe timed out for {flag}") from exc
    output = _normalize_text_output(completed.stdout, completed.stderr)
    return completed.returncode, output


def _normalize_text_output(stdout: str, stderr: str) -> str:
    combined = stdout
    if stderr:
        combined = combined + ("\n" if combined and not combined.endswith("\n") else "") + stderr
    if combined and not combined.endswith("\n"):
        combined += "\n"
    return combined


def _decode_memory_value(payload: bytes, value_type: MemoryValueType) -> int | float:
    if value_type is MemoryValueType.F32:
        return float(struct.unpack("<f", payload)[0])
    return int.from_bytes(payload, "little")


def _expand_capture_argument(argument: str, *, iso: Path, capture: Path) -> str:
    expanded = argument.replace("{iso}", str(iso.resolve())).replace(
        "{capture}", str(capture.resolve())
    )
    if "{" in expanded or "}" in expanded:
        raise PpssppHarnessError(f"unresolved capture argument placeholder: {argument}")
    if "\x00" in expanded:
        raise PpssppHarnessError("capture arguments must not contain NUL bytes")
    return expanded


def _verify_bundle_file_hash(
    path: Path,
    expected: object,
    label: str,
    diagnostics: set[str],
) -> None:
    if not path.is_file() or path.is_symlink():
        diagnostics.add(f"missing capture file: {label}")
        return
    if not isinstance(expected, str) or _hash_file(path) != expected:
        diagnostics.add(f"capture file hash mismatch: {label}")


def _address_mapping(address: Address) -> dict[str, object]:
    return {
        "address_type": address.address_type.value,
        "value": address.value,
    }


def _safe_relative_path(path: str, label: str) -> tuple[str, ...]:
    if not path or "\\" in path or "\x00" in path:
        raise ValueError(f"unsafe {label} path: {path!r}")
    pure = PurePosixPath(path)
    if pure.is_absolute() or not pure.parts:
        raise ValueError(f"unsafe {label} path: {path!r}")
    if any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError(f"unsafe {label} path: {path!r}")
    return tuple(pure.parts)


def _capture_path(root: Path, path: str) -> Path:
    parts = _safe_relative_path(path, "capture artifact")
    candidate = root.joinpath(*parts)
    root_resolved = root.resolve()
    candidate_resolved = candidate.resolve(strict=False)
    if not candidate_resolved.is_relative_to(root_resolved):
        raise ValueError(f"capture artifact path escapes root: {path}")
    return candidate


def _validate_sha256(value: str, label: str) -> None:
    if len(value) != _SHA256_HEX_LENGTH or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(f"{label} must be 64 lowercase hexadecimal characters")


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(_COPY_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def _timeout_bytes(value: bytes | str | None) -> bytes:
    if value is None:
        return b""
    return value.encode("utf-8") if isinstance(value, str) else value


def _json(payload: object) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _replace_directory(
    temporary: Path,
    destination: Path,
    backup: Path,
    *,
    force: bool,
) -> None:
    moved_existing = False
    try:
        if destination.exists():
            if not force:
                raise FileExistsError(f"capture directory already exists: {destination}")
            os.replace(destination, backup)
            moved_existing = True
        os.replace(temporary, destination)
    except Exception:
        if moved_existing and destination.exists():
            _remove_path(destination)
        if moved_existing and backup.exists():
            os.replace(backup, destination)
        raise
    if moved_existing:
        _remove_path(backup)


def _remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()
