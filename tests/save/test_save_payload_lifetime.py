from __future__ import annotations

from pathlib import Path

from fnr3_re.evidence import AddressType, Confidence
from fnr3_re.save_payload_lifetime import load_save_payload_lifetime_map

_ROOT = Path(__file__).resolve().parents[2]
_ARTIFACT = _ROOT / "analysis/save/save-payload-lifetime.json"


def test_payload_workspace_is_fixed_bss_envelope() -> None:
    payload_map = load_save_payload_lifetime_map(_ARTIFACT)
    workspace = payload_map.workspace

    assert payload_map.schema_version == 1
    assert payload_map.source_revision == "ULUS10066-v1.00"
    assert workspace.module == "BOOT.BIN"
    assert workspace.storage_class == "module_bss"
    assert workspace.confidence is Confidence.CONFIRMED
    assert workspace.relocation_addend.address_type is AddressType.MODULE_RELATIVE
    assert workspace.relocation_addend.value == 0x00030668
    assert workspace.runtime_base.address_type is AddressType.RUNTIME
    assert workspace.runtime_base.value == 0x005BAF10
    assert workspace.total_size == 0x755C
    assert workspace.envelope_header_size == 0x2C
    assert workspace.active_body_size_offset == 0x28
    assert workspace.body_offset == 0x2C
    assert workspace.body_capacity == 0x7530
    assert workspace.utility_capacity == 0x755C
    assert workspace.utility_active_size == 0x755C
    assert workspace.body_active_size == "dynamic"
    assert workspace.unused_body_tail == "zero_filled_on_save"


def test_payload_registration_and_operation_lifetime_are_separate() -> None:
    payload_map = load_save_payload_lifetime_map(_ARTIFACT)
    registration = payload_map.registration
    operations = {operation.role: operation for operation in payload_map.operations}

    assert registration.pointer_global.value == 0x005C250C
    assert registration.size_global.value == 0x005C2510
    assert registration.clear_function.value == 0x003401D0
    assert registration.set_function.value == 0x0034025C
    assert registration.ownership == "borrowed_external_buffer"
    assert registration.lifetime == "until_next_clear_or_replacement"

    assert operations["body_serializer_capacity_boundary"].address.value == 0x0034526C
    assert operations["body_serializer_capacity_boundary"].maximum_size == 0x7530
    assert operations["body_serializer_capacity_boundary"].size_behavior == (
        "returns_dynamic_active_body_size"
    )
    assert operations["save_envelope_provider"].address.value == 0x00340DC8
    assert operations["save_envelope_provider"].clear_size == 0x7530
    assert operations["load_envelope_provider"].address.value == 0x00340F00
    assert operations["load_envelope_provider"].clear_size == 0x755C
    assert operations["load_body_commit"].address.value == 0x00340F64
    assert operations["load_body_commit"].copy_size_source_offset == 0x28

    assert payload_map.workspace_lifetime == "module_load_to_module_unload"
    assert payload_map.workspace_allocation == "none_static_bss"
    assert payload_map.workspace_release == "none_static_bss"
    assert "per-field serializer writer set" in payload_map.remaining_unknowns
    assert "per-field deserializer reader set" in payload_map.remaining_unknowns
