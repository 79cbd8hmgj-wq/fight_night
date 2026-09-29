from __future__ import annotations

from fnr3_re.overhaul.fight_session import PROVEN_LAYOUT, FightSessionSingletonLayout


def test_proven_layout_matches_disassembly_citations() -> None:
    assert PROVEN_LAYOUT.accessor_func == 0x001B3EA8
    assert PROVEN_LAYOUT.constructor_func == 0x001AF768
    assert PROVEN_LAYOUT.init_flag_address == 0x000081F0
    assert PROVEN_LAYOUT.object_address == 0x000081F8

    assert PROVEN_LAYOUT.set_session_mode_func == 0x001AFFDC
    assert PROVEN_LAYOUT.set_venue_selection_func == 0x001B00A0
    assert PROVEN_LAYOUT.set_boxer_selection_func == 0x001B00B4

    assert PROVEN_LAYOUT.session_mode_offset == 0x19A8
    assert PROVEN_LAYOUT.venue_id_offset == 0x19AC
    assert PROVEN_LAYOUT.boxer_id_left_offset == 0x19B0
    assert PROVEN_LAYOUT.boxer_id_right_offset == 0x19B4
    assert PROVEN_LAYOUT.boxer_id_mirror_left_offset == 0x19B8
    assert PROVEN_LAYOUT.boxer_id_mirror_right_offset == 0x19BC


def test_layout_is_immutable_and_default_constructible() -> None:
    layout = FightSessionSingletonLayout()
    assert layout == PROVEN_LAYOUT
