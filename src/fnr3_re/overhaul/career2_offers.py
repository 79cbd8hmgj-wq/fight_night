"""Career Mode 2.0 fight-offer and career-flow primitives.

Retail FNR3 already has a dynamic offer generator, a contract-template table,
an eligibility evaluator, a selected-contract installation seam, and a
weeks-to-fight scheduling value. This module models only the parts whose
semantics/comparisons are statically proven.

Fields whose exact meaning is still unresolved remain explicitly raw. In
particular, Career Mode 2.0 does not assign new semantics to template +0x24,
most bits of +0x30, or +0x50.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, StrEnum

# Exact ULUS10066-v1.00 retail boundaries. These are evidence constants rather
# than portable patch sites.
FIGHTS_FNC_LOADER_VADDR = 0x001A3D48
CONTRACT_TEMPLATE_SIZE = 0x44
CONTRACT_TEMPLATE_COUNT = 50
CONTRACT_TEMPLATE_POINTER_GLOBAL_VADDR = 0x0055D530
CONTRACT_TEMPLATE_COUNT_GLOBAL_VADDR = 0x0055D534

CONTRACT_TYPE_RESOLVER_VADDR = 0x001A2C98
CONTRACT_SELECT_COPY_VADDR = 0x001A2FA0
CONTRACT_ELIGIBILITY_VADDR = 0x001A3FBC
CONTRACT_LIST_PROVIDER_VADDR = 0x0020002C
CONTRACT_SELECTION_HANDLER_VADDR = 0x001FF210
AUTOMATIC_OFFER_SELECTOR_VADDR = 0x001A319C
AUTOMATIC_OFFER_MAX_ELIGIBLE = 10

CONTRACT_BANK_GATE_OFFSET = 0x14
CONTRACT_WORSE_RANK_BOUND_OFFSET = 0x18
CONTRACT_BETTER_RANK_BOUND_OFFSET = 0x1C
CONTRACT_WEEKS_TO_FIGHT_OFFSET = 0x20
CONTRACT_PREREQUISITE_RAW_OFFSET = 0x24
CONTRACT_ELIGIBILITY_FLAGS_OFFSET = 0x30
CONTRACT_TYPE_OFFSET = 0x34
CONTRACT_FINE_PRINT_FLAGS_OFFSET = 0x44
CONTRACT_PERCENTAGE_THRESHOLD_RAW_OFFSET = 0x50

PROFILE_CAREER_PHASE_OFFSET = 0x121
PROFILE_BANK_OFFSET = 0xA0
PROGRESSION_RANK_OFFSET = 0x04
PROGRESSION_WINS_OFFSET = 0x05
PROGRESSION_LOSSES_OFFSET = 0x06
PROGRESSION_DRAWS_OFFSET = 0x07

RANK_BOUND_DISABLED = -1
MAX_RETAIL_RANK = 49


class CareerOfferError(ValueError):
    """Raised when a Career 2.0 offer model violates a proven boundary."""


class SpecialContractType(IntEnum):
    """Special retail career contract types whose semantics are proven."""

    GO_PRO = 23
    RETIRE = 27


class EligibilityBlocker(StrEnum):
    """Proven reasons this subset of retail eligibility can reject a template."""

    PHASE_SIDE = "phase_side"
    BETTER_RANK_BOUND = "better_rank_bound"
    WORSE_RANK_BOUND = "worse_rank_bound"
    BANK = "bank"


@dataclass(frozen=True, slots=True)
class CareerOfferContext:
    """Retail-backed career values consumed by the offer evaluator."""

    career_phase: int
    current_rank: int
    bank: int
    wins: int
    losses: int
    draws: int

    def __post_init__(self) -> None:
        if not 0 <= self.career_phase <= 0xFF:
            raise CareerOfferError("career_phase must fit retail uint8 storage")
        if not 0 <= self.current_rank <= 0xFF:
            raise CareerOfferError("current_rank must fit retail uint8 storage")
        if not -(1 << 31) <= self.bank <= (1 << 31) - 1:
            raise CareerOfferError("bank must fit signed retail int32 storage")
        for name, value in (
            ("wins", self.wins),
            ("losses", self.losses),
            ("draws", self.draws),
        ):
            if not 0 <= value <= 0xFF:
                raise CareerOfferError(f"{name} must fit retail uint8 storage")

    @property
    def noninitial_phase(self) -> bool:
        """Mirror the retail evaluator's bool(profile+0x121) conversion."""

        return self.career_phase != 0

    @property
    def completed_fights(self) -> int:
        return self.wins + self.losses + self.draws

    @property
    def rounded_win_percentage(self) -> int | None:
        """Expose the proven retail record-gate input without applying +0x50.

        Static evidence proves that the evaluator forms a rounded win
        percentage from W/L/D before the final +0x50 gate, but +0x50's exact
        semantic label/comparison policy is intentionally not asserted here.
        """

        total = self.completed_fights
        if total == 0:
            return None
        return (self.wins * 100 + total // 2) // total


@dataclass(frozen=True, slots=True)
class RetailFightContractTemplate:
    """Evidence-backed subset of one 0x44-byte fights.fnc template."""

    contract_id: int
    contract_type: int
    bank_gate_value: int
    worse_rank_bound: int
    better_rank_bound: int
    weeks_to_fight: int
    prerequisite_raw: int
    eligibility_flags: int
    fine_print_flags: int
    percentage_threshold_raw: int

    def __post_init__(self) -> None:
        if not 0 <= self.contract_id < CONTRACT_TEMPLATE_COUNT:
            raise CareerOfferError(
                f"contract_id must be 0..{CONTRACT_TEMPLATE_COUNT - 1}"
            )
        if not 1 <= self.contract_type <= 27:
            raise CareerOfferError("contract_type must be in retail range 1..27")
        for name, value in (
            ("worse_rank_bound", self.worse_rank_bound),
            ("better_rank_bound", self.better_rank_bound),
        ):
            if value != RANK_BOUND_DISABLED and not 0 <= value <= MAX_RETAIL_RANK:
                raise CareerOfferError(
                    f"{name} must be -1 or 0..{MAX_RETAIL_RANK}"
                )
        if (
            self.worse_rank_bound != RANK_BOUND_DISABLED
            and self.better_rank_bound != RANK_BOUND_DISABLED
            and self.better_rank_bound > self.worse_rank_bound
        ):
            raise CareerOfferError(
                "better_rank_bound cannot be numerically worse than "
                "worse_rank_bound"
            )
        if not 0 <= self.weeks_to_fight <= 0xFFFFFFFF:
            raise CareerOfferError("weeks_to_fight must fit uint32")
        if not -(1 << 31) <= self.bank_gate_value <= (1 << 31) - 1:
            raise CareerOfferError("bank_gate_value must fit signed int32")
        for name, value in (
            ("prerequisite_raw", self.prerequisite_raw),
            ("eligibility_flags", self.eligibility_flags),
            ("fine_print_flags", self.fine_print_flags),
            ("percentage_threshold_raw", self.percentage_threshold_raw),
        ):
            if not 0 <= value <= 0xFFFFFFFF:
                raise CareerOfferError(f"{name} must fit uint32")

    @property
    def phase_side_bit(self) -> int:
        """Return the only currently proven eligibility bit from +0x30."""

        return self.eligibility_flags & 1

    @property
    def is_go_pro(self) -> bool:
        return self.contract_type == int(SpecialContractType.GO_PRO)

    @property
    def is_retire(self) -> bool:
        return self.contract_type == int(SpecialContractType.RETIRE)

    def evaluate_proven_gates(
        self,
        context: CareerOfferContext,
    ) -> "OfferEligibility":
        """Evaluate only the retail gates whose comparison semantics are proven.

        Retail also performs type-specific prechecks and gates involving
        +0x24/+0x50/additional career state. Those are deliberately excluded
        until their meanings and comparison direction are fully recovered.
        """

        blockers: list[EligibilityBlocker] = []

        # Exact relationship from the recovered evaluator:
        # bool(profile+0x121) == NOT(record+0x30 bit 0).
        expected_noninitial = self.phase_side_bit == 0
        if context.noninitial_phase is not expected_noninitial:
            blockers.append(EligibilityBlocker.PHASE_SIDE)

        if (
            self.better_rank_bound != RANK_BOUND_DISABLED
            and context.current_rank < self.better_rank_bound
        ):
            blockers.append(EligibilityBlocker.BETTER_RANK_BOUND)

        if (
            self.worse_rank_bound != RANK_BOUND_DISABLED
            and context.current_rank > self.worse_rank_bound
        ):
            blockers.append(EligibilityBlocker.WORSE_RANK_BOUND)

        if context.bank < self.bank_gate_value:
            blockers.append(EligibilityBlocker.BANK)

        return OfferEligibility(blockers=tuple(blockers))


@dataclass(frozen=True, slots=True)
class OfferEligibility:
    """Result of the proven-gate subset of retail eligibility."""

    blockers: tuple[EligibilityBlocker, ...]

    @property
    def passes_proven_gates(self) -> bool:
        return not self.blockers


@dataclass(frozen=True, slots=True)
class EligibleOfferSet:
    """Ordered candidate IDs accepted by the proven gate subset."""

    contract_ids: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.contract_ids) > AUTOMATIC_OFFER_MAX_ELIGIBLE:
            raise CareerOfferError(
                "automatic eligible-offer set cannot exceed retail capacity 10"
            )
        if len(set(self.contract_ids)) != len(self.contract_ids):
            raise CareerOfferError("eligible-offer set contains duplicate IDs")
        for contract_id in self.contract_ids:
            if not 0 <= contract_id < CONTRACT_TEMPLATE_COUNT:
                raise CareerOfferError("eligible-offer contract ID is out of range")


