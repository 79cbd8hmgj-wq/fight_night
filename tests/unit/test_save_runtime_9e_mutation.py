from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from fnr3_re.save_runtime_9e import (
    PayloadLifetimeContract,
    Task9EPlanError,
    hash_savedata_slot,
    prepare_corrupted_savedata,
)


def _contract() -> PayloadLifetimeContract:
    return PayloadLifetimeContract(
        source_revision="ULUS10066-v1.00",
        boot_sha256=(
            "906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9"
        ),
        total_size=20,
        envelope_header_size=8,
        active_body_size_offset=4,
        body_offset=8,
        body_capacity=12,
    )


def _write_slot(root: Path, *, active_size: int = 6, body: bytes | None = None) -> Path:
    root.mkdir()
    if body is None:
        body = bytes((0, 0x10, 0x20, 0, 0x30, 0x40, 0, 0, 0, 0, 0, 0))
    header = b"ABCD" + active_size.to_bytes(4, "little")
    (root / "DATA.BIN").write_bytes(header + body)
    (root / "PARAM.SFO").write_bytes(b"synthetic companion")
    nested = root / "nested"
    nested.mkdir()
    (nested / "ICON0.PNG").write_bytes(b"not a real png")
    return root


def test_hash_savedata_slot_is_sorted_and_complete(tmp_path: Path) -> None:
    slot = _write_slot(tmp_path / "slot")

    inventory = hash_savedata_slot(slot)

    assert [entry.relative_path for entry in inventory] == [
        "DATA.BIN",
        "nested/ICON0.PNG",
        "PARAM.SFO",
    ]
    assert all(len(entry.sha256) == 64 for entry in inventory)
    assert {entry.relative_path: entry.size for entry in inventory}["DATA.BIN"] == 20


def test_corrupted_copy_changes_exactly_first_active_nonzero_byte(tmp_path: Path) -> None:
    source = _write_slot(tmp_path / "source")
    destination = tmp_path / "scratch" / "slot-copy"
    original_data = (source / "DATA.BIN").read_bytes()
    original_inventory = hash_savedata_slot(source)

    mutation = prepare_corrupted_savedata(source, destination, _contract())

    assert (source / "DATA.BIN").read_bytes() == original_data
    assert hash_savedata_slot(source) == original_inventory
    assert (destination / "PARAM.SFO").read_bytes() == b"synthetic companion"
    assert (destination / "nested/ICON0.PNG").read_bytes() == b"not a real png"

    mutated_data = (destination / "DATA.BIN").read_bytes()
    changed = [
        index
        for index, (before, after) in enumerate(zip(original_data, mutated_data, strict=True))
        if before != after
    ]
    assert changed == [9]
    assert len(mutated_data) == len(original_data) == 20
    assert mutation.relative_path == "DATA.BIN"
    assert mutation.offset == 9
    assert mutation.original_byte == 0x10
    assert mutation.replacement_byte == 0x11
    assert mutation.source_sha256 == hashlib.sha256(original_data).hexdigest()
    assert mutation.mutated_sha256 == hashlib.sha256(mutated_data).hexdigest()
    assert mutation.source_inventory == original_inventory
    assert mutation.mutated_inventory == hash_savedata_slot(destination)


@pytest.mark.parametrize("active_size", [0, 13])
def test_corrupted_copy_rejects_invalid_active_body_size(
    tmp_path: Path,
    active_size: int,
) -> None:
    source = _write_slot(tmp_path / "source", active_size=active_size)
    destination = tmp_path / "scratch"

    with pytest.raises(Task9EPlanError, match="active body"):
        prepare_corrupted_savedata(source, destination, _contract())

    assert not destination.exists()


def test_corrupted_copy_rejects_wrong_data_size_and_no_nonzero_byte(tmp_path: Path) -> None:
    truncated = _write_slot(tmp_path / "truncated")
    (truncated / "DATA.BIN").write_bytes((truncated / "DATA.BIN").read_bytes()[:-1])
    with pytest.raises(Task9EPlanError, match="size"):
        prepare_corrupted_savedata(truncated, tmp_path / "truncated-copy", _contract())

    zero_body = _write_slot(tmp_path / "zero", active_size=6, body=bytes(12))
    with pytest.raises(Task9EPlanError, match="nonzero"):
        prepare_corrupted_savedata(zero_body, tmp_path / "zero-copy", _contract())


def test_savedata_slot_rejects_missing_data_and_symlinks(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    missing.mkdir()
    (missing / "PARAM.SFO").write_bytes(b"x")
    with pytest.raises(Task9EPlanError, match=r"DATA\.BIN"):
        prepare_corrupted_savedata(missing, tmp_path / "missing-copy", _contract())

    source = _write_slot(tmp_path / "source")
    symlinked_file = source / "linked.bin"
    symlinked_file.symlink_to(source / "PARAM.SFO")
    with pytest.raises(Task9EPlanError, match="symlink"):
        hash_savedata_slot(source)

    symlinked_slot = tmp_path / "slot-link"
    symlinked_slot.symlink_to(source, target_is_directory=True)
    with pytest.raises(Task9EPlanError, match="symlink"):
        hash_savedata_slot(symlinked_slot)

    if os.name != "nt":
        assert symlinked_slot.is_symlink()
