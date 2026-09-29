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
    C2EX_MAX_LEDGER_ENTRIES,
    C2EX_V1_PAYLOAD_SIZE,
    C2EX_V1_TOTAL_SIZE,
    C2EX_V2_BASE_TOTAL_SIZE,
    C2EX_VERSION,
    C2EX_VERSION_V1,
    C2EXAmateurDevelopment,
    C2EXError,
    append_c2ex,
    decode_c2ex,
    encode_c2ex,
    encode_c2ex_v1,
    split_c2ex,
)
from fnr3_re.overhaul.career2_history import CareerHistoryResult
from fnr3_re.overhaul.career2_legacy import (
    LEGACY_FIGHT_ENTRY_SIZE,
    LegacyFightEntry,
    LegacyFightLedger,
    LegacyTitleStake,
)
from fnr3_re.overhaul.career2_living_divisions import WeightClass
from fnr3_re.overhaul.career2_retirement import CareerRecordSummary


def _entry(
    *,
    opponent_id: int = 12,
    career_week: int = 8,
) -> LegacyFightEntry:
    return LegacyFightEntry(
        opponent_id=opponent_id,
        career_week=career_week,
        opponent_rank_at_fight=3,
        division=WeightClass.MIDDLEWEIGHT,
        title_stakes=LegacyTitleStake.TITLE_FIGHT,
        opponent_overall_at_fight=84,
        opponent_record_at_fight=CareerRecordSummary(
            wins=20,
            losses=2,
            draws=1,
            knockouts=13,
        ),
        result=CareerHistoryResult.WIN_DECISION,
        rounds_lasted=10,
        finish_seconds=0,
    )


def _data(
    *,
    ledger: LegacyFightLedger | None = None,
    schema_version: int = C2EX_VERSION,
) -> C2EXAmateurDevelopment:
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
        legacy_ledger=ledger or LegacyFightLedger(),
        schema_version=schema_version,
    )


def test_v1_compatibility_layout_remains_exact() -> None:
    block = encode_c2ex_v1(_data())

    assert C2EX_HEADER_SIZE == 16
    assert C2EX_V1_PAYLOAD_SIZE == 36
    assert C2EX_V1_TOTAL_SIZE == 52
    assert len(block) == C2EX_V1_TOTAL_SIZE
    assert struct.unpack_from("<H", block, 4)[0] == C2EX_VERSION_V1


def test_v2_empty_ledger_layout_is_small_and_within_proven_tail() -> None:
    block = encode_c2ex(_data())

    assert C2EX_V2_BASE_TOTAL_SIZE == 56
    assert len(block) == C2EX_V2_BASE_TOTAL_SIZE
    assert len(block) <= C2EX_MAX_BYTES
    assert struct.unpack_from("<H", block, 4)[0] == C2EX_VERSION


def test_v2_encode_is_deterministic_and_round_trips_ledger() -> None:
    ledger = LegacyFightLedger(
        entries=(
            _entry(opponent_id=12, career_week=8),
            _entry(opponent_id=18, career_week=16),
        )
    )
    data = _data(ledger=ledger)

    first = encode_c2ex(data)
    second = encode_c2ex(data)
    decoded = decode_c2ex(first)

    assert first == second
    assert first[:4] == C2EX_MAGIC
    assert decoded.schema_version == C2EX_VERSION
    assert decoded.rating_plan.ceilings == data.rating_plan.ceilings
    assert decoded.rating_plan.learning_rate_bps == data.rating_plan.learning_rate_bps
    assert decoded.physical_plan == data.physical_plan
    assert decoded.legacy_ledger == ledger
    assert len(first) == C2EX_V2_BASE_TOTAL_SIZE + 2 * LEGACY_FIGHT_ENTRY_SIZE


def test_v1_decode_upgrades_model_with_empty_ledger() -> None:
    block = encode_c2ex_v1(_data())

    decoded = decode_c2ex(block)

    assert decoded.schema_version == C2EX_VERSION_V1
    assert decoded.legacy_ledger == LegacyFightLedger()
    assert decoded.rating_plan == _data().rating_plan
    assert decoded.physical_plan == _data().physical_plan


def test_latest_header_uses_little_endian_version_flags_length_and_crc() -> None:
    block = encode_c2ex(_data())
    magic, version, flags, payload_length, checksum = struct.unpack_from(
        "<4sHHII",
        block,
    )

    assert magic == C2EX_MAGIC
    assert version == C2EX_VERSION == 2
    assert flags == 0
    assert payload_length == len(block) - C2EX_HEADER_SIZE
    assert checksum != 0


