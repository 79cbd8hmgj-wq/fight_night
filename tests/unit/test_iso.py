from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from fnr3_re.iso import IsoFormatError, build_workspace, scan_iso, verify_workspace
from fnr3_re.revision import ReferenceRevision

SECTOR_SIZE = 2048


def directory_record(
    identifier: bytes,
    extent: int,
    size: int,
    *,
    directory: bool,
    flags: int = 0,
) -> bytes:
    padding = b"\x00" if len(identifier) % 2 == 0 else b""
    record_length = 33 + len(identifier) + len(padding)
    record = bytearray(record_length)
    record[0] = record_length
    record[2:6] = extent.to_bytes(4, "little")
    record[6:10] = extent.to_bytes(4, "big")
    record[10:14] = size.to_bytes(4, "little")
    record[14:18] = size.to_bytes(4, "big")
    record[25] = flags | (0x02 if directory else 0x00)
    record[28:30] = (1).to_bytes(2, "little")
    record[30:32] = (1).to_bytes(2, "big")
    record[32] = len(identifier)
    record[33 : 33 + len(identifier)] = identifier
    return bytes(record)


def write_directory(image: bytearray, sector: int, records: list[bytes]) -> None:
    payload = memoryview(image)[sector * SECTOR_SIZE : (sector + 1) * SECTOR_SIZE]
    cursor = 0
    for record in records:
        payload[cursor : cursor + len(record)] = record
        cursor += len(record)


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


def build_test_iso(
    *,
    duplicate_boot: bool = False,
    overlapping_files: bool = False,
    unsafe_name: bool = False,
    multi_extent: bool = False,
    declared_sectors: int | None = None,
) -> bytes:
    sectors = 32
    image = bytearray(sectors * SECTOR_SIZE)
    root_sector = 20
    psp_game_sector = 21
    sysdir_sector = 22
    usrdir_sector = 23
    param_sector = 24
    boot_sector = 25
    data_sector = boot_sector if overlapping_files else 26

    param_payload = build_sfo(
        {
            "DISC_ID": "ULUS10066",
            "DISC_VERSION": "1.00",
            "TITLE": "Fixture",
            "PSP_SYSTEM_VER": "2.60",
        }
    )
    boot_payload = b"BOOT-CONTENT"
    data_payload = b"RESOURCE-CONTENT"

    pvd = memoryview(image)[16 * SECTOR_SIZE : 17 * SECTOR_SIZE]
    pvd[0] = 1
    pvd[1:6] = b"CD001"
    pvd[6] = 1
    pvd[40:72] = b"FNR3TEST".ljust(32, b" ")
    volume_sectors = declared_sectors if declared_sectors is not None else sectors
    pvd[80:84] = volume_sectors.to_bytes(4, "little")
    pvd[84:88] = volume_sectors.to_bytes(4, "big")
    pvd[128:130] = SECTOR_SIZE.to_bytes(2, "little")
    pvd[130:132] = SECTOR_SIZE.to_bytes(2, "big")
    root_record = directory_record(b"\x00", root_sector, SECTOR_SIZE, directory=True)
    pvd[156 : 156 + len(root_record)] = root_record

    terminator = memoryview(image)[17 * SECTOR_SIZE : 18 * SECTOR_SIZE]
    terminator[0] = 255
    terminator[1:6] = b"CD001"
    terminator[6] = 1

    write_directory(
        image,
        root_sector,
        [
            directory_record(b"\x00", root_sector, SECTOR_SIZE, directory=True),
            directory_record(b"\x01", root_sector, SECTOR_SIZE, directory=True),
            directory_record(b"PSP_GAME", psp_game_sector, SECTOR_SIZE, directory=True),
        ],
    )
    write_directory(
        image,
        psp_game_sector,
        [
            directory_record(b"\x00", psp_game_sector, SECTOR_SIZE, directory=True),
            directory_record(b"\x01", root_sector, SECTOR_SIZE, directory=True),
            directory_record(b"SYSDIR", sysdir_sector, SECTOR_SIZE, directory=True),
            directory_record(b"USRDIR", usrdir_sector, SECTOR_SIZE, directory=True),
            directory_record(b"PARAM.SFO;1", param_sector, len(param_payload), directory=False),
        ],
    )

    sysdir_records = [
        directory_record(b"\x00", sysdir_sector, SECTOR_SIZE, directory=True),
        directory_record(b"\x01", psp_game_sector, SECTOR_SIZE, directory=True),
        directory_record(
            b"BOOT.BIN;1",
            boot_sector,
            len(boot_payload),
            directory=False,
            flags=0x80 if multi_extent else 0,
        ),
    ]
    if duplicate_boot:
        sysdir_records.append(
            directory_record(b"BOOT.BIN;1", 27, len(boot_payload), directory=False)
        )
    write_directory(image, sysdir_sector, sysdir_records)

    resource_name = b"BAD/NAME.BIN;1" if unsafe_name else b"DATA.BIN;1"
    write_directory(
        image,
        usrdir_sector,
        [
            directory_record(b"\x00", usrdir_sector, SECTOR_SIZE, directory=True),
            directory_record(b"\x01", psp_game_sector, SECTOR_SIZE, directory=True),
            directory_record(
                resource_name,
                data_sector,
                len(data_payload),
                directory=False,
            ),
        ],
    )

    image[param_sector * SECTOR_SIZE : param_sector * SECTOR_SIZE + len(param_payload)] = (
        param_payload
    )
    image[boot_sector * SECTOR_SIZE : boot_sector * SECTOR_SIZE + len(boot_payload)] = (
        boot_payload
    )
    image[data_sector * SECTOR_SIZE : data_sector * SECTOR_SIZE + len(data_payload)] = (
        data_payload
    )
    return bytes(image)


