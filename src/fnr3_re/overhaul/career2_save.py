"""Career Mode 2.0 save/load orchestration around the C2EX tail codec.

The stock active body remains authoritative for every original retail field.
C2EX only persists Career 2.0-owned development state. This module provides
the host-side contract the eventual PSP serializer/deserializer hooks must
implement:

1. preserve the stock 0x5674-byte body byte-for-byte;
2. append/replace one validated C2EX block after that stock prefix;
3. treat a missing/zero tail as an explicit legacy-save migration case;
4. never invent migration defaults inside the codec or overwrite retail data.

The actual PSP instruction patch is intentionally outside this module. Retail
save/load hook bytes are not yet sufficiently transfer-matched for a guarded
binary patch.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from fnr3_re.overhaul.career2_amateur import AmateurDevelopmentState
from fnr3_re.overhaul.career2_c2ex import (
    C2EXAmateurDevelopment,
    append_c2ex,
    split_c2ex,
)


class Career2SaveSource(str, Enum):
    """Origin of the development data found in one active save body."""

    LEGACY_RETAIL = "legacy_retail"
    C2EX_V1 = "c2ex_v1"


class Career2SaveError(ValueError):
    """Raised when Career 2.0 save orchestration is used inconsistently."""


@dataclass(frozen=True, slots=True)
class Career2SaveLoad:
    """Result of splitting a retail-compatible active body."""

    stock_active_body: bytes
    source: Career2SaveSource
    extension: C2EXAmateurDevelopment | None

    @property
    def needs_migration(self) -> bool:
        return self.source is Career2SaveSource.LEGACY_RETAIL

    def require_extension(self) -> C2EXAmateurDevelopment:
        """Return C2EX data or fail if this is a legacy save.

        Migration policy is deliberately caller-owned. A legacy save cannot
        silently acquire made-up potential or learning-rate values.
        """

        if self.extension is None:
            raise Career2SaveError(
                "legacy retail save has no C2EX development state; "
                "explicit migration data is required"
            )
        return self.extension


def extension_from_state(state: AmateurDevelopmentState) -> C2EXAmateurDevelopment:
    """Project only Career 2.0-owned fields from the amateur state into C2EX."""

    return C2EXAmateurDevelopment(
        rating_plan=state.rating_plan,
        physical_plan=state.physical_plan,
    )


def load_career2_active_body(active_body: bytes) -> Career2SaveLoad:
    """Load one stock or Career 2.0 active body without inventing defaults."""

    stock, extension = split_c2ex(active_body)
    if extension is None:
        return Career2SaveLoad(
            stock_active_body=stock,
            source=Career2SaveSource.LEGACY_RETAIL,
            extension=None,
        )
    return Career2SaveLoad(
        stock_active_body=stock,
        source=Career2SaveSource.C2EX_V1,
        extension=extension,
    )


def write_career2_active_body(
    active_body: bytes,
    extension: C2EXAmateurDevelopment,
) -> bytes:
    """Write or replace C2EX while preserving the original stock prefix.

    active_body may be either a legacy stock body, a stock body with its
    retail zero-filled tail, or a body that already contains C2EX. Existing
    extension bytes are removed before the new block is appended, so repeated
    saves never accumulate multiple extension blocks.
    """

    stock, _ = split_c2ex(active_body)
    return append_c2ex(stock, extension)


def write_state_to_active_body(
    active_body: bytes,
    state: AmateurDevelopmentState,
) -> bytes:
    """Persist one amateur-development state's mod-owned data into C2EX."""

    return write_career2_active_body(active_body, extension_from_state(state))


def migrate_legacy_active_body(
    active_body: bytes,
    extension: C2EXAmateurDevelopment,
) -> bytes:
    """Convert a legacy save using explicit caller-supplied migration data.

    This function refuses to run on an already-extended save. That distinction
    keeps first-time migration separate from ordinary save updates and makes it
    impossible for migration code to silently replace existing Career 2.0
    development state.
    """

    loaded = load_career2_active_body(active_body)
    if not loaded.needs_migration:
        raise Career2SaveError("save already contains C2EX development state")
    return append_c2ex(loaded.stock_active_body, extension)
