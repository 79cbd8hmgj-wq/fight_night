from __future__ import annotations

import pytest

from fnr3_re.address_map import AddressTranslationError, AddressTranslator
from fnr3_re.elf32 import parse_elf32
from fnr3_re.evidence import Address, AddressType
from tests.support.elf32 import build_test_elf


def translator() -> AddressTranslator:
    return AddressTranslator(
        module_id="fixture",
        elf=parse_elf32(build_test_elf()),
        runtime_base=0x08804000,
        stored_elf_offset=0,
        iso_file_offset=0x00100000,
        sector_size=2048,
    )


def test_translates_across_typed_address_spaces() -> None:
    mapping = translator()
    source = Address(AddressType.ELF_VIRTUAL, 0x1004)

    assert mapping.translate(source, AddressType.MODULE_RELATIVE).value == 4
    assert mapping.translate(source, AddressType.ELF_FILE_OFFSET).value == 0x104
    assert mapping.translate(source, AddressType.RUNTIME).value == 0x08804004
    assert mapping.translate(source, AddressType.STORED_PRX_OFFSET).value == 0x104
    assert mapping.translate(source, AddressType.ISO_OFFSET).value == 0x00100104


def test_file_header_offsets_translate_without_runtime_mapping() -> None:
    mapping = translator()

    assert mapping.translate(
        Address(AddressType.ELF_FILE_OFFSET, 0),
        AddressType.STORED_PRX_OFFSET,
    ).value == 0
    assert mapping.translate(
        Address(AddressType.ELF_FILE_OFFSET, 0x34),
        AddressType.ISO_OFFSET,
    ).value == 0x00100034
    assert mapping.translate(
        Address(AddressType.ISO_OFFSET, 0x00100034),
        AddressType.ELF_FILE_OFFSET,
    ).value == 0x34


def test_reverse_translation_preserves_exact_address() -> None:
    mapping = translator()
    runtime = Address(AddressType.RUNTIME, 0x08805004)

    virtual = mapping.translate(runtime, AddressType.ELF_VIRTUAL)
    stored = mapping.translate(runtime, AddressType.STORED_PRX_OFFSET)
    iso = mapping.translate(runtime, AddressType.ISO_OFFSET)

    assert virtual.value == 0x2004
    assert stored.value == 0x204
    assert iso.value == 0x00100204
    assert mapping.translate(iso, AddressType.RUNTIME) == runtime


def test_iso_lba_requires_an_exact_sector_boundary() -> None:
    mapping = translator()

    aligned = Address(AddressType.ISO_OFFSET, 0x00100000)
    assert mapping.translate(aligned, AddressType.ISO_LBA).value == 0x200
    assert mapping.translate(
        Address(AddressType.ISO_LBA, 0x200), AddressType.ISO_OFFSET
    ).value == 0x00100000

    with pytest.raises(AddressTranslationError, match="not sector aligned"):
        mapping.translate(
            Address(AddressType.ISO_OFFSET, 0x00100104), AddressType.ISO_LBA
        )


def test_bss_has_runtime_and_virtual_addresses_but_no_file_offsets() -> None:
    mapping = translator()
    bss = Address(AddressType.ELF_VIRTUAL, 0x2014)

    assert mapping.translate(bss, AddressType.MODULE_RELATIVE).value == 0x1014
    assert mapping.translate(bss, AddressType.RUNTIME).value == 0x08805014
    with pytest.raises(AddressTranslationError, match="not backed by file data"):
        mapping.translate(bss, AddressType.ELF_FILE_OFFSET)


def test_runtime_translation_requires_explicit_runtime_base() -> None:
    mapping = AddressTranslator(
        module_id="fixture",
        elf=parse_elf32(build_test_elf()),
        runtime_base=None,
        stored_elf_offset=0,
        iso_file_offset=0x00100000,
    )

    with pytest.raises(AddressTranslationError, match="runtime base is unknown"):
        mapping.translate(
            Address(AddressType.ELF_VIRTUAL, 0x1000), AddressType.RUNTIME
        )


def test_archive_offsets_are_not_silently_conflated() -> None:
    mapping = translator()

    with pytest.raises(AddressTranslationError, match="unsupported address space"):
        mapping.translate(
            Address(AddressType.ARCHIVE_OFFSET, 0), AddressType.ELF_VIRTUAL
        )
    with pytest.raises(AddressTranslationError, match="unsupported address space"):
        mapping.translate(
            Address(AddressType.ELF_VIRTUAL, 0x1000), AddressType.ARCHIVE_OFFSET
        )
