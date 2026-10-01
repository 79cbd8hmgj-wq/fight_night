from __future__ import annotations

import pytest

from fnr3_re.overhaul.career2_living_divisions import ChampionshipSlots
from fnr3_re.overhaul.career2_living_world import (
    NORMAL_AI_MATCH_SUBTYPE,
    TITLE_CHALLENGE_SUBTYPE,
    TITLE_DEFENSE_SUBTYPE,
    LivingWorldError,
    ProgressionRecordState,
    assign_retail_ai_match,
    assign_title_match,
    resolve_scheduled_match,
    transfer_championship,
)


def _record(index: int, *, rank: int = 0) -> ProgressionRecordState:
    return ProgressionRecordState(boxer_index=index, rank=rank)


def test_retail_ai_match_uses_subtype_zero_and_reciprocal_opponents() -> None:
    first, second = assign_retail_ai_match(
        _record(4),
        _record(9),
        scheduled_date=0x12345678,
    )

    assert first.match_descriptor is not None
    assert second.match_descriptor is not None
    assert first.match_descriptor.opponent_index == 9
    assert second.match_descriptor.opponent_index == 4
    assert first.match_descriptor.subtype == NORMAL_AI_MATCH_SUBTYPE == 0
    assert second.match_descriptor.subtype == NORMAL_AI_MATCH_SUBTYPE
    assert first.scheduled_date == second.scheduled_date == 0x12345678


@pytest.mark.parametrize("subtype", [TITLE_CHALLENGE_SUBTYPE, TITLE_DEFENSE_SUBTYPE])
def test_title_match_accepts_only_proven_title_subtypes(subtype: int) -> None:
    challenger, champion = assign_title_match(
        _record(2),
        _record(7),
        subtype=subtype,
        scheduled_date=99,
    )

    assert challenger.match_descriptor is not None
    assert champion.match_descriptor is not None
    assert challenger.match_descriptor.subtype == subtype
    assert champion.match_descriptor.subtype == subtype


def test_title_match_rejects_unproven_subtype() -> None:
    with pytest.raises(LivingWorldError, match="8 or 9"):
        assign_title_match(
            _record(2),
            _record(7),
            subtype=6,
            scheduled_date=99,
        )


@pytest.mark.parametrize(
    ("result_code", "first_counts", "second_counts"),
    [
        (1, (0, 0, 1, 0), (0, 0, 1, 0)),
        (2, (1, 0, 0, 1), (0, 1, 0, 0)),
        (3, (1, 0, 0, 1), (0, 1, 0, 0)),
        (4, (1, 0, 0, 0), (0, 1, 0, 0)),
        (5, (1, 0, 0, 0), (0, 1, 0, 0)),
        (6, (1, 0, 0, 0), (0, 1, 0, 0)),
        (7, (0, 1, 0, 0), (1, 0, 0, 1)),
        (8, (0, 1, 0, 0), (1, 0, 0, 1)),
        (9, (0, 1, 0, 0), (1, 0, 0, 0)),
        (10, (0, 1, 0, 0), (1, 0, 0, 0)),
        (11, (0, 1, 0, 0), (1, 0, 0, 0)),
    ],
)
def test_resolved_match_applies_proven_record_classes(
    result_code: int,
    first_counts: tuple[int, int, int, int],
    second_counts: tuple[int, int, int, int],
) -> None:
    first, second = assign_retail_ai_match(
        _record(3),
        _record(8),
        scheduled_date=1234,
    )

    resolved = resolve_scheduled_match(
        first,
        second,
        result_code_for_first=result_code,
    )

    assert (
        resolved.first.wins,
        resolved.first.losses,
        resolved.first.draws,
        resolved.first.kos,
    ) == first_counts
    assert (
        resolved.second.wins,
        resolved.second.losses,
        resolved.second.draws,
        resolved.second.kos,
    ) == second_counts
    assert resolved.first.match_descriptor is None
    assert resolved.second.match_descriptor is None
    assert resolved.first.scheduled_date == 0
    assert resolved.second.scheduled_date == 0


