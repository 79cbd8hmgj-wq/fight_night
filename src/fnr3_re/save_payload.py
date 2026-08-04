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
_PAYLOAD_DIRECTIONS = frozenset({"save", "load"})
_CONTROLLER_DIRECTIONS = frozenset({"save", "load", "non_payload"})


@dataclass(frozen=True, slots=True)
class SavePayloadDispatchEntry:
    role: str
    entry_offset: int
    target: Address
    direction: str
    confidence: Confidence
    target_region: BinaryRegion
    observations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.role.strip():
            raise ValueError("payload dispatch entry role is required")
        if self.entry_offset < 0 or self.entry_offset % 4:
            raise ValueError("payload dispatch entry offset must be aligned")
        if self.target.address_type is not AddressType.ELF_VIRTUAL:
            raise ValueError("payload dispatch target must be ELF virtual")
        if self.direction not in _PAYLOAD_DIRECTIONS:
            raise ValueError("payload dispatch direction must be save or load")
        _require_elf_region(self.target_region, "payload dispatch target")
        if self.target_region.address != self.target:
            raise ValueError("payload dispatch target must match target-region start")
        _validate_nonempty_strings(self.observations, "dispatch observation")
        if self.confidence is Confidence.CONFIRMED:
            raise ValueError("static payload dispatch entries cannot be CONFIRMED")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SavePayloadDispatchEntry:
        return cls(
            role=_required_string(payload, "role"),
            entry_offset=_required_int(payload, "entry_offset"),
            target=Address.from_mapping(_required_mapping(payload, "target")),
            direction=_required_string(payload, "direction"),
            confidence=Confidence(_required_string(payload, "confidence")),
            target_region=BinaryRegion.from_mapping(
                _required_mapping(payload, "target_region")
            ),
            observations=tuple(_string_list(payload, "observations")),
        )


@dataclass(frozen=True, slots=True)
class SavePayloadDispatchTable:
    module: str
    runtime_base: Address
    installer_region: BinaryRegion
    copier_region: BinaryRegion
    entries: tuple[SavePayloadDispatchEntry, ...]
    observations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.module.strip():
            raise ValueError("payload dispatch module is required")
        if self.runtime_base.address_type is not AddressType.RUNTIME:
            raise ValueError("payload dispatch runtime base must be a runtime address")
        _require_elf_region(self.installer_region, "payload dispatch installer")
        _require_elf_region(self.copier_region, "payload dispatch copier")
        if not self.entries:
            raise ValueError("payload dispatch entries are required")
        if self.installer_region.module != self.module:
            raise ValueError("payload dispatch installer module mismatch")
        if self.copier_region.module != self.module:
            raise ValueError("payload dispatch copier module mismatch")
        _validate_unique((entry.role for entry in self.entries), "dispatch entry role")
        offsets = tuple(entry.entry_offset for entry in self.entries)
        if tuple(sorted(set(offsets))) != offsets:
            raise ValueError("payload dispatch offsets must be sorted and unique")
        for dispatch_entry in self.entries:
            if dispatch_entry.target_region.module != self.module:
                raise ValueError("payload dispatch target module mismatch")
        _validate_nonempty_strings(self.observations, "dispatch table observation")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SavePayloadDispatchTable:
        return cls(
            module=_required_string(payload, "module"),
            runtime_base=Address.from_mapping(_required_mapping(payload, "runtime_base")),
            installer_region=BinaryRegion.from_mapping(
                _required_mapping(payload, "installer_region")
            ),
            copier_region=BinaryRegion.from_mapping(
                _required_mapping(payload, "copier_region")
            ),
            entries=tuple(
                SavePayloadDispatchEntry.from_mapping(item)
                for item in _mapping_list(payload, "entries")
            ),
            observations=tuple(_string_list(payload, "observations")),
        )


