from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from fnr3_re import cli
from fnr3_re.manifests import WorkspaceManifest
from fnr3_re.revision import ReferenceRevision


def test_verify_workspace_cli_reports_invalid_missing_workspace(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = tmp_path / "missing"

    code = cli.main(["verify-workspace", str(workspace), "--json"])

    assert code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["valid"] is False
    assert result["workspace"] == str(workspace)


def test_extract_image_cli_forwards_revision_and_force(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    image = tmp_path / "game.iso"
    workspace = tmp_path / "workspace"
    config = tmp_path / "revision.json"
    revision = ReferenceRevision(
        revision_id="fixture-v1",
        disc_id="ULUS10066",
        disc_version="1.00",
        title="Fixture",
        psp_system_version="2.60",
        iso_size=1,
        iso_sha256="0" * 64,
    )
    manifest = WorkspaceManifest(
        revision_id="fixture-v1",
        source_iso_size=1,
        source_iso_sha256="0" * 64,
        volume_id="FIXTURE",
        sector_size=2048,
        volume_sectors=1,
        directories=(),
        files=(),
    )
    observed: dict[str, Any] = {}

    monkeypatch.setattr(cli, "load_reference_revision", lambda path: revision)

    def fake_build_workspace(
        received_image: Path,
        received_workspace: Path,
        received_revision: ReferenceRevision,
        *,
        force: bool,
    ) -> WorkspaceManifest:
        observed.update(
            image=received_image,
            workspace=received_workspace,
            revision=received_revision,
            force=force,
        )
        return manifest

    monkeypatch.setattr(cli, "build_workspace", fake_build_workspace)

    code = cli.main(
        [
            "extract-image",
            str(image),
            str(workspace),
            "--revision-config",
            str(config),
            "--force",
            "--json",
        ]
    )

    assert code == 0
    assert observed == {
        "image": image,
        "workspace": workspace,
        "revision": revision,
        "force": True,
    }
    assert json.loads(capsys.readouterr().out)["revision_id"] == "fixture-v1"
