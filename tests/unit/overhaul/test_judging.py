from __future__ import annotations

import pytest

from fnr3_re.overhaul.judging import (
    TOTAL_JUDGES,
    JudgingError,
    RoundStats,
    Scorecard,
    decision,
    score_round_for_judge,
)


def test_total_judges_is_three() -> None:
    assert TOTAL_JUDGES == 3


def test_even_round_scores_ten_ten() -> None:
    a = RoundStats(punches_landed=10, knockdowns_scored=0)
    b = RoundStats(punches_landed=10, knockdowns_scored=0)
    assert score_round_for_judge(a, b, 0) == (10, 10)


def test_clear_winner_scores_ten_nine() -> None:
    a = RoundStats(punches_landed=20, knockdowns_scored=0)
    b = RoundStats(punches_landed=5, knockdowns_scored=0)
    assert score_round_for_judge(a, b, 0) == (10, 9)


def test_knockdown_deducts_an_extra_point() -> None:
    a = RoundStats(punches_landed=20, knockdowns_scored=1)
    b = RoundStats(punches_landed=15, knockdowns_scored=0)
    assert score_round_for_judge(a, b, 0) == (10, 8)


@pytest.mark.parametrize("judge_index", range(TOTAL_JUDGES))
def test_all_three_judges_score_identically_by_default(judge_index: int) -> None:
    # Direct consequence of this pass's disassembly finding: T_001F7248
    # applies identical call-site logic to all 3 judges.
    a = RoundStats(punches_landed=20, knockdowns_scored=0)
    b = RoundStats(punches_landed=5, knockdowns_scored=0)
    assert score_round_for_judge(a, b, judge_index) == (10, 9)


def test_invalid_judge_index_rejected() -> None:
    a = RoundStats(punches_landed=1, knockdowns_scored=0)
    with pytest.raises(JudgingError, match="judge_index"):
        score_round_for_judge(a, a, TOTAL_JUDGES)


def test_scorecard_accumulates_across_rounds() -> None:
    card = Scorecard()
    card = card.add_round(10, 9)
    card = card.add_round(9, 10)
    assert card.boxer_a_total == 19
    assert card.boxer_b_total == 19


def test_decision_unanimous() -> None:
    cards = (
        Scorecard(120, 108),
        Scorecard(118, 110),
        Scorecard(119, 109),
    )
    assert decision(cards) == "boxer_a"


def test_decision_draw() -> None:
    cards = (Scorecard(114, 114), Scorecard(114, 114), Scorecard(114, 114))
    assert decision(cards) == "draw"


def test_decision_requires_exactly_three_scorecards() -> None:
    with pytest.raises(JudgingError, match="exactly 3"):
        decision((Scorecard(), Scorecard()))  # type: ignore[arg-type]