@dataclass(frozen=True, slots=True)
class SavePayloadControllerSite:
    role: str
    direction: str
    mode_values: tuple[int, ...]
    callback_entry_offset: int | None
    callback_callsite: Address | None
    utility_callsite: Address
    confidence: Confidence
    region: BinaryRegion
    observations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.role.strip():
            raise ValueError("payload controller role is required")
        if self.direction not in _CONTROLLER_DIRECTIONS:
            raise ValueError("invalid payload controller direction")
        if not self.mode_values:
            raise ValueError("payload controller mode values are required")
        if tuple(sorted(set(self.mode_values))) != self.mode_values:
            raise ValueError("payload controller modes must be sorted and unique")
        if any(mode < 0 or mode > 7 for mode in self.mode_values):
            raise ValueError("payload controller modes must be in the range 0..7")
        _require_elf_region(self.region, "payload controller")
        if self.utility_callsite.address_type is not AddressType.ELF_VIRTUAL:
            raise ValueError("payload utility callsite must be ELF virtual")
        _require_inside(self.utility_callsite, self.region, "payload utility callsite")
        if self.direction == "non_payload":
            if self.callback_entry_offset is not None or self.callback_callsite is not None:
                raise ValueError("non-payload controller cannot use a payload callback")
        else:
            if self.callback_entry_offset is None or self.callback_callsite is None:
                raise ValueError("payload controller callback evidence is required")
            if self.callback_entry_offset < 0 or self.callback_entry_offset % 4:
                raise ValueError("payload callback offset must be aligned")
            if self.callback_callsite.address_type is not AddressType.ELF_VIRTUAL:
                raise ValueError("payload callback callsite must be ELF virtual")
            _require_inside(self.callback_callsite, self.region, "payload callback callsite")
        _validate_nonempty_strings(self.observations, "controller observation")
        if self.confidence is Confidence.CONFIRMED:
            raise ValueError("static payload controller sites cannot be CONFIRMED")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SavePayloadControllerSite:
        callback_payload = _optional_mapping(payload, "callback_callsite")
        return cls(
            role=_required_string(payload, "role"),
            direction=_required_string(payload, "direction"),
            mode_values=tuple(_int_list(payload, "mode_values")),
            callback_entry_offset=_optional_int(payload, "callback_entry_offset"),
            callback_callsite=(
                Address.from_mapping(callback_payload)
                if callback_payload is not None
                else None
            ),
            utility_callsite=Address.from_mapping(
                _required_mapping(payload, "utility_callsite")
            ),
            confidence=Confidence(_required_string(payload, "confidence")),
            region=BinaryRegion.from_mapping(_required_mapping(payload, "region")),
            observations=tuple(_string_list(payload, "observations")),
        )


