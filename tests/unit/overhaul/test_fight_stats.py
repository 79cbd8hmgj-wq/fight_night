from __future__ import annotations

import pytest

from fnr3_re.overhaul.fight_stats import punch_accuracy_percent


def test_zero_thrown_sentinel_is_zero_not_a_crash() -> None:
    assert punch_accuracy_percent(0, 0) == 0


def test_exact_percentage() -> None:
    assert punch_accuracy_percent(50, 100) == 50


def test_truncates_toward_zero_not_rounds() -> None:
    # 33.333...% must truncate to 33, not round to 33 (same here) --
    # use a case where truncation and rounding disagree to prove it.
    assert punch_accuracy_percent(2, 3) == 66  # 66.66...% -> 66, not 67


def test_all_hit() -> None:
    assert punch_accuracy_percent(10, 10) == 100


def test_more_hit_than_thrown_is_not_special_cased() -> None:
    # The original does not guard against this (nonsensical) input domain;
    # reproduce its behavior rather than inventing a new guard.
    assert punch_accuracy_percent(15, 10) == 150


@pytest.mark.parametrize("hit,thrown", [(-1, 10), (1, -10)])
def test_rejects_negative_inputs(hit: int, thrown: int) -> None:
    with pytest.raises(ValueError, match="non-negative"):
        punch_accuracy_percent(hit, thrown)
