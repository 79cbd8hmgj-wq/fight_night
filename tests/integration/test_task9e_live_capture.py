from __future__ import annotations

import os
from pathlib import Path

import pytest

from fnr3_re import cli
from fnr3_re.iso import build_workspace
from fnr3_re.ppsspp_bundle import verify_ppsspp_bundle
from fnr3_re.revision import load_reference_revision, validate_image

_REQUIRED_ENV = (
    "FNR3_REFERENCE_ISO",
    "FNR3_PPSSPP_BUNDLE",
    "FNR3_TASK9E_STATE",
    "FNR3_TASK9E_SAVEDATA_SLOT",
)
_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_REVISION_CONFIG = (
    _REPOSITORY_ROOT / "config" / "revisions" / "ulus10066-v1.00.json"
)
_PLAN = _REPOSITORY_ROOT / "analysis" / "save" / "checkpoint-9e-runtime-capture-plan.json"
_PAYLOAD = _REPOSITORY_ROOT / "analysis" / "save" / "save-payload-lifetime.json"


def _configured_paths() -> dict[str, Path]:
    missing = [name for name in _REQUIRED_ENV if not os.environ.get(name)]
    if missing:
        pytest.skip("Task 9E live runtime is not configured: " + ", ".join(missing))
    return {name: Path(os.environ[name]).expanduser() for name in _REQUIRED_ENV}


def test_task9e_live_capture_requires_exact_provisioned_runtime(tmp_path: Path) -> None:
    paths = _configured_paths()
    iso = paths["FNR3_REFERENCE_ISO"]
    bundle = paths["FNR3_PPSSPP_BUNDLE"]
    state = paths["FNR3_TASK9E_STATE"]
    savedata_slot = paths["FNR3_TASK9E_SAVEDATA_SLOT"]

    revision = load_reference_revision(_REVISION_CONFIG)
    image_result = validate_image(iso, revision)
    assert image_result.valid, image_result.diagnostics
    bundle_identity = verify_ppsspp_bundle(bundle)
    assert bundle_identity.host == "127.0.0.1"
    assert state.is_file() and not state.is_symlink()
    assert savedata_slot.is_dir() and not savedata_slot.is_symlink()

    workspace = tmp_path / "workspace"
    build_workspace(iso, workspace, revision)
    summary = cli._execute_capture_save_9e(
        workspace=workspace,
        bundle=bundle,
        iso=iso,
        state=state,
        savedata_slot=savedata_slot,
        plan_path=_PLAN,
        payload_lifetime_path=_PAYLOAD,
        capture_id="live-task9e",
    )

    assert summary.valid
    assert summary.capture_id == "live-task9e"
    assert summary.evidence_path == (
        workspace / "manifests" / "task-9e-runtime-evidence.json"
    )
    assert summary.evidence_path.is_file()
