from __future__ import annotations

from collections.abc import Callable

import pytest

from fnr3_re.overhaul.career2_living_divisions import (
    PROGRESSION_DRAWS_OFFSET,
    PROGRESSION_KOS_OFFSET,
    PROGRESSION_LOSSES_OFFSET,
    PROGRESSION_RANK_OFFSET,
    PROGRESSION_TITLE_DEFENSES_OFFSET,
    PROGRESSION_TITLE_FORFEITURES_OFFSET,
    PROGRESSION_TITLE_LOSSES_OFFSET,
    PROGRESSION_TITLE_WINS_OFFSET,
    PROGRESSION_WINS_OFFSET,
)
from fnr3_re.overhaul.career2_retirement import (
    PROFILE_MONEY_OFFSET,
    PROFILE_RETIRED_OFFSET,
    RETAIL_LEGACY_FIELD_OFFSETS,
    RETIRED_NEXT_EVENT_CODE,
    CareerRecordSummary,
    ChampionshipRecordSummary,
    LegacyEvidenceSnapshot,
    RetirementLegacyError,
    RetirementState,
)


def _record() -> CareerRecordSummary:
    return CareerRecordSummary(wins=24, losses=2, draws=1, knockouts=18)


def _titles() -> ChampionshipRecordSummary:
    return ChampionshipRecordSummary(
        title_wins=3,
        title_losses=1,
        title_defenses=7,
        title_forfeitures=0,
    )


def test_retirement_projects_to_proven_flag_and_next_event_override() -> None:
    active = RetirementState()
    retired = active.retire()

    assert active.retail_projection().profile_u8 == {PROFILE_RETIRED_OFFSET: 0}
    assert active.retail_projection().forced_next_event == -1
    assert retired.retail_projection().profile_u8 == {PROFILE_RETIRED_OFFSET: 1}
    assert retired.retail_projection().forced_next_event == RETIRED_NEXT_EVENT_CODE == 4


def test_retirement_is_one_way_until_comeback_path_is_proven() -> None:
    retired = RetirementState().retire()

    with pytest.raises(RetirementLegacyError, match="already retired"):
        retired.retire()


def test_record_summary_derives_bouts_and_ko_rate() -> None:
    record = _record()

    assert record.bouts == 27
    assert record.knockout_win_rate_bps == 7_500


def test_zero_win_record_has_zero_ko_rate() -> None:
    record = CareerRecordSummary(wins=0, losses=1, draws=0, knockouts=0)

    assert record.knockout_win_rate_bps == 0


def test_knockouts_cannot_exceed_wins() -> None:
    with pytest.raises(RetirementLegacyError, match="cannot exceed wins"):
        CareerRecordSummary(wins=2, losses=0, draws=0, knockouts=3)


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (
            lambda: CareerRecordSummary(
                wins=256,
                losses=0,
                draws=0,
                knockouts=0,
            ),
            "wins",
        ),
        (
            lambda: ChampionshipRecordSummary(
                title_wins=0,
                title_losses=0,
                title_defenses=-1,
                title_forfeitures=0,
            ),
            "title_defenses",
        ),
    ],
)
def test_retail_byte_counters_are_range_checked(
    factory: Callable[[], object],
    message: str,
) -> None:
    with pytest.raises(RetirementLegacyError, match=message):
        factory()


def test_legacy_snapshot_exposes_only_proven_retail_metrics() -> None:
    snapshot = LegacyEvidenceSnapshot(
        age=32,
        money=1_250_000,
        current_rank=0,
        record=_record(),
        championships=_titles(),
    )

    assert snapshot.display_rank == 1
    assert snapshot.proven_metrics() == {
        "age": 32,
        "money": 1_250_000,
        "wins": 24,
        "losses": 2,
        "draws": 1,
        "knockouts": 18,
        "bouts": 27,
        "title_wins": 3,
        "title_losses": 1,
        "title_defenses": 7,
        "title_forfeitures": 0,
        "zero_based_rank": 0,
        "display_rank": 1,
    }


def test_unranked_snapshot_does_not_invent_a_rank() -> None:
    snapshot = LegacyEvidenceSnapshot(
        age=20,
        money=0,
        current_rank=None,
        record=CareerRecordSummary(wins=0, losses=0, draws=0, knockouts=0),
        championships=ChampionshipRecordSummary(
            title_wins=0,
            title_losses=0,
            title_defenses=0,
            title_forfeitures=0,
        ),
    )

    assert snapshot.display_rank is None
    assert "zero_based_rank" not in snapshot.proven_metrics()
    assert "display_rank" not in snapshot.proven_metrics()


def test_snapshot_validates_age_money_and_rank_storage() -> None:
    with pytest.raises(RetirementLegacyError, match="age"):
        LegacyEvidenceSnapshot(
            age=256,
            money=0,
            current_rank=1,
            record=_record(),
            championships=_titles(),
        )

    with pytest.raises(RetirementLegacyError, match="money"):
        LegacyEvidenceSnapshot(
            age=30,
            money=1 << 31,
            current_rank=1,
            record=_record(),
            championships=_titles(),
        )

    with pytest.raises(RetirementLegacyError, match="rank"):
        LegacyEvidenceSnapshot(
            age=30,
            money=0,
            current_rank=256,
            record=_record(),
            championships=_titles(),
        )


def test_legacy_field_map_uses_recovered_retail_offsets() -> None:
    assert RETAIL_LEGACY_FIELD_OFFSETS == {
        "retired": PROFILE_RETIRED_OFFSET,
        "money": PROFILE_MONEY_OFFSET,
        "rank": PROGRESSION_RANK_OFFSET,
        "wins": PROGRESSION_WINS_OFFSET,
        "losses": PROGRESSION_LOSSES_OFFSET,
        "draws": PROGRESSION_DRAWS_OFFSET,
        "knockouts": PROGRESSION_KOS_OFFSET,
        "title_wins": PROGRESSION_TITLE_WINS_OFFSET,
        "title_losses": PROGRESSION_TITLE_LOSSES_OFFSET,
        "title_defenses": PROGRESSION_TITLE_DEFENSES_OFFSET,
        "title_forfeitures": PROGRESSION_TITLE_FORFEITURES_OFFSET,
    }
