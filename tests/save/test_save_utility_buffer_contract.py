from pathlib import Path

from fnr3_re.evidence import AddressType, Confidence
from fnr3_re.save_utility import load_save_utility_buffer_contract

_ROOT = Path(__file__).resolve().parents[2]
_ARTIFACT = _ROOT / "analysis/save/save-utility-buffer-contract.json"


def test_savedata_parameter_block_is_separate_from_game_payload() -> None:
    contract = load_save_utility_buffer_contract(_ARTIFACT)

    assert contract.schema_version == 1
    assert contract.source_revision == "ULUS10066-v1.00"
    assert contract.parameter_block.module == "BOOT.BIN"
    assert contract.parameter_block.size == 0x600
    assert contract.parameter_block.confidence is Confidence.PROBABLE
    assert contract.parameter_block.storage_expression == (
        "global profile/save workspace + 0x12A54"
    )

    fields = {field.name: field for field in contract.parameter_block.fields}
    assert fields["mode"].offset == 0x30
    assert fields["file_name"].offset == 0x64
    assert fields["data_buffer"].offset == 0x74
    assert fields["data_buffer_capacity"].offset == 0x78
    assert fields["data_size"].offset == 0x7C
    assert fields["sfo_title"].offset == 0x80
    assert fields["sfo_detail"].offset == 0x180
    assert fields["key"].offset == 0x5DC

    assert contract.payload_buffer.pointer_field_offset == 0x74
    assert contract.payload_buffer.capacity_field_offset == 0x78
    assert contract.payload_buffer.active_size_field_offset == 0x7C
    assert contract.payload_buffer.flow_direction == "unresolved"
    assert contract.payload_buffer.confidence is Confidence.PROBABLE


def test_two_controllers_build_the_same_savedata_parameter_contract() -> None:
    contract = load_save_utility_buffer_contract(_ARTIFACT)

    controllers = {site.role: site for site in contract.controller_sites}
    assert (
        controllers["list_save_controller"].address.address_type
        is AddressType.ELF_VIRTUAL
    )
    assert controllers["list_save_controller"].address.value == 0x0042C834
    assert controllers["list_save_controller"].mode_values == (5,)
    assert controllers["save_or_autoload_controller"].address.value == 0x0042CF8C
    assert controllers["save_or_autoload_controller"].mode_values == (0, 3)

    callbacks = {site.role: site for site in contract.payload_buffer.callback_sites}
    assert callbacks["list_save_payload_provider"].address.value == 0x0042C888
    assert (
        callbacks["save_or_autoload_payload_provider"].address.value
        == 0x0042CFDC
    )
    assert all(site.argument_offsets == (0x74, 0x78) for site in callbacks.values())

    assert contract.utility_init.address.value == 0x004F6B4C
    assert contract.utility_init.nid == 0x50C4CD57
    assert contract.utility_init.confidence is Confidence.PROBABLE


def test_static_contract_keeps_serializer_direction_and_ownership_unresolved() -> None:
    contract = load_save_utility_buffer_contract(_ARTIFACT)

    assert "payload provider callback target and owner" in contract.remaining_unknowns
    assert "serializer writer set" in contract.remaining_unknowns
    assert "deserializer reader set" in contract.remaining_unknowns
    assert "checksum and obfuscation" in contract.remaining_unknowns
    assert all(
        site.confidence is not Confidence.CONFIRMED
        for site in contract.controller_sites
    )
