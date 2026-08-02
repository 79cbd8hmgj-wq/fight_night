from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from enum import StrEnum
from typing import Any, cast


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_HEX_BYTES_RE = re.compile(r"^[0-9a-f]*$")


class AddressType(StrEnum):
    RUNTIME = "runtime"
    MODULE_RELATIVE = "module_relative"
    ELF_VIRTUAL = "elf_virtual"
    ELF_FILE_OFFSET = "elf_file_offset"
    STORED_PRX_OFFSET = "stored_prx_offset"
    ARCHIVE_OFFSET = "archive_offset"
    ISO_OFFSET = "iso_offset"
    ISO_LBA = "iso_lba"


class EvidenceType(StrEnum):
    EXACT_BINARY = "exact_binary"
    RUNTIME_CAPTURE = "runtime_capture"
    DETERMINISTIC_RECONSTRUCTION = "deterministic_reconstruction"
    BREAKPOINT = "breakpoint"
    SAVE_DIFF = "save_diff"
    REBUILT_GAME = "rebuilt_game"
    INPUT_OUTPUT = "input_output"
    DECOMPILER = "decompiler"


class Confidence(StrEnum):
    CONFIRMED = "CONFIRMED"
    PROBABLE = "PROBABLE"
    CANDIDATE = "CANDIDATE"
    REJECTED = "REJECTED"


class PackageStatus(StrEnum):
    UNSCOPED = "unscoped"
    CANDIDATE = "candidate"
    STATIC_MAPPED = "static_mapped"
    RUNTIME_IN_PROGRESS = "runtime_in_progress"
    FUNCTIONALLY_RECONSTRUCTED = "functionally_reconstructed"
    NEUTRAL_REPLACEMENT_VALIDATED = "neutral_replacement_validated"
    COMPLETE = "complete"
    BLOCKED = "blocked"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class Address:
    address_type: AddressType
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("address value must be non-negative")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> Address:
        return cls(
            address_type=AddressType(_required_string(payload, "address_type")),
            value=_required_int(payload, "value"),
        )


@dataclass(frozen=True, slots=True)
class BinaryRegion:
    module: str
    address: Address
    size: int
    sha256: str

    def __post_init__(self) -> None:
        if not self.module.strip():
            raise ValueError("binary region module is required")
        if self.size <= 0:
            raise ValueError("binary region size must be positive")
        _validate_sha256(self.sha256, "binary region sha256")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> BinaryRegion:
        return cls(
            module=_required_string(payload, "module"),
            address=Address.from_mapping(_required_mapping(payload, "address")),
            size=_required_int(payload, "size"),
            sha256=_required_string(payload, "sha256"),
        )


