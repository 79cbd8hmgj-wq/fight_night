"""Evidence-backed Career Mode 2.0 living-division primitives.

This module models only retail structures whose layouts/behaviour have been
statically proven: the six absolute weight classes, the three-slot career
window, packed match descriptors, ordered ranking entries, and three-slot
championship ownership.

It intentionally does not invent the Career 2.0 policy for autonomous AI title
bouts, mandatory challengers, eliminators, or the still-unnamed individual
fight-result methods. Those remain higher-level policy layered on these
primitives.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import IntEnum

CAREER_SLOT_COUNT = 3
ABSOLUTE_WEIGHT_CLASS_COUNT = 6
UNAVAILABLE_WEIGHT_CLASS = 7
INITIAL_AMATEUR_LADDER_SIZE = 20
PROFESSIONAL_LADDER_SIZE = 50
MAX_LADDER_ENTRIES = 50

PROFILE_WORKING_SLOT_OFFSET = 0x2A
PROFILE_COMMITTED_SLOT_OFFSET = 0x2B
PROFILE_SLOT_CLASS_BASE_OFFSET = 0x2D
PROFILE_CURRENT_CHAMPION_BASE_OFFSET = 0x50
PROFILE_PREVIOUS_CHAMPION_BASE_OFFSET = 0x56

PROGRESSION_RANK_OFFSET = 0x04
PROGRESSION_WINS_OFFSET = 0x05
PROGRESSION_LOSSES_OFFSET = 0x06
PROGRESSION_DRAWS_OFFSET = 0x07
PROGRESSION_KOS_OFFSET = 0x08
PROGRESSION_TITLE_WINS_OFFSET = 0x15
PROGRESSION_TITLE_LOSSES_OFFSET = 0x16
PROGRESSION_TITLE_DEFENSES_OFFSET = 0x17
PROGRESSION_TITLE_FORFEITURES_OFFSET = 0x18
PROGRESSION_RANKING_SCORE_OFFSET = 0x20
PROGRESSION_MATCH_DESCRIPTOR_OFFSET = 0x24
PROGRESSION_SCHEDULED_DATE_OFFSET = 0x28

RANKING_LADDER_BASE_OFFSET = 0x2E8
RANKING_LADDER_STRIDE = 0xC8
RANKING_ENTRY_SIZE = 4

_RECIPROCAL_RESULT_CODES: tuple[int, ...] = (
    0,
    1,
    7,
    8,
    9,
    10,
    11,
    2,
    3,
    4,
    5,
    6,
)


class LivingDivisionError(ValueError):
    """Raised when living-division state violates a proven storage boundary."""


class WeightClass(IntEnum):
    """Absolute retail weight-class enum used by the career system."""

    HEAVYWEIGHT = 0
    LIGHT_HEAVYWEIGHT = 1
    MIDDLEWEIGHT = 2
    WELTERWEIGHT = 3
    LIGHTWEIGHT = 4
    FEATHERWEIGHT = 5


def classify_weight(weight_lbs: int) -> WeightClass:
    """Return the exact retail class selected by function 0x0018600C.

    Retail accepts integer weights through 280 lb and treats 281+ as invalid.
    """

    if weight_lbs <= 0:
        raise LivingDivisionError("weight must be positive")
    if weight_lbs <= 126:
        return WeightClass.FEATHERWEIGHT
    if weight_lbs <= 135:
        return WeightClass.LIGHTWEIGHT
    if weight_lbs <= 147:
        return WeightClass.WELTERWEIGHT
    if weight_lbs <= 168:
        return WeightClass.MIDDLEWEIGHT
    if weight_lbs <= 190:
        return WeightClass.LIGHT_HEAVYWEIGHT
    if weight_lbs <= 280:
        return WeightClass.HEAVYWEIGHT
    raise LivingDivisionError("retail weight classifier rejects weights >= 281 lb")


@dataclass(frozen=True, slots=True)
class CareerWeightClassWindow:
    """The proven three-slot moving career window.

    Slot 0 is the classified base class. Slot 1 is one class heavier
    (enum value base-1), and slot 2 is one class lighter (base+1). At either
    end of the six-class enum, retail stores sentinel value 7.
    """

    slot_classes: tuple[int, int, int]
    working_slot: int = 0
    committed_slot: int = 0

    def __post_init__(self) -> None:
        valid_values = {*range(ABSOLUTE_WEIGHT_CLASS_COUNT), UNAVAILABLE_WEIGHT_CLASS}
        for value in self.slot_classes:
            if value not in valid_values:
                raise LivingDivisionError(f"invalid absolute weight-class value {value}")
        self._validate_slot(self.working_slot)
        self._validate_slot(self.committed_slot)

    @classmethod
    def from_base_class(cls, base_class: WeightClass) -> CareerWeightClassWindow:
        base = int(base_class)
        heavier = (
            base - 1
            if base > int(WeightClass.HEAVYWEIGHT)
            else UNAVAILABLE_WEIGHT_CLASS
        )
        lighter = (
            base + 1
            if base < int(WeightClass.FEATHERWEIGHT)
            else UNAVAILABLE_WEIGHT_CLASS
        )
        return cls(slot_classes=(base, heavier, lighter))

    @classmethod
    def from_weight(cls, weight_lbs: int) -> CareerWeightClassWindow:
        return cls.from_base_class(classify_weight(weight_lbs))

    def _validate_slot(self, slot: int) -> None:
        if not 0 <= slot < CAREER_SLOT_COUNT:
            raise LivingDivisionError("career slot must be in range 0..2")

    def absolute_class_for_slot(self, slot: int) -> WeightClass | None:
        self._validate_slot(slot)
        value = self.slot_classes[slot]
        if value == UNAVAILABLE_WEIGHT_CLASS:
            return None
        return WeightClass(value)

    def switch_committed_player_slot(self, slot: int) -> CareerWeightClassWindow:
        """Mirror the explicit retail player-facing slot setter.

        Function 0x0019527C writes the requested slot to profile+0x2A and
        profile+0x2B. It does not modify physical boxer weight.
        """

        self._validate_slot(slot)
        if self.slot_classes[slot] == UNAVAILABLE_WEIGHT_CLASS:
            raise LivingDivisionError("requested career slot is unavailable")
        return replace(self, working_slot=slot, committed_slot=slot)

    def select_background_working_slot(self, slot: int) -> CareerWeightClassWindow:
        """Select a slot for background processing without changing the shadow."""

        self._validate_slot(slot)
        if self.slot_classes[slot] == UNAVAILABLE_WEIGHT_CLASS:
            raise LivingDivisionError("requested career slot is unavailable")
        return replace(self, working_slot=slot)

    @property
    def is_committed_slot_synchronized(self) -> bool:
        return self.working_slot == self.committed_slot


@dataclass(frozen=True, slots=True)
class CareerMatchDescriptor:
    """Decoded progression-record +0x24 word for a scheduled fight."""

    opponent_index: int
    subtype: int
    result_code: int = 0
    secondary_code: int = 0

    def __post_init__(self) -> None:
        if not 0 <= self.opponent_index <= 0x7FFF:
            raise LivingDivisionError("opponent index must fit 15 bits")
        if not 0 <= self.subtype <= 0xFF:
            raise LivingDivisionError("match subtype must fit 8 bits")
        if not 0 <= self.result_code <= 0xF:
            raise LivingDivisionError("result code must fit 4 bits")
        if not 0 <= self.secondary_code <= 0xF:
            raise LivingDivisionError("secondary result/state code must fit 4 bits")

    def pack(self) -> int:
        return (
            (self.opponent_index & 0x7FFF) << 16
            | (self.subtype & 0xFF) << 8
            | (self.result_code & 0xF) << 4
            | (self.secondary_code & 0xF)
        )

    @classmethod
    def unpack(cls, packed: int) -> CareerMatchDescriptor:
        if not 0 <= packed <= 0xFFFFFFFF:
            raise LivingDivisionError("packed match descriptor must fit uint32")
        if packed & 0x80000000:
            raise LivingDivisionError("bit 31 is not produced by the retail packer")
        return cls(
            opponent_index=(packed >> 16) & 0x7FFF,
            subtype=(packed >> 8) & 0xFF,
            result_code=(packed >> 4) & 0xF,
            secondary_code=packed & 0xF,
        )

    @property
    def is_draw(self) -> bool:
        return self.result_code == 1

    @property
    def is_win_class(self) -> bool:
        return 2 <= self.result_code <= 6

    @property
    def is_loss_class(self) -> bool:
        return 7 <= self.result_code <= 11

    @property
    def counts_as_ko_win(self) -> bool:
        return self.result_code in {2, 3}

    def reciprocal(self, *, opponent_index: int) -> CareerMatchDescriptor:
        """Return the proven opposite-fighter perspective conversion.

        Retail's reciprocal table is proven only for result codes 0..11.
        """

        if self.result_code >= len(_RECIPROCAL_RESULT_CODES):
            raise LivingDivisionError(
                "reciprocal semantics are only proven for result codes 0..11"
            )
        return CareerMatchDescriptor(
            opponent_index=opponent_index,
            subtype=self.subtype,
            result_code=_RECIPROCAL_RESULT_CODES[self.result_code],
            secondary_code=self.secondary_code,
        )


@dataclass(frozen=True, slots=True)
class RankingEntry:
    """One persistent four-byte division-ladder entry."""

    score: int
    boxer_index: int

    def __post_init__(self) -> None:
        if not 0 <= self.score <= 0xFFFF:
            raise LivingDivisionError("ranking score must fit uint16")
        if not -0x8000 <= self.boxer_index <= 0x7FFF:
            raise LivingDivisionError("boxer index must fit int16")


def synchronize_public_ranks(
    ordered_entries: tuple[RankingEntry, ...],
) -> dict[int, int]:
    """Return rank bytes written from an already-sorted retail ladder.

    The synchronizer writes ladder position directly to progression
    record+0x04. This helper deliberately does not choose the score sort
    direction because that policy is outside this primitive.
    """

    if len(ordered_entries) > MAX_LADDER_ENTRIES:
        raise LivingDivisionError("division ladder cannot exceed 50 entries")
    result: dict[int, int] = {}
    for rank, entry in enumerate(ordered_entries):
        if entry.boxer_index in result:
            raise LivingDivisionError("division ladder contains duplicate boxer index")
        result[entry.boxer_index] = rank
    return result


def active_ladder_size(*, initial_amateur_division_zero: bool) -> int:
    """Return the two statically proven default active ladder lengths."""

    if initial_amateur_division_zero:
        return INITIAL_AMATEUR_LADDER_SIZE
    return PROFESSIONAL_LADDER_SIZE


@dataclass(frozen=True, slots=True)
class ChampionshipSlots:
    """Three persistent current/previous career-title holder slots."""

    current_holders: tuple[int, int, int]
    previous_holders: tuple[int, int, int]

    def __post_init__(self) -> None:
        for holder in (*self.current_holders, *self.previous_holders):
            if not -0x8000 <= holder <= 0x7FFF:
                raise LivingDivisionError("title holder index must fit int16")

    def transfer(self, *, slot: int, new_holder: int) -> tuple[ChampionshipSlots, int]:
        """Mirror the holder-array part of retail function 0x00196DC4.

        The displaced holder is returned so a higher-level career system can
        apply the proven +0x15/+0x16 title-history increments.
        """

        if not 0 <= slot < CAREER_SLOT_COUNT:
            raise LivingDivisionError("title slot must be in range 0..2")
        if not -0x8000 <= new_holder <= 0x7FFF:
            raise LivingDivisionError("new title holder index must fit int16")

        old_holder = self.current_holders[slot]
        c0, c1, c2 = self.current_holders
        p0, p1, p2 = self.previous_holders
        current = [c0, c1, c2]
        previous = [p0, p1, p2]
        previous[slot] = old_holder
        current[slot] = new_holder
        return (
            ChampionshipSlots(
                current_holders=(current[0], current[1], current[2]),
                previous_holders=(previous[0], previous[1], previous[2]),
            ),
            old_holder,
        )

    def holder_for_slot(self, slot: int) -> int:
        if not 0 <= slot < CAREER_SLOT_COUNT:
            raise LivingDivisionError("title slot must be in range 0..2")
        return self.current_holders[slot]
