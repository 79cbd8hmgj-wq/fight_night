"""Overhaul rule-engine module: the boxer rating model and its replacement
boundary.

## What is proven vs. what is not

Static evidence (this session and the prior delta pass) proves:

- The retail boxer-selection screen (``selectboxer.big``) names exactly 9
  rating fields, in a fixed order, bounded by a ``NUM_STATS`` constant:
  ``iPower``, ``iSpeed``, ``iAgility``, ``iStamina``, ``iChin``, ``iBody``,
  ``iHeart``, ``iCuts``, ``iOverall``.
- All 9 names exist as ``BOOT.BIN`` strings, each appearing twice, both
  instances owned by the same function pair (``T_001D54A0``/
  ``T_001E83E0``) -- confirmed this pass to be generic UI native-function
  *registration* trampolines for this stat block (not the reader itself).
- ``xdbboxr.adf`` (``preload/db.viv``) is the boxer database: its proven
  8-word header's ``word0`` is consumed by real code (``func_001AD268``) as
  a per-entry count (121 in the tracked sample), and a packed 2-bit flags
  array was proven at payload offset ``+0x18``.

What is **not** proven, despite a focused attempt this pass (a raw
structural read of the decoded ``xdbboxr.adf`` payload past the flags
array): the exact byte offset, width, and encoding of each of the 9 rating
fields within one boxer's record. No consumer function was found this pass
that reads those payload bytes and correlates them with the 9 proven stat
names -- only plausible-looking small integers were visible, which is not
proof. Per this project's discipline, plausible-looking bytes are not
patched or exposed as if their meaning were known.

## The replacement boundary this module actually implements

Because the per-record layout is unresolved, this module does **not**
read or write ``xdbboxr.adf`` bytes directly, and does not claim to. It
implements a **neutral replacement boundary** instead: an ID-keyed override
table, stored as its own JSON resource (``config/overhaul/alpha1/
boxer_rating_overrides.json``), which an eventual PSP-side hook would
consult *in place of* (or layered on top of) the still-unresolved original
record -- without ever guessing at or overwriting the original bytes. This
satisfies "a proven replacement boundary" per the milestone's own
instructions, rather than "an unrelated replacement model": the field
*names*, *count*, and *order* are all directly evidence-derived, only the
storage location is a new (documented, reversible) resource rather than
the still-unmapped original one.

``iOverall``: whether the original computes this from the other 8 or
stores it independently was not established this pass (T_001D54A0/
T_001E83E0 are registration-only, not the reader). This model defaults to
treating ``overall`` as independently stored (the conservative choice --
it never silently discards a value the original might have stored), and
optionally accepts a caller-supplied derivation function so a future pass
that does prove the relationship can wire it in without changing this
model's shape.
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

        Use only once a future static-RE pass has actually proven the
        original's Power/Speed/.../Cuts -> Overall relationship; until
        then, ``overall`` should be treated as independently stored (the
        default everywhere else in this module).
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

    This is the neutral replacement boundary described in this module's
    docstring: a new resource this mod introduces, never a patch to the
    still-unresolved ``xdbboxr.adf`` per-record bytes. ``boxer_id`` is
    treated as an opaque, non-negative integer key -- this pass did not
    prove ``xdbboxr.adf``'s own boxer-ID scheme, so no assumption is made
    about how these IDs relate to it beyond "the mod's own consistent
    identifier for one boxer slot."
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
                "Not a patch to xdbboxr.adf -- see fnr3_re.overhaul.boxer_model's "
                "module docstring for why the original per-record layout is not "
                "yet safely patchable."
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
