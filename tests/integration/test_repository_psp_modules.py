from __future__ import annotations

from pathlib import Path

from fnr3_re.elf32 import parse_elf32
from fnr3_re.psp_container import parse_psp_container

ROOT = Path(__file__).resolve().parents[2]


def test_tracked_boot_bin_matches_plain_psp_elf_contract() -> None:
    payload = (ROOT / "BOOT.BIN").read_bytes()
    image = parse_elf32(payload)

    assert len(payload) == 7_270_664
    assert image.header.object_type == 0xFFA0
    assert image.header.machine == 8
    assert image.header.version == 1
    assert image.header.entry_point == 0x34DECC
    assert image.header.program_header_offset == 0x34
    assert image.header.section_header_offset == 0x592940
    assert image.header.flags == 0x10A23001
    assert image.header.header_size == 52
    assert image.header.program_header_entry_size == 32
    assert image.header.program_header_count == 2
    assert image.header.section_header_entry_size == 40
    assert image.header.section_header_count == 62
    assert image.header.section_name_table_index == 61
    assert len(image.load_segments) == 2
    assert image.virtual_to_file_offset(image.header.entry_point) < len(payload)


def test_tracked_eboot_container_matches_plain_elf_identity() -> None:
    boot_payload = (ROOT / "BOOT.BIN").read_bytes()
    eboot_payload = (ROOT / "EBOOT.BIN").read_bytes()
    boot = parse_elf32(boot_payload)
    container = parse_psp_container(eboot_payload)

    assert len(eboot_payload) == 7_271_008
    assert container.module_name == "FightNight"
    assert container.module_version == (1, 1)
    assert container.header_version == 1
    assert container.segment_count == 2
    assert container.elf_size == len(boot_payload)
    assert container.psp_size == len(eboot_payload)
    assert container.entry_point == boot.header.entry_point
    assert container.module_info_offset == 0x4F6F74
    assert container.bss_size == 0x355C8
    assert container.segment_alignments == (0x100, 0x40)
