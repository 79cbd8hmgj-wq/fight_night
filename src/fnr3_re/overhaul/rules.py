"""Overhaul rule-engine module: fight rules/options.

Anchors: the retail options menu (decoded this delta pass from
``optionsettings.big!optionSettings.const``) names 17 real, distinct
gameplay-rule toggles, of which the ones below are directly relevant to
this Alpha's combat/damage/stamina systems. The exact underlying storage
(a packed bitfield at fight-session-singleton offset ``+0x15C``, per
``fnr3_re.overhaul.fight_session``) was located but not fully bit-mapped
this pass -- so this module's :class:`FightRules` is this mod's own
tunable rule *set*, evidence-anchored in name and existence, not a
bit-for-bit reproduction of the original's storage.

Proven anchors, by field:

- ``difficulty``: a named 3-level enum, ``Easy``/``Medium``/``Hard``,
  proven this pass by a raw-byte search of ``optionsettings.big`` (an
  ``m_arrText`` UI array bound to the ``cpToggleDifficulty`` widget).
- ``three_knockdown_rule``: ``M_3_Knockdown_Rule``, proven in ``BOOT.BIN``
  (0x50e17c/0x50eb6c), referenced by two separate functions, plus the
  matching ``cpToggleKnockdownRule`` UI toggle.
- ``auto_recovery``, ``ko_moment``, ``fight_stoppage``, ``illegal_blows``,
  ``saved_by_bell``: named UI toggles (``cpToggleAutoRecovery`` etc.)
  proven to exist this pass; their underlying original semantics were not
  disassembled, only their existence and names.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class Difficulty(StrEnum):
    """The proven 3-level retail difficulty enum (Easy/Medium/Hard)."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class RulesError(ValueError):
    """Raised for an invalid fight-rules configuration."""


@dataclass(frozen=True, slots=True)
class FightRules:
    difficulty: Difficulty = Difficulty.MEDIUM
    three_knockdown_rule: bool = True
    auto_recovery: bool = True
    ko_moment: bool = True
    fight_stoppage: bool = True
    illegal_blows: bool = True
    saved_by_the_bell: bool = True
    num_rounds: int = 12

    def __post_init__(self) -> None:
        if self.num_rounds <= 0:
            raise RulesError("num_rounds must be positive")

    def to_mapping(self) -> dict[str, object]:
        return {
            "difficulty": self.difficulty.value,
            "three_knockdown_rule": self.three_knockdown_rule,
            "auto_recovery": self.auto_recovery,
            "ko_moment": self.ko_moment,
            "fight_stoppage": self.fight_stoppage,
            "illegal_blows": self.illegal_blows,
            "saved_by_the_bell": self.saved_by_the_bell,
            "num_rounds": self.num_rounds,
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> FightRules:
        try:
            difficulty = Difficulty(payload.get("difficulty", Difficulty.MEDIUM.value))
        except ValueError as exc:
            raise RulesError(f"invalid difficulty: {payload.get('difficulty')!r}") from exc
        num_rounds = payload.get("num_rounds", 12)
        if not isinstance(num_rounds, int) or isinstance(num_rounds, bool):
            raise RulesError(f"num_rounds must be an integer, got {num_rounds!r}")
        return cls(
            difficulty=difficulty,
            three_knockdown_rule=bool(payload.get("three_knockdown_rule", True)),
            auto_recovery=bool(payload.get("auto_recovery", True)),
            ko_moment=bool(payload.get("ko_moment", True)),
            fight_stoppage=bool(payload.get("fight_stoppage", True)),
            illegal_blows=bool(payload.get("illegal_blows", True)),
            saved_by_the_bell=bool(payload.get("saved_by_the_bell", True)),
            num_rounds=num_rounds,
        )
