from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from .elf32 import Elf32Error, parse_elf32
from .evidence import Address, AddressType, BinaryRegion, Confidence

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class SavePayloadWorkspace:
    module: str
    storage_class: str
    relocation_segment_base: Address
    relocation_addend: Address
    runtime_base: Address
    bss_start: Address
    bss_size: int
    total_size: int
    envelope_header_size: int
    active_body_size_offset: int
    body_offset: int
    body_capacity: int
    utility_capacity: int
    utility_active_size: int
    body_active_size: str
    unused_body_tail: str
    confidence: Confidence
    observations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.module.strip():
            raise ValueError("payload workspace module is required")
        if self.storage_class != "module_bss":
            raise ValueError("payload workspace must be module_bss")
        if self.relocation_segment_base.address_type is not AddressType.ELF_VIRTUAL:
            raise ValueError("relocation segment base must be ELF virtual")
        if self.relocation_addend.address_type is not AddressType.MODULE_RELATIVE:
            raise ValueError("workspace relocation addend must be module relative")
        if self.runtime_base.address_type is not AddressType.RUNTIME:
            raise ValueError("workspace runtime base must be runtime")
        if self.bss_start.address_type is not AddressType.ELF_VIRTUAL:
            raise ValueError("BSS start must be ELF virtual")
        if self.bss_size <= 0 or self.total_size <= 0:
            raise ValueError("workspace and BSS sizes must be positive")
        if self.runtime_base.value != (
            self.relocation_segment_base.value + self.relocation_addend.value
        ):
            raise ValueError("workspace runtime base does not match relocation")
        if self.body_offset != self.envelope_header_size:
            raise ValueError("payload body must immediately follow its envelope")
        if self.total_size != self.envelope_header_size + self.body_capacity:
            raise ValueError("payload envelope and body sizes do not total workspace size")
        if self.active_body_size_offset < 0:
            raise ValueError("active body size offset must be non-negative")
        if self.active_body_size_offset + 4 > self.envelope_header_size:
            raise ValueError("active body size field must be within the envelope")
        if self.utility_capacity != self.total_size:
            raise ValueError("utility capacity must equal fixed envelope size")
        if self.utility_active_size != self.total_size:
            raise ValueError("utility active size must equal fixed envelope size")
        if self.body_active_size != "dynamic":
            raise ValueError("body active size must remain dynamic")
        if self.unused_body_tail != "zero_filled_on_save":
            raise ValueError("unused body tail must be zero-filled on save")
        bss_end = self.bss_start.value + self.bss_size
        workspace_end = self.runtime_base.value + self.total_size
        if not self.bss_start.value <= self.runtime_base.value < workspace_end <= bss_end:
            raise ValueError("payload workspace must be fully contained in BSS")
        _validate_nonempty_strings(self.observations, "workspace observation")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SavePayloadWorkspace:
        return cls(
            module=_required_string(payload, "module"),
            storage_class=_required_string(payload, "storage_class"),
            relocation_segment_base=Address.from_mapping(
                _required_mapping(payload, "relocation_segment_base")
            ),
            relocation_addend=Address.from_mapping(
                _required_mapping(payload, "relocation_addend")
            ),
            runtime_base=Address.from_mapping(_required_mapping(payload, "runtime_base")),
            bss_start=Address.from_mapping(_required_mapping(payload, "bss_start")),
            bss_size=_required_int(payload, "bss_size"),
            total_size=_required_int(payload, "total_size"),
            envelope_header_size=_required_int(payload, "envelope_header_size"),
            active_body_size_offset=_required_int(payload, "active_body_size_offset"),
            body_offset=_required_int(payload, "body_offset"),
            body_capacity=_required_int(payload, "body_capacity"),
            utility_capacity=_required_int(payload, "utility_capacity"),
            utility_active_size=_required_int(payload, "utility_active_size"),
            body_active_size=_required_string(payload, "body_active_size"),
            unused_body_tail=_required_string(payload, "unused_body_tail"),
            confidence=Confidence(_required_string(payload, "confidence")),
            observations=tuple(_string_list(payload, "observations")),
        )


