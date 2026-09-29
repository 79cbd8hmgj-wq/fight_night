"""Career Mode 2.0 save/load orchestration around the C2EX tail codec."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from fnr3_re.overhaul.career2_amateur import AmateurDevelopmentState
from fnr3_re.overhaul.career2_c2ex import (
    C2EX_VERSION,
    C2EX_VERSION_V1,
    C2EXAmateurDevelopment,
    append_c2ex,
    split_c2ex,
)
from fnr3_re.overhaul.career2_legacy import LegacyFightLedger


class Career2SaveSource(StrEnum):
    """Origin/version of one loaded Career 2.0 active body."""

    LEGACY_RETAIL = "legacy_retail"
    C2EX_V1 = "c2ex_v1"
    C2EX_V2 = "c2ex_v2"


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

    @property
    def needs_schema_upgrade(self) -> bool:
        return self.source is Career2SaveSource.C2EX_V1

    def require_extension(self) -> C2EXAmateurDevelopment:
        if self.extension is None:
            raise Career2SaveError(
                "legacy retail save has no C2EX development state; "
                "explicit migration data is required"
            )
        return self.extension


def extension_from_state(
    state: AmateurDevelopmentState,
    *,
    legacy_ledger: LegacyFightLedger | None = None,
) -> C2EXAmateurDevelopment:
    """Project mod-owned state into the latest C2EX schema."""

    return C2EXAmateurDevelopment(
        rating_plan=state.rating_plan,
        physical_plan=state.physical_plan,
        legacy_ledger=legacy_ledger or LegacyFightLedger(),
        schema_version=C2EX_VERSION,
    )


def load_career2_active_body(active_body: bytes) -> Career2SaveLoad:
    """Load stock, C2EX v1, or C2EX v2 without inventing defaults."""

    stock, extension = split_c2ex(active_body)
    if extension is None:
        return Career2SaveLoad(
            stock_active_body=stock,
            source=Career2SaveSource.LEGACY_RETAIL,
            extension=None,
        )
    if extension.schema_version == C2EX_VERSION_V1:
        source = Career2SaveSource.C2EX_V1
    elif extension.schema_version == C2EX_VERSION:
        source = Career2SaveSource.C2EX_V2
    else:
        raise Career2SaveError(
            f"unsupported decoded C2EX schema {extension.schema_version}"
        )
    return Career2SaveLoad(
        stock_active_body=stock,
        source=source,
        extension=extension,
    )


def write_career2_active_body(
    active_body: bytes,
    extension: C2EXAmateurDevelopment,
) -> bytes:
    """Write latest-version C2EX while preserving the stock prefix."""

    stock, _ = split_c2ex(active_body)
    return append_c2ex(stock, extension)


def write_state_to_active_body(
    active_body: bytes,
    state: AmateurDevelopmentState,
) -> bytes:
    """Update development state while preserving any existing legacy ledger.

    A v1 block is automatically upgraded to v2 on write. A legacy retail save
    begins with an empty ledger.
    """

    loaded = load_career2_active_body(active_body)
    ledger = (
        LegacyFightLedger()
        if loaded.extension is None
        else loaded.extension.legacy_ledger
    )
    extension = extension_from_state(state, legacy_ledger=ledger)
    return append_c2ex(loaded.stock_active_body, extension)


def write_state_and_ledger_to_active_body(
    active_body: bytes,
    state: AmateurDevelopmentState,
    legacy_ledger: LegacyFightLedger,
) -> bytes:
    """Persist development state and an explicit full-career legacy ledger."""

    loaded = load_career2_active_body(active_body)
    extension = extension_from_state(state, legacy_ledger=legacy_ledger)
    return append_c2ex(loaded.stock_active_body, extension)


def migrate_legacy_active_body(
    active_body: bytes,
    extension: C2EXAmateurDevelopment,
) -> bytes:
    """Convert a retail save using explicit caller-supplied C2EX state."""

    loaded = load_career2_active_body(active_body)
    if not loaded.needs_migration:
        raise Career2SaveError("save already contains C2EX development state")
    return append_c2ex(loaded.stock_active_body, extension)
