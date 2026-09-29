"""Versioned C2EX codec for Career Mode 2.0 development data.

Retail save evidence proves that the stock active body occupies 0x5674 bytes
inside a 0x7530-byte body capacity. Stock load/save code clears the unused
tail and does not parse bytes at or after 0x5674. C2EX therefore appends a
versioned extension at that boundary without modifying the stock prefix.

Version 1 stores only Career 2.0-owned amateur-development data:
per-rating potential ceilings, per-rating learning rates, and physical-growth
targets. Current age, phase, ratings, height and weight remain in their proven
retail fields and are intentionally not duplicated here.
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass

from fnr3_re.overhaul.career2_amateur import (
    C2EX_MAX_BYTES,
    C2EX_OFFSET,
    TRAINABLE_RATINGS,
    PhysicalGrowthPlan,
    RatingDevelopmentPlan,
)

C2EX_MAGIC = b"C2EX"
C2EX_VERSION = 1
C2EX_FLAGS_NONE = 0

# magic, version, flags, payload length, CRC32(payload)
_HEADER = struct.Struct("<4sHHII")
# 8 potential ceilings, 8 learning-rate basis-point values, height target,
# weight target. All are explicit unsigned 16-bit Career 2.0 values.
_V1_PAYLOAD = struct.Struct("<" + ("H" * 18))

C2EX_HEADER_SIZE = _HEADER.size
C2EX_V1_PAYLOAD_SIZE = _V1_PAYLOAD.size
C2EX_V1_TOTAL_SIZE = C2EX_HEADER_SIZE + C2EX_V1_PAYLOAD_SIZE


class C2EXError(ValueError):
    """Raised when a C2EX block is malformed, unsupported, or out of range."""


@dataclass(frozen=True, slots=True)
class C2EXAmateurDevelopment:
    """Career 2.0 development data persisted outside the stock save chunks."""

    rating_plan: RatingDevelopmentPlan
    physical_plan: PhysicalGrowthPlan


def _as_u16(value: int, *, field: str) -> int:
    if not 0 <= value <= 0xFFFF:
        raise C2EXError(f"{field}={value} does not fit C2EX v1 uint16 storage")
    return value


def encode_c2ex(data: C2EXAmateurDevelopment) -> bytes:
    """Encode one deterministic C2EX v1 block."""

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

    payload = _V1_PAYLOAD.pack(*ceilings, *rates, height, weight)
    checksum = zlib.crc32(payload) & 0xFFFFFFFF
    block = _HEADER.pack(
        C2EX_MAGIC,
        C2EX_VERSION,
        C2EX_FLAGS_NONE,
        len(payload),
        checksum,
    ) + payload
    if len(block) > C2EX_MAX_BYTES:
        raise C2EXError("C2EX block exceeds the proven stock save-tail capacity")
    return block


def decode_c2ex(block: bytes) -> C2EXAmateurDevelopment:
    """Decode and validate one C2EX block.

    The decoder is deliberately fail-closed: unsupported flags/versions,
    inconsistent lengths, trailing bytes, and CRC failures are rejected rather
    than silently interpreted.
    """

    if len(block) < C2EX_HEADER_SIZE:
        raise C2EXError("C2EX block is shorter than its header")

    magic, version, flags, payload_length, checksum = _HEADER.unpack_from(block)
    if magic != C2EX_MAGIC:
        raise C2EXError("invalid C2EX magic")
    if version != C2EX_VERSION:
        raise C2EXError(f"unsupported C2EX version {version}")
    if flags != C2EX_FLAGS_NONE:
        raise C2EXError(f"unsupported C2EX flags 0x{flags:04X}")
    if payload_length != C2EX_V1_PAYLOAD_SIZE:
        raise C2EXError(
            f"invalid C2EX v1 payload length {payload_length}; "
            f"expected {C2EX_V1_PAYLOAD_SIZE}"
        )
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

    values = _V1_PAYLOAD.unpack(payload)
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
    )


def append_c2ex(
    stock_active_body: bytes,
    data: C2EXAmateurDevelopment,
) -> bytes:
    """Append C2EX after an unchanged stock 0x5674-byte active body."""

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
