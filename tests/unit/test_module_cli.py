from __future__ import annotations

import json
from pathlib import Path

import pytest

from fnr3_re import cli
from fnr3_re.module_map import ModuleMap


def test_module_map_cli_prints_and_writes_deterministic_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    output = tmp_path / "modules.json"
    module_map = ModuleMap(revision_id="fixture-v1", modules=())
    monkeypatch.setattr(cli, "build_workspace_module_map", lambda path: module_map)

    code = cli.main(
        [
            "module-map",
            str(workspace),
            "--output",
            str(output),
            "--json",
        ]
    )

    assert code == 0
    assert json.loads(capsys.readouterr().out)["revision_id"] == "fixture-v1"
    assert output.read_text(encoding="utf-8") == module_map.to_json()


def test_module_map_cli_requires_force_for_existing_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    output = tmp_path / "modules.json"
    output.write_text("existing", encoding="utf-8")
    module_map = ModuleMap(revision_id="fixture-v1", modules=())
    monkeypatch.setattr(cli, "build_workspace_module_map", lambda path: module_map)

    with pytest.raises(FileExistsError, match="output already exists"):
        cli.main(["module-map", str(workspace), "--output", str(output)])

    assert (
        cli.main(
            [
                "module-map",
                str(workspace),
                "--output",
                str(output),
                "--force",
            ]
        )
        == 0
    )
    assert output.read_text(encoding="utf-8") == module_map.to_json()
