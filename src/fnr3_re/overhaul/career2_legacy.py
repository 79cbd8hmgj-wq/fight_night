"""Career Mode 2.0 persistent legacy-fight ledger.

The exact retail Career History record is only a 25-byte display record and
retains at most 20 amateur plus 20 professional bouts. It does not contain a
stable opponent identity, opponent rank-at-fight, division, career date, title
stakes, or opponent-quality snapshot.

This module defines the mod-owned ledger needed for those historical facts.
It does not assign a final legacy score. The ledger preserves raw inputs so
scoring policy can be changed without destroying the underlying career record.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntFlag
import struct
from types import MappingProxyType

from fnr3_re.overhaul.career2_history import CareerHistoryResult
from fnr3_re.overhaul.career2_living_divisions import (
    MAX_LADDER_ENTRIES,
    WeightClass,
)
from fnr3_re.overhaul.career2_retirement import CareerRecordSummary

LEGACY_FIGHT_ENTRY_SIZE = 16
LEGACY_UNRANKED_SENTINEL = 0xFF

# u16 stable C2EX opponent id
# u16 Career 2.0 week ordinal
# u8 opponent zero-based rank (0xFF = unranked)
# u8 absolute retail WeightClass
# u8 title-stakes flags
# u8 opponent overall snapshot
# u8 opponent W/L/D/KO snapshot (four fields)
# u8 result, rounds, finish seconds
# u8 reserved, currently zero
_LEGACY_FIGHT = struct.Struct("<HHBBBBBBBBBBBB")


class LegacyLedgerError(ValueError):
    """Raised when Career 2.0 legacy-ledger data violates its schema."""


class LegacyTitleStake(IntFlag):
    """Career 2.0-owned title context stored with a historical bout."""

    NONE = 0
    TITLE_FIGHT = 1 << 0
    PLAYER_DEFENDING = 1 << 1
    OPPONENT_DEFENDING = 1 << 2
    ELIMINATOR = 1 << 3


_KNOWN_TITLE_STAKE_MASK = int(
    LegacyTitleStake.TITLE_FIGHT
    | LegacyTitleStake.PLAYER_DEFENDING
    | LegacyTitleStake.OPPONENT_DEFENDING
    | LegacyTitleStake.ELIMINATOR
)


@dataclass(frozen=True, slots=True)
class LegacyFightEntry:
    """One immutable 16-byte Career 2.0 legacy-ledger record.

    opponent_id is a C2EX-owned stable identity, not a claim that a retail
    progression-record index is permanently stable across generated-boxer
    reuse. The integration layer is responsible for assigning that identity.

    career_week is a monotonically increasing Career 2.0 calendar ordinal.
    It deliberately does not reinterpret the retail date representation.
    """

    opponent_id: int
    career_week: int
    opponent_rank_at_fight: int | None
    division: WeightClass
    title_stakes: LegacyTitleStake
    opponent_overall_at_fight: int
    opponent_record_at_fight: CareerRecordSummary
    result: CareerHistoryResult
    rounds_lasted: int
    finish_seconds: int

    def __post_init__(self) -> None:
        if not 0 <= self.opponent_id <= 0xFFFF:
            raise LegacyLedgerError("opponent_id must fit uint16")
        if not 0 <= self.career_week <= 0xFFFF:
            raise LegacyLedgerError("career_week must fit uint16")
        if self.opponent_rank_at_fight is not None and not (
            0 <= self.opponent_rank_at_fight < MAX_LADDER_ENTRIES
        ):
            raise LegacyLedgerError(
                f"opponent rank must be 0..{MAX_LADDER_ENTRIES - 1} or None"
            )
        if int(self.title_stakes) & ~_KNOWN_TITLE_STAKE_MASK:
            raise LegacyLedgerError("title_stakes contains unknown flag bits")
        if not 0 <= self.opponent_overall_at_fight <= 0xFF:
            raise LegacyLedgerError("opponent overall must fit uint8")
        if not 0 <= self.rounds_lasted <= 0xFF:
            raise LegacyLedgerError("rounds_lasted must fit uint8")
        if not 0 <= self.finish_seconds <= 0xFF:
            raise LegacyLedgerError("finish_seconds must fit uint8")

    @property
    def is_win(self) -> bool:
        return self.result in {
            CareerHistoryResult.WIN_KO,
            CareerHistoryResult.WIN_DECISION,
        }

    @property
    def is_loss(self) -> bool:
        return self.result in {
            CareerHistoryResult.LOSS_KO,
            CareerHistoryResult.LOSS_DECISION,
        }

    @property
    def is_draw(self) -> bool:
        return self.result is CareerHistoryResult.DRAW

    @property
    def is_ko_win(self) -> bool:
        return self.result is CareerHistoryResult.WIN_KO

    @property
    def is_title_fight(self) -> bool:
        return bool(self.title_stakes & LegacyTitleStake.TITLE_FIGHT)

    @property
    def is_player_title_defense(self) -> bool:
        return bool(self.title_stakes & LegacyTitleStake.PLAYER_DEFENDING)

    def to_bytes(self) -> bytes:
        rank = (
            LEGACY_UNRANKED_SENTINEL
            if self.opponent_rank_at_fight is None
            else self.opponent_rank_at_fight
        )
        record = self.opponent_record_at_fight
        return _LEGACY_FIGHT.pack(
            self.opponent_id,
            self.career_week,
            rank,
            int(self.division),
            int(self.title_stakes),
            self.opponent_overall_at_fight,
            record.wins,
            record.losses,
            record.draws,
            record.knockouts,
            int(self.result),
            self.rounds_lasted,
            self.finish_seconds,
            0,
        )

    @classmethod
    def from_bytes(cls, raw: bytes) -> LegacyFightEntry:
        if len(raw) != LEGACY_FIGHT_ENTRY_SIZE:
            raise LegacyLedgerError(
                f"legacy fight entry must be exactly {LEGACY_FIGHT_ENTRY_SIZE} bytes"
            )
        (
            opponent_id,
            career_week,
            rank,
            division,
            stakes,
            overall,
            wins,
            losses,
            draws,
            knockouts,
            result,
            rounds,
            finish_seconds,
            reserved,
        ) = _LEGACY_FIGHT.unpack(raw)
        if reserved != 0:
            raise LegacyLedgerError("legacy fight reserved byte must be zero")
        try:
            weight_class = WeightClass(division)
        except ValueError as exc:
            raise LegacyLedgerError(
                f"invalid legacy fight weight class {division}"
            ) from exc
        try:
            result_code = CareerHistoryResult(result)
        except ValueError as exc:
            raise LegacyLedgerError(
                f"invalid legacy fight result code {result}"
            ) from exc
        return cls(
            opponent_id=opponent_id,
            career_week=career_week,
            opponent_rank_at_fight=(
                None if rank == LEGACY_UNRANKED_SENTINEL else rank
            ),
            division=weight_class,
            title_stakes=LegacyTitleStake(stakes),
            opponent_overall_at_fight=overall,
            opponent_record_at_fight=CareerRecordSummary(
                wins=wins,
                losses=losses,
                draws=draws,
                knockouts=knockouts,
            ),
            result=result_code,
            rounds_lasted=rounds,
            finish_seconds=finish_seconds,
        )


@dataclass(frozen=True, slots=True)
class LegacyFightLedger:
    """Append-only full-career ledger used as legacy-scoring evidence."""

    entries: tuple[LegacyFightEntry, ...] = ()

    def __post_init__(self) -> None:
        previous_week = -1
        for entry in self.entries:
            if entry.career_week < previous_week:
                raise LegacyLedgerError(
                    "legacy fight ledger must be ordered by nondecreasing career_week"
                )
            previous_week = entry.career_week

    def append(self, entry: LegacyFightEntry) -> LegacyFightLedger:
        if self.entries and entry.career_week < self.entries[-1].career_week:
            raise LegacyLedgerError("cannot append a fight before the current ledger end")
        return LegacyFightLedger(entries=(*self.entries, entry))

    @property
    def packed_size(self) -> int:
        return len(self.entries) * LEGACY_FIGHT_ENTRY_SIZE

    def proven_metrics(self) -> Mapping[str, int]:
        """Aggregate historical inputs without assigning legacy-score weights."""

        wins = sum(entry.is_win for entry in self.entries)
        losses = sum(entry.is_loss for entry in self.entries)
        draws = sum(entry.is_draw for entry in self.entries)
        ko_wins = sum(entry.is_ko_win for entry in self.entries)
        title_fights = sum(entry.is_title_fight for entry in self.entries)
        title_defense_wins = sum(
            entry.is_win and entry.is_player_title_defense for entry in self.entries
        )
        eliminators = sum(
            bool(entry.title_stakes & LegacyTitleStake.ELIMINATOR)
            for entry in self.entries
        )
        ranked = [
            entry for entry in self.entries if entry.opponent_rank_at_fight is not None
        ]
        ranked_wins = [entry for entry in ranked if entry.is_win]
        divisions = {entry.division for entry in self.entries}

        metrics: dict[str, int] = {
            "ledger_bouts": len(self.entries),
            "ledger_wins": wins,
            "ledger_losses": losses,
            "ledger_draws": draws,
            "ledger_ko_wins": ko_wins,
            "title_fights": title_fights,
            "title_defense_wins": title_defense_wins,
            "eliminators": eliminators,
            "ranked_opponents": len(ranked),
            "wins_over_ranked_opponents": len(ranked_wins),
            "distinct_divisions": len(divisions),
        }
        if ranked_wins:
            metrics["best_zero_based_rank_beaten"] = min(
                entry.opponent_rank_at_fight
                for entry in ranked_wins
                if entry.opponent_rank_at_fight is not None
            )
        if self.entries:
            metrics["career_ledger_span_weeks"] = (
                self.entries[-1].career_week - self.entries[0].career_week
            )
        return MappingProxyType(metrics)
