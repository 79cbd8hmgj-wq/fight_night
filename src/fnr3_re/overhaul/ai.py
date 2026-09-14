"""Overhaul rule-engine module: the Alpha 1 AI response layer.

Anchors:

- ``fnr3_re.overhaul.rules.Difficulty`` -- the proven 3-level retail
  difficulty enum (Easy/Medium/Hard), found this pass by a raw-byte search
  of ``optionsettings.big``.
- Named per-player-slot AI tuning categories proven in ``BOOT.BIN`` (prior
  pass): ``ai/mods/p%d/misc offense``, ``.../defense``,
  ``.../bagotricks``, ``.../attack power``, ``.../energy and health``,
  ``.../phys damage``.

This module does not attempt to reach or replace the original AI decision
loop -- its owning function was not located by any pass so far (the
``ai/mods/p%d/...`` strings' two known consumers, ``func_00093C5C`` and
``func_00091D24``, were not disassembled this pass). It implements the
overhaul's own new AI *response* layer: a small rule-based policy that
reacts to the Alpha 1 stamina/damage state this milestone actually
introduces, per this milestone's explicit priority list (pace management,
aggression vs. conservation, reaction to low stamina, reaction to being
hurt, defensive adjustment, opponent-condition awareness). The named
``ai/mods`` categories are used as this policy's own tunable knob names so
that a future pass which does locate the real modifier table can map this
policy's outputs onto it without a shape change.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from fnr3_re.overhaul.damage import DamageState
from fnr3_re.overhaul.rules import Difficulty
from fnr3_re.overhaul.stamina import StaminaState
from fnr3_re.overhaul.tunables_io import load_tunables, save_tunables


class Action(StrEnum):
    PRESSURE = "pressure"  # aggressive advance, throw more power punches
    JAB_AND_MOVE = "jab_and_move"  # moderate pace, favor jabs
    CONSERVE = "conserve"  # low output, prioritize stamina recovery
    COVER_UP = "cover_up"  # defensive, minimize output while hurt
    FINISH = "finish"  # opponent badly hurt/exhausted: press for stoppage


@dataclass(frozen=True, slots=True)
class AIModifiers:
    """This policy's own tunable knobs, named after the proven
    ``ai/mods/p%d/...`` categories so a future pass can re-target them.
    """

    misc_offense: float = 1.0
    defense: float = 1.0
    bag_o_tricks: float = 1.0
    attack_power: float = 1.0
    energy_and_health: float = 1.0
    phys_damage: float = 1.0


#: Per-difficulty defaults. Values are this Alpha's own design choice
#: (higher difficulty = more aggressive, better defense, lower stamina
#: sensitivity threshold) -- not reverse-engineered retail values.
DIFFICULTY_MODIFIERS: dict[Difficulty, AIModifiers] = {
    Difficulty.EASY: AIModifiers(
        misc_offense=0.7, defense=0.7, attack_power=0.8, energy_and_health=1.2
    ),
    Difficulty.MEDIUM: AIModifiers(),
    Difficulty.HARD: AIModifiers(
        misc_offense=1.2, defense=1.3, attack_power=1.1, energy_and_health=0.9
    ),
}


class AIError(ValueError):
    """Raised for an invalid AI policy configuration or input."""


@dataclass(frozen=True, slots=True)
class AIPolicyTunables:
    low_stamina_fraction: float = 0.35
    hurt_health_fraction: float = 0.30
    finish_opponent_health_fraction: float = 0.20
    finish_opponent_stamina_fraction: float = 0.25

    def __post_init__(self) -> None:
        for name in (
            "low_stamina_fraction",
            "hurt_health_fraction",
            "finish_opponent_health_fraction",
            "finish_opponent_stamina_fraction",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise AIError(f"{name} must be within [0, 1]")

    def save(self, path: Path) -> None:
        save_tunables(self, path)

    @classmethod
    def load(cls, path: Path) -> AIPolicyTunables:
        return load_tunables(cls, path)


DEFAULT_POLICY_TUNABLES = AIPolicyTunables()


def choose_action(
    *,
    own_stamina: StaminaState,
    own_damage: DamageState,
    opponent_stamina: StaminaState,
    opponent_damage: DamageState,
    difficulty: Difficulty = Difficulty.MEDIUM,
    tunables: AIPolicyTunables = DEFAULT_POLICY_TUNABLES,
) -> Action:
    """Choose the CPU boxer's next high-level action.

    Priority order matches this milestone's own listed priorities:
    reaction to being hurt and low stamina come first (self-preservation),
    then opponent-condition awareness (pressing an advantage), then
    default pace management by difficulty.
    """

    self_hurt = own_damage.health_fraction <= tunables.hurt_health_fraction
    self_low_stamina = (
        own_stamina.is_exhausted() or own_stamina.fraction <= tunables.low_stamina_fraction
    )

    if self_hurt and self_low_stamina:
        return Action.COVER_UP
    if self_hurt:
        return Action.COVER_UP
    if self_low_stamina:
        return Action.CONSERVE

    opponent_finishable = (
        opponent_damage.health_fraction <= tunables.finish_opponent_health_fraction
        or opponent_stamina.fraction <= tunables.finish_opponent_stamina_fraction
    )
    if opponent_finishable:
        return Action.FINISH

    modifiers = DIFFICULTY_MODIFIERS[difficulty]
    if modifiers.misc_offense >= 1.0:
        return Action.PRESSURE
    return Action.JAB_AND_MOVE
