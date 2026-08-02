# Decompilation Gate

## Locked rule

> Before overhaul implementation begins, every system modified by the overhaul—and every system that owns, stores, calls, derives, caches, serializes, validates, displays, or consumes its data—must be functionally reverse-engineered to a verified replacement boundary.

This rule is mandatory. It may only become stricter when new consumers, fixed-size structures, save dependencies, UI bindings, or module-budget constraints are discovered.

## Scope classes

### Class A — functional reconstruction required

Use Class A when Phase II changes the subsystem's internal behavior or relies on its internal behavior.

A complete Class A package must identify:

- owning executable or PRX;
- runtime base, storage region, and lifetime;
- confirmed functions, globals, tables, fields, enums, and transitions;
- readable reconstructed source or a precise typed executable model;
- readers, writers, callers, callees, and indirect consumers;
- initialization, update, reset, destruction, and alternate paths;
- original-behavior tests;
- replacement ABI, storage, fallback, rollback, and budget;
- save, UI, resource, module, and performance consequences;
- no unresolved blocking unknowns.

### Class B — interface-boundary mapping required

Use Class B when Phase II calls a subsystem or supplies data to it without changing its internals.

A complete Class B package must identify:

- game-facing inputs and outputs;
- owner and lifetime;
- calling convention;
- resource ownership and failure behavior;
- compatibility tests;
- evidence that deeper reconstruction is unnecessary.

### Class C — inventory only

Use Class C when a subsystem is unrelated to every modified object, resource, save block, ID, enum, UI path, and module budget.

A Class C record must identify its owner and the evidence supporting exclusion. Classification is provisional until ownership and consumers are confirmed.

## Phase I permissions

Phase I may include:

- exact-build validation;
- extraction and rebuilding;
- resource codecs;
- static and runtime instrumentation;
- neutral replacements;
- functional reconstruction of original behavior;
- normalized evidence and regression tests.

Phase I may not include:

- new gameplay rules;
- roster additions;
- Bantamweight or Cruiserweight insertion;
- new weight-class identities;
- Career Mode 2.0 behavior;
- Amateur Career 2.0 behavior;
- save expansion carrying new feature data.

## Phase I completion gate

Phase II remains blocked until all of the following are approved together:

1. Every required Class A package is `complete`.
2. Every connected Class B interface is `complete`.
3. Fixed counts, ID widths, arrays, object layouts, save layouts, UI lists, and module budgets are resolved.
4. Neutral replacements reproduce original behavior.
5. Save migration has a validated neutral round trip.
6. Boot, menu, exhibition, career, result, save, restart, and load regressions pass.
7. Memory, frame-time, executable, PRX, BSS, heap, stack, archive, and save budgets are recorded.
8. Every future replacement has an original fallback and rollback path.
9. A decompilation-completeness review explicitly approves Phase II.

No individual feature may bypass this cross-system gate.
