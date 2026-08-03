from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from fnr3_re.revision import (
    ReferenceRevision,
    load_reference_revision,
    read_iso9660_file,
    validate_image,
)

SECTOR_SIZE = 2048


def directory_record(identifier: bytes, extent: int, size: int, *, directory: bool) -> bytes:
    padding = b"\x00" if len(identifier) % 2 == 0 else b""
    record_length = 33 + len(identifier) + len(padding)
    record = bytearray(record_length)
    record[0] = record_length
    record[2:6] = extent.to_bytes(4, "little")
    record[6:10] = extent.to_bytes(4, "big")
    record[10:14] = size.to_bytes(4, "little")
    record[14:18] = size.to_bytes(4, "big")
    record[25] = 0x02 if directory else 0x00
    record[28:30] = (1).to_bytes(2, "little")
    record[30:32] = (1).to_bytes(2, "big")
    record[32] = len(identifier)
    record[33 : 33 + len(identifier)] = identifier
    return bytes(record)


def build_sfo(values: dict[str, str]) -> bytes:
    keys = bytearray()
    data = bytearray()
    entries: list[tuple[int, int, int, int, int]] = []
    for key, value in values.items():
        key_offset = len(keys)
        keys.extend(key.encode("utf-8") + b"\x00")
        while len(data) % 4:
            data.append(0)
        encoded = value.encode("utf-8") + b"\x00"
        data_offset = len(data)
        data.extend(encoded)
        entries.append((key_offset, 0x0204, len(encoded), len(encoded), data_offset))

    entry_table_size = 16 * len(entries)
    key_table_offset = 20 + entry_table_size
    data_table_offset = (key_table_offset + len(keys) + 3) & ~3
    output = bytearray(data_table_offset + len(data))
    output[0:4] = b"\x00PSF"
    output[4:8] = (0x00000101).to_bytes(4, "little")
    output[8:12] = key_table_offset.to_bytes(4, "little")
    output[12:16] = data_table_offset.to_bytes(4, "little")
    output[16:20] = len(entries).to_bytes(4, "little")
    for index, (key_offset, value_type, value_len, max_len, data_offset) in enumerate(entries):
        offset = 20 + index * 16
        output[offset : offset + 2] = key_offset.to_bytes(2, "little")
        output[offset + 2 : offset + 4] = value_type.to_bytes(2, "little")
        output[offset + 4 : offset + 8] = value_len.to_bytes(4, "little")
        output[offset + 8 : offset + 12] = max_len.to_bytes(4, "little")
        output[offset + 12 : offset + 16] = data_offset.to_bytes(4, "little")
    output[key_table_offset : key_table_offset + len(keys)] = keys
    output[data_table_offset : data_table_offset + len(data)] = data
    return bytes(output)


def build_iso(metadata: dict[str, str]) -> bytes:
    sectors = 32
    image = bytearray(sectors * SECTOR_SIZE)
    root_sector = 20
    psp_game_sector = 21
    sfo_sector = 22
    sfo = build_sfo(metadata)

    pvd = memoryview(image)[16 * SECTOR_SIZE : 17 * SECTOR_SIZE]
    pvd[0] = 1
    pvd[1:6] = b"CD001"
    pvd[6] = 1
    pvd[128:130] = SECTOR_SIZE.to_bytes(2, "little")
    pvd[130:132] = SECTOR_SIZE.to_bytes(2, "big")
    root_record = directory_record(b"\x00", root_sector, SECTOR_SIZE, directory=True)
    pvd[156 : 156 + len(root_record)] = root_record

    terminator = memoryview(image)[17 * SECTOR_SIZE : 18 * SECTOR_SIZE]
    terminator[0] = 255
    terminator[1:6] = b"CD001"
    terminator[6] = 1

    root = memoryview(image)[root_sector * SECTOR_SIZE : (root_sector + 1) * SECTOR_SIZE]
    records = [
        directory_record(b"\x00", root_sector, SECTOR_SIZE, directory=True),
        directory_record(b"\x01", root_sector, SECTOR_SIZE, directory=True),
        directory_record(b"PSP_GAME", psp_game_sector, SECTOR_SIZE, directory=True),
    ]
    cursor = 0
    for record in records:
        root[cursor : cursor + len(record)] = record
        cursor += len(record)

    psp_game = memoryview(image)[
        psp_game_sector * SECTOR_SIZE : (psp_game_sector + 1) * SECTOR_SIZE
    ]
    records = [
        directory_record(b"\x00", psp_game_sector, SECTOR_SIZE, directory=True),
        directory_record(b"\x01", root_sector, SECTOR_SIZE, directory=True),
        directory_record(b"PARAM.SFO;1", sfo_sector, len(sfo), directory=False),
    ]
    cursor = 0
    for record in records:
        psp_game[cursor : cursor + len(record)] = record
        cursor += len(record)

    start = sfo_sector * SECTOR_SIZE
    image[start : start + len(sfo)] = sfo
    return bytes(image)


