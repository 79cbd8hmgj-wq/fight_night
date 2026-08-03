from pathlib import Path

_WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/build-ppsspp-research.yml"


def test_ppsspp_research_builder_is_manual_only_and_pinned() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in text
    assert "pull_request:" not in text
    assert "\n  push:" not in text
    assert "default: v1.20.4" in text
    assert "git checkout --detach" in text
    assert "git rev-parse HEAD" in text


def test_ppsspp_research_builder_targets_headless_without_game_inputs() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")

    assert "-DHEADLESS=ON" in text
    assert "--target PPSSPPHeadless" in text
    assert "actions/upload-artifact@v4" in text
    assert "PPSSPPHeadless.sha256" in text
    assert "ppsspp-resolved-revision.txt" in text
    assert "secrets." not in text
    assert "FNR3_REFERENCE_ISO" not in text
    assert "*.iso" not in text.casefold()
