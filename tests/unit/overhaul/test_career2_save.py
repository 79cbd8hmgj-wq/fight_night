from __future__ import annotations

import pytest

from fnr3_re.overhaul.boxer_model import BoxerRatings
from fnr3_re.overhaul.career2_amateur import (
    C2EX_OFFSET,
    TRAINABLE_RATINGS,
    AmateurDevelopmentState,
    PhysicalGrowthPlan,
    RatingDevelopmentPlan,
)
from fnr3_re.overhaul.career2_c2ex import (
    C2EX_VERSION,
    C2EX_VERSION_V1,
    C2EXAmateurDevelopment,
    encode_c2ex_v1,
)
from fnr3_re.overhaul.career2_history import CareerHistoryResult
from fnr3_re.overhaul.career2_legacy import (
    LegacyFightEntry,
    LegacyFightLedger,
    LegacyTitleStake,
)
from fnr3_re.overhaul.career2_living_divisions import WeightClass
from fnr3_re.overhaul.career2_retirement import CareerRecordSummary
from fnr3_re.overhaul.career2_save import (
    Career2SaveError,
    Career2SaveSource,
    extension_from_state,
    load_career2_active_body,
    migrate_legacy_active_body,
    write_career2_active_body,
    write_state_and_ledger_to_active_body,
    write_state_to_active_body,
)


def _ratings() -> BoxerRatings:
    return BoxerRatings(
        power=50,
        speed=51,
        agility=52,
        stamina=53,
        chin=54,
        body=55,
        heart=56,
        cuts=57,
        overall=58,
    )


def _plan(*, ceiling_base: int = 75) -> RatingDevelopmentPlan:
    return RatingDevelopmentPlan(
        ceilings={
            field: ceiling_base + index
            for index, field in enumerate(TRAINABLE_RATINGS)
        },
        learning_rate_bps={
            field: 1_000 + index * 100
            for index, field in enumerate(TRAINABLE_RATINGS)
        },
    )


def _ledger() -> LegacyFightLedger:
    return LegacyFightLedger(
        entries=(
            LegacyFightEntry(
                opponent_id=41,
                career_week=12,
                opponent_rank_at_fight=2,
                division=WeightClass.MIDDLEWEIGHT,
                title_stakes=LegacyTitleStake.TITLE_FIGHT,
                opponent_overall_at_fight=85,
                opponent_record_at_fight=CareerRecordSummary(
                    wins=18,
                    losses=2,
                    draws=1,
                    knockouts=12,
                ),
                result=CareerHistoryResult.WIN_DECISION,
                rounds_lasted=10,
                finish_seconds=0,
            ),
        )
    )


def _extension(
    *,
    ceiling_base: int = 75,
    ledger: LegacyFightLedger | None = None,
) -> C2EXAmateurDevelopment:
    return C2EXAmateurDevelopment(
        rating_plan=_plan(ceiling_base=ceiling_base),
        physical_plan=PhysicalGrowthPlan(
            target_height_inches=73,
            target_weight_lbs=180,
        ),
        legacy_ledger=ledger or LegacyFightLedger(),
    )


def _state() -> AmateurDevelopmentState:
    return AmateurDevelopmentState.new_career(
        ratings=_ratings(),
        rating_plan=_plan(),
        height_inches=68,
        weight_lbs=155,
        physical_plan=PhysicalGrowthPlan(
            target_height_inches=73,
            target_weight_lbs=180,
        ),
    )


def test_legacy_stock_body_is_reported_as_needing_migration() -> None:
    stock = b"\x11" * C2EX_OFFSET

    loaded = load_career2_active_body(stock)

    assert loaded.stock_active_body == stock
    assert loaded.source is Career2SaveSource.LEGACY_RETAIL
    assert loaded.extension is None
    assert loaded.needs_migration
    assert not loaded.needs_schema_upgrade


def test_zero_filled_retail_tail_is_also_legacy() -> None:
    stock = b"\x22" * C2EX_OFFSET

    loaded = load_career2_active_body(stock + bytes(256))

    assert loaded.stock_active_body == stock
    assert loaded.source is Career2SaveSource.LEGACY_RETAIL
    assert loaded.needs_migration


def test_require_extension_fails_closed_on_legacy_save() -> None:
    loaded = load_career2_active_body(b"\x33" * C2EX_OFFSET)

    with pytest.raises(Career2SaveError, match="explicit migration data"):
        loaded.require_extension()