def reference_for(image: bytes, *, iso_sha256: str | None = None) -> ReferenceRevision:
    return ReferenceRevision(
        revision_id="fixture-v1",
        disc_id="ULUS10066",
        disc_version="1.00",
        title="EA SPORTS™ FIGHT NIGHT Round 3",
        psp_system_version="2.60",
        iso_size=len(image),
        iso_sha256=iso_sha256 or hashlib.sha256(image).hexdigest(),
    )


@pytest.fixture
def metadata() -> dict[str, str]:
    return {
        "DISC_ID": "ULUS10066",
        "DISC_VERSION": "1.00",
        "TITLE": "EA SPORTS™ FIGHT NIGHT Round 3",
        "PSP_SYSTEM_VER": "2.60",
    }


def test_reference_config_locks_known_usa_revision() -> None:
    root = Path(__file__).resolve().parents[2]
    revision = load_reference_revision(root / "config" / "revisions" / "ulus10066-v1.00.json")

    assert revision.revision_id == "ULUS10066-v1.00"
    assert revision.disc_id == "ULUS10066"
    assert revision.disc_version == "1.00"
    assert revision.iso_size == 1_137_737_728
    assert revision.iso_sha256 == "b11da5afe208d9791eecd9f6a44d0f57946f7d9de165b7d8dd22f5ee740f4ee2"


def test_valid_synthetic_reference_image_passes(tmp_path: Path, metadata: dict[str, str]) -> None:
    image = build_iso(metadata)
    path = tmp_path / "game.iso"
    path.write_bytes(image)

    result = validate_image(path, reference_for(image))

    assert result.valid
    assert result.diagnostics == ()
    assert result.observed_metadata == metadata
    assert json.loads(result.to_json())["valid"] is True


def test_hash_mismatch_is_rejected_even_when_metadata_matches(
    tmp_path: Path, metadata: dict[str, str]
) -> None:
    image = build_iso(metadata)
    path = tmp_path / "game.iso"
    path.write_bytes(image)

    result = validate_image(path, reference_for(image, iso_sha256="0" * 64))

    assert not result.valid
    assert any(item.startswith("ISO SHA-256 mismatch:") for item in result.diagnostics)


def test_metadata_mismatch_is_reported_independently(
    tmp_path: Path, metadata: dict[str, str]
) -> None:
    modified = dict(metadata)
    modified["DISC_ID"] = "ULUS99999"
    image = build_iso(modified)
    path = tmp_path / "game.iso"
    path.write_bytes(image)

    result = validate_image(path, reference_for(image))

    assert not result.valid
    assert "PARAM.SFO DISC_ID mismatch: expected ULUS10066, got ULUS99999" in result.diagnostics


def test_missing_or_malformed_iso_is_rejected(tmp_path: Path, metadata: dict[str, str]) -> None:
    missing = validate_image(tmp_path / "missing.iso", reference_for(build_iso(metadata)))
    assert not missing.valid
    assert missing.diagnostics == ("image file does not exist",)

    malformed_path = tmp_path / "malformed.iso"
    malformed_path.write_bytes(b"not an ISO")
    malformed = validate_image(malformed_path, reference_for(b"not an ISO"))
    assert not malformed.valid
    assert any(item.startswith("invalid ISO9660 image:") for item in malformed.diagnostics)


def test_iso9660_lookup_is_case_insensitive_and_strips_version(
    tmp_path: Path, metadata: dict[str, str]
) -> None:
    image = build_iso(metadata)
    path = tmp_path / "game.iso"
    path.write_bytes(image)

    value = read_iso9660_file(path, "psp_game/param.sfo")

    assert value == build_sfo(metadata)
