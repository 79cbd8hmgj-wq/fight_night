from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from fnr3_re import cli


@dataclass(frozen=True, slots=True)
class _FakeBootstrapReport:
    revision_id: str = "ULUS10066-v1.00"
    runtime_iso_sha256: str = "1" * 64
    savedata_slot_name: str = "ULUS10066PROFILE"
    state_sha256: str = "2" * 64

    def to_json(self) -> str:
        return (
            json.dumps(
                {
                    "revision_id": self.revision_id,
                    "runtime_iso_sha256": self.runtime_iso_sha256,
                    "savedata_slot_name": self.savedata_slot_name,
                    "state_sha256": self.state_sha256,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )


def test_bootstrap_parser_exposes_runtime_bundle_and_trace(tmp_path: Path) -> None:
    args = cli.build_parser().parse_args(
        [
            "bootstrap-save-9e",
            str(tmp_path / "runtime"),
            "--bundle",
            str(tmp_path / "bundle"),
            "--trace",
            str(tmp_path / "trace.json"),
        ]
    )

    assert args.command == "bootstrap-save-9e"
    assert args.runtime_root == tmp_path / "runtime"
    assert args.bundle == tmp_path / "bundle"
    assert args.trace == tmp_path / "trace.json"


def test_bootstrap_cli_dispatches_and_emits_safe_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, object] = {}
    report = _FakeBootstrapReport()

    def fake_execute(**kwargs: object) -> _FakeBootstrapReport:
        observed.update(kwargs)
        return report

    monkeypatch.setattr(cli, "_execute_bootstrap_save_9e", fake_execute, raising=False)
    result = cli.main(
        [
            "bootstrap-save-9e",
            str(tmp_path / "runtime"),
            "--bundle",
            str(tmp_path / "bundle"),
            "--trace",
            str(tmp_path / "trace.json"),
            "--json",
        ]
    )

    assert result == 0
    assert observed == {
        "bundle": tmp_path / "bundle",
        "runtime_root": tmp_path / "runtime",
        "trace_path": tmp_path / "trace.json",
    }
    output = capsys.readouterr().out
    decoded = json.loads(output)
    assert decoded["savedata_slot_name"] == "ULUS10066PROFILE"
    assert decoded["state_sha256"] == "2" * 64
    assert str(tmp_path) not in output
    for forbidden in ("DATA.BIN", "data_hex", "raw_memory", "transcript", "ppst fixture"):
        assert forbidden not in output
