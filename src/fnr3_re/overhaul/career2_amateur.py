"""Career Mode 2.0 amateur-development domain model.

This module separates retail-backed fields whose PSP offsets and phase values
are statically proven from Career 2.0-owned development data. Retail FNR3
already has current age, phase 0/1/2 transition machinery, persistent
height/weight, starting-stat archetypes, natural rating emphasis, and a coarse
AI career-performance curve. It does not provide proven per-rating potential
ceilings or a technical learning-rate field. Those richer values therefore
remain mod-owned and are intended for the C2EX save extension.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from enum import IntEnum
from types import MappingProxyType

from fnr3_re.overhaul.boxer_model import BoxerRatings

TRAINABLE_RATINGS: tuple[str, ...] = (
    "power",
    "speed",
    "agility",
    "stamina",
    "chin",
    "body",
    "heart",
    "cuts",
)

PROFILE_AGE_MIRROR_OFFSET = 0x41
PROFILE_PHASE_OFFSET = 0x121
PROGRESSION_CURRENT_AGE_OFFSET = 0x09
BOXER_HEIGHT_OFFSET = 0x6A
BOXER_WEIGHT_OFFSET = 0x6C
BOXER_SECOND_HEIGHT_LINKED_OFFSET = 0x70
BOXER_SECOND_WEIGHT_LINKED_OFFSET = 0x72
DEFAULT_NEW_CAREER_AGE = 20

C2EX_OFFSET = 0x5674
C2EX_MAX_BYTES = 0x1EBC


class Career2DevelopmentError(ValueError):
    """Raised when Career 2.0 development state violates its invariants."""


class CareerPhase(IntEnum):
    """Proven values of persistent profile field +0x121."""

    AMATEUR = 0
    AMATEUR_TRANSITION = 1
    PROFESSIONAL = 2


@dataclass(frozen=True, slots=True)
class RatingDevelopmentPlan:
    """Career 2.0-owned per-rating development state.

    ceilings and learning_rate_bps are new mod data. They are not aliases for
    retail progression-record fields. Learning rate is expressed in basis
    points so training is deterministic and requires no floating point.
    """

    ceilings: Mapping[str, int]
    learning_rate_bps: Mapping[str, int]

    def __post_init__(self) -> None:
        expected = set(TRAINABLE_RATINGS)
        if set(self.ceilings) != expected:
            raise Career2DevelopmentError(
                "ceilings must contain exactly the eight trainable ratings"
            )
        if set(self.learning_rate_bps) != expected:
            raise Career2DevelopmentError(
                "learning_rate_bps must contain exactly the eight trainable ratings"
            )
        if any(value < 0 for value in self.learning_rate_bps.values()):
            raise Career2DevelopmentError("learning rates must be non-negative")
        object.__setattr__(self, "ceilings", MappingProxyType(dict(self.ceilings)))
        object.__setattr__(
            self,
            "learning_rate_bps",
            MappingProxyType(dict(self.learning_rate_bps)),
        )

    def validate_against(self, ratings: BoxerRatings) -> None:
        for field in TRAINABLE_RATINGS:
            current = int(getattr(ratings, field))
            ceiling = self.ceilings[field]
            if ceiling < current:
                raise Career2DevelopmentError(
                    f"{field} ceiling {ceiling} is below current rating {current}"
                )

    def apply_training(
        self,
        ratings: BoxerRatings,
        *,
        field: str,
        effort: int,
    ) -> BoxerRatings:
        """Apply one deterministic Career 2.0 training increment.

        The gain formula is mod policy: effort * learning_rate_bps // 10000.
        The result is capped by the mod-owned per-rating ceiling. overall is
        intentionally left untouched because retail computes it through
        func_001D50F4 and that formula is not reconstructed here.
        """

        if field not in TRAINABLE_RATINGS:
            raise Career2DevelopmentError(f"rating {field!r} is not trainable")
        if effort < 0:
            raise Career2DevelopmentError("training effort must be non-negative")
        self.validate_against(ratings)

        current = int(getattr(ratings, field))
        gain = effort * self.learning_rate_bps[field] // 10_000
        next_value = min(self.ceilings[field], current + gain)
        return replace(ratings, **{field: next_value})


@dataclass(frozen=True, slots=True)
class PhysicalGrowthPlan:
    """Career 2.0-owned annual growth targets.

    Retail proves persistent height and weight fields and shows generated
    boxers synchronizing paired height-/weight-linked fields. It does not
    prove a built-in annual physical-growth schedule, so yearly step sizes
    are supplied explicitly by the caller.
    """

    target_height_inches: int
    target_weight_lbs: int

    def advance(
        self,
        *,
        current_height_inches: int,
        current_weight_lbs: int,
        height_step_inches: int,
        weight_step_lbs: int,
    ) -> tuple[int, int]:
        if self.target_height_inches < current_height_inches:
            raise Career2DevelopmentError("target height is below current height")
        if self.target_weight_lbs < current_weight_lbs:
            raise Career2DevelopmentError("target weight is below current weight")
        if height_step_inches < 0 or weight_step_lbs < 0:
            raise Career2DevelopmentError("annual growth steps must be non-negative")

        height = min(
            self.target_height_inches,
            current_height_inches + height_step_inches,
        )
        weight = min(
            self.target_weight_lbs,
            current_weight_lbs + weight_step_lbs,
        )
        return height, weight


@dataclass(frozen=True, slots=True)
class RetailCareerProjection:
    """Values an eventual PSP hook may write to statically proven fields."""

    profile_u8: Mapping[int, int]
    progression_u8: Mapping[int, int]
    boxer_i16: Mapping[int, int]

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_u8", MappingProxyType(dict(self.profile_u8)))
        object.__setattr__(
            self,
            "progression_u8",
            MappingProxyType(dict(self.progression_u8)),
        )
        object.__setattr__(self, "boxer_i16", MappingProxyType(dict(self.boxer_i16)))


@dataclass(frozen=True, slots=True)
class AmateurDevelopmentState:
    """Host-side Career Mode 2.0 amateur-development state."""

    age: int
    phase: CareerPhase
    ratings: BoxerRatings
    rating_plan: RatingDevelopmentPlan
    height_inches: int
    weight_lbs: int
    physical_plan: PhysicalGrowthPlan

    def __post_init__(self) -> None:
        if not 0 <= self.age <= 255:
            raise Career2DevelopmentError("age must fit the proven retail u8 field")
        if self.height_inches <= 0:
            raise Career2DevelopmentError("height must be positive")
        if self.weight_lbs <= 0:
            raise Career2DevelopmentError("weight must be positive")
        self.rating_plan.validate_against(self.ratings)
        if self.physical_plan.target_height_inches < self.height_inches:
            raise Career2DevelopmentError("target height is below current height")
        if self.physical_plan.target_weight_lbs < self.weight_lbs:
            raise Career2DevelopmentError("target weight is below current weight")

    @classmethod
    def new_career(
        cls,
        *,
        ratings: BoxerRatings,
        rating_plan: RatingDevelopmentPlan,
        height_inches: int,
        weight_lbs: int,
        physical_plan: PhysicalGrowthPlan,
    ) -> AmateurDevelopmentState:
        """Create the evidence-backed retail starting phase at age 20."""

        return cls(
            age=DEFAULT_NEW_CAREER_AGE,
            phase=CareerPhase.AMATEUR,
            ratings=ratings,
            rating_plan=rating_plan,
            height_inches=height_inches,
            weight_lbs=weight_lbs,
            physical_plan=physical_plan,
        )

    def train(self, *, field: str, effort: int) -> AmateurDevelopmentState:
        if self.phase is CareerPhase.PROFESSIONAL:
            raise Career2DevelopmentError(
                "amateur-development training cannot run after the pro transition"
            )
        ratings = self.rating_plan.apply_training(
            self.ratings,
            field=field,
            effort=effort,
        )
        return replace(self, ratings=ratings)

    def advance_year(
        self,
        *,
        height_step_inches: int = 0,
        weight_step_lbs: int = 0,
    ) -> AmateurDevelopmentState:
        if self.age == 255:
            raise Career2DevelopmentError("age cannot exceed the retail u8 field")
        height, weight = self.physical_plan.advance(
            current_height_inches=self.height_inches,
            current_weight_lbs=self.weight_lbs,
            height_step_inches=height_step_inches,
            weight_step_lbs=weight_step_lbs,
        )
        return replace(
            self,
            age=self.age + 1,
            height_inches=height,
            weight_lbs=weight,
        )

    def begin_pro_transition(self) -> AmateurDevelopmentState:
        """Mirror the proven retail 0 -> 1 transition without rebuilding state."""

        if self.phase is not CareerPhase.AMATEUR:
            raise Career2DevelopmentError("begin_pro_transition requires phase 0")
        return replace(self, phase=CareerPhase.AMATEUR_TRANSITION)

    def complete_pro_transition(self) -> AmateurDevelopmentState:
        """Mirror the proven retail 1 -> 2 Go Pro transition."""

        if self.phase is not CareerPhase.AMATEUR_TRANSITION:
            raise Career2DevelopmentError("complete_pro_transition requires phase 1")
        return replace(self, phase=CareerPhase.PROFESSIONAL)

    def retail_projection(self) -> RetailCareerProjection:
        """Project only values whose retail destinations are statically proven.

        Potential ceilings and learning rates are intentionally absent because
        they belong in C2EX. Paired physical fields stay synchronized, matching
        proven generated/create-boxer initialization until their independent
        semantics are resolved.
        """

        return RetailCareerProjection(
            profile_u8={
                PROFILE_AGE_MIRROR_OFFSET: self.age,
                PROFILE_PHASE_OFFSET: int(self.phase),
            },
            progression_u8={PROGRESSION_CURRENT_AGE_OFFSET: self.age},
            boxer_i16={
                BOXER_HEIGHT_OFFSET: self.height_inches,
                BOXER_SECOND_HEIGHT_LINKED_OFFSET: self.height_inches,
                BOXER_WEIGHT_OFFSET: self.weight_lbs,
                BOXER_SECOND_WEIGHT_LINKED_OFFSET: self.weight_lbs,
            },
        )
