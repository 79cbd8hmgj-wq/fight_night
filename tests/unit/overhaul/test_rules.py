from __future__ import annotations

import pytest

from fnr3_re.overhaul.rules import Difficulty, FightRules, RulesError


def test_default_rules_are_valid() -> None:
    rules = FightRules()
    assert rules.difficulty == Difficulty.MEDIUM
    assert rules.num_rounds == 12


def test_round_trips_through_mapping() -> None:
    rules = FightRules(difficulty=Difficulty.HARD, three_knockdown_rule=False, num_rounds=10)
    restored = FightRules.from_mapping(rules.to_mapping())
    assert restored == rules


def test_invalid_difficulty_rejected() -> None:
    with pytest.raises(RulesError, match="invalid difficulty"):
        FightRules.from_mapping({"difficulty": "impossible"})


def test_non_positive_rounds_rejected() -> None:
    with pytest.raises(RulesError, match="num_rounds"):
        FightRules(num_rounds=0)
