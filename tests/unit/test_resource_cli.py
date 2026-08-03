from __future__ import annotations

import json
from pathlib import Path

import pytest

from fnr3_re import cli
from fnr3_re.ea_archive import build_ea_archive


def test_refpack_cli_round_trip_and_output_guard(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "source.bin"
    encoded = tmp_path / "source.qfs"
    decoded = tmp_path / "decoded.bin"
    source.write_bytes(b"FIGHTNIGHT" * 100)

    assert cli.main(["refpack-encode", str(source), str(encoded)]) == 0
    assert cli.main(["refpack-decode", str(encoded), str(decoded)]) == 0
    assert decoded.read_bytes() == source.read_bytes()
    with pytest.raises(FileExistsError, match="output already exists"):
        cli.main(["refpack-encode", str(source), str(encoded)])
    assert cli.main(["refpack-encode", str(source), str(encoded), "--force"]) == 0
    assert "wrote:" in capsys.readouterr().out


def test_archive_list_and_extract_cli(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    archive_path = tmp_path / "fixture.big"
    destination = tmp_path / "members"
    archive_path.write_bytes(
        build_ea_archive((("one.bin", b"1"), ("dir/two.bin", b"22")))
    )

    assert cli.main(["archive-list", str(archive_path), "--json"]) == 0
    listing = json.loads(capsys.readouterr().out)
    assert listing["magic"] == "BIGF"
    assert [member["name"] for member in listing["members"]] == [
        "one.bin",
        "dir/two.bin",
    ]

    assert (
        cli.main(
            [
                "archive-extract",
                str(archive_path),
                str(destination),
                "--json",
            ]
        )
        == 0
    )
    manifest = json.loads(capsys.readouterr().out)
    assert [entry["name"] for entry in manifest] == ["one.bin", "dir/two.bin"]
    assert (destination / "one.bin").read_bytes() == b"1"
    assert (destination / "dir" / "two.bin").read_bytes() == b"22"
