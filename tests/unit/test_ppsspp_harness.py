from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from fnr3_re.evidence import Address, AddressType
from fnr3_re.ppsspp import (
    BreakpointEvent,
    BreakpointJournal,
    CaptureArtifact,
    CapturePlan,
    CaptureScenario,
    EmulatorProbe,
    InputEvent,
    InputTrace,
    MemorySnapshot,
    MemoryValueType,
    PpssppHarnessError,
    compare_memory,
    discover_ppsspp,
    probe_ppsspp,
    run_capture,
    verify_capture_bundle,
)


def write_fake_ppsspp(path: Path) -> Path:
    path.write_text(
        """#!/usr/bin/env python3
import pathlib
import sys
import time

if '--version' in sys.argv:
    print('PPSSPP 9.9.9-fixture')
    raise SystemExit(0)
if '--help' in sys.argv:
    print('usage: PPSSPPHeadless [--log FILE] [--debugger] GAME')
    print('supports headless logging and debugger capture')
    raise SystemExit(0)
if '--sleep' in sys.argv:
    time.sleep(5)
if '--fail' in sys.argv:
    print('fixture failure', file=sys.stderr)
    raise SystemExit(7)
if '--artifact' in sys.argv:
    index = sys.argv.index('--artifact')
    artifact = pathlib.Path(sys.argv[index + 1])
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(b'capture-data')
print('fixture launch')
""",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def probe_for(executable: Path) -> EmulatorProbe:
    return probe_ppsspp(executable)


def trace() -> InputTrace:
    return InputTrace(
        trace_id="tutorial-fight",
        frames_per_second=60,
        events=(
            InputEvent(frame=0, buttons=("CROSS",), analog_x=0, analog_y=0),
            InputEvent(frame=3, buttons=(), analog_x=20, analog_y=-10),
        ),
    )


def scenario(iso: Path, input_trace: InputTrace) -> CaptureScenario:
    return CaptureScenario(
        scenario_id="career-fight-entry",
        source_revision="ULUS10066-v1.00",
        rebuilt_iso_sha256=hashlib.sha256(iso.read_bytes()).hexdigest(),
        mode="career",
        fighters=("player", "opponent"),
        round_number=1,
        clock_seconds=180,
        input_trace_sha256=input_trace.sha256,
        save_sha256=None,
        state_sha256=None,
        notes=("fixture",),
    )


def capture_plan(
    executable: Path,
    iso: Path,
    output: Path,
    *,
    arguments: tuple[str, ...] | None = None,
    timeout_seconds: float = 5.0,
) -> CapturePlan:
    emulator = probe_for(executable)
    input_trace = trace()
    selected_arguments = arguments or (
        "--artifact",
        "{capture}/artifacts/result.bin",
        "{iso}",
    )
    return CapturePlan(
        plan_id="fixture-plan",
        emulator=emulator,
        scenario=scenario(iso, input_trace),
        input_trace=input_trace,
        arguments=selected_arguments,
        environment=(("PPSSPP_FIXTURE", "1"),),
        timeout_seconds=timeout_seconds,
        expected_artifacts=(CaptureArtifact("artifacts/result.bin", required=True),),
        capture_directory=output,
    )


def test_discovers_explicit_or_environment_ppsspp(tmp_path: Path) -> None:
    executable = write_fake_ppsspp(tmp_path / "PPSSPPHeadless")

    assert discover_ppsspp(explicit=executable) == executable.resolve()
    assert discover_ppsspp(environment={"PPSSPP_EXECUTABLE": str(executable)}) == (
        executable.resolve()
    )

    with pytest.raises(PpssppHarnessError, match="PPSSPP executable was not found"):
        discover_ppsspp(environment={}, search_path="")


def test_probe_records_exact_binary_version_help_and_capabilities(tmp_path: Path) -> None:
    executable = write_fake_ppsspp(tmp_path / "PPSSPPHeadless")

    first = probe_ppsspp(executable)
    second = probe_ppsspp(executable)

    assert first == second
    assert first.executable == executable.resolve()
    assert first.executable_sha256 == hashlib.sha256(executable.read_bytes()).hexdigest()
    assert first.version == "PPSSPP 9.9.9-fixture"
    assert first.version_return_code == 0
    assert first.help_return_code == 0
    assert first.capabilities == (
        "debugger_reference",
        "headless_frontend",
        "logging_reference",
    )
    assert first.help_sha256 == hashlib.sha256(first.help_output.encode()).hexdigest()


def test_input_trace_is_canonical_and_hash_stable() -> None:
    input_trace = trace()

    assert input_trace.to_json() == trace().to_json()
    assert input_trace.sha256 == hashlib.sha256(input_trace.to_json().encode()).hexdigest()
    assert json.loads(input_trace.to_json())["events"][0]["buttons"] == ["CROSS"]


@pytest.mark.parametrize(
    "event",
    [
        InputEvent(frame=-1, buttons=()),
        InputEvent(frame=0, buttons=("CROSS", "CROSS")),
        InputEvent(frame=0, buttons=("unknown",)),
        InputEvent(frame=0, buttons=(), analog_x=128),
        InputEvent(frame=0, buttons=(), analog_y=-129),
    ],
)
def test_input_event_rejects_invalid_values(event: InputEvent) -> None:
    with pytest.raises(ValueError):
        InputTrace(trace_id="invalid", frames_per_second=60, events=(event,))


def test_input_trace_requires_strict_frame_order() -> None:
    with pytest.raises(ValueError, match="strictly increasing"):
        InputTrace(
            trace_id="invalid",
            frames_per_second=60,
            events=(InputEvent(2, ()), InputEvent(2, ())),
        )


def test_memory_comparison_supports_bytes_halfwords_words_and_floats() -> None:
    before = MemorySnapshot(
        snapshot_id="before",
        source_revision="ULUS10066-v1.00",
        module="main",
        address=Address(AddressType.RUNTIME, 0x08800000),
        data=b"\x01\x02\x03\x04\x00\x00\x80\x3f",
    )
    after = MemorySnapshot(
        snapshot_id="after",
        source_revision="ULUS10066-v1.00",
        module="main",
        address=before.address,
        data=b"\x01\x09\x03\x04\x00\x00\x00\x40",
    )

    byte_changes = compare_memory(before, after, MemoryValueType.U8)
    halfword_changes = compare_memory(before, after, MemoryValueType.U16)
    word_changes = compare_memory(before, after, MemoryValueType.U32)
    float_changes = compare_memory(before, after, MemoryValueType.F32)

    assert [change.offset for change in byte_changes if change.changed] == [1, 6, 7]
    assert [change.offset for change in halfword_changes if change.changed] == [0, 6]
    assert [change.offset for change in word_changes if change.changed] == [0, 4]
    assert float_changes[1].before_value == pytest.approx(1.0)
    assert float_changes[1].after_value == pytest.approx(2.0)


def test_unknown_initial_memory_is_labeled_not_guessed() -> None:
    after = MemorySnapshot(
        snapshot_id="after",
        source_revision="ULUS10066-v1.00",
        module="main",
        address=Address(AddressType.RUNTIME, 0x08800000),
        data=b"\x01\x02",
    )

    changes = compare_memory(None, after, MemoryValueType.U8)

    assert all(change.classification == "unknown_initial" for change in changes)
    assert all(change.before_value is None for change in changes)


def test_breakpoint_journal_serializes_typed_evidence_deterministically() -> None:
    snapshot = MemorySnapshot(
        snapshot_id="hit-memory",
        source_revision="ULUS10066-v1.00",
        module="main",
        address=Address(AddressType.RUNTIME, 0x08801000),
        data=b"\x01\x02\x03\x04",
    )
    event = BreakpointEvent(
        sequence=0,
        breakpoint=Address(AddressType.RUNTIME, 0x08802000),
        access="write",
        width=4,
        hit_count=1,
        pc=Address(AddressType.RUNTIME, 0x08803000),
        registers=(("a0", 1), ("sp", 0x09FFF000)),
        call_stack=(Address(AddressType.RUNTIME, 0x08804000),),
        memory=(snapshot,),
        note="controlled write",
    )
    journal = BreakpointJournal(
        journal_id="damage-write",
        source_revision="ULUS10066-v1.00",
        emulator_sha256="a" * 64,
        events=(event,),
    )

    assert journal.to_json() == journal.to_json()
    decoded = json.loads(journal.to_json())
    assert decoded["events"][0]["breakpoint"] == {
        "address_type": "runtime",
        "value": 0x08802000,
    }
    assert decoded["events"][0]["memory"][0]["data_hex"] == "01020304"


def test_capture_run_is_transactional_and_verifiable(tmp_path: Path) -> None:
    executable = write_fake_ppsspp(tmp_path / "PPSSPPHeadless")
    iso = tmp_path / "game.iso"
    iso.write_bytes(b"fixture-iso")
    output = tmp_path / "capture"
    plan = capture_plan(executable, iso, output)

    result = run_capture(plan, iso)

    assert result.valid
    assert result.return_code == 0
    assert not result.timed_out
    assert result.missing_artifacts == ()
    assert (output / "artifacts" / "result.bin").read_bytes() == b"capture-data"
    assert (output / "stdout.log").read_text(encoding="utf-8") == "fixture launch\n"
    assert verify_capture_bundle(output).valid
    assert json.loads((output / "capture-result.json").read_text())["valid"] is True


def test_capture_rejects_changed_emulator_or_iso_before_launch(tmp_path: Path) -> None:
    executable = write_fake_ppsspp(tmp_path / "PPSSPPHeadless")
    iso = tmp_path / "game.iso"
    iso.write_bytes(b"fixture-iso")
    output = tmp_path / "capture"
    plan = capture_plan(executable, iso, output)

    executable.write_text(executable.read_text() + "\n# changed\n", encoding="utf-8")
    executable.chmod(0o755)
    with pytest.raises(PpssppHarnessError, match="emulator hash mismatch"):
        run_capture(plan, iso)
    assert not output.exists()

    executable = write_fake_ppsspp(executable)
    plan = capture_plan(executable, iso, output)
    iso.write_bytes(b"changed-iso")
    with pytest.raises(PpssppHarnessError, match="ISO hash mismatch"):
        run_capture(plan, iso)
    assert not output.exists()


def test_capture_reports_timeout_nonzero_and_missing_artifacts(tmp_path: Path) -> None:
    executable = write_fake_ppsspp(tmp_path / "PPSSPPHeadless")
    iso = tmp_path / "game.iso"
    iso.write_bytes(b"fixture-iso")

    timeout_plan = capture_plan(
        executable,
        iso,
        tmp_path / "timeout",
        arguments=("--sleep", "{iso}"),
        timeout_seconds=0.1,
    )
    timeout_result = run_capture(timeout_plan, iso)
    assert not timeout_result.valid
    assert timeout_result.timed_out
    assert timeout_result.missing_artifacts == ("artifacts/result.bin",)

    failure_plan = capture_plan(
        executable,
        iso,
        tmp_path / "failure",
        arguments=("--fail", "{iso}"),
    )
    failure_result = run_capture(failure_plan, iso)
    assert not failure_result.valid
    assert failure_result.return_code == 7


def test_capture_output_requires_force_and_bundle_detects_tampering(tmp_path: Path) -> None:
    executable = write_fake_ppsspp(tmp_path / "PPSSPPHeadless")
    iso = tmp_path / "game.iso"
    iso.write_bytes(b"fixture-iso")
    output = tmp_path / "capture"
    plan = capture_plan(executable, iso, output)
    run_capture(plan, iso)

    with pytest.raises(FileExistsError):
        run_capture(plan, iso)
    run_capture(plan, iso, force=True)

    artifact = output / "artifacts" / "result.bin"
    artifact.write_bytes(b"tampered")
    verification = verify_capture_bundle(output)
    assert not verification.valid
    assert "artifact hash mismatch: artifacts/result.bin" in verification.diagnostics


def test_capture_artifact_path_must_be_safe() -> None:
    with pytest.raises(ValueError, match="unsafe capture artifact path"):
        CaptureArtifact("../escape.bin", required=True)
