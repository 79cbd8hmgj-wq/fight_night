"""Overhaul rule-engine module: the Alpha 1 stamina/endurance layer.

This is new, tunable overhaul logic, not a reconstruction of a proven
original formula. Static RE this pass and the prior delta pass explicitly
*ruled out* the one lead that looked promising (``T_001D54A0``/
``T_001E83E0`` were proven to be UI rating-card registration trampolines,
not the in-fight stamina mechanic -- see ``docs/overhaul/alpha1/README.md``
for the correction) and did not locate the real in-fight stamina
consumption/regeneration code. Per this milestone's own instructions
("do not overwrite unresolved original behavior blindly"), this module
does not attempt to patch or replace that still-unlocated original code;
it implements the overhaul's *own* new stamina layer as data-driven,
tunable, and independently testable logic, anchored to the one proven
interface fact available: the boxer's ``stamina`` rating field (see
``fnr3_re.overhaul.boxer_model.BoxerRatings``) is a named, real, 9th-of-9
rating exposed on the retail boxer-selection screen.

See ``docs/overhaul/alpha1/README.md``'s "Section D: blockers" for exactly
what remains before this can be wired into a real PSP-side hook.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


class StaminaError(ValueError):
    """Raised for an invalid stamina configuration or state."""


@dataclass(frozen=True, slots=True)
class StaminaTunables:
    """All Alpha 1 stamina constants, kept out of patch/formula code.

    ``rating_to_capacity``: capacity = base_capacity + stamina_rating *
    this factor. A boxer with a proven-schema ``stamina`` rating of 0
    still gets ``base_capacity`` so a boxer never has zero maximum
    stamina from a single low rating.
    """

    base_capacity: float = 100.0
    rating_to_capacity: float = 1.0
    action_costs: dict[str, float] | None = None
    passive_recovery_per_second: float = 0.6
    between_round_recovery_fraction: float = 0.35
    exhausted_threshold_fraction: float = 0.15
    exhausted_cost_multiplier: float = 1.3
    exhausted_recovery_multiplier: float = 0.6

    def __post_init__(self) -> None:
        if self.base_capacity <= 0:
            raise StaminaError("base_capacity must be positive")
        if not 0.0 <= self.exhausted_threshold_fraction <= 1.0:
            raise StaminaError("exhausted_threshold_fraction must be within [0, 1]")
        if not 0.0 <= self.between_round_recovery_fraction <= 1.0:
            raise StaminaError("between_round_recovery_fraction must be within [0, 1]")

    def resolved_action_costs(self) -> dict[str, float]:
        if self.action_costs is not None:
            return dict(self.action_costs)
        # Default action set anchored to strings this project has proven
        # exist in BOOT.BIN's punch-type evidence (program-06): 'hook',
        # 'uppercut'. 'jab' and 'power_punch' are this mod's own additions
        # for a playable action set, not claimed as retail-proven names.
        return {
            "jab": 3.0,
            "hook": 6.0,
            "uppercut": 7.0,
            "power_punch": 9.0,
            "clinch": 1.5,
        }

    def to_mapping(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["action_costs"] = self.resolved_action_costs()
        return payload

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> StaminaTunables:
        data = dict(payload)
        action_costs = data.get("action_costs")
        if action_costs is not None:
            data["action_costs"] = {str(k): float(v) for k, v in action_costs.items()}
        return cls(**data)

    def save(self, path: Path) -> None:
        path.write_text(
            json.dumps(self.to_mapping(), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> StaminaTunables:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise StaminaError(f"invalid stamina tunables file: {exc}") from exc
        if not isinstance(payload, Mapping):
            raise StaminaError("stamina tunables root must be an object")
        return cls.from_mapping(payload)


DEFAULT_TUNABLES = StaminaTunables()


@dataclass(frozen=True, slots=True)
class StaminaState:
    current: float
    capacity: float

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise StaminaError("capacity must be positive")
        if self.current < 0:
            raise StaminaError("current stamina cannot be negative")

    @property
    def fraction(self) -> float:
        return self.current / self.capacity

    def is_exhausted(self, tunables: StaminaTunables = DEFAULT_TUNABLES) -> bool:
        return self.fraction <= tunables.exhausted_threshold_fraction

    def clamp(self) -> StaminaState:
        clamped_current = max(0.0, min(self.current, self.capacity))
        return StaminaState(current=clamped_current, capacity=self.capacity)


def initial_state(
    stamina_rating: int, tunables: StaminaTunables = DEFAULT_TUNABLES
) -> StaminaState:
    capacity = tunables.base_capacity + stamina_rating * tunables.rating_to_capacity
    return StaminaState(current=capacity, capacity=capacity)


def apply_action_cost(
    state: StaminaState,
    action: str,
    *,
    tunables: StaminaTunables = DEFAULT_TUNABLES,
) -> StaminaState:
    costs = tunables.resolved_action_costs()
    if action not in costs:
        raise StaminaError(f"unknown stamina action: {action!r}")
    cost = costs[action]
    if state.is_exhausted(tunables):
        cost *= tunables.exhausted_cost_multiplier
    clamped_current = max(0.0, min(state.current - cost, state.capacity))
    return StaminaState(current=clamped_current, capacity=state.capacity)


def apply_passive_recovery(
    state: StaminaState,
    seconds: float,
    *,
    tunables: StaminaTunables = DEFAULT_TUNABLES,
) -> StaminaState:
    if seconds < 0:
        raise StaminaError("seconds must be non-negative")
    rate = tunables.passive_recovery_per_second
    if state.is_exhausted(tunables):
        rate *= tunables.exhausted_recovery_multiplier
    return StaminaState(current=state.current + rate * seconds, capacity=state.capacity).clamp()


def apply_between_round_recovery(
    state: StaminaState,
    *,
    tunables: StaminaTunables = DEFAULT_TUNABLES,
) -> StaminaState:
    recovered = state.capacity * tunables.between_round_recovery_fraction
    return StaminaState(current=state.current + recovered, capacity=state.capacity).clamp()
