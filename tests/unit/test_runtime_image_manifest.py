from __future__ import annotations

import json
from pathlib import Path

import pytest

from fnr3_re.runtime_image import RuntimeImageError, load_runtime_payload_manifest

_REVISION = "ULUS10066-v1.00"
_BLOB_A = "a" * 40
_BLOB_B = "b" * 40


def _entry(
    *,
    source: str = "BOOT.BIN",
    destination: str = "PSP_GAME/SYSDIR/BOOT.BIN",
    size: int = 7_270_664,
    git_blob_sha1: str = _BLOB_A,
    role: str = "executable",
    sha256: str | None = None,
) -> dict[str, object]:
    entry: dict[str, object] = {
        "source": source,
        "destination": destination,
        "size": size,
        "git_blob_sha1": git_blob_sha1,
        "role": role,
    }
    if sha256 is not None:
        entry["sha256"] = sha256
    return entry


def _write_manifest(
    path: Path,
    *,
    revision_id: str = _REVISION,
    entries: list[dict[str, object]] | None = None,
) -> Path:
    payload = {
        "schema_version": 1,
        "revision_id": revision_id,
        "entries": [_entry()] if entries is None else entries,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_payload_manifest_loads_canonical_entry(tmp_path: Path) -> None:
    path = _write_manifest(tmp_path / "manifest.json")

    manifest = load_runtime_payload_manifest(path)

    assert manifest.schema_version == 1
    assert manifest.revision_id == _REVISION
    assert len(manifest.entries) == 1
    assert manifest.entries[0].source.as_posix() == "BOOT.BIN"
    assert manifest.entries[0].destination.as_posix() == "PSP_GAME/SYSDIR/BOOT.BIN"
    assert manifest.entries[0].size == 7_270_664
    assert manifest.entries[0].git_blob_sha1 == _BLOB_A
    assert manifest.entries[0].role == "executable"
    assert manifest.entries[0].sha256 is None
    assert len(manifest.sha256) == 64


def test_payload_manifest_rejects_wrong_revision(tmp_path: Path) -> None:
    path = _write_manifest(tmp_path / "manifest.json", revision_id="ULES00000-v0.00")

    with pytest.raises(RuntimeImageError, match="revision"):
        load_runtime_payload_manifest(path)


@pytest.mark.parametrize("field", ["source", "destination"])
@pytest.mark.parametrize("value", ["/absolute.bin", "../escape.bin", "safe/../../escape.bin"])
def test_payload_manifest_rejects_unsafe_paths(tmp_path: Path, field: str, value: str) -> None:
    entry = _entry()
    entry[field] = value
    path = _write_manifest(tmp_path / "manifest.json", entries=[entry])

    with pytest.raises(RuntimeImageError, match="path"):
        load_runtime_payload_manifest(path)


def test_payload_manifest_rejects_duplicate_destinations(tmp_path: Path) -> None:
    entries = [
        _entry(),
        _entry(
            source="EBOOT.BIN",
            destination="PSP_GAME/SYSDIR/BOOT.BIN",
            size=7_271_008,
            git_blob_sha1=_BLOB_B,
        ),
    ]
    path = _write_manifest(tmp_path / "manifest.json", entries=entries)

    with pytest.raises(RuntimeImageError, match="duplicate destination"):
        load_runtime_payload_manifest(path)


def test_payload_manifest_rejects_duplicate_sources(tmp_path: Path) -> None:
    entries = [
        _entry(),
        _entry(
            destination="PSP_GAME/SYSDIR/EBOOT.BIN",
            git_blob_sha1=_BLOB_B,
        ),
    ]
    path = _write_manifest(tmp_path / "manifest.json", entries=entries)

    with pytest.raises(RuntimeImageError, match="duplicate source"):
        load_runtime_payload_manifest(path)


@pytest.mark.parametrize("git_blob_sha1", ["", "g" * 40, "a" * 39, "A" * 40])
def test_payload_manifest_rejects_invalid_git_blob_sha1(
    tmp_path: Path,
    git_blob_sha1: str,
) -> None:
    path = _write_manifest(
        tmp_path / "manifest.json",
        entries=[_entry(git_blob_sha1=git_blob_sha1)],
    )

    with pytest.raises(RuntimeImageError, match="git_blob_sha1"):
        load_runtime_payload_manifest(path)


@pytest.mark.parametrize("size", [0, -1, True])
def test_payload_manifest_rejects_invalid_size(tmp_path: Path, size: object) -> None:
    entry = _entry()
    entry["size"] = size
    path = _write_manifest(tmp_path / "manifest.json", entries=[entry])

    with pytest.raises(RuntimeImageError, match="size"):
        load_runtime_payload_manifest(path)


def test_payload_manifest_rejects_unknown_role(tmp_path: Path) -> None:
    path = _write_manifest(
        tmp_path / "manifest.json",
        entries=[_entry(role="documentation")],
    )

    with pytest.raises(RuntimeImageError, match="role"):
        load_runtime_payload_manifest(path)


def test_payload_manifest_rejects_malformed_optional_sha256(tmp_path: Path) -> None:
    path = _write_manifest(
        tmp_path / "manifest.json",
        entries=[_entry(sha256="f" * 63)],
    )

    with pytest.raises(RuntimeImageError, match="sha256"):
        load_runtime_payload_manifest(path)


def test_payload_manifest_rejects_empty_entries(tmp_path: Path) -> None:
    path = _write_manifest(tmp_path / "manifest.json", entries=[])

    with pytest.raises(RuntimeImageError, match="entries"):
        load_runtime_payload_manifest(path)