def test_resolved_match_uses_exact_reciprocal_result_code() -> None:
    first, second = assign_retail_ai_match(
        _record(3),
        _record(8),
        scheduled_date=1234,
    )

    resolved = resolve_scheduled_match(
        first,
        second,
        result_code_for_first=5,
        secondary_code=4,
    )

    assert resolved.first_result.result_code == 5
    assert resolved.second_result.result_code == 10
    assert resolved.first_result.secondary_code == 4
    assert resolved.second_result.secondary_code == 4


@pytest.mark.parametrize("result_code", [0, 12, 13, 14, 15])
def test_resolved_match_rejects_unproven_or_unresolved_result(
    result_code: int,
) -> None:
    first, second = assign_retail_ai_match(
        _record(3),
        _record(8),
        scheduled_date=1234,
    )

    with pytest.raises(LivingWorldError):
        resolve_scheduled_match(
            first,
            second,
            result_code_for_first=result_code,
        )


def test_scheduling_rejects_self_match() -> None:
    with pytest.raises(LivingWorldError, match="against itself"):
        assign_retail_ai_match(
            _record(3),
            _record(3),
            scheduled_date=1234,
        )


def test_scheduling_rejects_already_scheduled_record() -> None:
    first, second = assign_retail_ai_match(
        _record(3),
        _record(8),
        scheduled_date=1234,
    )

    with pytest.raises(LivingWorldError, match="already has"):
        assign_retail_ai_match(first, second, scheduled_date=2000)


def test_resolve_rejects_nonreciprocal_schedule() -> None:
    first, second = assign_retail_ai_match(
        _record(3),
        _record(8),
        scheduled_date=1234,
    )
    wrong_second = ProgressionRecordState(
        boxer_index=second.boxer_index,
        rank=second.rank,
        match_descriptor=second.match_descriptor,
        scheduled_date=9999,
    )

    with pytest.raises(LivingWorldError, match="same date"):
        resolve_scheduled_match(
            first,
            wrong_second,
            result_code_for_first=2,
        )


def test_title_transfer_updates_holder_banks_and_history_counters() -> None:
    championships = ChampionshipSlots(
        current_holders=(10, 20, 30),
        previous_holders=(-1, -1, -1),
    )
    challenger = ProgressionRecordState(
        boxer_index=77,
        rank=0,
        title_wins=2,
    )
    champion = ProgressionRecordState(
        boxer_index=20,
        rank=0,
        title_losses=1,
    )

    result = transfer_championship(
        championships,
        slot=1,
        new_champion=challenger,
        displaced_champion=champion,
    )

    assert result.championships.current_holders == (10, 77, 30)
    assert result.championships.previous_holders == (-1, 20, -1)
    assert result.new_champion.title_wins == 3
    assert result.displaced_champion is not None
    assert result.displaced_champion.title_losses == 2


def test_vacant_title_transfer_records_win_without_loss() -> None:
    championships = ChampionshipSlots(
        current_holders=(-1, 20, 30),
        previous_holders=(-1, -1, -1),
    )

    result = transfer_championship(
        championships,
        slot=0,
        new_champion=_record(77),
        displaced_champion=None,
    )

    assert result.championships.current_holders[0] == 77
    assert result.new_champion.title_wins == 1
    assert result.displaced_champion is None


def test_title_transfer_requires_exact_current_holder_record() -> None:
    championships = ChampionshipSlots(
        current_holders=(10, 20, 30),
        previous_holders=(-1, -1, -1),
    )

    with pytest.raises(LivingWorldError, match="does not match"):
        transfer_championship(
            championships,
            slot=1,
            new_champion=_record(77),
            displaced_champion=_record(21),
        )


def test_title_defense_and_forfeiture_counters_are_separate() -> None:
    record = _record(4)

    defended = record.record_title_defense()
    forfeited = defended.record_title_forfeiture()

    assert defended.title_defenses == 1
    assert defended.title_forfeitures == 0
    assert forfeited.title_defenses == 1
    assert forfeited.title_forfeitures == 1


def test_u8_counter_overflow_fails_closed() -> None:
    record = ProgressionRecordState(
        boxer_index=4,
        rank=0,
        title_defenses=255,
    )

    with pytest.raises(LivingWorldError, match="overflow"):
        record.record_title_defense()
