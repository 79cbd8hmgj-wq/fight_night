from __future__ import annotations

import pytest

from fnr3_re.overhaul.career2_living_divisions import (
    INITIAL_AMATEUR_LADDER_SIZE,
    PROFESSIONAL_LADDER_SIZE,
    UNAVAILABLE_WEIGHT_CLASS,
    CareerMatchDescriptor,
    CareerWeightClassWindow,
    ChampionshipSlots,
    LivingDivisionError,
    RankingEntry,
    WeightClass,
    active_ladder_size,
    classify_weight,
    synchronize_public_ranks,
)


@pytest.mark.parametrize(
    ("weight", "expected"),
    [
        (126, WeightClass.FEATHERWEIGHT),
        (127, WeightClass.LIGHTWEIGHT),
        (135, WeightClass.LIGHTWEIGHT),
        (136, WeightClass.WELTERWEIGHT),
        (147, WeightClass.WELTERWEIGHT),
        (148, WeightClass.MIDDLEWEIGHT),
        (168, WeightClass.MIDDLEWEIGHT),
        (169, WeightClass.LIGHT_HEAVYWEIGHT),
        (190, WeightClass.LIGHT_HEAVYWEIGHT),
        (191, WeightClass.HEAVYWEIGHT),
        (280, WeightClass.HEAVYWEIGHT),
    ],
)
def test_weight_classifier_matches_retail_thresholds(
    weight: int,
    expected: WeightClass,
) -> None:
    assert classify_weight(weight) is expected


@pytest.mark.parametrize("weight", [0, -1, 281, 400])
def test_weight_classifier_rejects_outside_retail_domain(weight: int) -> None:
    with pytest.raises(LivingDivisionError):
        classify_weight(weight)


def test_middleweight_window_is_base_heavier_lighter() -> None:
    window = CareerWeightClassWindow.from_base_class(WeightClass.MIDDLEWEIGHT)

    assert window.slot_classes == (
        int(WeightClass.MIDDLEWEIGHT),
        int(WeightClass.LIGHT_HEAVYWEIGHT),
        int(WeightClass.WELTERWEIGHT),
    )


def test_weight_window_uses_boundary_sentinel() -> None:
    heavyweight = CareerWeightClassWindow.from_base_class(WeightClass.HEAVYWEIGHT)
    featherweight = CareerWeightClassWindow.from_base_class(
        WeightClass.FEATHERWEIGHT
    )

    assert heavyweight.slot_classes == (
        int(WeightClass.HEAVYWEIGHT),
        UNAVAILABLE_WEIGHT_CLASS,
        int(WeightClass.LIGHT_HEAVYWEIGHT),
    )
    assert featherweight.slot_classes == (
        int(WeightClass.FEATHERWEIGHT),
        int(WeightClass.LIGHTWEIGHT),
        UNAVAILABLE_WEIGHT_CLASS,
    )


def test_committed_slot_switch_updates_both_retail_slot_roles() -> None:
    window = CareerWeightClassWindow.from_base_class(WeightClass.MIDDLEWEIGHT)

    switched = window.switch_committed_player_slot(2)

    assert switched.working_slot == 2
    assert switched.committed_slot == 2
    assert switched.is_committed_slot_synchronized


def test_background_slot_selection_changes_only_working_slot() -> None:
    window = CareerWeightClassWindow.from_base_class(WeightClass.MIDDLEWEIGHT)

    background = window.select_background_working_slot(1)

    assert background.working_slot == 1
    assert background.committed_slot == 0
    assert not background.is_committed_slot_synchronized


def test_unavailable_edge_slot_cannot_be_selected() -> None:
    window = CareerWeightClassWindow.from_base_class(WeightClass.HEAVYWEIGHT)

    with pytest.raises(LivingDivisionError, match="unavailable"):
        window.switch_committed_player_slot(1)


