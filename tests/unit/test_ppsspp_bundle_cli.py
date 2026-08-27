from __future__ import annotations

import json
from pathlib import Path

from fnr3_re import cli
from fnr3_re.ppsspp_bundle import DebuggerBundleIdentity


def _identity(root: Path) -> DebuggerBundleIdentity:
    return DebuggerBundleIdentity(
        root=root,
        revision="fixture-revision",
        sdl_path=root / "PPSSPPSDL",
        sdl_sha256="a" * 64,
        headless_path=root / "PPSSPPHeadless",
        headless_sha256="b" * 64,
        xvfb_path=root / "bin" / "Xvfb",
        xvfb_sha256="c" * 64,
        launcher_path=root / "launch-debug.sh",
        client_path=root / "ppsspp_ws.py",
        config_path=root / "ppsspp-debug.ini",
        host="127.0.0.1",
        port=56244,
    )


def test_ppsspp_bundle_verify_cli_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    bundle = tmp_path / "bundle"
    expected = _identity(bundle.resolve())
    monkeypatch.setattr(cli, "verify_ppsspp_bundle", lambda path: expected, raising=False)

    assert cli.main(["ppsspp-bundle", "verify", str(bundle)]) == 0

    output = capsys.readouterr().out
    assert "fixture-revision" in output
    assert "127.0.0.1:56244" in output


def test_ppsspp_bundle_verify_cli_json_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    bundle = tmp_path / "bundle"
    expected = _identity(bundle.resolve())
    monkeypatch.setattr(cli, "verify_ppsspp_bundle", lambda path: expected, raising=False)

    assert cli.main(["ppsspp-bundle", "verify", str(bundle), "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "headless_sha256": "b" * 64,
        "host": "127.0.0.1",
        "port": 56244,
        "revision": "fixture-revision",
        "sdl_sha256": "a" * 64,
        "xvfb_sha256": "c" * 64,
    }