@dataclass(frozen=True, slots=True)
class SavePayloadDirectionMap:
    schema_version: int
    source_revision: str
    boot_sha256: str
    owner_module: str
    owner_confidence: Confidence
    owner_observations: tuple[str, ...]
    dispatch_table: SavePayloadDispatchTable
    controller_sites: tuple[SavePayloadControllerSite, ...]
    remaining_unknowns: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported save payload direction schema version")
        if not self.source_revision.strip():
            raise ValueError("save payload source revision is required")
        _validate_sha256(self.boot_sha256, "BOOT.BIN sha256")
        if not self.owner_module.strip():
            raise ValueError("save payload owner module is required")
        if self.owner_confidence is Confidence.CONFIRMED:
            raise ValueError("static payload ownership cannot be CONFIRMED")
        _validate_nonempty_strings(self.owner_observations, "owner observation")
        if self.dispatch_table.module != self.owner_module:
            raise ValueError("dispatch table must belong to the payload owner module")
        if not self.controller_sites:
            raise ValueError("payload controller sites are required")
        _validate_unique((site.role for site in self.controller_sites), "controller role")
        all_modes = tuple(
            mode
            for controller_site in self.controller_sites
            for mode in controller_site.mode_values
        )
        if set(all_modes) != set(range(8)) or len(all_modes) != 8:
            raise ValueError("payload direction map must classify utility modes 0 through 7")
        entries_by_offset = {
            dispatch_entry.entry_offset: dispatch_entry
            for dispatch_entry in self.dispatch_table.entries
        }
        for controller_site in self.controller_sites:
            if controller_site.region.module != self.owner_module:
                raise ValueError("payload controller module mismatch")
            callback_offset = controller_site.callback_entry_offset
            if callback_offset is None:
                continue
            dispatch_entry = entries_by_offset.get(callback_offset)
            if dispatch_entry is None:
                raise ValueError("controller references an unknown dispatch entry")
            if dispatch_entry.direction != controller_site.direction:
                raise ValueError("controller and dispatch directions disagree")
        save_modes = {
            mode
            for controller_site in self.controller_sites
            if controller_site.direction == "save"
            for mode in controller_site.mode_values
        }
        load_modes = {
            mode
            for controller_site in self.controller_sites
            if controller_site.direction == "load"
            for mode in controller_site.mode_values
        }
        non_payload_modes = {
            mode
            for controller_site in self.controller_sites
            if controller_site.direction == "non_payload"
            for mode in controller_site.mode_values
        }
        if save_modes != {1, 3, 5}:
            raise ValueError("save controller modes must be 1, 3, and 5")
        if load_modes != {0, 2, 4}:
            raise ValueError("load controller modes must be 0, 2, and 4")
        if non_payload_modes != {6, 7}:
            raise ValueError("non-payload controller modes must be 6 and 7")
        _validate_nonempty_strings(self.remaining_unknowns, "save payload unknown")
        _validate_unique(self.remaining_unknowns, "save payload unknown")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SavePayloadDirectionMap:
        return cls(
            schema_version=_required_int(payload, "schema_version"),
            source_revision=_required_string(payload, "source_revision"),
            boot_sha256=_required_string(payload, "boot_sha256"),
            owner_module=_required_string(payload, "owner_module"),
            owner_confidence=Confidence(_required_string(payload, "owner_confidence")),
            owner_observations=tuple(_string_list(payload, "owner_observations")),
            dispatch_table=SavePayloadDispatchTable.from_mapping(
                _required_mapping(payload, "dispatch_table")
            ),
            controller_sites=tuple(
                SavePayloadControllerSite.from_mapping(item)
                for item in _mapping_list(payload, "controller_sites")
            ),
            remaining_unknowns=tuple(_string_list(payload, "remaining_unknowns")),
        )


@dataclass(frozen=True, slots=True)
class SavePayloadDirectionVerification:
    valid: bool
    diagnostics: tuple[str, ...]
    checked_regions: int


def load_save_payload_direction_map(path: Path) -> SavePayloadDirectionMap:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("save payload direction map must be a JSON object")
    return SavePayloadDirectionMap.from_mapping(cast(Mapping[str, Any], payload))


def verify_save_payload_direction_map(
    binary: Path,
    payload_map: SavePayloadDirectionMap,
) -> SavePayloadDirectionVerification:
    binary_payload = binary.read_bytes()
    if hashlib.sha256(binary_payload).hexdigest() != payload_map.boot_sha256:
        return SavePayloadDirectionVerification(
            valid=False,
            diagnostics=("BOOT.BIN sha256 mismatch",),
            checked_regions=0,
        )

    regions = [
        payload_map.dispatch_table.installer_region,
        payload_map.dispatch_table.copier_region,
    ]
    regions.extend(
        dispatch_entry.target_region
        for dispatch_entry in payload_map.dispatch_table.entries
    )
    regions.extend(
        controller_site.region for controller_site in payload_map.controller_sites
    )

    diagnostics: list[str] = []
    for guarded_region in regions:
        file_offset = guarded_region.address.value + _BOOT_ELF_FILE_BIAS
        actual = binary_payload[file_offset : file_offset + guarded_region.size]
        if hashlib.sha256(actual).hexdigest() != guarded_region.sha256:
            diagnostics.append(
                f"guarded region mismatch at 0x{guarded_region.address.value:08x}"
            )

    return SavePayloadDirectionVerification(
        valid=not diagnostics,
        diagnostics=tuple(diagnostics),
        checked_regions=len(regions),
    )


def _require_elf_region(region: BinaryRegion, label: str) -> None:
    if region.address.address_type is not AddressType.ELF_VIRTUAL:
        raise ValueError(f"{label} region must use an ELF virtual address")


def _require_inside(address: Address, region: BinaryRegion, label: str) -> None:
    if not (
        region.address.value <= address.value < region.address.value + region.size
    ):
        raise ValueError(f"{label} must be within its guarded region")


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


def _optional_mapping(
    payload: Mapping[str, Any], key: str
) -> Mapping[str, Any] | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be an object or null")
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
