"""Career Mode 2.0 living-world result and championship state.

This layer composes the retail-backed primitives recovered in
career2_living_divisions. It deliberately implements state transitions whose
storage semantics are proven while leaving ranking-score math, AI outcome
selection, title eligibility, and mandatory-challenger policy to separate
policy layers.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from fnr3_re.overhaul.career2_living_divisions import (
    CareerMatchDescriptor,
    ChampionshipSlots,
    LivingDivisionError,
)

NORMAL_AI_MATCH_SUBTYPE = 0
TITLE_CHALLENGE_SUBTYPE = 8
TITLE_DEFENSE_SUBTYPE = 9
MAX_U8 = 0xFF
MAX_U16 = 0xFFFF


class LivingWorldError(LivingDivisionError):
    """Raised when a living-world transition violates proven retail state."""


def _checked_u8(value: int, *, field: str) -> int:
    if not 0 <= value <= MAX_U8:
        raise LivingWorldError(f"{field} must fit uint8")
    return value


def _increment_u8(value: int, *, field: str) -> int:
    if value >= MAX_U8:
        raise LivingWorldError(f"{field} would overflow uint8")
    return value + 1


@dataclass(frozen=True, slots=True)
class ProgressionRecordState:
    """Host representation of the proven living-world progression fields."""

    boxer_index: int
    rank: int
    wins: int = 0
    losses: int = 0
    draws: int = 0
    kos: int = 0
    title_wins: int = 0
    title_losses: int = 0
    title_defenses: int = 0
    title_forfeitures: int = 0
    ranking_score: int = 0
    cooldown_weeks: int = 0
    match_descriptor: CareerMatchDescriptor | None = None
    scheduled_date: int = 0

    def __post_init__(self) -> None:
        if not -0x8000 <= self.boxer_index <= 0x7FFF:
            raise LivingWorldError("boxer index must fit int16")
        _checked_u8(self.rank, field="rank")
        _checked_u8(self.wins, field="wins")
        _checked_u8(self.losses, field="losses")
        _checked_u8(self.draws, field="draws")
        _checked_u8(self.kos, field="kos")
        _checked_u8(self.title_wins, field="title_wins")
        _checked_u8(self.title_losses, field="title_losses")
        _checked_u8(self.title_defenses, field="title_defenses")
        _checked_u8(self.title_forfeitures, field="title_forfeitures")
        _checked_u8(self.cooldown_weeks, field="cooldown_weeks")
        if not 0 <= self.ranking_score <= MAX_U16:
            raise LivingWorldError("ranking_score must fit uint16")
        if not 0 <= self.scheduled_date <= 0xFFFFFFFF:
            raise LivingWorldError("scheduled_date must fit uint32")
        if self.match_descriptor is None and self.scheduled_date != 0:
            raise LivingWorldError(
                "scheduled_date cannot be nonzero without a match descriptor"
            )
        if self.match_descriptor is not None and self.scheduled_date == 0:
            raise LivingWorldError(
                "scheduled match descriptor requires a nonzero scheduled_date"
            )

    @property
    def has_scheduled_match(self) -> bool:
        return self.match_descriptor is not None

    def schedule(
        self,
        descriptor: CareerMatchDescriptor,
        *,
        scheduled_date: int,
    ) -> ProgressionRecordState:
        if self.has_scheduled_match:
            raise LivingWorldError("progression record already has a scheduled match")
        if scheduled_date == 0:
            raise LivingWorldError("scheduled match date must be nonzero")
        return replace(
            self,
            match_descriptor=descriptor,
            scheduled_date=scheduled_date,
        )

    def clear_schedule(self) -> ProgressionRecordState:
        return replace(self, match_descriptor=None, scheduled_date=0)

    def apply_result(
        self,
        descriptor: CareerMatchDescriptor,
    ) -> ProgressionRecordState:
        """Apply the proven record-counter result classes, then clear schedule."""

        if descriptor.result_code == 0:
            raise LivingWorldError("cannot apply an unresolved result code")

        updates: dict[str, int | CareerMatchDescriptor | None] = {
            "match_descriptor": None,
            "scheduled_date": 0,
        }
        if descriptor.is_draw:
            updates["draws"] = _increment_u8(self.draws, field="draws")
        elif descriptor.is_win_class:
            updates["wins"] = _increment_u8(self.wins, field="wins")
            if descriptor.counts_as_ko_win:
                updates["kos"] = _increment_u8(self.kos, field="kos")
        elif descriptor.is_loss_class:
            updates["losses"] = _increment_u8(self.losses, field="losses")
        else:
            raise LivingWorldError(
                "result semantics are only proven for codes 1..11"
            )
        return replace(self, **updates)

    def with_rank(self, rank: int) -> ProgressionRecordState:
        _checked_u8(rank, field="rank")
        return replace(self, rank=rank)

    def with_ranking_score(self, score: int) -> ProgressionRecordState:
        if not 0 <= score <= MAX_U16:
            raise LivingWorldError("ranking score must fit uint16")
        return replace(self, ranking_score=score)

    def record_title_win(self) -> ProgressionRecordState:
        return replace(
            self,
            title_wins=_increment_u8(self.title_wins, field="title_wins"),
        )

    def record_title_loss(self) -> ProgressionRecordState:
        return replace(
            self,
            title_losses=_increment_u8(self.title_losses, field="title_losses"),
        )

    def record_title_defense(self) -> ProgressionRecordState:
        return replace(
            self,
            title_defenses=_increment_u8(
                self.title_defenses,
                field="title_defenses",
            ),
        )

    def record_title_forfeiture(self) -> ProgressionRecordState:
        return replace(
            self,
            title_forfeitures=_increment_u8(
                self.title_forfeitures,
                field="title_forfeitures",
            ),
        )


@dataclass(frozen=True, slots=True)
class ResolvedCareerMatch:
    """Two fighter records after one reciprocal scheduled result is applied."""

    first: ProgressionRecordState
    second: ProgressionRecordState
    first_result: CareerMatchDescriptor
    second_result: CareerMatchDescriptor


@dataclass(frozen=True, slots=True)
class ChampionshipTransferResult:
    """State returned from the proven championship-holder transfer operation."""

    championships: ChampionshipSlots
    new_champion: ProgressionRecordState
    displaced_champion: ProgressionRecordState | None


def assign_match_pair(
    first: ProgressionRecordState,
    second: ProgressionRecordState,
    *,
    subtype: int,
    scheduled_date: int,
) -> tuple[ProgressionRecordState, ProgressionRecordState]:
    """Create the reciprocal +0x24/+0x28 schedule state used by retail."""

    if first.boxer_index == second.boxer_index:
        raise LivingWorldError("a boxer cannot be scheduled against itself")
    first_descriptor = CareerMatchDescriptor(
        opponent_index=second.boxer_index,
        subtype=subtype,
    )
    second_descriptor = first_descriptor.reciprocal(
        opponent_index=first.boxer_index
    )
    return (
        first.schedule(first_descriptor, scheduled_date=scheduled_date),
        second.schedule(second_descriptor, scheduled_date=scheduled_date),
    )


def assign_retail_ai_match(
    first: ProgressionRecordState,
    second: ProgressionRecordState,
    *,
    scheduled_date: int,
) -> tuple[ProgressionRecordState, ProgressionRecordState]:
    """Schedule the exact subtype used by the recovered retail AI matcher."""

    return assign_match_pair(
        first,
        second,
        subtype=NORMAL_AI_MATCH_SUBTYPE,
        scheduled_date=scheduled_date,
    )


def assign_title_match(
    challenger: ProgressionRecordState,
    champion: ProgressionRecordState,
    *,
    subtype: int,
    scheduled_date: int,
) -> tuple[ProgressionRecordState, ProgressionRecordState]:
    """Schedule title plumbing after a separate policy has selected the bout.

    Retail uses subtype 8 for title-challenge assignments and subtype 9 for
    title-defense assignments. This helper validates those proven encodings;
    it does not decide whether the fighters are eligible.
    """

    if subtype not in {TITLE_CHALLENGE_SUBTYPE, TITLE_DEFENSE_SUBTYPE}:
        raise LivingWorldError("title match subtype must be 8 or 9")
    return assign_match_pair(
        challenger,
        champion,
        subtype=subtype,
        scheduled_date=scheduled_date,
    )


def resolve_scheduled_match(
    first: ProgressionRecordState,
    second: ProgressionRecordState,
    *,
    result_code_for_first: int,
    secondary_code: int = 0,
) -> ResolvedCareerMatch:
    """Apply one externally selected result to a reciprocal scheduled pair.

    Result selection itself is intentionally external: static evidence proves
    that retail uses rank/performance state and RNG, but the exact outcome
    formula has not been normalized into a safe Career 2.0 policy.
    """

    first_scheduled = first.match_descriptor
    second_scheduled = second.match_descriptor
    if first_scheduled is None or second_scheduled is None:
        raise LivingWorldError("both fighters must have a scheduled match")
    if first.scheduled_date != second.scheduled_date:
        raise LivingWorldError("scheduled fighters must share the same date")
    if first_scheduled.opponent_index != second.boxer_index:
        raise LivingWorldError("first fighter's opponent index is inconsistent")
    if second_scheduled.opponent_index != first.boxer_index:
        raise LivingWorldError("second fighter's opponent index is inconsistent")
    if first_scheduled.subtype != second_scheduled.subtype:
        raise LivingWorldError("scheduled fighters must share the same subtype")

    first_result = CareerMatchDescriptor(
        opponent_index=second.boxer_index,
        subtype=first_scheduled.subtype,
        result_code=result_code_for_first,
        secondary_code=secondary_code,
    )
    second_result = first_result.reciprocal(opponent_index=first.boxer_index)
    return ResolvedCareerMatch(
        first=first.apply_result(first_result),
        second=second.apply_result(second_result),
        first_result=first_result,
        second_result=second_result,
    )


def transfer_championship(
    championships: ChampionshipSlots,
    *,
    slot: int,
    new_champion: ProgressionRecordState,
    displaced_champion: ProgressionRecordState | None,
) -> ChampionshipTransferResult:
    """Apply the holder-bank and +0x15/+0x16 accounting proven in retail."""

    current_holder = championships.holder_for_slot(slot)
    if current_holder >= 0:
        if displaced_champion is None:
            raise LivingWorldError(
                "existing championship holder requires a displaced record"
            )
        if displaced_champion.boxer_index != current_holder:
            raise LivingWorldError(
                "displaced champion does not match the current title holder"
            )
    elif displaced_champion is not None:
        raise LivingWorldError(
            "vacant title cannot have a displaced champion record"
        )

    updated_slots, displaced_index = championships.transfer(
        slot=slot,
        new_holder=new_champion.boxer_index,
    )
    if displaced_index != current_holder:
        raise LivingWorldError("championship transfer returned inconsistent holder")

    updated_new = new_champion.record_title_win()
    updated_displaced = (
        displaced_champion.record_title_loss()
        if displaced_champion is not None
        else None
    )
    return ChampionshipTransferResult(
        championships=updated_slots,
        new_champion=updated_new,
        displaced_champion=updated_displaced,
    )
