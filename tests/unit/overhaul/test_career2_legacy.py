from __future__ import annotations

import pytest

from fnr3_re.overhaul.career2_history import CareerHistoryResult
from fnr3_re.overhaul.career2_legacy import (
    LEGACY_FIGHT_ENTRY_SIZE,
    LEGACY_UNRANKED_SENTINEL,
    LegacyFightEntry,
    LegacyFightLedger,
    LegacyLedgerError,
    LegacyTitleStake,
)
from fnr3_re.overhaul.career2_living_divisions import WeightClass
from fnr3_re.overhaul.career2_retirement import CareerRecordSummary


def _entry(
    *,
    opponent_id: int = 41,
    career_week: int = 12,
    rank: int | None = 3,
    division: WeightClass = WeightClass.MIDDLEWEIGHT,
    stakes: LegacyTitleStake = LegacyTitleStake.NONE,
    overall: int = 82,
    wins: int = 18,
    losses: int = 2,
    draws: int = 1,
    knockouts: int = 11,
    result: CareerHistoryResult = CareerHistoryResult.WIN_DECISION,
    rounds: int = 10,
    finish_seconds: int = 0,
) -> LegacyFightEntry:
    return LegacyFightEntry(
        opponent_id=opponent_id,
        career_week=career_week,
        opponent_rank_at_fight=rank,
        division=division,
        title_stakes=stakes,
        opponent_overall_at_fight=overall,
        opponent_record_at_fight=CareerRecordSummary(
            wins=wins,
            losses=losses,
            draws=draws,
            knockouts=knockouts,
        ),
        result=result,
        rounds_lasted=rounds,
        finish_seconds=finish_seconds,
    )


def test_legacy_fight_entry_is_exactly_16_bytes_and_round_trips() -> None:
    entry = _entry(
        stakes=(
            LegacyTitleStake.TITLE_FIGHT
            | LegacyTitleStake.OPPONENT_DEFENDING
        ),
        result=CareerHistoryResult.WIN_KO,
        rounds=7,
        finish_seconds=94,
    )

    raw = entry.to_bytes()
    restored = LegacyFightEntry.from_bytes(raw)

    assert len(raw) == LEGACY_FIGHT_ENTRY_SIZE == 16
    assert restored == entry
    assert restored.is_win
    assert restored.is_ko_win
    assert restored.is_title_fight


def test_unranked_opponent_uses_explicit_ff_sentinel() -> None:
    entry = _entry(rank=None)

    raw = entry.to_bytes()
    restored = LegacyFightEntry.from_bytes(raw)

    assert raw[4] == LEGACY_UNRANKED_SENTINEL == 0xFF
    assert restored.opponent_rank_at_fight is None


def test_entry_keeps_historical_opponent_quality_snapshot() -> None:
    entry = _entry(
        rank=0,
        overall=91,
        wins=30,
        losses=1,
        draws=0,
        knockouts=24,
    )

    restored = LegacyFightEntry.from_bytes(entry.to_bytes())

    assert restored.opponent_rank_at_fight == 0
    assert restored.opponent_overall_at_fight == 91
    assert restored.opponent_record_at_fight == CareerRecordSummary(
        wins=30,
        losses=1,
        draws=0,
        knockouts=24,
    )


def test_title_stake_flags_are_mod_owned_and_composable() -> None:
    entry = _entry(
        stakes=(
            LegacyTitleStake.TITLE_FIGHT
            | LegacyTitleStake.PLAYER_DEFENDING
            | LegacyTitleStake.ELIMINATOR
        )
    )

    assert entry.is_title_fight
    assert entry.is_player_title_defense
    assert entry.title_stakes & LegacyTitleStake.ELIMINATOR


def test_entry_storage_ranges_are_enforced() -> None:
    with pytest.raises(LegacyLedgerError, match="opponent_id"):
        _entry(opponent_id=0x1_0000)
    with pytest.raises(LegacyLedgerError, match="career_week"):
        _entry(career_week=0x1_0000)
    with pytest.raises(LegacyLedgerError, match="opponent rank"):
        _entry(rank=50)
    with pytest.raises(LegacyLedgerError, match="opponent rank"):
        _entry(rank=-1)
    with pytest.raises(LegacyLedgerError, match="opponent overall"):
        _entry(overall=256)
    with pytest.raises(LegacyLedgerError, match="rounds_lasted"):
        _entry(rounds=256)
    with pytest.raises(LegacyLedgerError, match="finish_seconds"):
        _entry(finish_seconds=-1)


