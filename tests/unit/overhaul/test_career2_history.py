from __future__ import annotations

import pytest

from fnr3_re.overhaul.career2_history import (
    AMATEUR_HISTORY_LAYOUT,
    HISTORY_COMPLETED_FIGHT_CALLER_VADDR,
    HISTORY_READER_VADDR,
    HISTORY_RESULT_TABLE_VADDR,
    HISTORY_TKO_FORMATTER_VADDR,
    HISTORY_UI_PROVIDER_VADDR,
    HISTORY_WRITER_VADDR,
    PRO_HISTORY_LAYOUT,
    RESULT_LOCALIZATION_KEYS,
    RETAIL_HISTORY_ENTRY_SIZE,
    RETAIL_HISTORY_NAME_SIZE,
    RETAIL_HISTORY_RING_CAPACITY,
    CareerHistoryClass,
    CareerHistoryError,
    CareerHistoryResult,
    RetailCareerHistoryEntry,
)


def _name_buffer(name: bytes) -> bytes:
    assert len(name) < RETAIL_HISTORY_NAME_SIZE
    return name + bytes(RETAIL_HISTORY_NAME_SIZE - len(name))


@pytest.mark.parametrize(
    ("code", "key"),
    [
        (CareerHistoryResult.WIN_KO, "$M_Win_KO"),
        (CareerHistoryResult.WIN_DECISION, "$M_Win_Decision"),
        (CareerHistoryResult.LOSS_KO, "$M_Loss_KO"),
        (CareerHistoryResult.LOSS_DECISION, "$M_Loss_Decision"),
        (CareerHistoryResult.DRAW, "$M_Draw"),
    ],
)
def test_result_codes_match_exact_retail_label_table(
    code: CareerHistoryResult,
    key: str,
) -> None:
    assert RESULT_LOCALIZATION_KEYS[code] == key


def test_entry_round_trips_exact_25_byte_layout() -> None:
    raw = _name_buffer(b"Joe Frazier") + bytes((0, 3, 85))

    entry = RetailCareerHistoryEntry.from_bytes(raw)

    assert entry.opponent_name_bytes == b"Joe Frazier"
    assert entry.result is CareerHistoryResult.WIN_KO
    assert entry.localization_key == "$M_Win_KO"
    assert entry.rounds_lasted == 3
    assert entry.tko_time_seconds == 85
    assert entry.tko_minutes_seconds == (1, 25)
    assert entry.to_bytes() == raw


def test_zero_tko_time_uses_retail_placeholder_path() -> None:
    entry = RetailCareerHistoryEntry.from_bytes(
        _name_buffer(b"Opponent") + bytes((1, 10, 0))
    )

    assert not entry.has_stoppage_time
    assert entry.tko_minutes_seconds == (0, 0)


@pytest.mark.parametrize(
    ("result", "win", "loss", "draw", "knockout"),
    [
        (CareerHistoryResult.WIN_KO, True, False, False, True),
        (CareerHistoryResult.WIN_DECISION, True, False, False, False),
        (CareerHistoryResult.LOSS_KO, False, True, False, True),
        (CareerHistoryResult.LOSS_DECISION, False, True, False, False),
        (CareerHistoryResult.DRAW, False, False, True, False),
    ],
)
def test_result_classification(
    result: CareerHistoryResult,
    win: bool,
    loss: bool,
    draw: bool,
    knockout: bool,
) -> None:
    entry = RetailCareerHistoryEntry(
        opponent_name_raw=_name_buffer(b"Opponent"),
        result=result,
        rounds_lasted=5,
        tko_time_seconds=0,
    )

    assert entry.is_win is win
    assert entry.is_loss is loss
    assert entry.is_draw is draw
    assert entry.is_knockout_result is knockout


def test_invalid_entry_size_and_result_code_fail_closed() -> None:
    with pytest.raises(CareerHistoryError, match="exactly 25 bytes"):
        RetailCareerHistoryEntry.from_bytes(bytes(RETAIL_HISTORY_ENTRY_SIZE - 1))

    raw = _name_buffer(b"Opponent") + bytes((5, 1, 0))
    with pytest.raises(CareerHistoryError, match="result code 5"):
        RetailCareerHistoryEntry.from_bytes(raw)


def test_field_ranges_are_checked() -> None:
    with pytest.raises(CareerHistoryError, match="exactly 22 bytes"):
        RetailCareerHistoryEntry(
            opponent_name_raw=b"short",
            result=CareerHistoryResult.DRAW,
            rounds_lasted=1,
            tko_time_seconds=0,
        )

    with pytest.raises(CareerHistoryError, match="rounds_lasted"):
        RetailCareerHistoryEntry(
            opponent_name_raw=bytes(RETAIL_HISTORY_NAME_SIZE),
            result=CareerHistoryResult.DRAW,
            rounds_lasted=256,
            tko_time_seconds=0,
        )

    with pytest.raises(CareerHistoryError, match="tko_time_seconds"):
        RetailCareerHistoryEntry(
            opponent_name_raw=bytes(RETAIL_HISTORY_NAME_SIZE),
            result=CareerHistoryResult.DRAW,
            rounds_lasted=1,
            tko_time_seconds=-1,
        )


def test_ring_layouts_match_recovered_profile_offsets() -> None:
    assert AMATEUR_HISTORY_LAYOUT.history_class is CareerHistoryClass.AMATEUR
    assert AMATEUR_HISTORY_LAYOUT.count_offset == 0x2AA0
    assert AMATEUR_HISTORY_LAYOUT.ring_index_offset == 0x2AA2
    assert AMATEUR_HISTORY_LAYOUT.storage_base_offset == 0x26B8
    assert PRO_HISTORY_LAYOUT.history_class is CareerHistoryClass.PROFESSIONAL
    assert PRO_HISTORY_LAYOUT.count_offset == 0x2AA1
    assert PRO_HISTORY_LAYOUT.ring_index_offset == 0x2AA3
    assert PRO_HISTORY_LAYOUT.storage_base_offset == 0x28AC
    assert AMATEUR_HISTORY_LAYOUT.capacity == RETAIL_HISTORY_RING_CAPACITY == 20
    assert PRO_HISTORY_LAYOUT.entry_size == RETAIL_HISTORY_ENTRY_SIZE == 25


def test_retail_history_evidence_addresses_are_locked() -> None:
    assert HISTORY_WRITER_VADDR == 0x001939DC
    assert HISTORY_READER_VADDR == 0x00193BB8
    assert HISTORY_COMPLETED_FIGHT_CALLER_VADDR == 0x001B7894
    assert HISTORY_UI_PROVIDER_VADDR == 0x001EE2D0
    assert HISTORY_RESULT_TABLE_VADDR == 0x0055FF88
    assert HISTORY_TKO_FORMATTER_VADDR == 0x00206E18
