from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath

import pytest

from fnr3_re.revision import ReferenceRevision
from fnr3_re.runtime_image import (
    RuntimeImageError,
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


def _manifest(repository_root: Path) -> RuntimePayloadManifest:
    entries: list[RuntimePayloadEntry] = []
    for source, destination, payload in (
        ("BOOT.BIN", "PSP_GAME/SYSDIR/BOOT.BIN", b"BOOT"),
        ("EBOOT.BIN", "PSP_GAME/SYSDIR/EBOOT.BIN", b"EBOOT"),
    ):
        path = repository_root / source
        path.write_bytes(payload)
        entries.append(
            RuntimePayloadEntry(
                source=PurePosixPath(source),
                destination=PurePosixPath(destination),
                size=len(payload),
                git_blob_sha1=_git_blob_sha1(payload),
                role="executable",
                sha256=hashlib.sha256(payload).hexdigest(),
            )
        )
    return RuntimePayloadManifest(
        schema_version=1,
        revision_id="ULUS10066-v1.00",
        entries=tuple(entries),
        sha256="2" * 64,
    )


def test_prepare_runtime_image_rejects_symlink_output_component(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    manifest = _manifest(repository_root)
    outside = tmp_path / "outside"
    outside.mkdir()
    linked_parent = tmp_path / "linked"
    linked_parent.symlink_to(outside, target_is_directory=True)

    with pytest.raises(RuntimeImageError, match="symlink"):
        prepare_runtime_image(
            repository_root,
            linked_parent / "runtime",
            manifest,
            _revision(),
        )

    assert not (outside / "runtime").exists()


def test_force_replace_rolls_back_if_atomic_swap_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    manifest = _manifest(repository_root)
    output = tmp_path / "runtime"
    output.mkdir()
    marker = output / "known-good.txt"
    marker.write_text("preserve me", encoding="utf-8")

    real_replace = os.replace
    failed_final_swap = False

    def fail_final_replace(source: str | Path, destination: str | Path) -> None:
        nonlocal failed_final_swap
        source_path = Path(source)
        destination_path = Path(destination)
        if (
            not failed_final_swap
            and destination_path == output
            and source_path.name.startswith(".runtime.tmp-")
        ):
            failed_final_swap = True
            raise OSError("simulated atomic replacement failure")
        real_replace(source, destination)

    monkeypatch.setattr("fnr3_re.runtime_image.os.replace", fail_final_replace)

    with pytest.raises(OSError, match="simulated atomic replacement failure"):
        prepare_runtime_image(
            repository_root,
            output,
            manifest,
            _revision(),
            force=True,
        )

    assert marker.read_text(encoding="utf-8") == "preserve me"
    assert not list(tmp_path.glob(".runtime.tmp-*"))
    assert not list(tmp_path.glob(".runtime.bak-*"))
