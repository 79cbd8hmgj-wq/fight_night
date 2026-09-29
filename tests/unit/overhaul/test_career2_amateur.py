from __future__ import annotations

import pytest

from fnr3_re.overhaul.boxer_model import BoxerRatings
from fnr3_re.overhaul.career2_amateur import (
    BOXER_HEIGHT_OFFSET,
    BOXER_SECOND_HEIGHT_LINKED_OFFSET,
    BOXER_SECOND_WEIGHT_LINKED_OFFSET,
    BOXER_WEIGHT_OFFSET,
    DEFAULT_NEW_CAREER_AGE,
    PROFILE_AGE_MIRROR_OFFSET,
    PROFILE_PHASE_OFFSET,
    PROGRESSION_CURRENT_AGE_OFFSET,
    TRAINABLE_RATINGS,
    AmateurDevelopmentState,
    Career2DevelopmentError,
    CareerPhase,
    PhysicalGrowthPlan,
    RatingDevelopmentPlan,
)


def _ratings(**overrides: int) -> BoxerRatings:
    values = {
        "power": 50,
        "speed": 50,
        "agility": 50,
        "stamina": 50,
        "chin": 50,
        "body": 50,
        "heart": 50,
        "cuts": 50,
        "overall": 50,
    }
    values.update(overrides)
    return BoxerRatings(**values)


def _rating_plan(
    *,
    ceiling: int = 80,
    learning_rate_bps: int = 5_000,
) -> RatingDevelopmentPlan:
    return RatingDevelopmentPlan(
        ceilings={field: ceiling for field in TRAINABLE_RATINGS},
        learning_rate_bps={
            field: learning_rate_bps for field in TRAINABLE_RATINGS
        },
    )


def _state() -> AmateurDevelopmentState:
    return AmateurDevelopmentState.new_career(
        ratings=_ratings(),
        rating_plan=_rating_plan(),
        height_inches=68,
        weight_lbs=155,
        physical_plan=PhysicalGrowthPlan(
            target_height_inches=72,
            target_weight_lbs=170,
        ),
    )


def test_new_career_uses_proven_default_age_and_phase() -> None:
    state = _state()

    assert state.age == DEFAULT_NEW_CAREER_AGE == 20
    assert state.phase is CareerPhase.AMATEUR


def test_training_uses_mod_learning_rate_and_respects_ceiling() -> None:
    state = _state()

    first = state.train(field="speed", effort=20)
    capped = first.train(field="speed", effort=1000)

    assert first.ratings.speed == 60
    assert capped.ratings.speed == 80
    assert capped.ratings.overall == 50


def test_training_rejects_unknown_rating_and_negative_effort() -> None:
    state = _state()

    with pytest.raises(Career2DevelopmentError, match="not trainable"):
        state.train(field="overall", effort=10)
    with pytest.raises(Career2DevelopmentError, match="non-negative"):
        state.train(field="power", effort=-1)


def test_rating_plan_requires_all_eight_fields() -> None:
    ceilings = {field: 80 for field in TRAINABLE_RATINGS}
    del ceilings["cuts"]

    with pytest.raises(Career2DevelopmentError, match="exactly the eight"):
        RatingDevelopmentPlan(
            ceilings=ceilings,
            learning_rate_bps={
                field: 5_000 for field in TRAINABLE_RATINGS
            },
        )


def test_rating_ceiling_may_not_be_below_current_rating() -> None:
    state = _state()
    ceilings = {field: 80 for field in TRAINABLE_RATINGS}
    ceilings["power"] = 49

    with pytest.raises(Career2DevelopmentError, match="below current rating"):
        AmateurDevelopmentState.new_career(
            ratings=state.ratings,
            rating_plan=RatingDevelopmentPlan(
                ceilings=ceilings,
                learning_rate_bps={
                    field: 5_000 for field in TRAINABLE_RATINGS
                },
            ),
            height_inches=68,
            weight_lbs=155,
            physical_plan=state.physical_plan,
        )


def test_annual_growth_increments_age_and_caps_physical_targets() -> None:
    state = _state()

    year_one = state.advance_year(
        height_step_inches=2,
        weight_step_lbs=10,
    )
    year_two = year_one.advance_year(
        height_step_inches=8,
        weight_step_lbs=20,
    )

    assert year_one.age == 21
    assert (year_one.height_inches, year_one.weight_lbs) == (70, 165)
    assert year_two.age == 22
    assert (year_two.height_inches, year_two.weight_lbs) == (72, 170)


def test_pro_transition_is_strict_zero_to_one_to_two_and_preserves_state() -> None:
    state = _state().train(field="power", effort=20)
    transition = state.begin_pro_transition()
    professional = transition.complete_pro_transition()

    assert transition.phase is CareerPhase.AMATEUR_TRANSITION
    assert professional.phase is CareerPhase.PROFESSIONAL
    assert professional.ratings == state.ratings
    assert professional.height_inches == state.height_inches
    assert professional.weight_lbs == state.weight_lbs

    with pytest.raises(Career2DevelopmentError, match="requires phase 0"):
        transition.begin_pro_transition()
    with pytest.raises(Career2DevelopmentError, match="requires phase 1"):
        state.complete_pro_transition()


def test_amateur_training_stops_after_go_pro() -> None:
    professional = _state().begin_pro_transition().complete_pro_transition()

    with pytest.raises(Career2DevelopmentError, match="after the pro transition"):
        professional.train(field="power", effort=20)


def test_retail_projection_targets_only_proven_retail_fields() -> None:
    state = _state().advance_year(
        height_step_inches=1,
        weight_step_lbs=5,
    )
    projection = state.retail_projection()

    assert projection.profile_u8 == {
        PROFILE_AGE_MIRROR_OFFSET: 21,
        PROFILE_PHASE_OFFSET: int(CareerPhase.AMATEUR),
    }
    assert projection.progression_u8 == {
        PROGRESSION_CURRENT_AGE_OFFSET: 21,
    }
    assert projection.boxer_i16 == {
        BOXER_HEIGHT_OFFSET: 69,
        BOXER_SECOND_HEIGHT_LINKED_OFFSET: 69,
        BOXER_WEIGHT_OFFSET: 160,
        BOXER_SECOND_WEIGHT_LINKED_OFFSET: 160,
    }


def test_growth_plan_rejects_negative_growth_steps() -> None:
    state = _state()

    with pytest.raises(Career2DevelopmentError, match="non-negative"):
        state.advance_year(height_step_inches=-1)


def test_age_cannot_exceed_retail_u8_storage() -> None:
    state = _state()
    state = AmateurDevelopmentState(
        age=255,
        phase=state.phase,
        ratings=state.ratings,
        rating_plan=state.rating_plan,
        height_inches=state.height_inches,
        weight_lbs=state.weight_lbs,
        physical_plan=state.physical_plan,
    )

    with pytest.raises(Career2DevelopmentError, match="cannot exceed"):
        state.advance_year()
