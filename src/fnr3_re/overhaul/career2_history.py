"""Exact retail Career History record model for Career Mode 2.0.

ULUS10066-v1.00 stores two 20-entry history rings (Amateur and Professional).
Each record is exactly 25 bytes: 22 bytes of opponent display-name storage,
then result code, rounds lasted, and TKO/KO time in whole seconds.

The stock record is display history, not a durable legacy ledger. It contains
no proven stable opponent ID, rank-at-fight, division, date, or title stakes.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum
from types import MappingProxyType

RETAIL_HISTORY_ENTRY_SIZE = 25
RETAIL_HISTORY_NAME_SIZE = 22
RETAIL_HISTORY_RING_CAPACITY = 20

AMATEUR_HISTORY_COUNT_OFFSET = 0x2AA0
PRO_HISTORY_COUNT_OFFSET = 0x2AA1
AMATEUR_HISTORY_INDEX_OFFSET = 0x2AA2
PRO_HISTORY_INDEX_OFFSET = 0x2AA3
AMATEUR_HISTORY_BASE_OFFSET = 0x26B8
PRO_HISTORY_BASE_OFFSET = 0x28AC

HISTORY_WRITER_VADDR = 0x001939DC
HISTORY_READER_VADDR = 0x00193BB8
HISTORY_COMPLETED_FIGHT_CALLER_VADDR = 0x001B7894
HISTORY_UI_PROVIDER_VADDR = 0x001EE2D0
HISTORY_RESULT_TABLE_VADDR = 0x0055FF88
HISTORY_TKO_FORMATTER_VADDR = 0x00206E18


class CareerHistoryError(ValueError):
    """Raised when a retail Career History record violates its proven layout."""


class CareerHistoryClass(IntEnum):
    """Retail Career History ring selector."""

    AMATEUR = 0
    PROFESSIONAL = 1


class CareerHistoryResult(IntEnum):
    """Exact result codes emitted by the retail history writer."""

    WIN_KO = 0
    WIN_DECISION = 1
    LOSS_KO = 2
    LOSS_DECISION = 3
    DRAW = 4


RESULT_LOCALIZATION_KEYS: Mapping[CareerHistoryResult, str] = MappingProxyType(
    {
        CareerHistoryResult.WIN_KO: "$M_Win_KO",
        CareerHistoryResult.WIN_DECISION: "$M_Win_Decision",
        CareerHistoryResult.LOSS_KO: "$M_Loss_KO",
        CareerHistoryResult.LOSS_DECISION: "$M_Loss_Decision",
        CareerHistoryResult.DRAW: "$M_Draw",
    }
)


@dataclass(frozen=True, slots=True)
class RetailCareerHistoryEntry:
    """One exact 25-byte stock Career History entry.

    opponent_name_raw remains raw bytes deliberately. The exact retail text
    encoding is not asserted by static evidence, so byte preservation avoids
    corrupting names outside ASCII.
    """

    opponent_name_raw: bytes
    result: CareerHistoryResult
    rounds_lasted: int
    tko_time_seconds: int

    def __post_init__(self) -> None:
        if len(self.opponent_name_raw) != RETAIL_HISTORY_NAME_SIZE:
            raise CareerHistoryError("opponent_name_raw must be exactly 22 bytes")
        if not 0 <= self.rounds_lasted <= 0xFF:
            raise CareerHistoryError("rounds_lasted must fit uint8")
        if not 0 <= self.tko_time_seconds <= 0xFF:
            raise CareerHistoryError("tko_time_seconds must fit uint8")

    @classmethod
    def from_bytes(cls, raw: bytes) -> "RetailCareerHistoryEntry":
        if len(raw) != RETAIL_HISTORY_ENTRY_SIZE:
            raise CareerHistoryError(
                f"retail history entry must be exactly {RETAIL_HISTORY_ENTRY_SIZE} bytes"
            )
        try:
            result = CareerHistoryResult(raw[0x16])
        except ValueError as exc:
            raise CareerHistoryError(
                f"unsupported retail history result code {raw[0x16]}"
            ) from exc
        return cls(
            opponent_name_raw=raw[:RETAIL_HISTORY_NAME_SIZE],
            result=result,
            rounds_lasted=raw[0x17],
            tko_time_seconds=raw[0x18],
        )

    def to_bytes(self) -> bytes:
        return self.opponent_name_raw + bytes(
            (int(self.result), self.rounds_lasted, self.tko_time_seconds)
        )

    @property
    def opponent_name_bytes(self) -> bytes:
        """Return display-name bytes through the first NUL terminator."""

        return self.opponent_name_raw.split(b"\\0", 1)[0]

    @property
    def localization_key(self) -> str:
        return RESULT_LOCALIZATION_KEYS[self.result]

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
    def is_knockout_result(self) -> bool:
        return self.result in {
            CareerHistoryResult.WIN_KO,
            CareerHistoryResult.LOSS_KO,
        }

    @property
    def has_stoppage_time(self) -> bool:
        """Retail uses zero as the no-time/placeholder UI path."""

        return self.tko_time_seconds > 0

    @property
    def tko_minutes_seconds(self) -> tuple[int, int]:
        """Mirror formatter 0x00206E18 division by 60."""

        return divmod(self.tko_time_seconds, 60)


@dataclass(frozen=True, slots=True)
class RetailCareerHistoryRingLayout:
    """Profile offsets for one of the two proven stock history rings."""

    history_class: CareerHistoryClass
    count_offset: int
    ring_index_offset: int
    storage_base_offset: int
    capacity: int = RETAIL_HISTORY_RING_CAPACITY
    entry_size: int = RETAIL_HISTORY_ENTRY_SIZE


AMATEUR_HISTORY_LAYOUT = RetailCareerHistoryRingLayout(
    history_class=CareerHistoryClass.AMATEUR,
    count_offset=AMATEUR_HISTORY_COUNT_OFFSET,
    ring_index_offset=AMATEUR_HISTORY_INDEX_OFFSET,
    storage_base_offset=AMATEUR_HISTORY_BASE_OFFSET,
)

PRO_HISTORY_LAYOUT = RetailCareerHistoryRingLayout(
    history_class=CareerHistoryClass.PROFESSIONAL,
    count_offset=PRO_HISTORY_COUNT_OFFSET,
    ring_index_offset=PRO_HISTORY_INDEX_OFFSET,
    storage_base_offset=PRO_HISTORY_BASE_OFFSET,
)
