from __future__ import annotations

import pytest

from fnr3_re.overhaul.career2_offers import (
    AUTOMATIC_OFFER_MAX_ELIGIBLE,
    AUTOMATIC_OFFER_SELECTOR_VADDR,
    CONTRACT_BANK_GATE_OFFSET,
    CONTRACT_BETTER_RANK_BOUND_OFFSET,
    CONTRACT_ELIGIBILITY_FLAGS_OFFSET,
    CONTRACT_ELIGIBILITY_VADDR,
    CONTRACT_FINE_PRINT_FLAGS_OFFSET,
    CONTRACT_LIST_PROVIDER_VADDR,
    CONTRACT_PERCENTAGE_THRESHOLD_RAW_OFFSET,
    CONTRACT_PREREQUISITE_RAW_OFFSET,
    CONTRACT_SELECTION_HANDLER_VADDR,
    CONTRACT_TEMPLATE_COUNT,
    CONTRACT_TEMPLATE_COUNT_GLOBAL_VADDR,
    CONTRACT_TEMPLATE_POINTER_GLOBAL_VADDR,
    CONTRACT_TEMPLATE_SIZE,
    CONTRACT_TYPE_OFFSET,
    CONTRACT_TYPE_RESOLVER_VADDR,
    CONTRACT_WEEKS_TO_FIGHT_OFFSET,
    CONTRACT_WORSE_RANK_BOUND_OFFSET,
    FIGHTS_FNC_LOADER_VADDR,
    CareerOfferContext,
    CareerOfferError,
    EligibilityBlocker,
    RetailFightContractTemplate,
    SpecialContractType,
    collect_automatic_eligible_offers,
    project_selected_offer_to_calendar,
)


def _context(
    *,
    phase: int = 2,
    rank: int = 12,
    bank: int = 10_000,
    wins: int = 10,
    losses: int = 2,
    draws: int = 1,
) -> CareerOfferContext:
    return CareerOfferContext(
        career_phase=phase,
        current_rank=rank,
        bank=bank,
        wins=wins,
        losses=losses,
        draws=draws,
    )


def _offer(
    *,
    contract_id: int = 5,
    contract_type: int = 5,
    bank_gate_value: int = 5_000,
    worse_rank_bound: int = 20,
    better_rank_bound: int = 5,
    weeks_to_fight: int = 4,
    prerequisite_raw: int = 0,
    eligibility_flags: int = 0,
    fine_print_flags: int = 0,
    percentage_threshold_raw: int = 0,
) -> RetailFightContractTemplate:
    return RetailFightContractTemplate(
        contract_id=contract_id,
        contract_type=contract_type,
        bank_gate_value=bank_gate_value,
        worse_rank_bound=worse_rank_bound,
        better_rank_bound=better_rank_bound,
        weeks_to_fight=weeks_to_fight,
        prerequisite_raw=prerequisite_raw,
        eligibility_flags=eligibility_flags,
        fine_print_flags=fine_print_flags,
        percentage_threshold_raw=percentage_threshold_raw,
    )


def test_exact_retail_offer_boundaries_are_locked() -> None:
    assert FIGHTS_FNC_LOADER_VADDR == 0x001A3D48
    assert CONTRACT_TEMPLATE_SIZE == 0x44
    assert CONTRACT_TEMPLATE_COUNT == 50
    assert CONTRACT_TEMPLATE_POINTER_GLOBAL_VADDR == 0x0055D530
    assert CONTRACT_TEMPLATE_COUNT_GLOBAL_VADDR == 0x0055D534
    assert CONTRACT_TYPE_RESOLVER_VADDR == 0x001A2C98
    assert CONTRACT_ELIGIBILITY_VADDR == 0x001A3FBC
    assert CONTRACT_LIST_PROVIDER_VADDR == 0x0020002C
    assert CONTRACT_SELECTION_HANDLER_VADDR == 0x001FF210
    assert AUTOMATIC_OFFER_SELECTOR_VADDR == 0x001A319C


def test_proven_template_offsets_remain_explicit() -> None:
    assert CONTRACT_BANK_GATE_OFFSET == 0x14
    assert CONTRACT_WORSE_RANK_BOUND_OFFSET == 0x18
    assert CONTRACT_BETTER_RANK_BOUND_OFFSET == 0x1C
    assert CONTRACT_WEEKS_TO_FIGHT_OFFSET == 0x20
    assert CONTRACT_PREREQUISITE_RAW_OFFSET == 0x24
    assert CONTRACT_ELIGIBILITY_FLAGS_OFFSET == 0x30
    assert CONTRACT_TYPE_OFFSET == 0x34
    assert CONTRACT_FINE_PRINT_FLAGS_OFFSET == 0x44
    assert CONTRACT_PERCENTAGE_THRESHOLD_RAW_OFFSET == 0x50


def test_special_contract_types_match_retail_go_pro_and_retire() -> None:
    assert int(SpecialContractType.GO_PRO) == 23
    assert int(SpecialContractType.RETIRE) == 27
    assert _offer(contract_type=23).is_go_pro
    assert _offer(contract_type=27).is_retire
    assert not _offer(contract_type=22).is_go_pro


def test_phase_side_bit_reproduces_proven_boolean_relationship() -> None:
    post_initial_offer = _offer(eligibility_flags=0)
    initial_offer = _offer(eligibility_flags=1)

    assert post_initial_offer.phase_side_bit == 0
    assert post_initial_offer.evaluate_proven_gates(
        _context(phase=2)
    ).passes_proven_gates
    assert EligibilityBlocker.PHASE_SIDE in post_initial_offer.evaluate_proven_gates(
        _context(phase=0)
    ).blockers

    assert initial_offer.phase_side_bit == 1
    assert initial_offer.evaluate_proven_gates(
        _context(phase=0)
    ).passes_proven_gates
    assert EligibilityBlocker.PHASE_SIDE in initial_offer.evaluate_proven_gates(
        _context(phase=2)
    ).blockers


