from __future__ import annotations

import os
from pathlib import Path

import pytest

from fnr3_re.iso import build_workspace
from fnr3_re.module_map import ModuleKind, build_workspace_module_map
from fnr3_re.revision import load_reference_revision

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_CONFIG = ROOT / "config" / "revisions" / "ulus10066-v1.00.json"


@pytest.mark.skipif(
    "FNR3_REFERENCE_ISO" not in os.environ,
    reason="FNR3_REFERENCE_ISO is not configured",
)
def test_reference_image_contains_main_pair_and_six_prx_modules(tmp_path: Path) -> None:
    reference = Path(os.environ["FNR3_REFERENCE_ISO"])
    revision = load_reference_revision(REFERENCE_CONFIG)
    workspace = tmp_path / "workspace"
    build_workspace(reference, workspace, revision)

    module_map = build_workspace_module_map(workspace)
    paths = [module.path for module in module_map.modules]
    prx_modules = [module for module in module_map.modules if module.path.lower().endswith(".prx")]

    assert module_map.revision_id == revision.revision_id
    assert len(module_map.modules) == 8
    assert len(prx_modules) == 6
    assert "PSP_GAME/SYSDIR/BOOT.BIN" in paths
    assert "PSP_GAME/SYSDIR/EBOOT.BIN" in paths
    assert sum(module.kind is ModuleKind.PLAIN_ELF for module in module_map.modules) >= 1
    assert all(module.runtime_base is None for module in module_map.modules)
    assert module_map.to_json() == build_workspace_module_map(workspace).to_json()
