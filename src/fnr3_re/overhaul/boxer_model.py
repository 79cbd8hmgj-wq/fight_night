"""Overhaul rule-engine module: boxer rating model and override boundary.

Static RE now proves more than the original Alpha 1 implementation did:

- `xdbboxr.adf` contains 121 fields and 37 records.
- its descriptor matrix starts at payload `+0x38`, with record stride `0xF2`.
- the real `UpdateSelectBoxerInfo` handler is `0x001D53F0`.
- rating fields `0x10..0x18` are direct signed-int16 record fields:
  Power components A/B, Speed, Agility, Stamina, Chin, Heart, Cuts, Body.
- `iPower` is the average of fields `0x10/0x11`.
- `iOverall` is computed through `func_001D50F4`; it is not asserted to be
  one independently stored raw XDB field.

The exact raw offset for a type-0 rating field is
`0x38 + record_index*0xF2 + field_id*2`; see `fnr3_re.xdb` and
`analysis/resources/xdbboxr-schema.json`.

This module still keeps an ID-keyed JSON override table as a reversible mod
boundary. That is a design choice, not a claim that the original rating bytes
are unknown. A future patch layer may now safely target the recovered XDB
rating fields once boxer-ID/record-ID policy and rebuild constraints are
finalized.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

#: Proven field order (selectboxer.big!selectBoxer.const, entries 145-154;
#: see docs/overhaul/alpha1/README.md for the exact string-table citation).
RATING_FIELDS: tuple[str, ...] = (
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


class BoxerModelError(ValueError):
    """Raised for invalid boxer rating data."""


@dataclass(frozen=True, slots=True)
class BoxerRatings:
    """The 9 proven boxer rating fields, order-matched to retail evidence.

    No specific numeric range is asserted here (e.g. "0-100") because no
    static evidence this pass proved the original's legal range for any
    field -- asserting one would be exactly the kind of "assume semantic
    meaning from strings alone" this project's discipline forbids. Callers
    that need a bounded scale must supply their own validation (see
    :func:`BoxerRatings.validated`).
    """

    power: int
    speed: int
    agility: int
    stamina: int
    chin: int
    body: int
    heart: int
    cuts: int
    overall: int

    def as_dict(self) -> dict[str, int]:
        return asdict(self)

    def with_overall_derived(
        self, derive: Callable[[BoxerRatings], int]
    ) -> BoxerRatings:
        """Return a copy with ``overall`` recomputed by ``derive``.

        The original now has a recovered computed-Overall helper boundary
        (``func_001D50F4``), but its full formula is not reconstructed here.
        Callers may supply a derivation explicitly rather than having this
        module guess that formula.
        """

        return replace(self, overall=derive(self))

    @classmethod
    def validated(
        cls,
        *,
        minimum: int,
        maximum: int,
        **fields: int,
    ) -> BoxerRatings:
        """Construct with an explicit, caller-supplied legal range.

        The range is a parameter, not a constant, precisely because this
        project has not proven what the original's range is -- callers
        must state their own assumption explicitly rather than inherit an
        unstated one from this module.
        """

        if minimum > maximum:
            raise BoxerModelError("minimum must not exceed maximum")
        missing = set(RATING_FIELDS) - fields.keys()
        if missing:
            raise BoxerModelError(f"missing rating fields: {sorted(missing)}")
        extra = fields.keys() - set(RATING_FIELDS)
        if extra:
            raise BoxerModelError(f"unknown rating fields: {sorted(extra)}")
        for name, value in fields.items():
            if not minimum <= value <= maximum:
                raise BoxerModelError(
                    f"{name}={value} is outside the caller-supplied range "
                    f"[{minimum}, {maximum}]"
                )
        return cls(**fields)


@dataclass(frozen=True, slots=True)
class BoxerRatingOverrideTable:
    """A boxer-ID-keyed table of :class:`BoxerRatings` overrides.

    This remains a reversible mod-owned override resource. The original
    XDB rating byte layout is now recovered, but the project still avoids
    silently equating every front-end boxer ID with an XDB record index until
    that identity mapping is explicitly bounded. ``boxer_id`` therefore
    remains an opaque, non-negative mod key here.
    """

    schema_version: int
    overrides: Mapping[int, BoxerRatings]

    @classmethod
    def empty(cls) -> BoxerRatingOverrideTable:
        return cls(schema_version=1, overrides={})

    def with_override(self, boxer_id: int, ratings: BoxerRatings) -> BoxerRatingOverrideTable:
        if boxer_id < 0:
            raise BoxerModelError("boxer_id must be non-negative")
        updated = dict(self.overrides)
        updated[boxer_id] = ratings
        return BoxerRatingOverrideTable(schema_version=self.schema_version, overrides=updated)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "purpose": (
                "Neutral replacement-boundary override table for boxer ratings. "
                "Kept separate from xdbboxr.adf as a reversible mod boundary; "
                "see fnr3_re.overhaul.boxer_model for the recovered original "
                "rating layout and remaining ID-mapping constraints."
            ),
            "overrides": {
                str(boxer_id): ratings.as_dict()
                for boxer_id, ratings in sorted(self.overrides.items())
            },
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> BoxerRatingOverrideTable:
        schema_version = payload.get("schema_version")
        if not isinstance(schema_version, int):
            raise BoxerModelError("schema_version must be an integer")
        raw_overrides = payload.get("overrides")
        if not isinstance(raw_overrides, Mapping):
            raise BoxerModelError("overrides must be an object")
        overrides: dict[int, BoxerRatings] = {}
        for key, value in raw_overrides.items():
            try:
                boxer_id = int(key)
            except (TypeError, ValueError) as exc:
                raise BoxerModelError(f"invalid boxer_id key: {key!r}") from exc
            if not isinstance(value, Mapping):
                raise BoxerModelError(f"ratings for boxer_id {boxer_id} must be an object")
            missing = set(RATING_FIELDS) - value.keys()
            if missing:
                raise BoxerModelError(
                    f"boxer_id {boxer_id} is missing rating fields: {sorted(missing)}"
                )
            overrides[boxer_id] = BoxerRatings(**{name: int(value[name]) for name in RATING_FIELDS})
        return cls(schema_version=schema_version, overrides=overrides)

    def save(self, path: Path) -> None:
        path.write_text(
            json.dumps(self.to_mapping(), indent=2, sort_keys=False, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> BoxerRatingOverrideTable:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BoxerModelError(f"invalid override table: {exc}") from exc
        if not isinstance(payload, Mapping):
            raise BoxerModelError("override table root must be an object")
        return cls.from_mapping(payload)
