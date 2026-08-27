from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from fnr3_re import cli
from fnr3_re.save_runtime_9e import Task9EPlanError


@dataclass(frozen=True, slots=True)
class _FakeSummary:
    valid: bool
    capture_id: str
    callback_target: int | None
    first_divergence: str | None
    evidence_path: Path

    def to_mapping(self) -> dict[str, object]:
        return {
            "callback_target": self.callback_target,
            "capture_id": self.capture_id,
            "evidence_path": str(self.evidence_path),
            "first_divergence": self.first_divergence,
            "valid": self.valid,
        }


def _paths(tmp_path: Path) -> dict[str, Path]:
    return {
        "workspace": tmp_path / "workspace",
        "bundle": tmp_path / "bundle",
        "iso": tmp_path / "game.iso",
        "state": tmp_path / "load.ppst",
        "slot": tmp_path / "PSP" / "SAVEDATA" / "ULUS10066SLOT",
        "plan": tmp_path / "custom-plan.json",
        "payload": tmp_path / "custom-payload.json",
    }


def test_capture_save_9e_cli_forwards_exact_paths_and_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paths = _paths(tmp_path)
    observed: dict[str, object] = {}

    def fake_execute(**kwargs: object) -> _FakeSummary:
        observed.update(kwargs)
        return _FakeSummary(
            valid=True,
            capture_id="capture-001",
            callback_target=0x08B488DC,
            first_divergence="memory_hash:before_followup_pointer_load:destination_body",
            evidence_path=paths["workspace"]
            / "manifests"
            / "task-9e-runtime-evidence.json",
        )

    monkeypatch.setattr(cli, "_execute_capture_save_9e", fake_execute, raising=False)

    result = cli.main(
        [
            "capture-save-9e",
            str(paths["workspace"]),
            "--bundle",
            str(paths["bundle"]),
            "--iso",
            str(paths["iso"]),
            "--state",
            str(paths["state"]),
            "--savedata-slot",
            str(paths["slot"]),
            "--plan",
            str(paths["plan"]),
            "--payload-lifetime",
            str(paths["payload"]),
            "--capture-id",
            "capture-001",
            "--json",
        ]
    )

    assert result == 0
    assert observed == {
        "bundle": paths["bundle"],
        "capture_id": "capture-001",
        "iso": paths["iso"],
        "payload_lifetime_path": paths["payload"],
        "plan_path": paths["plan"],
        "savedata_slot": paths["slot"],
        "state": paths["state"],
        "workspace": paths["workspace"],
    }
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "callback_target": 0x08B488DC,
        "capture_id": "capture-001",
        "evidence_path": str(
            paths["workspace"] / "manifests" / "task-9e-runtime-evidence.json"
        ),
        "first_divergence": "memory_hash:before_followup_pointer_load:destination_body",
        "valid": True,
    }


def test_capture_save_9e_cli_uses_committed_defaults_and_human_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paths = _paths(tmp_path)
    observed: dict[str, object] = {}

    def fake_execute(**kwargs: object) -> _FakeSummary:
        observed.update(kwargs)
        return _FakeSummary(
            valid=True,
            capture_id="capture-default",
            callback_target=0x08B488DC,
            first_divergence=None,
            evidence_path=paths["workspace"]
            / "manifests"
            / "task-9e-runtime-evidence.json",
        )

    monkeypatch.setattr(cli, "_execute_capture_save_9e", fake_execute, raising=False)

    result = cli.main(
        [
            "capture-save-9e",
            str(paths["workspace"]),
            "--bundle",
            str(paths["bundle"]),
            "--iso",
            str(paths["iso"]),
            "--state",
            str(paths["state"]),
            "--savedata-slot",
            str(paths["slot"]),
            "--capture-id",
            "capture-default",
        ]
    )

    assert result == 0
    plan_path = observed["plan_path"]
    payload_path = observed["payload_lifetime_path"]
    assert isinstance(plan_path, Path)
    assert isinstance(payload_path, Path)
    assert plan_path.as_posix().endswith(
        "analysis/save/checkpoint-9e-runtime-capture-plan.json"
    )
    assert payload_path.as_posix().endswith("analysis/save/save-payload-lifetime.json")

    output = capsys.readouterr().out
    assert "valid=true" in output
    assert "capture=capture-default" in output
    assert "callback=0x08B488DC" in output
    assert "divergence=none" in output
    assert "task-9e-runtime-evidence.json" in output
    for forbidden in ("DATA.BIN", "data_hex", "raw_memory", "transcript"):
        assert forbidden not in output


def test_capture_save_9e_requires_state_and_returns_nonzero_on_capture_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paths = _paths(tmp_path)
    base = [
        "capture-save-9e",
        str(paths["workspace"]),
        "--bundle",
        str(paths["bundle"]),
        "--iso",
        str(paths["iso"]),
        "--savedata-slot",
        str(paths["slot"]),
    ]
    with pytest.raises(SystemExit) as exc_info:
        cli.main(base)
    assert exc_info.value.code == 2

    def fail_execute(**_kwargs: object) -> _FakeSummary:
        raise Task9EPlanError("capture verification failed")

    monkeypatch.setattr(cli, "_execute_capture_save_9e", fail_execute, raising=False)
    result = cli.main([*base, "--state", str(paths["state"])])

    streams = capsys.readouterr()
    assert result == 1
    assert streams.out == ""
    assert "capture verification failed" in streams.err
    for forbidden in ("DATA.BIN", "data_hex", "raw_memory", "transcript"):
        assert forbidden not in streams.err
