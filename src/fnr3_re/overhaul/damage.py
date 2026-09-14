"""Overhaul rule-engine module: the Alpha 1 damage/stun/knockdown layer.

New overhaul logic, anchored to proven facts rather than a reconstruction
of the original's own (still largely undisassembled) damage/stun state
machine:

- **Knockdown/TKO-timer fields are proven real and named**:
  ``strKnockdownsLeft``/``strKnockdownsRight`` and ``astrTKOTime`` exist in
  ``BOOT.BIN`` and are read by ``T_001F2E00`` (this pass proved that
  function real, not a trampoline, and proved the exact accessor call
  shape -- see ``fnr3_re.overhaul.fight_stats``).
- **The 3-knockdown rule is proven real and named**: ``M_3_Knockdown_Rule``
  exists at two separate BOOT.BIN sites, and a matching
  ``cpToggleKnockdownRule`` UI option exists (see
  ``fnr3_re.overhaul.rules.FightRules.three_knockdown_rule``).
- **Cut/swelling damage geometry is a proven, separate resource family**
  from ratings (``HT_Swelling`` string, ``face_cuts.off`` damage-morph
  geometry) but this pass explicitly declines to implement cosmetic damage
  reconstruction, per this milestone's own scope note ("Do not attempt
  cosmetic damage reconstruction unless needed by this Alpha").

The health/vitality field structure and hit-resolution formula themselves
were not reverse-engineered this pass (program-08's own backlog entry
remains open) -- this module's health/stun numbers are therefore this
mod's own new design, not retail's.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fnr3_re.overhaul.rules import FightRules
from fnr3_re.overhaul.tunables_io import load_tunables, save_tunables


class DamageError(ValueError):
    """Raised for an invalid damage configuration or state."""


@dataclass(frozen=True, slots=True)
class DamageTunables:
    base_health: float = 100.0
    rating_to_health: float = 0.5  # scaled by the boxer's `chin` rating
    stun_threshold_fraction: float = 0.35
    stun_recovery_per_second: float = 0.5
    knockdown_health_fraction: float = 0.20
    max_knockdowns_per_round_before_stoppage: int = 3

    def __post_init__(self) -> None:
        if self.base_health <= 0:
            raise DamageError("base_health must be positive")
        if not 0.0 <= self.stun_threshold_fraction <= 1.0:
            raise DamageError("stun_threshold_fraction must be within [0, 1]")
        if self.max_knockdowns_per_round_before_stoppage <= 0:
            raise DamageError("max_knockdowns_per_round_before_stoppage must be positive")

    def save(self, path: Path) -> None:
        save_tunables(self, path)

    @classmethod
    def load(cls, path: Path) -> DamageTunables:
        return load_tunables(cls, path)


DEFAULT_TUNABLES = DamageTunables()


@dataclass(frozen=True, slots=True)
class DamageState:
    health: float
    max_health: float
    stun_meter: float = 0.0
    knockdowns_this_round: int = 0
    knockdowns_total: int = 0

    def __post_init__(self) -> None:
        if self.max_health <= 0:
            raise DamageError("max_health must be positive")
        if self.health < 0:
            raise DamageError("health cannot be negative")
        if self.stun_meter < 0:
            raise DamageError("stun_meter cannot be negative")

    @property
    def health_fraction(self) -> float:
        return self.health / self.max_health

    def is_stunned(self, tunables: DamageTunables = DEFAULT_TUNABLES) -> bool:
        return self.stun_meter >= tunables.stun_threshold_fraction * self.max_health

    def clamp(self) -> DamageState:
        return DamageState(
            health=max(0.0, min(self.health, self.max_health)),
            max_health=self.max_health,
            stun_meter=max(0.0, self.stun_meter),
            knockdowns_this_round=self.knockdowns_this_round,
            knockdowns_total=self.knockdowns_total,
        )


def initial_state(chin_rating: int, tunables: DamageTunables = DEFAULT_TUNABLES) -> DamageState:
    max_health = tunables.base_health + chin_rating * tunables.rating_to_health
    return DamageState(health=max_health, max_health=max_health)


@dataclass(frozen=True, slots=True)
class PunchResult:
    state: DamageState
    knockdown: bool
    stoppage: bool


def apply_punch_damage(
    state: DamageState,
    raw_damage: float,
    *,
    rules: FightRules,
    tunables: DamageTunables = DEFAULT_TUNABLES,
) -> PunchResult:
    """Apply damage and evaluate knockdown/stoppage per the given rules.

    A knockdown is triggered when accumulated damage since the last
    knockdown check would drop health below the knockdown threshold
    fraction of max health while the boxer is already stunned -- this
    mirrors the real game's *documented existence* of a stun-then-knockdown
    relationship (the 3-knockdown rule presupposes stun precedes
    knockdown) without claiming to reproduce its exact undisassembled
    formula.
    """

    if raw_damage < 0:
        raise DamageError("raw_damage must be non-negative")

    was_stunned = state.is_stunned(tunables)
    next_health = state.health - raw_damage
    next_stun = state.stun_meter + raw_damage

    knockdown = False
    knockdowns_this_round = state.knockdowns_this_round
    knockdowns_total = state.knockdowns_total
    if was_stunned and next_health <= tunables.knockdown_health_fraction * state.max_health:
        knockdown = True
        knockdowns_this_round += 1
        knockdowns_total += 1
        next_stun = 0.0  # a knockdown resets the stun meter (fresh start on recovery)

    stoppage = (
        rules.three_knockdown_rule
        and knockdowns_this_round >= tunables.max_knockdowns_per_round_before_stoppage
    )

    new_state = DamageState(
        health=max(0.0, min(next_health, state.max_health)),
        max_health=state.max_health,
        stun_meter=max(0.0, next_stun),
        knockdowns_this_round=knockdowns_this_round,
        knockdowns_total=knockdowns_total,
    )
    return PunchResult(state=new_state, knockdown=knockdown, stoppage=stoppage)


def apply_stun_recovery(
    state: DamageState,
    seconds: float,
    *,
    tunables: DamageTunables = DEFAULT_TUNABLES,
) -> DamageState:
    if seconds < 0:
        raise DamageError("seconds must be non-negative")
    recovered = tunables.stun_recovery_per_second * seconds
    return DamageState(
        health=state.health,
        max_health=state.max_health,
        stun_meter=max(0.0, state.stun_meter - recovered),
        knockdowns_this_round=state.knockdowns_this_round,
        knockdowns_total=state.knockdowns_total,
    )


def start_new_round(state: DamageState) -> DamageState:
    """Reset the per-round knockdown counter at a round boundary."""

    return DamageState(
        health=state.health,
        max_health=state.max_health,
        stun_meter=state.stun_meter,
        knockdowns_this_round=0,
        knockdowns_total=state.knockdowns_total,
    )