@dataclass(frozen=True, slots=True)
class SavePayloadRegistration:
    pointer_global: Address
    size_global: Address
    clear_function: Address
    set_function: Address
    ownership: str
    lifetime: str
    confidence: Confidence
    observations: tuple[str, ...]

    def __post_init__(self) -> None:
        for address in (self.pointer_global, self.size_global):
            if address.address_type is not AddressType.RUNTIME:
                raise ValueError("registration globals must use runtime addresses")
        for address in (self.clear_function, self.set_function):
            if address.address_type is not AddressType.ELF_VIRTUAL:
                raise ValueError("registration functions must use ELF virtual addresses")
        if self.ownership != "borrowed_external_buffer":
            raise ValueError("payload registration ownership must remain borrowed")
        if self.lifetime != "until_next_clear_or_replacement":
            raise ValueError("unexpected payload registration lifetime")
        _validate_nonempty_strings(self.observations, "registration observation")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SavePayloadRegistration:
        return cls(
            pointer_global=Address.from_mapping(
                _required_mapping(payload, "pointer_global")
            ),
            size_global=Address.from_mapping(_required_mapping(payload, "size_global")),
            clear_function=Address.from_mapping(
                _required_mapping(payload, "clear_function")
            ),
            set_function=Address.from_mapping(_required_mapping(payload, "set_function")),
            ownership=_required_string(payload, "ownership"),
            lifetime=_required_string(payload, "lifetime"),
            confidence=Confidence(_required_string(payload, "confidence")),
            observations=tuple(_string_list(payload, "observations")),
        )


@dataclass(frozen=True, slots=True)
class SavePayloadOperation:
    role: str
    address: Address
    maximum_size: int | None
    clear_size: int | None
    size_behavior: str | None
    copy_size_source_offset: int | None
    confidence: Confidence
    observations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.role.strip():
            raise ValueError("payload operation role is required")
        if self.address.address_type is not AddressType.ELF_VIRTUAL:
            raise ValueError("payload operation address must be ELF virtual")
        for name, value in (
            ("maximum_size", self.maximum_size),
            ("clear_size", self.clear_size),
            ("copy_size_source_offset", self.copy_size_source_offset),
        ):
            if value is not None and value < 0:
                raise ValueError(f"payload operation {name} must be non-negative")
        if self.size_behavior is not None and not self.size_behavior.strip():
            raise ValueError("payload operation size behavior must be non-empty")
        _validate_nonempty_strings(self.observations, "operation observation")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SavePayloadOperation:
        return cls(
            role=_required_string(payload, "role"),
            address=Address.from_mapping(_required_mapping(payload, "address")),
            maximum_size=_optional_int(payload, "maximum_size"),
            clear_size=_optional_int(payload, "clear_size"),
            size_behavior=_optional_string(payload, "size_behavior"),
            copy_size_source_offset=_optional_int(payload, "copy_size_source_offset"),
            confidence=Confidence(_required_string(payload, "confidence")),
            observations=tuple(_string_list(payload, "observations")),
        )


@dataclass(frozen=True, slots=True)
class SavePayloadGuard:
    role: str
    region: BinaryRegion

    def __post_init__(self) -> None:
        if not self.role.strip():
            raise ValueError("payload guard role is required")
        if self.region.address.address_type is not AddressType.ELF_VIRTUAL:
            raise ValueError("payload guard region must use ELF virtual address")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SavePayloadGuard:
        return cls(
            role=_required_string(payload, "role"),
            region=BinaryRegion.from_mapping(_required_mapping(payload, "region")),
        )