def test_unknown_title_stake_bits_fail_closed() -> None:
    with pytest.raises(LegacyLedgerError, match="unknown flag"):
        _entry(stakes=LegacyTitleStake(0x80))


def test_invalid_binary_weight_class_result_and_reserved_byte_fail_closed() -> None:
    raw = bytearray(_entry().to_bytes())

    raw[5] = 6
    with pytest.raises(LegacyLedgerError, match="weight class"):
        LegacyFightEntry.from_bytes(bytes(raw))

    raw = bytearray(_entry().to_bytes())
    raw[12] = 5
    with pytest.raises(LegacyLedgerError, match="result code"):
        LegacyFightEntry.from_bytes(bytes(raw))

    raw = bytearray(_entry().to_bytes())
    raw[15] = 1
    with pytest.raises(LegacyLedgerError, match="reserved"):
        LegacyFightEntry.from_bytes(bytes(raw))


def test_invalid_binary_size_fails_closed() -> None:
    with pytest.raises(LegacyLedgerError, match="exactly 16 bytes"):
        LegacyFightEntry.from_bytes(bytes(15))


def test_ledger_is_append_only_and_time_ordered() -> None:
    first = _entry(career_week=10)
    second = _entry(opponent_id=42, career_week=14)

    ledger = LegacyFightLedger().append(first).append(second)

    assert ledger.entries == (first, second)
    assert ledger.packed_size == 2 * LEGACY_FIGHT_ENTRY_SIZE

    with pytest.raises(LegacyLedgerError, match="before"):
        ledger.append(_entry(opponent_id=43, career_week=13))


def test_ledger_constructor_rejects_out_of_order_history() -> None:
    with pytest.raises(LegacyLedgerError, match="nondecreasing"):
        LegacyFightLedger(
            entries=(
                _entry(career_week=20),
                _entry(opponent_id=42, career_week=19),
            )
        )


def test_ledger_aggregates_legacy_inputs_without_scoring_weights() -> None:
    ledger = LegacyFightLedger(
        entries=(
            _entry(
                opponent_id=1,
                career_week=5,
                rank=9,
                division=WeightClass.WELTERWEIGHT,
                stakes=LegacyTitleStake.ELIMINATOR,
                result=CareerHistoryResult.WIN_DECISION,
            ),
            _entry(
                opponent_id=2,
                career_week=12,
                rank=0,
                division=WeightClass.MIDDLEWEIGHT,
                stakes=(
                    LegacyTitleStake.TITLE_FIGHT
                    | LegacyTitleStake.OPPONENT_DEFENDING
                ),
                result=CareerHistoryResult.WIN_KO,
                finish_seconds=88,
            ),
            _entry(
                opponent_id=3,
                career_week=20,
                rank=2,
                division=WeightClass.MIDDLEWEIGHT,
                stakes=(
                    LegacyTitleStake.TITLE_FIGHT
                    | LegacyTitleStake.PLAYER_DEFENDING
                ),
                result=CareerHistoryResult.WIN_DECISION,
            ),
            _entry(
                opponent_id=4,
                career_week=31,
                rank=None,
                division=WeightClass.LIGHT_HEAVYWEIGHT,
                result=CareerHistoryResult.LOSS_DECISION,
            ),
            _entry(
                opponent_id=5,
                career_week=40,
                rank=4,
                division=WeightClass.LIGHT_HEAVYWEIGHT,
                result=CareerHistoryResult.DRAW,
            ),
        )
    )

    assert ledger.proven_metrics() == {
        "ledger_bouts": 5,
        "ledger_wins": 3,
        "ledger_losses": 1,
        "ledger_draws": 1,
        "ledger_ko_wins": 1,
        "title_fights": 2,
        "title_defense_wins": 1,
        "eliminators": 1,
        "ranked_opponents": 4,
        "wins_over_ranked_opponents": 3,
        "distinct_divisions": 3,
        "best_zero_based_rank_beaten": 0,
        "career_ledger_span_weeks": 35,
    }
