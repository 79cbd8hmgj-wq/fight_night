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
from fnr3_re.overhaul.career2_c2ex import C2EXAmateurDevelopment
from fnr3_re.overhaul.career2_save import (
    Career2SaveError,
    Career2SaveSource,
    extension_from_state,
    load_career2_active_body,
    migrate_legacy_active_body,
    write_career2_active_body,
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


def _extension(*, ceiling_base: int = 75) -> C2EXAmateurDevelopment:
    return C2EXAmateurDevelopment(
        rating_plan=_plan(ceiling_base=ceiling_base),
        physical_plan=PhysicalGrowthPlan(
            target_height_inches=73,
            target_weight_lbs=180,
        ),
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


def test_explicit_legacy_migration_preserves_stock_prefix() -> None:
    stock = bytes((index * 13) & 0xFF for index in range(C2EX_OFFSET))
    migrated = migrate_legacy_active_body(stock, _extension())

    loaded = load_career2_active_body(migrated)

    assert loaded.stock_active_body == stock
    assert loaded.source is Career2SaveSource.C2EX_V1
    assert not loaded.needs_migration
    assert loaded.require_extension().rating_plan.ceilings["power"] == 75


def test_migration_refuses_to_replace_existing_c2ex() -> None:
    stock = b"\x44" * C2EX_OFFSET
    migrated = migrate_legacy_active_body(stock, _extension())

    with pytest.raises(Career2SaveError, match="already contains C2EX"):
        migrate_legacy_active_body(migrated, _extension(ceiling_base=80))


def test_write_replaces_existing_extension_without_accumulating_blocks() -> None:
    stock = b"\x55" * C2EX_OFFSET
    first = write_career2_active_body(stock, _extension(ceiling_base=75))
    second = write_career2_active_body(first, _extension(ceiling_base=85))

    first_loaded = load_career2_active_body(first)
    second_loaded = load_career2_active_body(second)

    assert second_loaded.stock_active_body == stock
    assert second_loaded.require_extension().rating_plan.ceilings["power"] == 85
    assert len(second) == len(first)
    assert first_loaded.require_extension().rating_plan.ceilings["power"] == 75


def test_extension_from_state_persists_only_mod_owned_plans() -> None:
    state = _state()

    extension = extension_from_state(state)

    assert extension.rating_plan == state.rating_plan
    assert extension.physical_plan == state.physical_plan


def test_write_state_round_trips_development_plan() -> None:
    stock = b"\x66" * C2EX_OFFSET
    state = _state().train(field="speed", effort=20).advance_year(
        height_step_inches=1,
        weight_step_lbs=5,
    )

    extended = write_state_to_active_body(stock, state)
    loaded = load_career2_active_body(extended)

    extension = loaded.require_extension()
    assert extension.rating_plan == state.rating_plan
    assert extension.physical_plan == state.physical_plan
    assert loaded.stock_active_body == stock
