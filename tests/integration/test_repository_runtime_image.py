from __future__ import annotations

import hashlib
from pathlib import Path

from fnr3_re.psp_sfo import build_runtime_param_sfo
from fnr3_re.revision import (
    hash_file,
    load_reference_revision,
    parse_param_sfo,
    read_iso9660_file,
)
from fnr3_re.runtime_image import load_runtime_payload_manifest, prepare_runtime_image

_LOCKED_BOOT_SHA256 = "906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9"
_LOCKED_RETAIL_ISO_SHA256 = "b11da5afe208d9791eecd9f6a44d0f57946f7d9de165b7d8dd22f5ee740f4ee2"


def test_repository_payload_builds_deterministic_runtime_iso(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    manifest = load_runtime_payload_manifest(
        root / "config/runtime/ulus10066-repository-payload.json"
    )
    revision = load_reference_revision(root / "config/revisions/ulus10066-v1.00.json")
    output = tmp_path / "runtime"

    report = prepare_runtime_image(root, output, manifest, revision)
    runtime_iso = output / "fight-night-runtime.iso"
    report_path = output / "runtime-image.json"

    assert runtime_iso.is_file()
    assert report_path.read_text(encoding="utf-8") == report.to_json()
    assert report.schema_version == 1
    assert report.revision_id == "ULUS10066-v1.00"
    assert report.source_mode == "repository_runtime_image"
    assert report.retail_iso_sha256 == _LOCKED_RETAIL_ISO_SHA256
    assert report.runtime_iso_sha256 == hash_file(runtime_iso)
    assert report.runtime_iso_sha256 != report.retail_iso_sha256
    assert report.runtime_iso_size == runtime_iso.stat().st_size
    assert report.runtime_iso_size < revision.iso_size
    assert report.payload_manifest_sha256 == manifest.sha256
    assert report.boot_sha256 == _LOCKED_BOOT_SHA256
    assert report.eboot_sha256 == hash_file(root / "EBOOT.BIN")
    assert report.deterministic is True
    assert len(report.files) == len(manifest.entries) + 1

    param_sfo = build_runtime_param_sfo(revision)
    param_sha256 = hashlib.sha256(param_sfo).hexdigest()
    assert report.generated_metadata == (("PSP_GAME/PARAM.SFO", param_sha256),)

    assert read_iso9660_file(runtime_iso, "PSP_GAME/SYSDIR/BOOT.BIN") == (
        root / "BOOT.BIN"
    ).read_bytes()
    assert read_iso9660_file(runtime_iso, "PSP_GAME/SYSDIR/EBOOT.BIN") == (
        root / "EBOOT.BIN"
    ).read_bytes()
    assert read_iso9660_file(runtime_iso, "PSP_GAME/USRDIR/bootfonts.txt") == (
        root / "bootfonts.txt"
    ).read_bytes()
    observed_sfo = read_iso9660_file(runtime_iso, "PSP_GAME/PARAM.SFO")
    assert observed_sfo == param_sfo
    metadata = parse_param_sfo(observed_sfo)
    assert metadata["DISC_ID"] == revision.disc_id
    assert metadata["DISC_VERSION"] == revision.disc_version
    assert metadata["PSP_SYSTEM_VER"] == revision.psp_system_version
    assert metadata["TITLE"] == revision.title
