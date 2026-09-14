"""Overhaul Alpha 1 -- Core Boxer + Fight Systems.

This package is the first implementation tranche of the planned Fight Night
Round 3 PSP overhaul. It is split into two kinds of module, and every
module's own docstring says which it is:

- **RE-grounded reference modules** (``fight_session``, ``fight_stats``)
  record only what static disassembly of ``BOOT.BIN`` has actually proven
  this pass -- addresses, offsets, call shapes, and one fully reconstructed
  formula (punch accuracy). Nothing in these modules is inferred from
  strings or UI labels alone.
- **New overhaul rule-engine modules** (``boxer_model``, ``stamina``,
  ``damage``, ``ai``, ``judging``, ``rules``) are this milestone's own new,
  tunable, data-driven gameplay logic -- the planned overhaul's Alpha 1
  behavior. They are NOT yet wired into ``BOOT.BIN`` via any byte patch:
  no safe, evidence-backed patch site was established for the underlying
  original stamina/damage/AI/judging *formulas* this pass (only their
  proven *data shapes* and a handful of real accessor functions were).
  See ``docs/overhaul/alpha1/README.md`` for the full replacement-boundary
  map and exactly what remains blocked before any of this can be stitched
  into a patched executable.
"""
