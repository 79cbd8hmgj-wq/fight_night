"""Overhaul rule-engine module: the Alpha 1 judging layer.

## Static evidence resolved this pass

The previously ``STATICALLY_AMBIGUOUS`` question "do the three judges use
identical calculations, separate weights, or different inputs?" was
directly investigated by disassembling ``T_001F7248`` (the real scorecard
aggregation function behind ``GetJudgesScoreInfo``, confirmed real by its
size -- 216 instructions -- versus the ~11-30 instruction registration
trampolines seen everywhere else).

Finding (CONFIRMED at the call-site level): ``T_001F7248`` fetches three
judge-object handles via ``func_01ED5C(context, judge_index)`` for
``judge_index`` in ``{0, 1, 2}`` (independently proving ``TOTAL_JUDGES ==
3``, matching ``judgesscores.big``'s own ``TOTAL_JUDGES`` UI constant),
then applies the **identical** call shape to each of the three judge
handles -- same functions (``func_08A02C``/``func_08A00C``), same argument
pattern, no per-judge multiplier, offset, or branch. This proves there is
no differential weighting **in this calling code**. It does not prove the
absence of a per-judge bias baked into each judge object's own internal
state (``func_08A02C``'s own body was not disassembled this pass) -- that
remains open and is recorded as such, not silently assumed resolved.

## What this module implements

Since the original's actual per-round scoring *formula* (as opposed to its
proven 3-judge, per-boxer, per-round data shape) was not reverse-engineered
this pass, this module implements the overhaul's own new judging formula:
a standard 10-point-must scoring convention (10 points to the round's
winner, 9 or fewer to the loser, adjusted for knockdowns), applied
identically across all 3 judges by default -- consistent with, not a
guess against, this pass's proven "no differential call-site weighting"
finding. An optional per-judge bias is exposed (defaulting to 0.0 for all
three) for future tuning, since retail's own possible per-judge-object
bias was not ruled out.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

TOTAL_JUDGES = 3  # proven: T_001F7248 (3 distinct judge-object fetches) and
# judgesscores.big!judgesScores.const's own TOTAL_JUDGES constant.


class JudgingError(ValueError):
    """Raised for an invalid judging configuration or input."""


@dataclass(frozen=True, slots=True)
class RoundStats:
    """Per-boxer statistics for one round, used to score that round."""

    punches_landed: int
    knockdowns_scored: int


@dataclass(frozen=True, slots=True)
class JudgingTunables:
    winner_points: int = 10
    max_loser_points: int = 9
    points_deducted_per_knockdown: int = 1
    #: One bias value per judge, added to the loser's score after the
    #: knockdown deduction (clamped back into [0, max_loser_points]).
    #: Defaults to no bias for any judge -- see module docstring.
    per_judge_bias: tuple[float, float, float] = field(default=(0.0, 0.0, 0.0))

    def __post_init__(self) -> None:
        if self.winner_points <= 0:
            raise JudgingError("winner_points must be positive")
        if self.max_loser_points < 0 or self.max_loser_points >= self.winner_points:
            raise JudgingError("max_loser_points must be within [0, winner_points)")
        if len(self.per_judge_bias) != TOTAL_JUDGES:
            raise JudgingError(f"per_judge_bias must have exactly {TOTAL_JUDGES} entries")

    def to_mapping(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["per_judge_bias"] = list(self.per_judge_bias)
        return payload

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> JudgingTunables:
        data = dict(payload)
        bias = data.get("per_judge_bias")
        if bias is not None:
            data["per_judge_bias"] = tuple(float(value) for value in bias)
        return cls(**data)

    def save(self, path: Path) -> None:
        path.write_text(
            json.dumps(self.to_mapping(), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> JudgingTunables:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise JudgingError(f"invalid judging tunables file: {exc}") from exc
        if not isinstance(payload, Mapping):
            raise JudgingError("judging tunables root must be an object")
        return cls.from_mapping(payload)


DEFAULT_TUNABLES = JudgingTunables()


def score_round_for_judge(
    boxer_a: RoundStats,
    boxer_b: RoundStats,
    judge_index: int,
    *,
    tunables: JudgingTunables = DEFAULT_TUNABLES,
) -> tuple[int, int]:
    """Score one round for one judge; returns (boxer_a_score, boxer_b_score).

    A round winner is the boxer with more landed punches, or more
    knockdowns scored in a tie. An exact tie in both scores 10-10 (a
    genuine even round -- not treated as an error).
    """

    if not 0 <= judge_index < TOTAL_JUDGES:
        raise JudgingError(f"judge_index must be within [0, {TOTAL_JUDGES})")

    a_edge = (boxer_a.knockdowns_scored, boxer_a.punches_landed)
    b_edge = (boxer_b.knockdowns_scored, boxer_b.punches_landed)

    if a_edge == b_edge:
        return tunables.winner_points, tunables.winner_points

    a_wins = a_edge > b_edge
    winner_kd = boxer_a.knockdowns_scored if a_wins else boxer_b.knockdowns_scored
    loser_kd = boxer_b.knockdowns_scored if a_wins else boxer_a.knockdowns_scored
    knockdown_margin = max(0, winner_kd - loser_kd)

    bias = tunables.per_judge_bias[judge_index]
    deduction = knockdown_margin * tunables.points_deducted_per_knockdown
    loser_score = tunables.max_loser_points - deduction
    loser_score = max(0, min(tunables.max_loser_points, round(loser_score + bias)))

    if a_wins:
        return tunables.winner_points, loser_score
    return loser_score, tunables.winner_points


@dataclass(frozen=True, slots=True)
class Scorecard:
    """One judge's running total across all completed rounds."""

    boxer_a_total: int = 0
    boxer_b_total: int = 0

    def add_round(self, boxer_a_points: int, boxer_b_points: int) -> Scorecard:
        return Scorecard(
            boxer_a_total=self.boxer_a_total + boxer_a_points,
            boxer_b_total=self.boxer_b_total + boxer_b_points,
        )


def decision(scorecards: tuple[Scorecard, Scorecard, Scorecard]) -> str:
    """Return 'boxer_a', 'boxer_b', 'draw', or 'split_draw'/'majority'-style
    outcomes collapsed to a simple winner/draw per this Alpha's scope.
    """

    if len(scorecards) != TOTAL_JUDGES:
        raise JudgingError(f"exactly {TOTAL_JUDGES} scorecards are required")
    a_wins = sum(1 for card in scorecards if card.boxer_a_total > card.boxer_b_total)
    b_wins = sum(1 for card in scorecards if card.boxer_b_total > card.boxer_a_total)
    if a_wins > b_wins:
        return "boxer_a"
    if b_wins > a_wins:
        return "boxer_b"
    return "draw"
