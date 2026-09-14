from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath

from fnr3_re.revision import ReferenceRevision, parse_param_sfo, read_iso9660_file
from fnr3_re.runtime_image import (
    RuntimePayloadEntry,
    RuntimePayloadManifest,
    prepare_runtime_image,
)


def _git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode()
    return hashlib.sha1(header + payload).hexdigest()


def _revision() -> ReferenceRevision:
    return ReferenceRevision(
        revision_id="ULUS10066-v1.00",
        disc_id="ULUS10066",
        disc_version="1.00",
        title="EA SPORTS™ FIGHT NIGHT Round 3",
        psp_system_version="2.60",
        iso_size=1,
        iso_sha256="1" * 64,
    )


def _write_payload(repository_root: Path) -> RuntimePayloadManifest:
    payloads = {
        "BOOT.BIN": b"BOOT-CONTENT",
        "EBOOT.BIN": b"EBOOT-CONTENT",
        "data/nested.bin": b"NESTED-CONTENT",
    }
    destinations = {
        "BOOT.BIN": "PSP_GAME/SYSDIR/BOOT.BIN",
        "EBOOT.BIN": "PSP_GAME/SYSDIR/EBOOT.BIN",
        "data/nested.bin": "PSP_GAME/USRDIR/data/nested.bin",
    }
    entries: list[RuntimePayloadEntry] = []
    for source, payload in payloads.items():
        path = repository_root / source
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        entries.append(
            RuntimePayloadEntry(
                source=PurePosixPath(source),
                destination=PurePosixPath(destinations[source]),
                size=len(payload),
                git_blob_sha1=_git_blob_sha1(payload),
                role="executable" if source in {"BOOT.BIN", "EBOOT.BIN"} else "game_data",
                sha256=hashlib.sha256(payload).hexdigest(),
            )
        )
    return RuntimePayloadManifest(
        schema_version=1,
        revision_id="ULUS10066-v1.00",
        entries=tuple(entries),
        sha256="2" * 64,
    )


def test_prepare_runtime_image_is_byte_deterministic_and_readable(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    manifest = _write_payload(repository_root)

    report_a = prepare_runtime_image(repository_root, tmp_path / "a", manifest, _revision())
    report_b = prepare_runtime_image(repository_root, tmp_path / "b", manifest, _revision())

    iso_a = tmp_path / "a" / "fight-night-runtime.iso"
    iso_b = tmp_path / "b" / "fight-night-runtime.iso"
    assert iso_a.read_bytes() == iso_b.read_bytes()
    assert report_a.runtime_iso_sha256 == report_b.runtime_iso_sha256
    assert report_a.runtime_iso_sha256 != report_a.retail_iso_sha256
    assert report_a.source_mode == "repository_runtime_image"
    assert report_a.deterministic is True

    assert read_iso9660_file(iso_a, "PSP_GAME/SYSDIR/BOOT.BIN") == b"BOOT-CONTENT"
    assert read_iso9660_file(iso_a, "PSP_GAME/SYSDIR/EBOOT.BIN") == b"EBOOT-CONTENT"
    assert read_iso9660_file(iso_a, "PSP_GAME/USRDIR/data/nested.bin") == b"NESTED-CONTENT"
    sfo = parse_param_sfo(read_iso9660_file(iso_a, "PSP_GAME/PARAM.SFO"))
    assert sfo["DISC_ID"] == "ULUS10066"
    assert sfo["DISC_VERSION"] == "1.00"
    assert sfo["PSP_SYSTEM_VER"] == "2.60"
    assert sfo["TITLE"] == "EA SPORTS™ FIGHT NIGHT Round 3"