@dataclass(frozen=True, slots=True)
class SavePayloadLifetimeMap:
    schema_version: int
    source_revision: str
    boot_sha256: str
    workspace: SavePayloadWorkspace
    registration: SavePayloadRegistration
    operations: tuple[SavePayloadOperation, ...]
    guards: tuple[SavePayloadGuard, ...]
    workspace_lifetime: str
    workspace_allocation: str
    workspace_release: str
    remaining_unknowns: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported save payload lifetime schema version")
        if not self.source_revision.strip():
            raise ValueError("save payload source revision is required")
        _validate_sha256(self.boot_sha256, "BOOT.BIN sha256")
        if self.workspace_lifetime != "module_load_to_module_unload":
            raise ValueError("unexpected payload workspace lifetime")
        if self.workspace_allocation != "none_static_bss":
            raise ValueError("payload workspace must not be heap allocated")
        if self.workspace_release != "none_static_bss":
            raise ValueError("payload workspace must not be heap released")
        if not self.operations or not self.guards:
            raise ValueError("payload operations and guards are required")
        _validate_unique((operation.role for operation in self.operations), "operation role")
        _validate_unique((guard.role for guard in self.guards), "guard role")
        _validate_nonempty_strings(self.remaining_unknowns, "payload lifetime unknown")
        _validate_unique(self.remaining_unknowns, "payload lifetime unknown")
        operation_roles = {operation.role for operation in self.operations}
        required_operations = {
            "body_serializer_capacity_boundary",
            "save_envelope_provider",
            "load_envelope_provider",
            "load_body_commit",
        }
        if not required_operations <= operation_roles:
            raise ValueError("required payload lifetime operations are missing")
        serializer = next(
            operation
            for operation in self.operations
            if operation.role == "body_serializer_capacity_boundary"
        )
        if serializer.maximum_size != self.workspace.body_capacity:
            raise ValueError("serializer capacity must match body capacity")
        save_provider = next(
            operation
            for operation in self.operations
            if operation.role == "save_envelope_provider"
        )
        if save_provider.clear_size != self.workspace.body_capacity:
            raise ValueError("save provider must clear the body capacity")
        load_provider = next(
            operation
            for operation in self.operations
            if operation.role == "load_envelope_provider"
        )
        if load_provider.clear_size != self.workspace.total_size:
            raise ValueError("load provider must clear the full envelope")
        load_commit = next(
            operation
            for operation in self.operations
            if operation.role == "load_body_commit"
        )
        if load_commit.copy_size_source_offset != self.workspace.active_body_size_offset:
            raise ValueError("load commit must consume the envelope body-size field")
        bss_end = self.workspace.bss_start.value + self.workspace.bss_size
        for address in (
            self.registration.pointer_global,
            self.registration.size_global,
        ):
            if not self.workspace.bss_start.value <= address.value < bss_end:
                raise ValueError("payload registration global must be inside BSS")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SavePayloadLifetimeMap:
        return cls(
            schema_version=_required_int(payload, "schema_version"),
            source_revision=_required_string(payload, "source_revision"),
            boot_sha256=_required_string(payload, "boot_sha256"),
            workspace=SavePayloadWorkspace.from_mapping(
                _required_mapping(payload, "workspace")
            ),
            registration=SavePayloadRegistration.from_mapping(
                _required_mapping(payload, "registration")
            ),
            operations=tuple(
                SavePayloadOperation.from_mapping(item)
                for item in _mapping_list(payload, "operations")
            ),
            guards=tuple(
                SavePayloadGuard.from_mapping(item)
                for item in _mapping_list(payload, "guards")
            ),
            workspace_lifetime=_required_string(payload, "workspace_lifetime"),
            workspace_allocation=_required_string(payload, "workspace_allocation"),
            workspace_release=_required_string(payload, "workspace_release"),
            remaining_unknowns=tuple(_string_list(payload, "remaining_unknowns")),
        )


@dataclass(frozen=True, slots=True)
class SavePayloadLifetimeVerification:
    valid: bool
    diagnostics: tuple[str, ...]
    checked_regions: int
    workspace_inside_bss: bool


def load_save_payload_lifetime_map(path: Path) -> SavePayloadLifetimeMap:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("save payload lifetime map must be a JSON object")
    return SavePayloadLifetimeMap.from_mapping(cast(Mapping[str, Any], payload))


def verify_save_payload_lifetime_map(
    binary: Path,
    payload_map: SavePayloadLifetimeMap,
) -> SavePayloadLifetimeVerification:
    binary_payload = binary.read_bytes()
    if hashlib.sha256(binary_payload).hexdigest() != payload_map.boot_sha256:
        return SavePayloadLifetimeVerification(
            valid=False,
            diagnostics=("BOOT.BIN sha256 mismatch",),
            checked_regions=0,
            workspace_inside_bss=False,
        )

    diagnostics: list[str] = []
    workspace_inside_bss = False
    try:
        image = parse_elf32(binary_payload)
        bss_sections = [section for section in image.sections if section.name == ".bss"]
        if len(bss_sections) != 1:
            diagnostics.append("exactly one .bss section is required")
        else:
            bss = bss_sections[0]
            expected = payload_map.workspace
            if bss.address != expected.bss_start.value or bss.size != expected.bss_size:
                diagnostics.append(".bss bounds mismatch")
            workspace_end = expected.runtime_base.value + expected.total_size
            bss_end = bss.address + bss.size
            workspace_inside_bss = (
                bss.address <= expected.runtime_base.value < workspace_end <= bss_end
            )
            if not workspace_inside_bss:
                diagnostics.append("payload workspace is outside .bss")

        for guard in payload_map.guards:
            region = guard.region
            file_offset = image.virtual_to_file_offset(
                region.address.value,
                size=region.size,
            )
            actual = binary_payload[file_offset : file_offset + region.size]
            if hashlib.sha256(actual).hexdigest() != region.sha256:
                diagnostics.append(
                    f"guarded region mismatch for {guard.role} at "
                    f"0x{region.address.value:08x}"
                )
    except Elf32Error as exc:
        diagnostics.append(str(exc))

    return SavePayloadLifetimeVerification(
        valid=not diagnostics,
        diagnostics=tuple(diagnostics),
        checked_regions=len(payload_map.guards),
        workspace_inside_bss=workspace_inside_bss,
    )


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


def _optional_string(payload: Mapping[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string or null")
    return value


def _required_int(payload: Mapping[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    return value


def _optional_int(payload: Mapping[str, Any], key: str) -> int | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} must be an integer or null")
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
