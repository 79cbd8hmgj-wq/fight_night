from __future__ import annotations

import pytest

from fnr3_re.overhaul.stamina import (
    DEFAULT_TUNABLES,
    StaminaError,
    StaminaState,
    apply_action_cost,
    apply_between_round_recovery,
    apply_passive_recovery,
    initial_state,
)


def test_initial_state_scales_with_stamina_rating() -> None:
    low = initial_state(0)
    high = initial_state(100)
    assert high.capacity > low.capacity
    assert low.current == low.capacity


def test_action_cost_reduces_current_stamina() -> None:
    state = initial_state(50)
    after = apply_action_cost(state, "jab")
    assert after.current < state.current
    assert after.capacity == state.capacity


def test_unknown_action_raises() -> None:
    state = initial_state(50)
    with pytest.raises(StaminaError, match="unknown stamina action"):
        apply_action_cost(state, "spinning_backfist")


def test_stamina_never_goes_negative() -> None:
    state = StaminaState(current=1.0, capacity=100.0)
    after = apply_action_cost(state, "power_punch")
    assert after.current == 0.0


def test_stamina_never_exceeds_capacity() -> None:
    state = StaminaState(current=99.0, capacity=100.0)
    after = apply_passive_recovery(state, seconds=1000.0)
    assert after.current == 100.0


def test_exhausted_actions_cost_more() -> None:
    tunables = DEFAULT_TUNABLES
    normal = StaminaState(current=100.0, capacity=100.0)
    exhausted = StaminaState(current=10.0, capacity=100.0)
    assert exhausted.is_exhausted(tunables)
    assert not normal.is_exhausted(tunables)

    normal_after = apply_action_cost(normal, "hook")
    exhausted_after = apply_action_cost(exhausted, "hook")
    normal_cost = normal.current - normal_after.current
    exhausted_cost = exhausted.current - exhausted_after.current
    assert exhausted_cost > normal_cost


def test_between_round_recovery_restores_a_fraction_of_capacity() -> None:
    state = StaminaState(current=0.0, capacity=100.0)
    after = apply_between_round_recovery(state)
    assert after.current == pytest.approx(35.0)


def test_negative_capacity_rejected() -> None:
    with pytest.raises(StaminaError):
        StaminaState(current=0.0, capacity=0.0)