def test_rank_bounds_use_zero_is_best_retail_ordering() -> None:
    offer = _offer(better_rank_bound=5, worse_rank_bound=20)

    assert offer.evaluate_proven_gates(_context(rank=5)).passes_proven_gates
    assert offer.evaluate_proven_gates(_context(rank=20)).passes_proven_gates
    assert offer.evaluate_proven_gates(_context(rank=12)).passes_proven_gates
    assert offer.evaluate_proven_gates(_context(rank=4)).blockers == (
        EligibilityBlocker.BETTER_RANK_BOUND,
    )
    assert offer.evaluate_proven_gates(_context(rank=21)).blockers == (
        EligibilityBlocker.WORSE_RANK_BOUND,
    )


def test_minus_one_disables_individual_rank_bound() -> None:
    offer = _offer(better_rank_bound=-1, worse_rank_bound=-1)

    assert offer.evaluate_proven_gates(_context(rank=0)).passes_proven_gates
    assert offer.evaluate_proven_gates(_context(rank=49)).passes_proven_gates


def test_bank_gate_uses_proven_current_bank_comparison() -> None:
    offer = _offer(bank_gate_value=5_000)

    assert offer.evaluate_proven_gates(_context(bank=5_000)).passes_proven_gates
    assert offer.evaluate_proven_gates(_context(bank=4_999)).blockers == (
        EligibilityBlocker.BANK,
    )


def test_multiple_proven_gate_failures_are_reported_without_hiding_each_other() -> None:
    offer = _offer(
        eligibility_flags=1,
        better_rank_bound=5,
        worse_rank_bound=20,
        bank_gate_value=9_000,
    )

    result = offer.evaluate_proven_gates(
        _context(phase=2, rank=30, bank=100)
    )

    assert result.blockers == (
        EligibilityBlocker.PHASE_SIDE,
        EligibilityBlocker.WORSE_RANK_BOUND,
        EligibilityBlocker.BANK,
    )


def test_record_context_exposes_but_does_not_apply_unresolved_percentage_gate() -> None:
    context = _context(wins=2, losses=1, draws=0)
    offer = _offer(percentage_threshold_raw=99)

    assert context.completed_fights == 3
    assert context.rounded_win_percentage == 67
    assert offer.evaluate_proven_gates(context).passes_proven_gates


def test_zero_fight_context_does_not_invent_percentage_fallback() -> None:
    context = _context(wins=0, losses=0, draws=0)

    assert context.completed_fights == 0
    assert context.rounded_win_percentage is None


def test_raw_unresolved_fields_are_preserved_without_semantic_aliases() -> None:
    offer = _offer(
        prerequisite_raw=0x12345678,
        eligibility_flags=0x10203040,
        fine_print_flags=0xAABBCCDD,
        percentage_threshold_raw=0x55667788,
    )

    assert offer.prerequisite_raw == 0x12345678
    assert offer.eligibility_flags == 0x10203040
    assert offer.fine_print_flags == 0xAABBCCDD
    assert offer.percentage_threshold_raw == 0x55667788


def test_automatic_offer_collection_preserves_order_deduplicates_and_caps_at_ten() -> None:
    candidates = tuple(
        _offer(
            contract_id=index,
            better_rank_bound=-1,
            worse_rank_bound=-1,
        )
        for index in range(15)
    )

    result = collect_automatic_eligible_offers(candidates, _context())

    assert result.contract_ids == tuple(range(AUTOMATIC_OFFER_MAX_ELIGIBLE))
    assert len(result.contract_ids) == 10


def test_automatic_offer_collection_skips_failed_proven_gates() -> None:
    candidates = (
        _offer(contract_id=1, bank_gate_value=20_000),
        _offer(contract_id=2, bank_gate_value=1_000),
        _offer(contract_id=2, bank_gate_value=1_000),
        _offer(contract_id=3, eligibility_flags=1),
        _offer(contract_id=4, bank_gate_value=1_000),
    )

    result = collect_automatic_eligible_offers(candidates, _context())

    assert result.contract_ids == (2, 4)


def test_calendar_projection_uses_proven_weeks_to_fight_value() -> None:
    selection = project_selected_offer_to_calendar(
        current_week=100,
        offer=_offer(contract_id=7, weeks_to_fight=6),
    )

    assert selection.current_week == 100
    assert selection.contract_id == 7
    assert selection.scheduled_week == 106


def test_calendar_projection_rejects_uint16_overflow() -> None:
    with pytest.raises(CareerOfferError, match="exceeds"):
        project_selected_offer_to_calendar(
            current_week=0xFFFF,
            offer=_offer(weeks_to_fight=1),
        )


def test_valid_template_boundary() -> None:
    offer = _offer(contract_id=49)

    assert offer.contract_id == 49


def test_invalid_template_and_context_boundaries_fail_closed() -> None:
    with pytest.raises(CareerOfferError, match="contract_id"):
        _offer(contract_id=50)
    with pytest.raises(CareerOfferError, match="contract_type"):
        _offer(contract_type=28)
    with pytest.raises(CareerOfferError, match="worse_rank_bound"):
        _offer(worse_rank_bound=50)
    with pytest.raises(CareerOfferError, match="better_rank_bound cannot"):
        _offer(better_rank_bound=20, worse_rank_bound=5)
    with pytest.raises(CareerOfferError, match="weeks_to_fight"):
        _offer(weeks_to_fight=-1)
    with pytest.raises(CareerOfferError, match="current_rank"):
        _context(rank=256)
    with pytest.raises(CareerOfferError, match="wins"):
        _context(wins=256)
