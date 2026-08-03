from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from fnr3_re import cli
from fnr3_re.iso import build_workspace
from tests.support.psp_iso import write_reference


def write_revision_config(path: Path, *, image: bytes) -> None:
    path.write_text(
        json.dumps(
            {
                "disc_id": "ULUS10066",
                "disc_version": "1.00",
                "iso_sha256": hashlib.sha256(image).hexdigest(),
                "iso_size": len(image),
                "psp_system_version": "2.60",
                "revision_id": "fixture-v1",
                "title": "Fixture",
            }
        ),
        encoding="utf-8",
    )


def test_rebuild_image_cli_performs_no_change_build(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    reference, revision, image = write_reference(tmp_path)
    workspace = tmp_path / "workspace"
    output = tmp_path / "rebuilt.iso"
    report_path = tmp_path / "report.json"
    revision_config = tmp_path / "revision.json"
    build_workspace(reference, workspace, revision)
    write_revision_config(revision_config, image=image)

    code = cli.main(
        [
            "rebuild-image",
            str(reference),
            str(workspace),
            str(output),
            "--revision-config",
            str(revision_config),
            "--report",
            str(report_path),
            "--json",
        ]
    )

    assert code == 0
    assert output.read_bytes() == image
    stdout_report = json.loads(capsys.readouterr().out)
    file_report = json.loads(report_path.read_text(encoding="utf-8"))
    assert stdout_report == file_report
    assert stdout_report["no_change"] is True


def test_rebuild_image_cli_loads_guarded_plan(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    reference, revision, image = write_reference(tmp_path)
    workspace = tmp_path / "workspace"
    output = tmp_path / "patched.iso"
    revision_config = tmp_path / "revision.json"
    plan_path = tmp_path / "plan.json"
    build_workspace(reference, workspace, revision)
    write_revision_config(revision_config, image=image)
    plan_path.write_text(
        json.dumps(
            {
                "patches": [
                    {
                        "expected_hex": "43",
                        "file_offset": 5,
                        "id": "boot-byte",
                        "path": "PSP_GAME/SYSDIR/BOOT.BIN",
                        "replacement_hex": "58",
                    }
                ],
                "revision_id": "fixture-v1",
                "schema_version": 1,
            }
        ),
        encoding="utf-8",
    )

    code = cli.main(
        [
            "rebuild-image",
            str(reference),
            str(workspace),
            str(output),
            "--revision-config",
            str(revision_config),
            "--plan",
            str(plan_path),
        ]
    )

    assert code == 0
    assert output.read_bytes() != image
    assert "patched" in capsys.readouterr().out
