from __future__ import annotations

import hashlib
import json
import stat
from pathlib import Path

import pytest

from fnr3_re.manifests import (
    ManifestDirectory,
    ManifestFile,
    WorkspaceManifest,
    classify_iso_path,
)
from fnr3_re.psp_modules import PspModuleAnalysisError, discover_psp_module_candidates
from tests.support.psp_exec import build_minimal_mips_elf

FNR3_ISO_SHA256 = "b11da5afe208d9791eecd9f6a44d0f57946f7d9de165b7d8dd22f5ee740f4ee2"


def _make_workspace(tmp_path: Path, files: dict[str, bytes]) -> Path:
    workspace = tmp_path / "workspace"
    original = workspace / "original"
    working = workspace / "working"
    modified = workspace / "modified"
    manifests = workspace / "manifests"
    original.mkdir(parents=True)
    working.mkdir()
    modified.mkdir()
    manifests.mkdir()

    manifest_files: list[ManifestFile] = []
    for order, (path, payload) in enumerate(files.items()):
        destination = original / Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        destination.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        manifest_files.append(
            ManifestFile(
                path=path,
                lba=100 + order,
                offset=(100 + order) * 2048,
                size=len(payload),
                sha256=hashlib.sha256(payload).hexdigest(),
                order=order,
                classification=classify_iso_path(path),
            )
        )

    manifest = WorkspaceManifest(
        revision_id="ULUS10066-v1.00",
        source_iso_size=1137737728,
        source_iso_sha256=FNR3_ISO_SHA256,
        volume_id="FNR3TEST",
        sector_size=2048,
        volume_sectors=555536,
        directories=(ManifestDirectory(path=".", lba=20, offset=40960, size=2048, order=0),),
        files=tuple(manifest_files),
    )
    (manifests / "workspace.json").write_text(manifest.to_json(), encoding="utf-8")
    return workspace


def test_discovery_uses_verified_manifest_paths_and_content(tmp_path: Path) -> None:
    workspace = _make_workspace(
        tmp_path,
        {
            "PSP_GAME/SYSDIR/BOOT.BIN": build_minimal_mips_elf(),
            "PSP_GAME/USRDIR/NET.PRX": build_minimal_mips_elf(),
            "PSP_GAME/USRDIR/OTHER.BIN": build_minimal_mips_elf(),
            "PSP_GAME/USRDIR/NOTE.TXT": b"plain text",
        },
    )

    found = discover_psp_module_candidates(workspace)

    assert [item.workspace_path for item in found] == [
        "PSP_GAME/SYSDIR/BOOT.BIN",
        "PSP_GAME/USRDIR/NET.PRX",
        "PSP_GAME/USRDIR/OTHER.BIN",
    ]
    assert found[0].is_boot is True
    assert found[0].iso_lba == 100
    assert found[0].iso_byte_offset == 100 * 2048


def test_workspace_hash_drift_is_rejected_before_discovery(tmp_path: Path) -> None:
    workspace = _make_workspace(
        tmp_path,
        {"PSP_GAME/SYSDIR/BOOT.BIN": build_minimal_mips_elf()},
    )
    boot = workspace / "original" / "PSP_GAME" / "SYSDIR" / "BOOT.BIN"
    boot.chmod(stat.S_IRUSR | stat.S_IWUSR)
    boot.write_bytes(b"drift")
    boot.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    with pytest.raises(PspModuleAnalysisError, match="workspace verification failed"):
        discover_psp_module_candidates(workspace)


def test_wrong_reference_revision_is_rejected(tmp_path: Path) -> None:
    workspace = _make_workspace(
        tmp_path,
        {"PSP_GAME/SYSDIR/BOOT.BIN": build_minimal_mips_elf()},
    )
    manifest_path = workspace / "manifests" / "workspace.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["source_iso_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(PspModuleAnalysisError, match=r"ULUS10066-v1\.00"):
        discover_psp_module_candidates(workspace)


def test_symbolic_link_in_original_is_rejected(tmp_path: Path) -> None:
    workspace = _make_workspace(
        tmp_path,
        {"PSP_GAME/SYSDIR/BOOT.BIN": build_minimal_mips_elf()},
    )
    outside = tmp_path / "outside.bin"
    outside.write_bytes(build_minimal_mips_elf())
    link = workspace / "original" / "PSP_GAME" / "USRDIR" / "ESCAPE.PRX"
    link.parent.mkdir(parents=True)
    link.symlink_to(outside)

    with pytest.raises(PspModuleAnalysisError, match="workspace verification failed"):
        discover_psp_module_candidates(workspace)
