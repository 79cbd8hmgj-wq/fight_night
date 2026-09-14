from __future__ import annotations

import os
from pathlib import Path

import pytest

from fnr3_re import cli
from fnr3_re.iso import build_workspace
from fnr3_re.ppsspp_bundle import verify_ppsspp_bundle
from fnr3_re.revision import load_reference_revision, validate_image

_RETAIL_REQUIRED_ENV = (
    "FNR3_REFERENCE_ISO",
    "FNR3_PPSSPP_BUNDLE",
    "FNR3_TASK9E_STATE",
    "FNR3_TASK9E_SAVEDATA_SLOT",
)
_REPOSITORY_REQUIRED_ENV = (
    "FNR3_PPSSPP_BUNDLE",
    "FNR3_TASK9E_RUNTIME_ROOT",
    "FNR3_TASK9E_WORKSPACE",
)
_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_REVISION_CONFIG = (
    _REPOSITORY_ROOT / "config" / "revisions" / "ulus10066-v1.00.json"
)
_PLAN = _REPOSITORY_ROOT / "analysis" / "save" / "checkpoint-9e-runtime-capture-plan.json"
_PAYLOAD = _REPOSITORY_ROOT / "analysis" / "save" / "save-payload-lifetime.json"


def _environment_path(name: str) -> Path:
    return Path(os.environ[name]).expanduser()


def _repository_mode() -> bool:
    return bool(os.environ.get("FNR3_TASK9E_RUNTIME_ROOT"))


def _require_environment(names: tuple[str, ...], mode: str) -> None:
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        pytest.skip(
            f"Task 9E {mode} live runtime is not configured: " + ", ".join(missing)
        )


def test_task9e_live_capture_requires_exact_provisioned_runtime(tmp_path: Path) -> None:
    if _repository_mode():
        _require_environment(_REPOSITORY_REQUIRED_ENV, "repository")
        runtime_root = _environment_path("FNR3_TASK9E_RUNTIME_ROOT")
        workspace = _environment_path("FNR3_TASK9E_WORKSPACE")
        bundle = _environment_path("FNR3_PPSSPP_BUNDLE")
        bootstrap_report = runtime_root / "bootstrap" / "task-9e-bootstrap.json"
        if not bootstrap_report.is_file() or bootstrap_report.is_symlink():
            pytest.skip(
                "Task 9E repository runtime has no provisioned bootstrap report; "
                "run bootstrap-save-9e first"
            )

        bundle_identity = verify_ppsspp_bundle(bundle)
        assert bundle_identity.host == "127.0.0.1"
        summary = cli._execute_capture_save_9e(
            workspace=workspace,
            bundle=bundle,
            iso=None,
            state=None,
            savedata_slot=None,
            runtime_root=runtime_root,
            bootstrap_report=bootstrap_report,
            plan_path=_PLAN,
            payload_lifetime_path=_PAYLOAD,
            capture_id="live-task9e-repository",
        )
        expected_capture_id = "live-task9e-repository"
    else:
        _require_environment(_RETAIL_REQUIRED_ENV, "retail")
        iso = _environment_path("FNR3_REFERENCE_ISO")
        bundle = _environment_path("FNR3_PPSSPP_BUNDLE")
        state = _environment_path("FNR3_TASK9E_STATE")
        savedata_slot = _environment_path("FNR3_TASK9E_SAVEDATA_SLOT")

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
            runtime_root=None,
            bootstrap_report=None,
            plan_path=_PLAN,
            payload_lifetime_path=_PAYLOAD,
            capture_id="live-task9e-retail",
        )
        expected_capture_id = "live-task9e-retail"

    assert summary.valid
    assert summary.capture_id == expected_capture_id
    assert summary.evidence_path == (
        workspace / "manifests" / "task-9e-runtime-evidence.json"
    )
    assert summary.evidence_path.is_file()
