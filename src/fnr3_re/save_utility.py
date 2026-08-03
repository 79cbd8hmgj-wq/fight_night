from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from .evidence import Address, AddressType, BinaryRegion, Confidence

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_BOOT_ELF_FILE_BIAS = 0x100


@dataclass(frozen=True, slots=True)
class SaveUtilityField:
    name: str
    offset: int
    size: int
    confidence: Confidence

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("save utility field name is required")
        if self.offset < 0:
            raise ValueError("save utility field offset must be non-negative")
        if self.size <= 0:
            raise ValueError("save utility field size must be positive")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SaveUtilityField:
        return cls(
            name=_required_string(payload, "name"),
            offset=_required_int(payload, "offset"),
            size=_required_int(payload, "size"),
            confidence=Confidence(_required_string(payload, "confidence")),
        )


@dataclass(frozen=True, slots=True)
class SaveUtilityParameterBlock:
    module: str
    size: int
    storage_expression: str
    confidence: Confidence
    fields: tuple[SaveUtilityField, ...]

    def __post_init__(self) -> None:
        if not self.module.strip():
            raise ValueError("save utility parameter module is required")
        if self.size <= 0:
            raise ValueError("save utility parameter size must be positive")
        if not self.storage_expression.strip():
            raise ValueError("save utility storage expression is required")
        if not self.fields:
            raise ValueError("save utility parameter fields are required")
        _validate_unique((field.name for field in self.fields), "save utility field")
        for field in self.fields:
            if field.offset + field.size > self.size:
                raise ValueError(f"save utility field exceeds block: {field.name}")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SaveUtilityParameterBlock:
        return cls(
            module=_required_string(payload, "module"),
            size=_required_int(payload, "size"),
            storage_expression=_required_string(payload, "storage_expression"),
            confidence=Confidence(_required_string(payload, "confidence")),
            fields=tuple(
                SaveUtilityField.from_mapping(item)
                for item in _mapping_list(payload, "fields")
            ),
        )


@dataclass(frozen=True, slots=True)
class SaveUtilityControllerSite:
    role: str
    confidence: Confidence
    region: BinaryRegion
    mode_values: tuple[int, ...]
    observations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.role.strip():
            raise ValueError("save utility controller role is required")
        _require_elf_region(self.region, "save utility controller")
        if not self.mode_values:
            raise ValueError("save utility controller mode values are required")
        if tuple(sorted(set(self.mode_values))) != self.mode_values:
            raise ValueError("save utility mode values must be sorted and unique")
        if any(value < 0 for value in self.mode_values):
            raise ValueError("save utility mode values must be non-negative")
        _validate_nonempty_strings(self.observations, "controller observation")
        if self.confidence is Confidence.CONFIRMED:
            raise ValueError("static controller sites cannot be CONFIRMED")

    @property
    def address(self) -> Address:
        return self.region.address

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SaveUtilityControllerSite:
        return cls(
            role=_required_string(payload, "role"),
            confidence=Confidence(_required_string(payload, "confidence")),
            region=BinaryRegion.from_mapping(_required_mapping(payload, "region")),
            mode_values=tuple(_int_list(payload, "mode_values")),
            observations=tuple(_string_list(payload, "observations")),
        )


@dataclass(frozen=True, slots=True)
class SavePayloadCallbackSite:
    role: str
    address: Address
    confidence: Confidence
    region: BinaryRegion
    argument_offsets: tuple[int, ...]
    observations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.role.strip():
            raise ValueError("payload callback role is required")
        if self.address.address_type is not AddressType.ELF_VIRTUAL:
            raise ValueError("payload callback address must be ELF virtual")
        _require_elf_region(self.region, "payload callback")
        if not (
            self.region.address.value
            <= self.address.value
            < self.region.address.value + self.region.size
        ):
            raise ValueError("payload callback address must be within guarded region")
        if not self.argument_offsets:
            raise ValueError("payload callback argument offsets are required")
        if tuple(sorted(set(self.argument_offsets))) != self.argument_offsets:
            raise ValueError("payload callback argument offsets must be sorted and unique")
        _validate_nonempty_strings(self.observations, "payload callback observation")
        if self.confidence is Confidence.CONFIRMED:
            raise ValueError("static payload callbacks cannot be CONFIRMED")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SavePayloadCallbackSite:
        return cls(
            role=_required_string(payload, "role"),
            address=Address.from_mapping(_required_mapping(payload, "address")),
            confidence=Confidence(_required_string(payload, "confidence")),
            region=BinaryRegion.from_mapping(_required_mapping(payload, "region")),
            argument_offsets=tuple(_int_list(payload, "argument_offsets")),
            observations=tuple(_string_list(payload, "observations")),
        )


