"""Career Mode 2.0 retirement and legacy evidence foundation.

Retail FNR3 already has a persistent retired flag and a hard retirement
next-event override. It also persists several career statistics that can feed a
Career Mode 2.0 legacy system: rank, W/L/D/KO record, championship history,
money, and age.

This module deliberately stops before assigning a final legacy-score formula.
Opposition quality, multi-division accomplishments, technique, longevity, and
health are Career Mode 2.0 policy/data questions that should not be silently
invented from unrelated retail fields.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from types import MappingProxyType

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

PROFILE_RETIRED_OFFSET = 0x00
PROFILE_MONEY_OFFSET = 0xA0
RETIRED_NEXT_EVENT_CODE = 4


class RetirementLegacyError(ValueError):
    """Raised when retirement/legacy state violates a proven boundary."""


@dataclass(frozen=True, slots=True)
class RetailRetirementProjection:
    """Retail values produced by a retired Career Mode 2.0 player."""

    profile_u8: Mapping[int, int]
    forced_next_event: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_u8", MappingProxyType(dict(self.profile_u8)))


@dataclass(frozen=True, slots=True)
class RetirementState:
    """One-way retirement state backed by retail profile+0x00.

    Retail evidence proves that nonzero profile+0x00 emits iRetired and forces
    GetNextEventState to code 4. A comeback/unretire write path has not yet
    been proven, so this foundation does not expose one.
    """

    retired: bool = False

    def retire(self) -> RetirementState:
        if self.retired:
            raise RetirementLegacyError("career is already retired")
        return replace(self, retired=True)

    def retail_projection(self) -> RetailRetirementProjection:
        return RetailRetirementProjection(
            profile_u8={PROFILE_RETIRED_OFFSET: int(self.retired)},
            forced_next_event=RETIRED_NEXT_EVENT_CODE if self.retired else -1,
        )


@dataclass(frozen=True, slots=True)
class CareerRecordSummary:
    """Retail-backed W/L/D/KO values from the current progression record."""

    wins: int
    losses: int
    draws: int
    knockouts: int

    def __post_init__(self) -> None:
        for name, value in (
            ("wins", self.wins),
            ("losses", self.losses),
            ("draws", self.draws),
            ("knockouts", self.knockouts),
        ):
            if not 0 <= value <= 0xFF:
                raise RetirementLegacyError(f"{name} must fit retail uint8 storage")
        if self.knockouts > self.wins:
            raise RetirementLegacyError("knockouts cannot exceed wins")

    @property
    def bouts(self) -> int:
        return self.wins + self.losses + self.draws

    @property
    def knockout_win_rate_bps(self) -> int:
        if self.wins == 0:
            return 0
        return self.knockouts * 10_000 // self.wins


@dataclass(frozen=True, slots=True)
class ChampionshipRecordSummary:
    """Retail-backed title counters from one progression record."""

    title_wins: int
    title_losses: int
    title_defenses: int
    title_forfeitures: int

    def __post_init__(self) -> None:
        for name, value in (
            ("title_wins", self.title_wins),
            ("title_losses", self.title_losses),
            ("title_defenses", self.title_defenses),
            ("title_forfeitures", self.title_forfeitures),
        ):
            if not 0 <= value <= 0xFF:
                raise RetirementLegacyError(f"{name} must fit retail uint8 storage")


@dataclass(frozen=True, slots=True)
class LegacyEvidenceSnapshot:
    """Legacy inputs already available from proven retail state.

    current_rank is the zero-based value stored at progression+0x04.
    money is the profile+0xA0 bank balance. age is supplied from the
    proven career age path used by the amateur-development slice.

    This is intentionally an evidence snapshot, not a score. Career 2.0 still
    needs explicit policy for opposition quality, division breadth, longevity,
    technique and health before a final legacy formula is locked.
    """

    age: int
    money: int
    current_rank: int | None
    record: CareerRecordSummary
    championships: ChampionshipRecordSummary

    def __post_init__(self) -> None:
        if not 0 <= self.age <= 0xFF:
            raise RetirementLegacyError("age must fit the retail uint8 field")
        if not -(1 << 31) <= self.money <= (1 << 31) - 1:
            raise RetirementLegacyError("money must fit signed retail int32 storage")
        if self.current_rank is not None and not 0 <= self.current_rank <= 0xFF:
            raise RetirementLegacyError("current rank must fit retail uint8 storage")

    @property
    def display_rank(self) -> int | None:
        if self.current_rank is None:
            return None
        return self.current_rank + 1

    def proven_metrics(self) -> Mapping[str, int]:
        """Return only score inputs whose retail source is already mapped."""

        metrics = {
            "age": self.age,
            "money": self.money,
            "wins": self.record.wins,
            "losses": self.record.losses,
            "draws": self.record.draws,
            "knockouts": self.record.knockouts,
            "bouts": self.record.bouts,
            "title_wins": self.championships.title_wins,
            "title_losses": self.championships.title_losses,
            "title_defenses": self.championships.title_defenses,
            "title_forfeitures": self.championships.title_forfeitures,
        }
        if self.current_rank is not None:
            metrics["zero_based_rank"] = self.current_rank
            metrics["display_rank"] = self.current_rank + 1
        return MappingProxyType(metrics)


RETAIL_LEGACY_FIELD_OFFSETS: Mapping[str, int] = MappingProxyType(
    {
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
)
