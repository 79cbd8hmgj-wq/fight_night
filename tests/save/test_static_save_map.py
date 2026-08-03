from pathlib import Path

from fnr3_re.evidence import AddressType, Confidence
from fnr3_re.save import load_save_static_map

_ARTIFACT = (
    Path(__file__).resolve().parents[2]
    / "analysis/save/save-system-static-candidates.json"
)


def test_static_save_map_identifies_probable_boot_owner() -> None:
    save_map = load_save_static_map(_ARTIFACT)

    assert save_map.schema_version == 1
    assert save_map.source_revision == "ULUS10066-v1.00"
    assert save_map.boot_sha256 == (
        "906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9"
    )
    assert save_map.owner.module == "BOOT.BIN"
    assert save_map.owner.confidence is Confidence.PROBABLE
    assert {reference.value for reference in save_map.owner.import_references} == {
        "IoFileMgrForUser",
        "sceUtility",
    }


def test_static_save_map_preserves_typed_addresses_and_exact_region_guards() -> None:
    save_map = load_save_static_map(_ARTIFACT)

    labels = {reference.label: reference for reference in save_map.string_references}
    assert labels["payload_filename"].value == "DATA.BIN"
    assert labels["payload_filename"].elf_address.address_type is AddressType.ELF_VIRTUAL
    assert labels["payload_filename"].elf_address.value == 0x0052940C
    assert labels["payload_filename"].file_offset.address_type is AddressType.ELF_FILE_OFFSET
    assert labels["payload_filename"].file_offset.value == 0x0052950C
    assert labels["payload_filename"].xrefs == (0x0042C928, 0x0042D088)

    candidates = {candidate.role: candidate for candidate in save_map.entry_points}
    assert candidates["savedata_directory_enumerator"].address.value == 0x004C62B8
    assert candidates["savedata_directory_enumerator"].region.size == 0x148
    assert candidates["corrupt_file_callback"].address.value == 0x003412CC
    assert all(candidate.region.sha256 for candidate in candidates.values())


def test_static_save_map_does_not_promote_unverified_serializer_semantics() -> None:
    save_map = load_save_static_map(_ARTIFACT)

    assert all(candidate.confidence is not Confidence.CONFIRMED for candidate in save_map.entry_points)
    assert "checksum algorithm" in save_map.remaining_unknowns
    assert "profile slot count" in save_map.remaining_unknowns
    assert "serializer and deserializer boundaries" in save_map.remaining_unknowns
