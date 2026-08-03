from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from .evidence import Address, AddressType, BinaryRegion, Confidence

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class SaveImportReference:
    value: str
    section: str
    address: Address
    size: int
    confidence: Confidence

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("save import value is required")
        if not self.section.strip():
            raise ValueError("save import section is required")
        if self.address.address_type is not AddressType.ELF_VIRTUAL:
            raise ValueError("save import addresses must be ELF virtual addresses")
        if self.size <= 0:
            raise ValueError("save import size must be positive")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SaveImportReference:
        return cls(
            value=_required_string(payload, "value"),
            section=_required_string(payload, "section"),
            address=Address.from_mapping(_required_mapping(payload, "address")),
            size=_required_int(payload, "size"),
            confidence=Confidence(_required_string(payload, "confidence")),
        )


@dataclass(frozen=True, slots=True)
class SaveOwnerCandidate:
    module: str
    confidence: Confidence
    import_references: tuple[SaveImportReference, ...]
    observations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.module.strip():
            raise ValueError("save owner module is required")
        if not self.import_references:
            raise ValueError("save owner requires import references")
        _validate_unique(
            (reference.value for reference in self.import_references),
            "save import reference",
        )
        _validate_nonempty_strings(self.observations, "save owner observation")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SaveOwnerCandidate:
        return cls(
            module=_required_string(payload, "module"),
            confidence=Confidence(_required_string(payload, "confidence")),
            import_references=tuple(
                SaveImportReference.from_mapping(item)
                for item in _mapping_list(payload, "import_references")
            ),
            observations=tuple(_string_list(payload, "observations")),
        )


@dataclass(frozen=True, slots=True)
class SaveStringReference:
    label: str
    value: str
    elf_address: Address
    file_offset: Address
    xrefs: tuple[int, ...]
    xref_region_sha256: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ValueError("save string label is required")
        if not self.value:
            raise ValueError("save string value is required")
        if self.elf_address.address_type is not AddressType.ELF_VIRTUAL:
            raise ValueError("save string address must be ELF virtual")
        if self.file_offset.address_type is not AddressType.ELF_FILE_OFFSET:
            raise ValueError("save string file offset must be an ELF file offset")
        if not self.xrefs:
            raise ValueError("save string requires at least one xref")
        if len(self.xrefs) != len(self.xref_region_sha256):
            raise ValueError("save string xrefs and hashes must have equal length")
        if tuple(sorted(set(self.xrefs))) != self.xrefs:
            raise ValueError("save string xrefs must be sorted and unique")
        for xref in self.xrefs:
            if xref < 0:
                raise ValueError("save string xrefs must be non-negative")
        for digest in self.xref_region_sha256:
            _validate_sha256(digest, "save string xref hash")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SaveStringReference:
        return cls(
            label=_required_string(payload, "label"),
            value=_required_string(payload, "value"),
            elf_address=Address.from_mapping(_required_mapping(payload, "elf_address")),
            file_offset=Address.from_mapping(_required_mapping(payload, "file_offset")),
            xrefs=tuple(_int_list(payload, "xrefs")),
            xref_region_sha256=tuple(_string_list(payload, "xref_region_sha256")),
        )


@dataclass(frozen=True, slots=True)
class SaveEntryPointCandidate:
    role: str
    confidence: Confidence
    region: BinaryRegion
    related_strings: tuple[str, ...]
    observations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.role.strip():
            raise ValueError("save entry-point role is required")
        if self.region.address.address_type is not AddressType.ELF_VIRTUAL:
            raise ValueError("save entry-point regions must use ELF virtual addresses")
        _validate_nonempty_strings(self.related_strings, "related save string")
        _validate_nonempty_strings(self.observations, "save entry-point observation")

    @property
    def address(self) -> Address:
        return self.region.address

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SaveEntryPointCandidate:
        return cls(
            role=_required_string(payload, "role"),
            confidence=Confidence(_required_string(payload, "confidence")),
            region=BinaryRegion.from_mapping(_required_mapping(payload, "region")),
            related_strings=tuple(_string_list(payload, "related_strings")),
            observations=tuple(_string_list(payload, "observations")),
        )


@dataclass(frozen=True, slots=True)
class SaveStaticMap:
    schema_version: int
    source_revision: str
    boot_sha256: str
    owner: SaveOwnerCandidate
    string_references: tuple[SaveStringReference, ...]
    entry_points: tuple[SaveEntryPointCandidate, ...]
    remaining_unknowns: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported save static-map schema version")
        if not self.source_revision.strip():
            raise ValueError("save static-map source revision is required")
        _validate_sha256(self.boot_sha256, "BOOT.BIN sha256")
        if not self.string_references:
            raise ValueError("save static map requires string references")
        if not self.entry_points:
            raise ValueError("save static map requires entry-point candidates")
        _validate_unique(
            (reference.label for reference in self.string_references),
            "save string label",
        )
        _validate_unique((candidate.role for candidate in self.entry_points), "save role")
        labels = {reference.label for reference in self.string_references}
        for candidate in self.entry_points:
            if candidate.region.module != self.owner.module:
                raise ValueError("save entry-point module must match owner module")
            missing = set(candidate.related_strings) - labels
            if missing:
                raise ValueError(
                    "save entry-point references unknown string labels: "
                    + ", ".join(sorted(missing))
                )
            if candidate.confidence is Confidence.CONFIRMED:
                raise ValueError(
                    "static save-map entry points cannot be CONFIRMED without runtime evidence"
                )
        _validate_nonempty_strings(self.remaining_unknowns, "save remaining unknown")
        _validate_unique(self.remaining_unknowns, "save remaining unknown")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SaveStaticMap:
        return cls(
            schema_version=_required_int(payload, "schema_version"),
            source_revision=_required_string(payload, "source_revision"),
            boot_sha256=_required_string(payload, "boot_sha256"),
            owner=SaveOwnerCandidate.from_mapping(_required_mapping(payload, "owner")),
            string_references=tuple(
                SaveStringReference.from_mapping(item)
                for item in _mapping_list(payload, "string_references")
            ),
            entry_points=tuple(
                SaveEntryPointCandidate.from_mapping(item)
                for item in _mapping_list(payload, "entry_points")
            ),
            remaining_unknowns=tuple(_string_list(payload, "remaining_unknowns")),
        )


def load_save_static_map(path: Path) -> SaveStaticMap:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("save static map must be a JSON object")
    return SaveStaticMap.from_mapping(cast(Mapping[str, Any], payload))


def _validate_sha256(value: str, label: str) -> None:
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{label} must be 64 lowercase hexadecimal characters")


def _validate_nonempty_strings(values: tuple[str, ...], label: str) -> None:
    if not values:
        raise ValueError(f"at least one {label} is required")
    for value in values:
        if not value.strip():
            raise ValueError(f"{label} values must be non-empty")


def _validate_unique(values: object, label: str) -> None:
    collected = tuple(cast(Any, values))
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
