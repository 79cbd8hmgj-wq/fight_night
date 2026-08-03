from __future__ import annotations

import json

from fnr3_re.module_map import ModuleKind, ModuleMap, inspect_module
from tests.support.elf32 import build_test_elf


def build_container() -> bytes:
    payload = bytearray(0x150)
    payload[0:4] = b"~PSP"
    payload[8:10] = b"\x01\x01"
    payload[10:38] = b"FixtureModule".ljust(28, b"\x00")
    payload[38] = 1
    payload[39] = 2
    payload[40:44] = (0x120).to_bytes(4, "little")
    payload[44:48] = len(payload).to_bytes(4, "little")
    payload[48:52] = (0x1234).to_bytes(4, "little")
    payload[52:56] = (0x80).to_bytes(4, "little")
    payload[56:60] = (0x40).to_bytes(4, "little")
    payload[60:64] = b"\x00\x01\x40\x00"
    payload[68:76] = (0x1000).to_bytes(4, "little") + (0x2000).to_bytes(
        4, "little"
    )
    payload[84:92] = (0x80).to_bytes(4, "little") + (0x40).to_bytes(
        4, "little"
    )
    return bytes(payload)


def test_inspects_plain_elf_without_inventing_runtime_base() -> None:
    record = inspect_module(
        "PSP_GAME/SYSDIR/BOOT.BIN",
        build_test_elf(),
        iso_file_offset=0x00100000,
        iso_lba=0x200,
    )

    assert record.kind is ModuleKind.PLAIN_ELF
    assert record.entry_point == 0x1000
    assert record.image_base == 0x1000
    assert record.runtime_base is None
    assert record.stored_elf_offset == 0
    assert record.iso_file_offset == 0x00100000
    assert record.iso_lba == 0x200
    assert record.address_mapping_status == "static_elf_mapped_runtime_base_pending"
    assert len(record.segments) == 2
    assert [section.name for section in record.sections] == [
        "",
        ".text",
        ".data",
        ".bss",
        ".shstrtab",
    ]
    assert "runtime load base" in record.unresolved


def test_inspects_packed_container_without_claiming_internal_file_mapping() -> None:
    record = inspect_module("PSP_GAME/SYSDIR/EBOOT.BIN", build_container())

    assert record.kind is ModuleKind.PSP_CONTAINER
    assert record.module_name == "FixtureModule"
    assert record.entry_point == 0x1234
    assert record.image_base is None
    assert record.runtime_base is None
    assert record.stored_elf_offset is None
    assert record.sections == ()
    assert record.container_elf_size == 0x120
    assert record.container_psp_size == 0x150
    assert record.address_mapping_status == "packed_container_requires_decrypted_elf"
    assert "decrypted ELF correspondence" in record.unresolved


def test_module_map_json_is_deterministic_and_preserves_module_order() -> None:
    first = inspect_module("BOOT.BIN", build_test_elf())
    second = inspect_module("EBOOT.BIN", build_container())
    module_map = ModuleMap(revision_id="fixture-v1", modules=(first, second))

    encoded = module_map.to_json()

    assert encoded == module_map.to_json()
    assert encoded.endswith("\n")
    decoded = json.loads(encoded)
    assert [module["path"] for module in decoded["modules"]] == [
        "BOOT.BIN",
        "EBOOT.BIN",
    ]
    assert decoded["modules"][0]["kind"] == "plain_elf"
    assert decoded["modules"][1]["kind"] == "psp_container"
