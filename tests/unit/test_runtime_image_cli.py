from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from fnr3_re import cli


@dataclass(frozen=True, slots=True)
class _FakeRuntimeReport:
    revision_id: str = "ULUS10066-v1.00"
    runtime_iso_sha256: str = "1" * 64
    files: tuple[str, ...] = ("BOOT.BIN", "EBOOT.BIN")

    def to_json(self) -> str:
        return (
            json.dumps(
                {
                    "revision_id": self.revision_id,
                    "runtime_iso_sha256": self.runtime_iso_sha256,
                    "files": list(self.files),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )


def test_prepare_runtime_parser_exposes_repository_output_and_bundle(tmp_path: Path) -> None:
    args = cli.build_parser().parse_args(
        [
            "prepare-fnr3-runtime",
            str(tmp_path / "repo"),
            str(tmp_path / "runtime"),
            "--bundle",
            str(tmp_path / "bundle"),
        ]
    )

    assert args.command == "prepare-fnr3-runtime"
    assert args.repository_root == tmp_path / "repo"
    assert args.output_root == tmp_path / "runtime"
    assert args.bundle == tmp_path / "bundle"
    assert isinstance(args.payload_manifest, Path)
    assert args.payload_manifest.as_posix().endswith(
        "config/runtime/ulus10066-repository-payload.json"
    )
    assert args.force is False


def test_prepare_runtime_cli_dispatches_and_emits_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, object] = {}
    report = _FakeRuntimeReport()

    def fake_execute(**kwargs: object) -> _FakeRuntimeReport:
        observed.update(kwargs)
        return report

    monkeypatch.setattr(cli, "_execute_prepare_fnr3_runtime", fake_execute, raising=False)
    result = cli.main(
        [
            "prepare-fnr3-runtime",
            str(tmp_path / "repo"),
            str(tmp_path / "runtime"),
            "--bundle",
            str(tmp_path / "bundle"),
            "--payload-manifest",
            str(tmp_path / "payload.json"),
            "--force",
            "--json",
        ]
    )

    assert result == 0
    assert observed == {
        "bundle": tmp_path / "bundle",
        "force": True,
        "output_root": tmp_path / "runtime",
        "payload_manifest_path": tmp_path / "payload.json",
        "repository_root": tmp_path / "repo",
    }
    assert json.loads(capsys.readouterr().out)["runtime_iso_sha256"] == "1" * 64
