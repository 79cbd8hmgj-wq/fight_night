from pathlib import Path

_REPOSITORY = Path(__file__).resolve().parents[2]
_WORKFLOW = _REPOSITORY / ".github/workflows/build-ppsspp-research.yml"
_BUNDLE_TOOLS = _REPOSITORY / "tools/ppsspp-debugger-bundle"
_DOC = _REPOSITORY / "docs/architecture/ppsspp-debugger-bundle.md"
_PINNED_PPSSPP_COMMIT = "49fb4f9b1a91bd210c2332958106a0bf6dc02c27"


def test_ppsspp_debugger_builder_is_manual_only_and_pinned() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in text
    assert "pull_request:" not in text
    assert "\n  push:" not in text
    assert f"default: {_PINNED_PPSSPP_COMMIT}" in text
    assert 'test "$resolved" = "$PPSSPP_REVISION"' in text
    assert "git checkout --detach" in text
    assert "git rev-parse HEAD" in text
    assert "permissions:\n  contents: read" in text


def test_ppsspp_debugger_builder_packages_both_frontends_and_wsdbg() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")

    assert "-DHEADLESS=ON" in text
    assert "--target PPSSPPHeadless" in text
    assert "-DHEADLESS=OFF" in text
    assert "--target PPSSPPSDL" in text
    assert "ppsspp/Tools/wsdbg/Cargo.toml" in text
    assert "test -f Tools/wsdbg/Cargo.lock" in text
    assert "bundle/wsdbg" in text
    assert "PPSSPP-WebSocket-Debugger.md" in text
    assert "memory.breakpoint.add" in text
    assert "input.buttons.send" in text


def test_ppsspp_debugger_builder_is_game_data_free() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")

    assert "actions/upload-artifact@v4" in text
    assert "ppsspp-resolved-revision.txt" in text
    assert "secrets." not in text
    assert "FNR3_REFERENCE_ISO" not in text
    assert "*.iso" not in text.casefold()
    assert "*.ppst" not in text.casefold()
    assert "savedata" not in text.casefold()


def test_ppsspp_debugger_bundle_launchers_use_confirmed_transport() -> None:
    headless = (_BUNDLE_TOOLS / "run-headless-debugger.sh").read_text(
        encoding="utf-8"
    )
    sdl = (_BUNDLE_TOOLS / "run-sdl-debugger.sh").read_text(encoding="utf-8")
    client = (_BUNDLE_TOOLS / "wsdbg.sh").read_text(encoding="utf-8")
    documentation = _DOC.read_text(encoding="utf-8")

    assert 'PPSSPPHeadless" --debugger="$PORT" "$ISO"' in headless
    assert 'PPSSPPSDL" --debugger="$PORT" "$ISO"' in sdl
    assert 'exec "$ROOT/wsdbg" "$PORT" "$@"' in client
    assert "debugger.ppsspp.org" in documentation
    assert "A PSP state is not required" in documentation
    assert "save state is optional" in documentation