@dataclass(frozen=True, slots=True)
class SavePayloadBufferContract:
    confidence: Confidence
    pointer_field_offset: int
    capacity_field_offset: int
    active_size_field_offset: int
    flow_direction: str
    callback_sites: tuple[SavePayloadCallbackSite, ...]
    observations: tuple[str, ...]

    def __post_init__(self) -> None:
        offsets = (
            self.pointer_field_offset,
            self.capacity_field_offset,
            self.active_size_field_offset,
        )
        if any(offset < 0 for offset in offsets):
            raise ValueError("payload buffer field offsets must be non-negative")
        if len(set(offsets)) != len(offsets):
            raise ValueError("payload buffer field offsets must be distinct")
        if self.flow_direction != "unresolved":
            raise ValueError("static payload flow direction must remain unresolved")
        if not self.callback_sites:
            raise ValueError("payload callback sites are required")
        _validate_unique((site.role for site in self.callback_sites), "payload callback role")
        _validate_nonempty_strings(self.observations, "payload buffer observation")
        if self.confidence is Confidence.CONFIRMED:
            raise ValueError("static payload buffer contract cannot be CONFIRMED")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SavePayloadBufferContract:
        return cls(
            confidence=Confidence(_required_string(payload, "confidence")),
            pointer_field_offset=_required_int(payload, "pointer_field_offset"),
            capacity_field_offset=_required_int(payload, "capacity_field_offset"),
            active_size_field_offset=_required_int(payload, "active_size_field_offset"),
            flow_direction=_required_string(payload, "flow_direction"),
            callback_sites=tuple(
                SavePayloadCallbackSite.from_mapping(item)
                for item in _mapping_list(payload, "callback_sites")
            ),
            observations=tuple(_string_list(payload, "observations")),
        )


@dataclass(frozen=True, slots=True)
class SaveUtilityInitBoundary:
    address: Address
    nid: int
    library: str
    confidence: Confidence
    stub_region: BinaryRegion
    import_descriptor_region: BinaryRegion
    nid_table_region: BinaryRegion
    observations: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.address.address_type is not AddressType.ELF_VIRTUAL:
            raise ValueError("save utility init address must be ELF virtual")
        if not 0 <= self.nid <= 0xFFFFFFFF:
            raise ValueError("save utility init NID must be an unsigned 32-bit integer")
        if not self.library.strip():
            raise ValueError("save utility init library is required")
        for region in (
            self.stub_region,
            self.import_descriptor_region,
            self.nid_table_region,
        ):
            _require_elf_region(region, "save utility init")
        if self.stub_region.address != self.address:
            raise ValueError("save utility init address must match stub-region start")
        _validate_nonempty_strings(self.observations, "utility init observation")
        if self.confidence is Confidence.CONFIRMED:
            raise ValueError("static utility init boundary cannot be CONFIRMED")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SaveUtilityInitBoundary:
        return cls(
            address=Address.from_mapping(_required_mapping(payload, "address")),
            nid=_required_int(payload, "nid"),
            library=_required_string(payload, "library"),
            confidence=Confidence(_required_string(payload, "confidence")),
            stub_region=BinaryRegion.from_mapping(
                _required_mapping(payload, "stub_region")
            ),
            import_descriptor_region=BinaryRegion.from_mapping(
                _required_mapping(payload, "import_descriptor_region")
            ),
            nid_table_region=BinaryRegion.from_mapping(
                _required_mapping(payload, "nid_table_region")
            ),
            observations=tuple(_string_list(payload, "observations")),
        )