def test_exact_v1_block_is_loaded_and_marked_for_schema_upgrade() -> None:
    stock = b"\x34" * C2EX_OFFSET
    active = stock + encode_c2ex_v1(_extension())

    loaded = load_career2_active_body(active)

    assert loaded.source is Career2SaveSource.C2EX_V1
    assert loaded.needs_schema_upgrade
    assert not loaded.needs_migration
    extension = loaded.require_extension()
    assert extension.schema_version == C2EX_VERSION_V1
    assert extension.legacy_ledger == LegacyFightLedger()


def test_explicit_legacy_migration_writes_latest_v2_and_preserves_stock() -> None:
    stock = bytes((index * 13) & 0xFF for index in range(C2EX_OFFSET))
    migrated = migrate_legacy_active_body(stock, _extension(ledger=_ledger()))

    loaded = load_career2_active_body(migrated)

    assert loaded.stock_active_body == stock
    assert loaded.source is Career2SaveSource.C2EX_V2
    assert not loaded.needs_migration
    assert not loaded.needs_schema_upgrade
    extension = loaded.require_extension()
    assert extension.schema_version == C2EX_VERSION
    assert extension.legacy_ledger == _ledger()


def test_migration_refuses_to_replace_existing_c2ex() -> None:
    stock = b"\x44" * C2EX_OFFSET
    migrated = migrate_legacy_active_body(stock, _extension())

    with pytest.raises(Career2SaveError, match="already contains C2EX"):
        migrate_legacy_active_body(migrated, _extension(ceiling_base=80))


def test_write_replaces_existing_extension_without_accumulating_blocks() -> None:
    stock = b"\x55" * C2EX_OFFSET
    ledger = _ledger()
    first = write_career2_active_body(
        stock,
        _extension(ceiling_base=75, ledger=ledger),
    )
    second = write_career2_active_body(
        first,
        _extension(ceiling_base=85, ledger=ledger),
    )

    first_loaded = load_career2_active_body(first)
    second_loaded = load_career2_active_body(second)

    assert second_loaded.stock_active_body == stock
    assert second_loaded.require_extension().rating_plan.ceilings["power"] == 85
    assert second_loaded.require_extension().legacy_ledger == ledger
    assert len(second) == len(first)
    assert first_loaded.require_extension().rating_plan.ceilings["power"] == 75


def test_extension_from_state_can_attach_explicit_ledger() -> None:
    state = _state()
    ledger = _ledger()

    extension = extension_from_state(state, legacy_ledger=ledger)

    assert extension.rating_plan == state.rating_plan
    assert extension.physical_plan == state.physical_plan
    assert extension.legacy_ledger == ledger
    assert extension.schema_version == C2EX_VERSION


def test_write_state_preserves_existing_ledger() -> None:
    stock = b"\x66" * C2EX_OFFSET
    ledger = _ledger()
    initial = write_state_and_ledger_to_active_body(stock, _state(), ledger)
    updated_state = _state().train(field="speed", effort=20).advance_year(
        height_step_inches=1,
        weight_step_lbs=5,
    )

    extended = write_state_to_active_body(initial, updated_state)
    loaded = load_career2_active_body(extended)

    extension = loaded.require_extension()
    assert extension.rating_plan == updated_state.rating_plan
    assert extension.physical_plan == updated_state.physical_plan
    assert extension.legacy_ledger == ledger
    assert loaded.stock_active_body == stock


def test_write_state_upgrades_v1_to_v2_without_changing_stock_prefix() -> None:
    stock = b"\x77" * C2EX_OFFSET
    v1_active = stock + encode_c2ex_v1(_extension())

    updated = write_state_to_active_body(v1_active, _state())
    loaded = load_career2_active_body(updated)

    assert loaded.stock_active_body == stock
    assert loaded.source is Career2SaveSource.C2EX_V2
    assert loaded.require_extension().schema_version == C2EX_VERSION
    assert loaded.require_extension().legacy_ledger == LegacyFightLedger()


def test_write_state_on_retail_save_starts_empty_ledger() -> None:
    stock = b"\x88" * C2EX_OFFSET

    extended = write_state_to_active_body(stock, _state())
    loaded = load_career2_active_body(extended)

    assert loaded.source is Career2SaveSource.C2EX_V2
    assert loaded.require_extension().legacy_ledger == LegacyFightLedger()
