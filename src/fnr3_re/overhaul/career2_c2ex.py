"""Versioned C2EX codec for Career Mode 2.0-owned save data.

Retail save evidence proves that the stock active body occupies 0x5674 bytes
inside a 0x7530-byte body capacity. C2EX appends after that boundary without
modifying the stock prefix.

Version 1 stored only amateur-development data. Version 2 keeps the exact v1
36-byte development prefix and appends a counted, fixed-width Career 2.0
legacy fight ledger. The decoder accepts both versions; new writes use v2.
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass, field

from fnr3_re.overhaul.career2_amateur import (
    C2EX_MAX_BYTES,
    C2EX_OFFSET,
    TRAINABLE_RATINGS,
    PhysicalGrowthPlan,
    RatingDevelopmentPlan,
)
from fnr3_re.overhaul.career2_legacy import (
    LEGACY_FIGHT_ENTRY_SIZE,
    LegacyFightEntry,
    LegacyFightLedger,
    LegacyLedgerError,
)

C2EX_MAGIC = b"C2EX"
C2EX_VERSION_V1 = 1
C2EX_VERSION = 2
C2EX_FLAGS_NONE = 0

# magic, version, flags, payload length, CRC32(payload)
_HEADER = struct.Struct("<4sHHII")

# v1/v2 shared development prefix:
# 8 potential ceilings, 8 learning-rate basis-point values, target height,
# target weight. All values are unsigned 16-bit Career 2.0-owned data.
_V1_PAYLOAD = struct.Struct("<" + ("H" * 18))

# v2 suffix directly after the unchanged 36-byte v1 prefix:
# ledger count, ledger entry size, then count * 16-byte entries.
_V2_LEDGER_HEADER = struct.Struct("<HH")

C2EX_HEADER_SIZE = _HEADER.size
C2EX_V1_PAYLOAD_SIZE = _V1_PAYLOAD.size
C2EX_V1_TOTAL_SIZE = C2EX_HEADER_SIZE + C2EX_V1_PAYLOAD_SIZE
C2EX_V2_FIXED_PAYLOAD_SIZE = C2EX_V1_PAYLOAD_SIZE + _V2_LEDGER_HEADER.size
C2EX_V2_BASE_TOTAL_SIZE = C2EX_HEADER_SIZE + C2EX_V2_FIXED_PAYLOAD_SIZE
C2EX_MAX_LEDGER_ENTRIES = (
    C2EX_MAX_BYTES - C2EX_V2_BASE_TOTAL_SIZE
) // LEGACY_FIGHT_ENTRY_SIZE


class C2EXError(ValueError):
    """Raised when a C2EX block is malformed, unsupported, or out of range."""


@dataclass(frozen=True, slots=True)
class C2EXAmateurDevelopment:
    """Career 2.0-owned extension state.

    The historical class name is retained for API compatibility. Since C2EX
    v2, the object also carries the mod-owned legacy fight ledger.
    """

    rating_plan: RatingDevelopmentPlan
    physical_plan: PhysicalGrowthPlan
    legacy_ledger: LegacyFightLedger = field(default_factory=LegacyFightLedger)
    schema_version: int = C2EX_VERSION

    def __post_init__(self) -> None:
        if self.schema_version not in {C2EX_VERSION_V1, C2EX_VERSION}:
            raise C2EXError(f"unsupported C2EX schema version {self.schema_version}")
        if self.schema_version == C2EX_VERSION_V1 and self.legacy_ledger.entries:
            raise C2EXError("C2EX v1 cannot contain a legacy fight ledger")
        if len(self.legacy_ledger.entries) > C2EX_MAX_LEDGER_ENTRIES:
            raise C2EXError(
                "legacy fight ledger exceeds the proven C2EX save-tail capacity"
            )


def _as_u16(value: int, *, field: str) -> int:
    if not 0 <= value <= 0xFFFF:
        raise C2EXError(f"{field}={value} does not fit C2EX uint16 storage")
    return value


def _development_payload(data: C2EXAmateurDevelopment) -> bytes:
    ceilings = [
        _as_u16(data.rating_plan.ceilings[name], field=f"{name}.ceiling")
        for name in TRAINABLE_RATINGS
    ]
    rates = [
        _as_u16(
            data.rating_plan.learning_rate_bps[name],
            field=f"{name}.learning_rate_bps",
        )
        for name in TRAINABLE_RATINGS
    ]
    height = _as_u16(
        data.physical_plan.target_height_inches,
        field="target_height_inches",
    )
    weight = _as_u16(
        data.physical_plan.target_weight_lbs,
        field="target_weight_lbs",
    )
    return _V1_PAYLOAD.pack(*ceilings, *rates, height, weight)


def _wrap_block(*, version: int, payload: bytes) -> bytes:
    checksum = zlib.crc32(payload) & 0xFFFFFFFF
    block = _HEADER.pack(
        C2EX_MAGIC,
        version,
        C2EX_FLAGS_NONE,
        len(payload),
        checksum,
    ) + payload
    if len(block) > C2EX_MAX_BYTES:
        raise C2EXError("C2EX block exceeds the proven stock save-tail capacity")
    return block


def encode_c2ex_v1(data: C2EXAmateurDevelopment) -> bytes:
    """Encode the original v1 layout for compatibility fixtures/migration tests."""

    if data.legacy_ledger.entries:
        raise C2EXError("cannot encode a nonempty legacy ledger as C2EX v1")
    return _wrap_block(
        version=C2EX_VERSION_V1,
        payload=_development_payload(data),
    )


def encode_c2ex(data: C2EXAmateurDevelopment) -> bytes:
    """Encode one deterministic latest-version (v2) C2EX block."""

    count = len(data.legacy_ledger.entries)
    if count > C2EX_MAX_LEDGER_ENTRIES:
        raise C2EXError(
            f"legacy fight ledger has {count} entries; "
            f"maximum is {C2EX_MAX_LEDGER_ENTRIES}"
        )
    ledger_payload = b"".join(entry.to_bytes() for entry in data.legacy_ledger.entries)
    payload = (
        _development_payload(data)
        + _V2_LEDGER_HEADER.pack(count, LEGACY_FIGHT_ENTRY_SIZE)
        + ledger_payload
    )
    return _wrap_block(version=C2EX_VERSION, payload=payload)


def _decode_development(
    payload: bytes,
    *,
    schema_version: int,
    ledger: LegacyFightLedger,
) -> C2EXAmateurDevelopment:
    values = _V1_PAYLOAD.unpack(payload[:C2EX_V1_PAYLOAD_SIZE])
    ceiling_values = values[: len(TRAINABLE_RATINGS)]
    rate_start = len(TRAINABLE_RATINGS)
    rate_end = rate_start + len(TRAINABLE_RATINGS)
    rate_values = values[rate_start:rate_end]
    target_height, target_weight = values[rate_end:]

    return C2EXAmateurDevelopment(
        rating_plan=RatingDevelopmentPlan(
            ceilings=dict(zip(TRAINABLE_RATINGS, ceiling_values, strict=True)),
            learning_rate_bps=dict(
                zip(TRAINABLE_RATINGS, rate_values, strict=True)
            ),
        ),
        physical_plan=PhysicalGrowthPlan(
            target_height_inches=target_height,
            target_weight_lbs=target_weight,
        ),
        legacy_ledger=ledger,
        schema_version=schema_version,
    )


def decode_c2ex(block: bytes) -> C2EXAmateurDevelopment:
    """Decode and validate a C2EX v1 or v2 block.

    The decoder is fail-closed: unsupported flags/versions, inconsistent
    lengths, entry-size changes, trailing bytes, and CRC failures are rejected.
    """

    if len(block) < C2EX_HEADER_SIZE:
        raise C2EXError("C2EX block is shorter than its header")

    magic, version, flags, payload_length, checksum = _HEADER.unpack_from(block)
    if magic != C2EX_MAGIC:
        raise C2EXError("invalid C2EX magic")
    if version not in {C2EX_VERSION_V1, C2EX_VERSION}:
        raise C2EXError(f"unsupported C2EX version {version}")
    if flags != C2EX_FLAGS_NONE:
        raise C2EXError(f"unsupported C2EX flags 0x{flags:04X}")

    expected_total = C2EX_HEADER_SIZE + payload_length
    if expected_total > C2EX_MAX_BYTES:
        raise C2EXError("C2EX block exceeds the proven stock save-tail capacity")
    if len(block) != expected_total:
        raise C2EXError(
            f"C2EX block length {len(block)} does not match header length "
            f"{expected_total}"
        )

    payload = block[C2EX_HEADER_SIZE:]
    actual_checksum = zlib.crc32(payload) & 0xFFFFFFFF
    if actual_checksum != checksum:
        raise C2EXError(
            f"C2EX CRC mismatch: expected 0x{checksum:08X}, "
            f"got 0x{actual_checksum:08X}"
        )

    if version == C2EX_VERSION_V1:
        if payload_length != C2EX_V1_PAYLOAD_SIZE:
            raise C2EXError(
                f"invalid C2EX v1 payload length {payload_length}; "
                f"expected {C2EX_V1_PAYLOAD_SIZE}"
            )
        return _decode_development(
            payload,
            schema_version=C2EX_VERSION_V1,
            ledger=LegacyFightLedger(),
        )

    if payload_length < C2EX_V2_FIXED_PAYLOAD_SIZE:
        raise C2EXError("C2EX v2 payload is shorter than its fixed prefix")

    count, entry_size = _V2_LEDGER_HEADER.unpack_from(
        payload,
        C2EX_V1_PAYLOAD_SIZE,
    )
    if entry_size != LEGACY_FIGHT_ENTRY_SIZE:
        raise C2EXError(
            f"unsupported C2EX v2 legacy entry size {entry_size}; "
            f"expected {LEGACY_FIGHT_ENTRY_SIZE}"
        )
    if count > C2EX_MAX_LEDGER_ENTRIES:
        raise C2EXError(
            f"C2EX v2 legacy count {count} exceeds maximum "
            f"{C2EX_MAX_LEDGER_ENTRIES}"
        )

    expected_payload_length = (
        C2EX_V2_FIXED_PAYLOAD_SIZE + count * LEGACY_FIGHT_ENTRY_SIZE
    )
    if payload_length != expected_payload_length:
        raise C2EXError(
            f"invalid C2EX v2 payload length {payload_length}; "
            f"expected {expected_payload_length} for {count} ledger entries"
        )

    ledger_start = C2EX_V2_FIXED_PAYLOAD_SIZE
    entries_list: list[LegacyFightEntry] = []
    for index in range(count):
        raw_entry = payload[
            ledger_start + index * LEGACY_FIGHT_ENTRY_SIZE :
            ledger_start + (index + 1) * LEGACY_FIGHT_ENTRY_SIZE
        ]
        try:
            entries_list.append(LegacyFightEntry.from_bytes(raw_entry))
        except LegacyLedgerError as exc:
            raise C2EXError(
                f"invalid C2EX v2 legacy entry {index}: {exc}"
            ) from exc
    entries = tuple(entries_list)
    return _decode_development(
        payload,
        schema_version=C2EX_VERSION,
        ledger=LegacyFightLedger(entries=entries),
    )


def append_c2ex(
    stock_active_body: bytes,
    data: C2EXAmateurDevelopment,
) -> bytes:
    """Append latest-version C2EX after an unchanged stock active body."""

    if len(stock_active_body) != C2EX_OFFSET:
        raise C2EXError(
            f"stock active body must be exactly 0x{C2EX_OFFSET:X} bytes, "
            f"got 0x{len(stock_active_body):X}"
        )
    block = encode_c2ex(data)
    active_body = stock_active_body + block
    if len(active_body) > C2EX_OFFSET + C2EX_MAX_BYTES:
        raise C2EXError("extended active body exceeds proven body capacity")
    return active_body


def split_c2ex(active_body: bytes) -> tuple[bytes, C2EXAmateurDevelopment | None]:
    """Split an active body into its unchanged stock prefix and optional C2EX.

    A body of exactly 0x5674 bytes is a legacy stock save. A zero-filled tail
    is also treated as legacy migration input because retail clears the unused
    save capacity. Any nonzero unrecognized tail fails closed.
    """

    if len(active_body) < C2EX_OFFSET:
        raise C2EXError(
            f"active body is shorter than stock size 0x{C2EX_OFFSET:X}"
        )
    stock = active_body[:C2EX_OFFSET]
    tail = active_body[C2EX_OFFSET:]
    if not tail or not any(tail):
        return stock, None
    if len(tail) > C2EX_MAX_BYTES:
        raise C2EXError("active-body tail exceeds proven C2EX capacity")
    if not tail.startswith(C2EX_MAGIC):
        raise C2EXError("nonzero save tail does not contain a recognized C2EX block")

    if len(tail) < C2EX_HEADER_SIZE:
        raise C2EXError("C2EX save tail is shorter than its header")
    _, _, _, payload_length, _ = _HEADER.unpack_from(tail)
    total_length = C2EX_HEADER_SIZE + payload_length
    if total_length > len(tail):
        raise C2EXError("C2EX save tail is truncated")

    block = tail[:total_length]
    trailing = tail[total_length:]
    if any(trailing):
        raise C2EXError("nonzero bytes follow the C2EX block")
    return stock, decode_c2ex(block)