def test_append_preserves_every_stock_byte() -> None:
    stock = bytes((index * 37) & 0xFF for index in range(C2EX_OFFSET))
    extended = append_c2ex(
        stock,
        _data(ledger=LegacyFightLedger(entries=(_entry(),))),
    )

    assert extended[:C2EX_OFFSET] == stock
    assert len(extended) <= C2EX_OFFSET + C2EX_MAX_BYTES


def test_split_round_trips_extended_body_and_preserves_stock_prefix() -> None:
    stock = b"\xA5" * C2EX_OFFSET
    ledger = LegacyFightLedger(entries=(_entry(),))
    extended = append_c2ex(stock, _data(ledger=ledger))

    restored_stock, extension = split_c2ex(extended)

    assert restored_stock == stock
    assert extension is not None
    assert extension.legacy_ledger == ledger
    assert extension.schema_version == C2EX_VERSION


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


def test_v1_bad_payload_length_is_rejected() -> None:
    block = bytearray(encode_c2ex_v1(_data()))
    struct.pack_into("<I", block, 8, C2EX_V1_PAYLOAD_SIZE - 1)

    with pytest.raises(C2EXError, match="block length"):
        decode_c2ex(bytes(block[:-1]))


def test_v2_bad_entry_size_is_rejected_after_crc_is_recomputed() -> None:
    block = bytearray(encode_c2ex(_data()))
    payload = bytearray(block[C2EX_HEADER_SIZE:])
    struct.pack_into("<H", payload, C2EX_V1_PAYLOAD_SIZE + 2, 15)
    checksum = __import__("zlib").crc32(payload) & 0xFFFFFFFF
    struct.pack_into("<I", block, 12, checksum)
    block[C2EX_HEADER_SIZE:] = payload

    with pytest.raises(C2EXError, match="legacy entry size"):
        decode_c2ex(bytes(block))


def test_v2_count_length_mismatch_is_rejected_after_crc_is_recomputed() -> None:
    block = bytearray(encode_c2ex(_data()))
    payload = bytearray(block[C2EX_HEADER_SIZE:])
    struct.pack_into("<H", payload, C2EX_V1_PAYLOAD_SIZE, 1)
    checksum = __import__("zlib").crc32(payload) & 0xFFFFFFFF
    struct.pack_into("<I", block, 12, checksum)
    block[C2EX_HEADER_SIZE:] = payload

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


def test_maximum_ledger_capacity_is_derived_from_proven_tail() -> None:
    entries = tuple(
        _entry(opponent_id=index, career_week=index)
        for index in range(C2EX_MAX_LEDGER_ENTRIES)
    )
    block = encode_c2ex(_data(ledger=LegacyFightLedger(entries=entries)))

    assert C2EX_MAX_LEDGER_ENTRIES == 488
    assert len(block) <= C2EX_MAX_BYTES
    assert C2EX_MAX_BYTES - len(block) < LEGACY_FIGHT_ENTRY_SIZE


def test_ledger_over_capacity_is_rejected() -> None:
    entries = tuple(
        _entry(opponent_id=index, career_week=index)
        for index in range(C2EX_MAX_LEDGER_ENTRIES + 1)
    )

    with pytest.raises(C2EXError, match="exceeds"):
        _data(ledger=LegacyFightLedger(entries=entries))


def test_v1_rejects_nonempty_ledger() -> None:
    ledger = LegacyFightLedger(entries=(_entry(),))

    with pytest.raises(C2EXError, match="v1 cannot contain"):
        C2EXAmateurDevelopment(
            rating_plan=_data().rating_plan,
            physical_plan=_data().physical_plan,
            legacy_ledger=ledger,
            schema_version=C2EX_VERSION_V1,
        )


def test_encode_v1_rejects_nonempty_ledger_even_on_latest_model() -> None:
    data = _data(ledger=LegacyFightLedger(entries=(_entry(),)))

    with pytest.raises(C2EXError, match="cannot encode"):
        encode_c2ex_v1(data)


def test_append_requires_exact_stock_active_body_size() -> None:
    with pytest.raises(C2EXError, match="exactly"):
        append_c2ex(b"\x00" * (C2EX_OFFSET - 1), _data())


def test_split_rejects_body_shorter_than_stock_layout() -> None:
    with pytest.raises(C2EXError, match="shorter than stock"):
        split_c2ex(b"\x00" * (C2EX_OFFSET - 1))
