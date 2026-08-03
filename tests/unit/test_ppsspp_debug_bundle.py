from __future__ import annotations

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_WORKFLOW = _ROOT / ".github/workflows/build-ppsspp-research.yml"
_TOOLS = _ROOT / "tools/ppsspp_debug_bundle"


def test_builder_packages_runtime_debugger_bundle() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")

    assert "actions/checkout@v4" in text
    assert "--target PPSSPPSDL" in text
    assert "--target PPSSPPHeadless" in text
    assert "scripts/websocket-test.py" in text
    assert "tools/ppsspp_debug_bundle" in text
    assert "PPSSPPSDL.sha256" in text
    assert "PPSSPPHeadless.sha256" in text
    assert "ppsspp-debug-linux-x86_64" in text
    assert "Fight Night" not in text
    assert "*.iso" not in text.casefold()
    assert "*.ppst" not in text.casefold()


def test_bundle_has_launcher_client_and_state_contract() -> None:
    required = {
        "README.md",
        "launch-debug.sh",
        "stop-debug.sh",
        "install-state.sh",
        "ppsspp-debug.ini",
        "ppsspp_ws.py",
    }
    assert required == {path.name for path in _TOOLS.iterdir() if path.is_file()}

    launcher = (_TOOLS / "launch-debug.sh").read_text(encoding="utf-8")
    assert "RemoteDebuggerOnStartup" in launcher
    assert "RemoteDebuggerLocal" in launcher
    assert "56244" in launcher
    assert "PPSSPP_STATE" in launcher
    assert "sha256sum" in launcher

    state_installer = (_TOOLS / "install-state.sh").read_text(encoding="utf-8")
    assert "PPSSPP_STATE" in state_installer
    assert "state-manifest.sha256" in state_installer
    assert "basename" in state_installer


def test_websocket_client_is_stdlib_only_and_exposes_health_command() -> None:
    client_path = _TOOLS / "ppsspp_ws.py"
    source = client_path.read_text(encoding="utf-8")
    assert "from websocket" not in source
    assert "import websockets" not in source
    assert '"game.status"' in source
    assert '"/debugger"' in source

    spec = importlib.util.spec_from_file_location("ppsspp_ws", client_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    encoded = module.encode_client_text_frame("{}", mask_key=b"\x01\x02\x03\x04")
    assert encoded[:2] == b"\x81\x82"
    assert encoded[2:6] == b"\x01\x02\x03\x04"
    assert encoded[6:] == b"z\x7f"
