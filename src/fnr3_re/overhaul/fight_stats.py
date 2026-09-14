"""RE-grounded reference: the generic fight-statistics accessor and one
fully reconstructed formula (punch accuracy).

Static evidence (this pass, disassembly of ``T_001F2E00``, the real
implementation behind the ``GetFightTotalsInfo`` native accessor --
confirmed real, not a registration trampoline, by its size: 716
instructions, versus the ~11-30 instruction registration trampolines seen
everywhere else this project has looked):

``T_001F2E00`` reads per-boxer fight statistics through a single generic
accessor, ``func_0BA748(context, boxer_slot, subcontext, stat_id) -> int``,
called identically for both corners by varying only ``boxer_slot``. Three
``stat_id`` values are proven by direct disassembly (the exact argument
immediates at each call site):

- ``STAT_PUNCHES_THROWN = 0``
- ``STAT_PUNCHES_HIT = 1``
- ``STAT_KNOCKDOWNS = 0xE`` (14) -- called with ``boxer_slot`` passed as an
  immediate 0/1 rather than the loop variable used for the punch stats,
  but the same accessor function and calling convention.

Two further IDs (``0x10``, ``0x11``) are called in the same loop body
immediately after IDs 0/1 but were not connected to any displayed UI field
by this pass -- recorded as unresolved, not guessed.

``T_001F2E00`` also contains one fully reconstructed formula: the
punch-accuracy percentage shown as ``aStrPunchPercentLeft``/
``...Right``. Reproduced here field-for-field from the disassembly
(MIPS FPU: ``div.s`` then ``mul.s`` by a loaded ``100.0`` constant, then
``trunc.w.s`` -- truncation, not rounding -- guarded by a ``beqz`` on the
thrown-count that produces a hard 0 sentinel instead of dividing by zero):

```
lui  $a0, 0x42C8          ; f20 = 100.0f  (IEEE-754 0x42C80000)
mtc1 $a0, $f20
...
beqz $s0, zero_case        ; s0 = punches thrown
  mtc1 $s5, $f12            ; s5 = punches hit
  mtc1 $s0, $f13
  cvt.s.w $f12,$f12 ; cvt.s.w $f13,$f13
  div.s $f12,$f12,$f13
  mul.s $f12,$f12,$f20
  trunc.w.s $f12,$f12
  ...
zero_case:
  ; $f12 = 0.0 (int 0 reinterpreted, then cvt.s.w'd -- net effect: 0.0)
```

Confidence: CONFIRMED for the formula shape and the three named stat IDs
(direct disassembly, not inference); PROBABLE for ``func_0BA748``'s general
signature (its own body was not disassembled -- only its call sites).
"""

from __future__ import annotations

STAT_PUNCHES_THROWN = 0x00
STAT_PUNCHES_HIT = 0x01
STAT_KNOCKDOWNS = 0x0E

#: Observed at the same call site as the punches-thrown/hit pair but not
#: connected to any displayed field this pass. Do not assume meaning.
STAT_ID_UNRESOLVED_0X10 = 0x10
STAT_ID_UNRESOLVED_0X11 = 0x11

BOXER_SLOT_LEFT = 0
BOXER_SLOT_RIGHT = 1

FIGHT_TOTALS_REAL_IMPLEMENTATION_FUNC = 0x001F2E00
GENERIC_STAT_ACCESSOR_FUNC = 0x000BA748


def punch_accuracy_percent(punches_hit: int, punches_thrown: int) -> int:
    """Reproduce ``T_001F2E00``'s punch-accuracy formula exactly.

    ``trunc((hit / thrown) * 100)`` as 32-bit IEEE-754 single-precision
    float math, truncated toward zero (not rounded), with a proven 0
    sentinel when ``punches_thrown == 0`` (the original guards the
    division, it does not crash or return a garbage value).

    Raises :class:`ValueError` for negative inputs -- the original's
    counts are unsigned accumulators and a negative count cannot occur in
    real play; static evidence does not cover that input domain, so this
    function refuses to guess its behavior there.
    """

    if punches_hit < 0 or punches_thrown < 0:
        raise ValueError("punch counts must be non-negative")
    if punches_thrown == 0:
        return 0
    # float32 round-trip, matching the original's single-precision math
    import struct

    ratio = struct.unpack("<f", struct.pack("<f", punches_hit / punches_thrown))[0]
    percent = struct.unpack("<f", struct.pack("<f", ratio * 100.0))[0]
    return int(percent)  # trunc.w.s truncates toward zero, like int()
