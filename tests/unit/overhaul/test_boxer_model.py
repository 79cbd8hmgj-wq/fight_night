from __future__ import annotations

from pathlib import Path

import pytest

from fnr3_re.overhaul.boxer_model import (
    RATING_FIELDS,
    BoxerModelError,
    BoxerRatingOverrideTable,
    BoxerRatings,
)


def _ratings(**overrides: int) -> BoxerRatings:
    base = dict.fromkeys(RATING_FIELDS, 50)
    base.update(overrides)
    return BoxerRatings(**base)


def test_rating_fields_match_proven_order() -> None:
    assert RATING_FIELDS == (
        "power",
        "speed",
        "agility",
        "stamina",
        "chin",
        "body",
        "heart",
        "cuts",
        "overall",
    )


def test_as_dict_round_trips_all_fields() -> None:
    ratings = _ratings(power=80, stamina=60)
    d = ratings.as_dict()
    assert d["power"] == 80
    assert d["stamina"] == 60
    assert set(d) == set(RATING_FIELDS)


def test_with_overall_derived_only_changes_overall() -> None:
    ratings = _ratings(power=80, speed=60, overall=0)
    derived = ratings.with_overall_derived(lambda r: (r.power + r.speed) // 2)
    assert derived.overall == 70
    assert derived.power == 80  # unchanged


def test_validated_accepts_in_range_values() -> None:
    fields = dict.fromkeys(RATING_FIELDS, 50)
    ratings = BoxerRatings.validated(minimum=0, maximum=100, **fields)
    assert ratings.power == 50


def test_validated_rejects_out_of_range() -> None:
    fields = dict.fromkeys(RATING_FIELDS, 50)
    fields["chin"] = 150
    with pytest.raises(BoxerModelError, match="outside the caller-supplied range"):
        BoxerRatings.validated(minimum=0, maximum=100, **fields)


def test_validated_rejects_missing_field() -> None:
    fields = dict.fromkeys(RATING_FIELDS, 50)
    del fields["cuts"]
    with pytest.raises(BoxerModelError, match="missing rating fields"):
        BoxerRatings.validated(minimum=0, maximum=100, **fields)


def test_override_table_round_trips_through_json(tmp_path: Path) -> None:
    table = BoxerRatingOverrideTable.empty().with_override(7, _ratings(power=90))
    path = tmp_path / "overrides.json"
    table.save(path)

    loaded = BoxerRatingOverrideTable.load(path)

    assert loaded.overrides[7].power == 90
    assert loaded.schema_version == 1


def test_override_table_rejects_negative_boxer_id() -> None:
    table = BoxerRatingOverrideTable.empty()
    with pytest.raises(BoxerModelError, match="non-negative"):
        table.with_override(-1, _ratings())


def test_override_table_load_rejects_missing_fields(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text('{"schema_version": 1, "overrides": {"1": {"power": 5}}}', encoding="utf-8")
    with pytest.raises(BoxerModelError, match="missing rating fields"):
        BoxerRatingOverrideTable.load(path)
