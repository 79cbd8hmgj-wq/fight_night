from __future__ import annotations

import struct

import pytest

from fnr3_re.overhaul.career2_amateur import (
    C2EX_MAX_BYTES,
    C2EX_OFFSET,
    TRAINABLE_RATINGS,
    PhysicalGrowthPlan,
    RatingDevelopmentPlan,
)
from fnr3_re.overhaul.career2_c2ex import (
    C2EX_HEADER_SIZE,
    C2EX_MAGIC,
    C2EX_V1_PAYLOAD_SIZE,
    C2EX_V1_TOTAL_SIZE,
    C2EX_VERSION,
    C2EXAmateurDevelopment,
    C2EXError,
    append_c2ex,
    decode_c2ex,
    encode_c2ex,
    split_c2ex,
)


def _data() -> C2EXAmateurDevelopment:
    return C2EXAmateurDevelopment(
        rating_plan=RatingDevelopmentPlan(
            ceilings={
                field: 70 + index
                for index, field in enumerate(TRAINABLE_RATINGS)
            },
            learning_rate_bps={
                field: 1_000 + index * 250
                for index, field in enumerate(TRAINABLE_RATINGS)
            },
        ),
        physical_plan=PhysicalGrowthPlan(
            target_height_inches=74,
            target_weight_lbs=185,
        ),
    )


def test_v1_layout_is_small_and_within_proven_save_tail() -> None:
    assert C2EX_HEADER_SIZE == 16
    assert C2EX_V1_PAYLOAD_SIZE == 36
    assert C2EX_V1_TOTAL_SIZE == 52
    assert C2EX_V1_TOTAL_SIZE <= C2EX_MAX_BYTES


def test_encode_is_deterministic_and_round_trips() -> None:
    data = _data()

    first = encode_c2ex(data)
    second = encode_c2ex(data)
    decoded = decode_c2ex(first)

    assert first == second
    assert first[:4] == C2EX_MAGIC
    assert decoded.rating_plan.ceilings == data.rating_plan.ceilings
    assert decoded.rating_plan.learning_rate_bps == data.rating_plan.learning_rate_bps
    assert decoded.physical_plan == data.physical_plan


def test_header_uses_little_endian_version_flags_length_and_crc() -> None:
    block = encode_c2ex(_data())
    magic, version, flags, payload_length, checksum = struct.unpack_from(
        "<4sHHII",
        block,
    )

    assert magic == C2EX_MAGIC
    assert version == C2EX_VERSION
    assert flags == 0
    assert payload_length == C2EX_V1_PAYLOAD_SIZE
    assert checksum != 0


def test_append_preserves_every_stock_byte() -> None:
    stock = bytes((index * 37) & 0xFF for index in range(C2EX_OFFSET))
    extended = append_c2ex(stock, _data())

    assert extended[:C2EX_OFFSET] == stock
    assert len(extended) == C2EX_OFFSET + C2EX_V1_TOTAL_SIZE
    assert len(extended) <= C2EX_OFFSET + C2EX_MAX_BYTES


def test_split_round_trips_extended_body_and_preserves_stock_prefix() -> None:
    stock = b"\xA5" * C2EX_OFFSET
    extended = append_c2ex(stock, _data())

    restored_stock, extension = split_c2ex(extended)

    assert restored_stock == stock
    assert extension is not None
    assert extension.rating_plan.ceilings == _data().rating_plan.ceilings
    assert extension.physical_plan == _data().physical_plan


def test_split_treats_exact_stock_body_as_legacy_save() -> None:
    stock = b"\x11" * C2EX_OFFSET

    restored_stock, extension = split_c2ex(stock)

    assert restored_stock == stock
    assert extension is None


def test_split_treats_zero_filled_stock_tail_as_legacy_save() -> None:
    stock = b"\x22" * C2EX_OFFSET
    full_capacity_body = stock + bytes(C2EX_MAX_BYTES)

    restored_stock, extension = split_c2ex(full_capacity_body)

    assert restored_stock == stock
    assert extension is None


def test_crc_failure_is_rejected() -> None:
    block = bytearray(encode_c2ex(_data()))
    block[-1] ^= 0x01

    with pytest.raises(C2EXError, match="CRC mismatch"):
        decode_c2ex(bytes(block))


def test_unsupported_version_and_flags_are_rejected() -> None:
    block = bytearray(encode_c2ex(_data()))

    struct.pack_into("<H", block, 4, C2EX_VERSION + 1)
    with pytest.raises(C2EXError, match="unsupported C2EX version"):
        decode_c2ex(bytes(block))

    block = bytearray(encode_c2ex(_data()))
    struct.pack_into("<H", block, 6, 1)
    with pytest.raises(C2EXError, match="unsupported C2EX flags"):
        decode_c2ex(bytes(block))


def test_bad_payload_length_is_rejected() -> None:
    block = bytearray(encode_c2ex(_data()))
    struct.pack_into("<I", block, 8, C2EX_V1_PAYLOAD_SIZE - 1)

    with pytest.raises(C2EXError, match="payload length"):
        decode_c2ex(bytes(block))


def test_nonzero_unknown_tail_is_rejected() -> None:
    stock = b"\x33" * C2EX_OFFSET

    with pytest.raises(C2EXError, match="recognized C2EX"):
        split_c2ex(stock + b"NOPE")


def test_nonzero_bytes_after_valid_block_are_rejected() -> None:
    stock = b"\x44" * C2EX_OFFSET
    extended = append_c2ex(stock, _data())

    with pytest.raises(C2EXError, match="follow the C2EX"):
        split_c2ex(extended + b"\x00\x01")


def test_zero_padding_after_valid_block_is_allowed() -> None:
    stock = b"\x55" * C2EX_OFFSET
    extended = append_c2ex(stock, _data())
    padded = extended + bytes(64)

    restored_stock, extension = split_c2ex(padded)

    assert restored_stock == stock
    assert extension is not None


def test_uint16_overflow_is_rejected() -> None:
    data = _data()
    ceilings = dict(data.rating_plan.ceilings)
    ceilings["power"] = 0x1_0000
    invalid = C2EXAmateurDevelopment(
        rating_plan=RatingDevelopmentPlan(
            ceilings=ceilings,
            learning_rate_bps=data.rating_plan.learning_rate_bps,
        ),
        physical_plan=data.physical_plan,
    )

    with pytest.raises(C2EXError, match="uint16"):
        encode_c2ex(invalid)


def test_append_requires_exact_stock_active_body_size() -> None:
    with pytest.raises(C2EXError, match="exactly"):
        append_c2ex(b"\x00" * (C2EX_OFFSET - 1), _data())


def test_split_rejects_body_shorter_than_stock_layout() -> None:
    with pytest.raises(C2EXError, match="shorter than stock"):
        split_c2ex(b"\x00" * (C2EX_OFFSET - 1))
