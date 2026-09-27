"""RE-grounded reference: the fight/match-context global singleton.

The retail ULUS10066-v1.00 static map identifies ``func_001B3EA8`` as the
lazy accessor for the global fight-session object constructed by
``func_001AF768``.

A follow-up cross-build trace using the ULES00270 review/debug BOOT.BIN
resolved several previously-misidentified fields. The debug build has the
same primary .text/.data/.bss sizes and the same bounded function/address
family used by the retail evidence, so these additions are recorded as
PROBABLE cross-build evidence rather than silently promoted to CONFIRMED.

Most importantly, ``singleton + 0x19B0`` / ``+0x19B4`` are numeric boxer
selection IDs/indices, not boxer-object pointers. ``DEBUG_OnAdvance`` parses
``iBox0`` / ``iBox1`` from AIP and passes those numeric values directly to
``func_001B00B4(session, corner, boxer_id)``. That setter stores the selected
value at ``+0x19B0 + corner*4``. Existing retail readers
``T_001F2E00`` and ``T_001F7248`` then pass the stored value to
``func_00186284``; disassembly of that resolver shows its second argument is a
numeric index used while walking the boxer-table registry/count space.

The same debug-menu path resolves two additional session fields:

* ``func_001B00A0(session, venue_id)`` stores the venue selection at
  ``+0x19AC`` when the signed value is below 12.
* ``func_001AFFDC(session, mode)`` stores the fight/session mode at
  ``+0x19A8`` (values below 9; out-of-range positive values collapse to -1).
  The developer quick-fight path sets this field to 1.

Confidence: PROBABLE for the cross-build field/write-site mapping. The
singleton accessor/constructor addresses remain grounded in the tracked retail
BOOT.BIN evidence.
"""

from __future__ import annotations

from dataclasses import dataclass

#: File-relative ELF virtual addresses. See
#: docs/architecture/psp-static-analysis.md for the address model.
SINGLETON_ACCESSOR_FUNC = 0x001B3EA8
SINGLETON_CONSTRUCTOR_FUNC = 0x001AF768
SINGLETON_INIT_FLAG_ADDRESS = 0x000081F0
SINGLETON_OBJECT_ADDRESS = 0x000081F8

#: Cross-build-resolved fight-session setters.
SET_SESSION_MODE_FUNC = 0x001AFFDC
SET_VENUE_SELECTION_FUNC = 0x001B00A0
SET_BOXER_SELECTION_FUNC = 0x001B00B4

#: Proven/probable field offsets within the singleton object.
OFFSET_SESSION_MODE = 0x19A8
OFFSET_VENUE_ID = 0x19AC
OFFSET_BOXER_ID_LEFT = 0x19B0
OFFSET_BOXER_ID_RIGHT = 0x19B4

#: ``func_001B00B4`` mirrors the selected numeric IDs into a second
#: per-corner pair while updating the boxer selection. The semantic
#: distinction between the primary and mirrored pair is not yet proven.
OFFSET_BOXER_ID_MIRROR_LEFT = 0x19B8
OFFSET_BOXER_ID_MIRROR_RIGHT = 0x19BC

#: Retail evidence: packed gameplay/options word consumed by the options
#: accessor family. Exact bit-to-option mapping remains open.
OFFSET_PACKED_OPTIONS_BITFIELD = 0x15C

KNOWN_BOXER_ID_READERS = (
    "T_001F2E00",  # GetFightTotalsInfo real implementation
    "T_001F7248",  # judging scorecard (GetJudgesScoreInfo family)
)


@dataclass(frozen=True, slots=True)
class FightSessionSingletonLayout:
    """The currently proven/probable subset of the fight-session layout."""

    accessor_func: int = SINGLETON_ACCESSOR_FUNC
    constructor_func: int = SINGLETON_CONSTRUCTOR_FUNC
    init_flag_address: int = SINGLETON_INIT_FLAG_ADDRESS
    object_address: int = SINGLETON_OBJECT_ADDRESS

    set_session_mode_func: int = SET_SESSION_MODE_FUNC
    set_venue_selection_func: int = SET_VENUE_SELECTION_FUNC
    set_boxer_selection_func: int = SET_BOXER_SELECTION_FUNC

    session_mode_offset: int = OFFSET_SESSION_MODE
    venue_id_offset: int = OFFSET_VENUE_ID
    boxer_id_left_offset: int = OFFSET_BOXER_ID_LEFT
    boxer_id_right_offset: int = OFFSET_BOXER_ID_RIGHT
    boxer_id_mirror_left_offset: int = OFFSET_BOXER_ID_MIRROR_LEFT
    boxer_id_mirror_right_offset: int = OFFSET_BOXER_ID_MIRROR_RIGHT
    packed_options_bitfield_offset: int = OFFSET_PACKED_OPTIONS_BITFIELD


PROVEN_LAYOUT = FightSessionSingletonLayout()