@dataclass(frozen=True, slots=True)
class RuntimeCapture:
    emulator: str
    state_sha256: str
    breakpoint: Address
    registers: tuple[tuple[str, int], ...] = ()
    memory: tuple[tuple[int, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.emulator.strip():
            raise ValueError("runtime capture emulator is required")
        _validate_sha256(self.state_sha256, "runtime capture state_sha256")
        for name, _value in self.registers:
            if not name.strip():
                raise ValueError("register names must be non-empty")
        for address, encoded in self.memory:
            if address < 0:
                raise ValueError("memory addresses must be non-negative")
            if len(encoded) % 2 or not _HEX_BYTES_RE.fullmatch(encoded):
                raise ValueError("memory bytes must be lowercase hexadecimal")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> RuntimeCapture:
        return cls(
            emulator=_required_string(payload, "emulator"),
            state_sha256=_required_string(payload, "state_sha256"),
            breakpoint=Address.from_mapping(_required_mapping(payload, "breakpoint")),
            registers=tuple(
                (
                    _sequence_string(item, 0, "register name"),
                    _sequence_int(item, 1, "register value"),
                )
                for item in _optional_sequences(payload, "registers")
            ),
            memory=tuple(
                (
                    _sequence_int(item, 0, "memory address"),
                    _sequence_string(item, 1, "memory bytes"),
                )
                for item in _optional_sequences(payload, "memory")
            ),
        )


@dataclass(frozen=True, slots=True)
class ReplacementBoundary:
    hook: Address
    abi: str
    storage: str
    lifetime: str
    fallback: str
    rollback: str
    budget: str

    def __post_init__(self) -> None:
        for boundary_field in fields(self):
            if boundary_field.name == "hook":
                continue
            value = getattr(self, boundary_field.name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"replacement boundary {boundary_field.name} is required")


_INDEPENDENT_CONFIRMATION = {
    EvidenceType.RUNTIME_CAPTURE,
    EvidenceType.DETERMINISTIC_RECONSTRUCTION,
    EvidenceType.BREAKPOINT,
    EvidenceType.SAVE_DIFF,
    EvidenceType.REBUILT_GAME,
    EvidenceType.INPUT_OUTPUT,
}


@dataclass(frozen=True, slots=True)
class EvidenceClaim:
    claim_id: str
    question: str
    source_revision: str
    module: str
    confidence: Confidence
    evidence_types: tuple[EvidenceType, ...]
    addresses: tuple[Address, ...]
    conclusion: str
    remaining_unknowns: tuple[str, ...] = ()
    binary_regions: tuple[BinaryRegion, ...] = ()
    runtime_captures: tuple[RuntimeCapture, ...] = ()

    def __post_init__(self) -> None:
        required = {
            "claim_id": self.claim_id,
            "question": self.question,
            "source_revision": self.source_revision,
            "module": self.module,
            "conclusion": self.conclusion,
        }
        for name, value in required.items():
            if not value.strip():
                raise ValueError(f"{name} is required")
        if not self.evidence_types:
            raise ValueError("at least one evidence type is required")
        if not self.addresses:
            raise ValueError("at least one typed address is required")
        if self.confidence is Confidence.CONFIRMED:
            if not (_INDEPENDENT_CONFIRMATION & set(self.evidence_types)):
                raise ValueError(
                    "CONFIRMED claims require independent evidence beyond decompiler output"
                )
            if EvidenceType.EXACT_BINARY not in self.evidence_types:
                raise ValueError("CONFIRMED claims require exact binary evidence")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> EvidenceClaim:
        return cls(
            claim_id=_required_string(payload, "claim_id"),
            question=_required_string(payload, "question"),
            source_revision=_required_string(payload, "source_revision"),
            module=_required_string(payload, "module"),
            confidence=Confidence(_required_string(payload, "confidence")),
            evidence_types=tuple(
                EvidenceType(str(value)) for value in _required_list(payload, "evidence_types")
            ),
            addresses=tuple(
                Address.from_mapping(item) for item in _mapping_list(payload, "addresses")
            ),
            conclusion=_required_string(payload, "conclusion"),
            remaining_unknowns=tuple(_optional_strings(payload, "remaining_unknowns")),
            binary_regions=tuple(
                BinaryRegion.from_mapping(item)
                for item in _optional_mapping_list(payload, "binary_regions")
            ),
            runtime_captures=tuple(
                RuntimeCapture.from_mapping(item)
                for item in _optional_mapping_list(payload, "runtime_captures")
            ),
        )


def _validate_sha256(value: str, label: str) -> None:
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{label} must be 64 lowercase hexadecimal characters")


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


def _required_list(payload: Mapping[str, Any], key: str) -> list[Any]:
    value = payload.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{key} must be a non-empty list")
    return value


def _mapping_list(payload: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    values = _required_list(payload, key)
    if not all(isinstance(value, Mapping) for value in values):
        raise ValueError(f"{key} must contain objects")
    return cast(list[Mapping[str, Any]], values)


def _optional_mapping_list(payload: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    value = payload.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, Mapping) for item in value):
        raise ValueError(f"{key} must contain objects")
    return cast(list[Mapping[str, Any]], value)


def _optional_strings(payload: Mapping[str, Any], key: str) -> list[str]:
    value = payload.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must contain strings")
    return cast(list[str], value)


def _optional_sequences(payload: Mapping[str, Any], key: str) -> list[Sequence[Any]]:
    value = payload.get(key, [])
    if not isinstance(value, list) or not all(
        isinstance(item, Sequence) and not isinstance(item, (str, bytes)) and len(item) == 2
        for item in value
    ):
        raise ValueError(f"{key} must contain two-value sequences")
    return cast(list[Sequence[Any]], value)


def _sequence_string(item: Sequence[Any], index: int, label: str) -> str:
    value = item[index]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _sequence_int(item: Sequence[Any], index: int, label: str) -> int:
    value = item[index]
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{label} must be an integer")
    return value


def to_jsonable(value: object) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {key: to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [to_jsonable(item) for item in value]
    return value


def dump_json(value: object) -> str:
    return json.dumps(to_jsonable(value), indent=2, sort_keys=True) + "\n"