def reference_for(image: bytes) -> ReferenceRevision:
    return ReferenceRevision(
        revision_id="fixture-v1",
        disc_id="ULUS10066",
        disc_version="1.00",
        title="Fixture",
        psp_system_version="2.60",
        iso_size=len(image),
        iso_sha256=hashlib.sha256(image).hexdigest(),
    )


def test_scan_iso_preserves_record_order_paths_and_offsets(tmp_path: Path) -> None:
    image = build_test_iso()
    path = tmp_path / "fixture.iso"
    path.write_bytes(image)

    inventory = scan_iso(path)

    assert inventory.volume_id == "FNR3TEST"
    assert inventory.volume_size == len(image)
    assert [directory.path for directory in inventory.directories] == [
        ".",
        "PSP_GAME",
        "PSP_GAME/SYSDIR",
        "PSP_GAME/USRDIR",
    ]
    assert [entry.path for entry in inventory.files] == [
        "PSP_GAME/SYSDIR/BOOT.BIN",
        "PSP_GAME/USRDIR/DATA.BIN",
        "PSP_GAME/PARAM.SFO",
    ]
    boot = inventory.files[0]
    assert boot.lba == 25
    assert boot.offset == 25 * SECTOR_SIZE
    assert boot.size == len(b"BOOT-CONTENT")
    assert boot.order == 0


def test_build_workspace_is_deterministic_and_original_is_read_only(tmp_path: Path) -> None:
    image = build_test_iso()
    image_path = tmp_path / "fixture.iso"
    image_path.write_bytes(image)
    first = tmp_path / "first"
    second = tmp_path / "second"

    first_manifest = build_workspace(image_path, first, reference_for(image))
    second_manifest = build_workspace(image_path, second, reference_for(image))

    assert first_manifest.to_json() == second_manifest.to_json()
    assert (first / "original" / "PSP_GAME" / "SYSDIR" / "BOOT.BIN").read_bytes() == (
        b"BOOT-CONTENT"
    )
    assert (first / "working").is_dir()
    assert (first / "modified").is_dir()
    assert (first / "manifests" / "workspace.json").read_text(encoding="utf-8") == (
        first_manifest.to_json()
    )
    assert not (
        first / "original" / "PSP_GAME" / "SYSDIR" / "BOOT.BIN"
    ).stat().st_mode & 0o200
    assert verify_workspace(first).valid


def test_verify_workspace_detects_missing_modified_and_extra_original_files(tmp_path: Path) -> None:
    image = build_test_iso()
    image_path = tmp_path / "fixture.iso"
    image_path.write_bytes(image)
    workspace = tmp_path / "workspace"
    build_workspace(image_path, workspace, reference_for(image))

    boot_path = workspace / "original" / "PSP_GAME" / "SYSDIR" / "BOOT.BIN"
    boot_path.chmod(0o644)
    boot_path.write_bytes(b"changed")
    extra_path = workspace / "original" / "EXTRA.BIN"
    extra_path.write_bytes(b"extra")

    result = verify_workspace(workspace)

    assert not result.valid
    assert "hash mismatch: PSP_GAME/SYSDIR/BOOT.BIN" in result.diagnostics
    assert "size mismatch: PSP_GAME/SYSDIR/BOOT.BIN" in result.diagnostics
    assert "unexpected original file: EXTRA.BIN" in result.diagnostics


def test_build_workspace_requires_force_and_replaces_transactionally(tmp_path: Path) -> None:
    image = build_test_iso()
    image_path = tmp_path / "fixture.iso"
    image_path.write_bytes(image)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    marker = workspace / "keep.txt"
    marker.write_text("old", encoding="utf-8")

    with pytest.raises(FileExistsError):
        build_workspace(image_path, workspace, reference_for(image))
    assert marker.read_text(encoding="utf-8") == "old"

    build_workspace(image_path, workspace, reference_for(image), force=True)

    assert not marker.exists()
    assert verify_workspace(workspace).valid


@pytest.mark.parametrize(
    ("image", "message"),
    [
        (build_test_iso(duplicate_boot=True), "duplicate ISO path"),
        (build_test_iso(overlapping_files=True), "overlapping extents"),
        (build_test_iso(unsafe_name=True), "unsafe ISO identifier"),
        (build_test_iso(multi_extent=True), "multi-extent files are unsupported"),
        (build_test_iso(declared_sectors=64), "ISO image is truncated"),
    ],
)
def test_scan_iso_rejects_unsafe_or_ambiguous_images(
    tmp_path: Path,
    image: bytes,
    message: str,
) -> None:
    path = tmp_path / "invalid.iso"
    path.write_bytes(image)

    with pytest.raises(IsoFormatError, match=message):
        scan_iso(path)
