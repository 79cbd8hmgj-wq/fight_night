from __future__ import annotations

from fnr3_re.overhaul.fight_session import PROVEN_LAYOUT, FightSessionSingletonLayout


def test_proven_layout_matches_disassembly_citations() -> None:
    assert PROVEN_LAYOUT.accessor_func == 0x001B3EA8
    assert PROVEN_LAYOUT.constructor_func == 0x001AF768
    assert PROVEN_LAYOUT.init_flag_address == 0x000081F0
    assert PROVEN_LAYOUT.object_address == 0x000081F8
    assert PROVEN_LAYOUT.boxer_ptr_left_offset == 0x19B0
    assert PROVEN_LAYOUT.boxer_ptr_right_offset == 0x19B4


def test_layout_is_immutable_and_default_constructible() -> None:
    layout = FightSessionSingletonLayout()
    assert layout == PROVEN_LAYOUT
