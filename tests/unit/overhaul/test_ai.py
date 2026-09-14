from __future__ import annotations

from fnr3_re.overhaul.ai import Action, choose_action
from fnr3_re.overhaul.damage import DamageState
from fnr3_re.overhaul.rules import Difficulty
from fnr3_re.overhaul.stamina import StaminaState


def _healthy() -> tuple[StaminaState, DamageState]:
    return StaminaState(current=100, capacity=100), DamageState(health=100, max_health=100)


def _low_stamina() -> tuple[StaminaState, DamageState]:
    return StaminaState(current=10, capacity=100), DamageState(health=100, max_health=100)


def _hurt() -> tuple[StaminaState, DamageState]:
    return StaminaState(current=100, capacity=100), DamageState(health=20, max_health=100)


def test_hurt_boxer_covers_up() -> None:
    own_stamina, own_damage = _hurt()
    opp_stamina, opp_damage = _healthy()
    action = choose_action(
        own_stamina=own_stamina,
        own_damage=own_damage,
        opponent_stamina=opp_stamina,
        opponent_damage=opp_damage,
    )
    assert action == Action.COVER_UP


def test_low_stamina_boxer_conserves() -> None:
    own_stamina, own_damage = _low_stamina()
    opp_stamina, opp_damage = _healthy()
    action = choose_action(
        own_stamina=own_stamina,
        own_damage=own_damage,
        opponent_stamina=opp_stamina,
        opponent_damage=opp_damage,
    )
    assert action == Action.CONSERVE


def test_presses_advantage_when_opponent_exhausted() -> None:
    own_stamina, own_damage = _healthy()
    opp_stamina, opp_damage = _low_stamina()
    action = choose_action(
        own_stamina=own_stamina,
        own_damage=own_damage,
        opponent_stamina=opp_stamina,
        opponent_damage=opp_damage,
    )
    assert action == Action.FINISH


def test_healthy_fighters_default_to_pressure_at_hard_difficulty() -> None:
    own_stamina, own_damage = _healthy()
    opp_stamina, opp_damage = _healthy()
    action = choose_action(
        own_stamina=own_stamina,
        own_damage=own_damage,
        opponent_stamina=opp_stamina,
        opponent_damage=opp_damage,
        difficulty=Difficulty.HARD,
    )
    assert action == Action.PRESSURE


def test_healthy_fighters_at_easy_difficulty_favor_jab_and_move() -> None:
    own_stamina, own_damage = _healthy()
    opp_stamina, opp_damage = _healthy()
    action = choose_action(
        own_stamina=own_stamina,
        own_damage=own_damage,
        opponent_stamina=opp_stamina,
        opponent_damage=opp_damage,
        difficulty=Difficulty.EASY,
    )
    assert action == Action.JAB_AND_MOVE


def test_self_priorities_outrank_opponent_condition() -> None:
    # Both own state AND opponent state qualify for different actions;
    # self-preservation (hurt) must win per this milestone's priority order.
    own_stamina, own_damage = _hurt()
    opp_stamina, opp_damage = _low_stamina()
    action = choose_action(
        own_stamina=own_stamina,
        own_damage=own_damage,
        opponent_stamina=opp_stamina,
        opponent_damage=opp_damage,
    )
    assert action == Action.COVER_UP