def collect_automatic_eligible_offers(
    candidates: tuple[RetailFightContractTemplate, ...],
    context: CareerOfferContext,
) -> EligibleOfferSet:
    """Mirror the retail automatic selector's bounded collection behavior.

    This function stops after ten candidates pass the *proven* gates. It does
    not claim to reproduce unresolved type-specific/+0x24/+0x50 conditions and
    does not perform the retail RNG choice.
    """

    accepted: list[int] = []
    seen: set[int] = set()
    for candidate in candidates:
        if candidate.contract_id in seen:
            continue
        if not candidate.evaluate_proven_gates(context).passes_proven_gates:
            continue
        accepted.append(candidate.contract_id)
        seen.add(candidate.contract_id)
        if len(accepted) == AUTOMATIC_OFFER_MAX_ELIGIBLE:
            break
    return EligibleOfferSet(contract_ids=tuple(accepted))


@dataclass(frozen=True, slots=True)
class CareerCalendarSelection:
    """Career 2.0-owned week projection of a selected retail offer."""

    current_week: int
    contract_id: int
    scheduled_week: int

    def __post_init__(self) -> None:
        if not 0 <= self.current_week <= 0xFFFF:
            raise CareerOfferError("current_week must fit uint16")
        if not 0 <= self.scheduled_week <= 0xFFFF:
            raise CareerOfferError("scheduled_week must fit uint16")
        if self.scheduled_week < self.current_week:
            raise CareerOfferError("scheduled_week cannot precede current_week")
        if not 0 <= self.contract_id < CONTRACT_TEMPLATE_COUNT:
            raise CareerOfferError("contract_id is out of range")


def project_selected_offer_to_calendar(
    *,
    current_week: int,
    offer: RetailFightContractTemplate,
) -> CareerCalendarSelection:
    """Project the proven weeks-to-fight value into the mod-owned week ordinal.

    The retail scheduler adds contract weeks * 7 days to its persistent date.
    Career Mode 2.0 stores a monotonic week ordinal, so the equivalent host
    projection is current_week + weeks_to_fight.
    """

    scheduled_week = current_week + offer.weeks_to_fight
    if scheduled_week > 0xFFFF:
        raise CareerOfferError("scheduled offer exceeds uint16 career calendar")
    return CareerCalendarSelection(
        current_week=current_week,
        contract_id=offer.contract_id,
        scheduled_week=scheduled_week,
    )