def test_match_descriptor_matches_proven_bit_layout() -> None:
    descriptor = CareerMatchDescriptor(
        opponent_index=0x1234,
        subtype=9,
        result_code=2,
        secondary_code=5,
    )

    assert descriptor.pack() == 0x12340925
    assert CareerMatchDescriptor.unpack(descriptor.pack()) == descriptor


def test_match_descriptor_result_predicates_match_retail_classes() -> None:
    assert CareerMatchDescriptor(1, 0, 1).is_draw
    assert CareerMatchDescriptor(1, 0, 2).is_win_class
    assert CareerMatchDescriptor(1, 0, 6).is_win_class
    assert CareerMatchDescriptor(1, 0, 7).is_loss_class
    assert CareerMatchDescriptor(1, 0, 11).is_loss_class
    assert CareerMatchDescriptor(1, 0, 2).counts_as_ko_win
    assert CareerMatchDescriptor(1, 0, 3).counts_as_ko_win
    assert not CareerMatchDescriptor(1, 0, 4).counts_as_ko_win


@pytest.mark.parametrize(
    ("result_code", "reciprocal"),
    [
        (0, 0),
        (1, 1),
        (2, 7),
        (3, 8),
        (4, 9),
        (5, 10),
        (6, 11),
        (7, 2),
        (8, 3),
        (9, 4),
        (10, 5),
        (11, 6),
    ],
)
def test_reciprocal_result_table_is_exact(
    result_code: int,
    reciprocal: int,
) -> None:
    descriptor = CareerMatchDescriptor(
        opponent_index=12,
        subtype=8,
        result_code=result_code,
        secondary_code=4,
    )

    converted = descriptor.reciprocal(opponent_index=7)

    assert converted.opponent_index == 7
    assert converted.subtype == 8
    assert converted.result_code == reciprocal
    assert converted.secondary_code == 4


def test_unproven_result_code_reciprocal_fails_closed() -> None:
    descriptor = CareerMatchDescriptor(1, 0, 12)

    with pytest.raises(LivingDivisionError, match="only proven"):
        descriptor.reciprocal(opponent_index=2)


def test_bit_31_descriptor_is_rejected() -> None:
    with pytest.raises(LivingDivisionError, match="bit 31"):
        CareerMatchDescriptor.unpack(0x80000000)


def test_public_rank_sync_uses_existing_ladder_order() -> None:
    entries = (
        RankingEntry(score=900, boxer_index=10),
        RankingEntry(score=700, boxer_index=3),
        RankingEntry(score=500, boxer_index=8),
    )

    assert synchronize_public_ranks(entries) == {10: 0, 3: 1, 8: 2}


def test_public_rank_sync_rejects_duplicate_boxer_indices() -> None:
    entries = (
        RankingEntry(score=900, boxer_index=10),
        RankingEntry(score=800, boxer_index=10),
    )

    with pytest.raises(LivingDivisionError, match="duplicate"):
        synchronize_public_ranks(entries)


def test_active_ladder_sizes_preserve_retail_defaults() -> None:
    assert (
        active_ladder_size(initial_amateur_division_zero=True)
        == INITIAL_AMATEUR_LADDER_SIZE
        == 20
    )
    assert (
        active_ladder_size(initial_amateur_division_zero=False)
        == PROFESSIONAL_LADDER_SIZE
        == 50
    )


def test_title_transfer_moves_current_holder_to_previous_bank() -> None:
    titles = ChampionshipSlots(
        current_holders=(10, 20, 30),
        previous_holders=(-1, -1, -1),
    )

    updated, displaced = titles.transfer(slot=1, new_holder=77)

    assert displaced == 20
    assert updated.current_holders == (10, 77, 30)
    assert updated.previous_holders == (-1, 20, -1)
    assert titles.current_holders == (10, 20, 30)


def test_title_transfer_rejects_invalid_slot() -> None:
    titles = ChampionshipSlots(
        current_holders=(10, 20, 30),
        previous_holders=(-1, -1, -1),
    )

    with pytest.raises(LivingDivisionError, match=r"0\.\.2"):
        titles.transfer(slot=3, new_holder=77)
