from __future__ import annotations

import pytest

from fnr3_re.overhaul.damage import (
    DEFAULT_TUNABLES,
    DamageError,
    DamageState,
    apply_punch_damage,
    apply_stun_recovery,
    initial_state,
    start_new_round,
)
from fnr3_re.overhaul.rules import FightRules


def test_initial_state_scales_with_chin_rating() -> None:
    low = initial_state(0)
    high = initial_state(100)
    assert high.max_health > low.max_health


def test_damage_reduces_health() -> None:
    state = initial_state(50)
    result = apply_punch_damage(state, 10.0, rules=FightRules())
    assert result.state.health < state.health
    assert not result.knockdown


def test_knockdown_requires_prior_stun() -> None:
    # A single huge hit from full health: not stunned yet, so per this
    # model's own rule, no knockdown fires on the very first punch even if
    # health crosses the knockdown threshold -- stun must precede it.
    state = initial_state(0)  # max_health = 100
    result = apply_punch_damage(state, 90.0, rules=FightRules())
    assert not result.knockdown


def test_knockdown_fires_once_stunned_and_below_threshold() -> None:
    rules = FightRules()
    state = initial_state(0)  # max_health = 100, stun_threshold=35% -> 35
    stunned = apply_punch_damage(state, 40.0, rules=rules).state
    assert stunned.is_stunned()
    result = apply_punch_damage(stunned, 50.0, rules=rules)
    assert result.knockdown
    assert result.state.knockdowns_this_round == 1
    assert result.state.stun_meter == 0.0


def test_three_knockdown_rule_triggers_stoppage() -> None:
    rules = FightRules(three_knockdown_rule=True)
    tunables = DEFAULT_TUNABLES
    state = initial_state(0)
    for _ in range(3):
        stunned = apply_punch_damage(state, 40.0, rules=rules, tunables=tunables).state
        result = apply_punch_damage(stunned, 50.0, rules=rules, tunables=tunables)
        state = result.state.clamp()
        state = DamageState(
            health=state.max_health,  # reset health between knockdowns for this test's isolation
            max_health=state.max_health,
            stun_meter=0.0,
            knockdowns_this_round=state.knockdowns_this_round,
            knockdowns_total=state.knockdowns_total,
        )
    stunned = apply_punch_damage(state, 40.0, rules=rules, tunables=tunables).state
    final = apply_punch_damage(stunned, 50.0, rules=rules, tunables=tunables)
    assert final.stoppage


def test_three_knockdown_rule_disabled_never_stops() -> None:
    rules = FightRules(three_knockdown_rule=False)
    state = initial_state(0)
    for _ in range(5):
        stunned = apply_punch_damage(state, 40.0, rules=rules).state
        result = apply_punch_damage(stunned, 50.0, rules=rules)
        state = DamageState(
            health=result.state.max_health,
            max_health=result.state.max_health,
            stun_meter=0.0,
            knockdowns_this_round=result.state.knockdowns_this_round,
            knockdowns_total=result.state.knockdowns_total,
        )
        assert not result.stoppage


def test_new_round_resets_per_round_knockdown_count() -> None:
    state = DamageState(health=50, max_health=100, knockdowns_this_round=2, knockdowns_total=2)
    reset = start_new_round(state)
    assert reset.knockdowns_this_round == 0
    assert reset.knockdowns_total == 2


def test_stun_recovers_over_time() -> None:
    state = DamageState(health=100, max_health=100, stun_meter=10.0)
    after = apply_stun_recovery(state, seconds=10.0)
    assert after.stun_meter < state.stun_meter


def test_negative_damage_rejected() -> None:
    state = initial_state(50)
    with pytest.raises(DamageError):
        apply_punch_damage(state, -1.0, rules=FightRules())