@dataclass(frozen=True, slots=True)
class SaveUtilityBufferContract:
    schema_version: int
    source_revision: str
    boot_sha256: str
    parameter_block: SaveUtilityParameterBlock
    controller_sites: tuple[SaveUtilityControllerSite, ...]
    payload_buffer: SavePayloadBufferContract
    utility_init: SaveUtilityInitBoundary
    remaining_unknowns: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported save utility contract schema version")
        if not self.source_revision.strip():
            raise ValueError("save utility contract source revision is required")
        _validate_sha256(self.boot_sha256, "BOOT.BIN sha256")
        if not self.controller_sites:
            raise ValueError("save utility controller sites are required")
        _validate_unique((site.role for site in self.controller_sites), "controller role")
        for site in self.controller_sites:
            if site.region.module != self.parameter_block.module:
                raise ValueError("controller module must match parameter-block module")
        for site in self.payload_buffer.callback_sites:
            if site.region.module != self.parameter_block.module:
                raise ValueError("callback module must match parameter-block module")
        for region in (
            self.utility_init.stub_region,
            self.utility_init.import_descriptor_region,
            self.utility_init.nid_table_region,
        ):
            if region.module != self.parameter_block.module:
                raise ValueError("utility-init module must match parameter-block module")
        field_offsets = {field.offset for field in self.parameter_block.fields}
        required_offsets = {
            self.payload_buffer.pointer_field_offset,
            self.payload_buffer.capacity_field_offset,
            self.payload_buffer.active_size_field_offset,
        }
        if not required_offsets <= field_offsets:
            raise ValueError("payload buffer offsets must reference known parameter fields")
        _validate_nonempty_strings(self.remaining_unknowns, "save utility unknown")
        _validate_unique(self.remaining_unknowns, "save utility unknown")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SaveUtilityBufferContract:
        return cls(
            schema_version=_required_int(payload, "schema_version"),
            source_revision=_required_string(payload, "source_revision"),
            boot_sha256=_required_string(payload, "boot_sha256"),
            parameter_block=SaveUtilityParameterBlock.from_mapping(
                _required_mapping(payload, "parameter_block")
            ),
            controller_sites=tuple(
                SaveUtilityControllerSite.from_mapping(item)
                for item in _mapping_list(payload, "controller_sites")
            ),
            payload_buffer=SavePayloadBufferContract.from_mapping(
                _required_mapping(payload, "payload_buffer")
            ),
            utility_init=SaveUtilityInitBoundary.from_mapping(
                _required_mapping(payload, "utility_init")
            ),
            remaining_unknowns=tuple(_string_list(payload, "remaining_unknowns")),
        )


@dataclass(frozen=True, slots=True)
class SaveUtilityContractVerification:
    valid: bool
    diagnostics: tuple[str, ...]
    checked_regions: int


def load_save_utility_buffer_contract(path: Path) -> SaveUtilityBufferContract:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("save utility buffer contract must be a JSON object")
    return SaveUtilityBufferContract.from_mapping(cast(Mapping[str, Any], payload))


def verify_save_utility_buffer_contract(
    binary: Path,
    contract: SaveUtilityBufferContract,
) -> SaveUtilityContractVerification:
    payload = binary.read_bytes()
    if hashlib.sha256(payload).hexdigest() != contract.boot_sha256:
        return SaveUtilityContractVerification(
            valid=False,
            diagnostics=("BOOT.BIN sha256 mismatch",),
            checked_regions=0,
        )

    regions = [site.region for site in contract.controller_sites]
    regions.extend(site.region for site in contract.payload_buffer.callback_sites)
    regions.extend(
        (
            contract.utility_init.stub_region,
            contract.utility_init.import_descriptor_region,
            contract.utility_init.nid_table_region,
        )
    )
    diagnostics: list[str] = []
    for region in regions:
        file_offset = region.address.value + _BOOT_ELF_FILE_BIAS
        actual = payload[file_offset : file_offset + region.size]
        if hashlib.sha256(actual).hexdigest() != region.sha256:
            diagnostics.append(
                f"guarded region mismatch at 0x{region.address.value:08x}"
            )

    return SaveUtilityContractVerification(
        valid=not diagnostics,
        diagnostics=tuple(diagnostics),
        checked_regions=len(regions),
    )


def _require_elf_region(region: BinaryRegion, label: str) -> None:
    if region.address.address_type is not AddressType.ELF_VIRTUAL:
        raise ValueError(f"{label} region must use an ELF virtual address")


def _validate_sha256(value: str, label: str) -> None:
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{label} must be 64 lowercase hexadecimal characters")


def _validate_nonempty_strings(values: tuple[str, ...], label: str) -> None:
    if not values:
        raise ValueError(f"at least one {label} is required")
    for value in values:
        if not value.strip():
            raise ValueError(f"{label} values must be non-empty")


def _validate_unique(values: Iterable[str], label: str) -> None:
    collected = tuple(values)
    if len(set(collected)) != len(collected):
        raise ValueError(f"duplicate {label}")


def _required_string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _required_int(payload: Mapping[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    return value


def _required_mapping(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be an object")
    return cast(Mapping[str, Any], value)


def _mapping_list(payload: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    value = payload.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{key} must be a non-empty list")
    result: list[Mapping[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError(f"{key} entries must be objects")
        result.append(cast(Mapping[str, Any], item))
    return result


def _string_list(payload: Mapping[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{key} must be a non-empty list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{key} entries must be non-empty strings")
        result.append(item)
    return result


def _int_list(payload: Mapping[str, Any], key: str) -> list[int]:
    value = payload.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{key} must be a non-empty list")
    result: list[int] = []
    for item in value:
        if not isinstance(item, int) or isinstance(item, bool):
            raise ValueError(f"{key} entries must be integers")
        result.append(item)
    return result
