"""RE-grounded reference: the fight/match-context global singleton.

Static evidence (this pass, via disassembly of a hash-verified ``BOOT.BIN``
sample, see ``docs/architecture/revisions.md`` for the tracked hash):

``func_001B3EA8`` is a lazily-initialized singleton accessor, structurally
identical to the already-proven boxer-table singleton accessor
(``func_00186408``): it tests a flag word, and on first call constructs the
singleton by calling ``func_001AF768`` (previously misread by an earlier
pass as a "UI/menu-construction routine" -- it is in fact this singleton's
lazy constructor, consumed from at least three unrelated call sites this
pass: the fight-totals stat screen, the judging scorecard screen, and the
options-settings bitfield decoder, none of which are the boxer-select
screen). Confirmed by disassembly of ``func_001B3EA8`` itself:

```
lui $a0, 0x1; lw $a1, -0x7E10($a0)      ; flag @ FLAG_ADDRESS
bnez $a1, already_initialized
sw   1, -0x7E10($a0)
jal  func_1AF768                        ; a0 = OBJECT_ADDRESS (constructor)
already_initialized:
return OBJECT_ADDRESS
```

Three independent call sites (``T_001F2E00`` fight-totals, ``T_001F7248``
judging scorecard, and -- per the prior pass -- ``T_001D9A08`` options
bitfield decoder) all call ``func_001B3EA8`` and then read
``singleton + 0x19B0`` / ``singleton + 0x19B4`` as two consecutive per-corner
boxer object pointers, each immediately handed to ``func_186284`` (a
"resolve boxer display info from pointer" callback observed both times).
This is the strongest static evidence found so far for Program 05's
fight-session/context object: a single global singleton holding (at least)
the two participating boxers' object pointers.

Confidence: PROBABLE. The exact size and full field layout of the singleton
are NOT proven -- only the specific offsets independently corroborated by
multiple call sites are recorded here. Do not treat unlisted offsets as
free/unused; they were simply not reached by any function disassembled
this pass.
"""

from __future__ import annotations

from dataclasses import dataclass

#: File-relative ELF virtual addresses (BOOT.BIN, ULUS10066-v1.00). See
#: docs/architecture/psp-static-analysis.md for the address model.
SINGLETON_ACCESSOR_FUNC = 0x001B3EA8
SINGLETON_CONSTRUCTOR_FUNC = 0x001AF768
SINGLETON_INIT_FLAG_ADDRESS = 0x000081F0
SINGLETON_OBJECT_ADDRESS = 0x000081F8

#: Field offsets within the singleton object, each corroborated by 2+
#: independent disassembled call sites this pass.
OFFSET_BOXER_PTR_LEFT = 0x19B0
OFFSET_BOXER_PTR_RIGHT = 0x19B4

#: Corroborated by the prior pass's disassembly of T_001D9A08 (a packed
#: options-settings bitfield); exact bit-to-option mapping remains open,
#: see analysis/resources/static-re-backlog.json.
OFFSET_PACKED_OPTIONS_BITFIELD = 0x15C

#: Owning functions for the two corroborated field-access sites, kept for
#: cross-reference/audit -- not used at runtime by this package (this
#: project performs no runtime observation).
KNOWN_READERS = (
    "T_001F2E00",  # GetFightTotalsInfo real implementation
    "T_001F7248",  # judging scorecard (GetJudgesScoreInfo family)
)


@dataclass(frozen=True, slots=True)
class FightSessionSingletonLayout:
    """The proven subset of the fight-session singleton's field layout.

    This is a documentation/analysis object, not a live memory reader --
    this project performs no runtime observation. It exists so that future
    patch work has one authoritative, cited source for these offsets
    instead of re-deriving them from scratch.
    """

    accessor_func: int = SINGLETON_ACCESSOR_FUNC
    constructor_func: int = SINGLETON_CONSTRUCTOR_FUNC
    init_flag_address: int = SINGLETON_INIT_FLAG_ADDRESS
    object_address: int = SINGLETON_OBJECT_ADDRESS
    boxer_ptr_left_offset: int = OFFSET_BOXER_PTR_LEFT
    boxer_ptr_right_offset: int = OFFSET_BOXER_PTR_RIGHT
    packed_options_bitfield_offset: int = OFFSET_PACKED_OPTIONS_BITFIELD


PROVEN_LAYOUT = FightSessionSingletonLayout()
