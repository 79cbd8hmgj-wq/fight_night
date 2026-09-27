# AIP native dispatch and debug-menu bridge

## Scope

This package records the static bridge between FNR3's compiled APT front end and
native BOOT.BIN handlers. It was recovered by cross-referencing the verified
ULUS10066-v1.00 retail map with a user-provided ULES00270 debug/review BOOT.BIN.

The binary itself is not tracked.

## Resolved registration semantics

The previously-generic registration pair now has bounded semantics:

- `func_000CDA70` registers an **FSCommand** handler.
- `func_000CDAC0` registers a **LoadVariables** handler.
- `func_000CDA9C` unregisters an FSCommand handler.
- `func_000CDAEC` unregisters a LoadVariables handler.
- `func_000CF9C4` inserts into the FS handler binary-search tree.
- `func_000CFE08` inserts into the LoadVariables handler binary-search tree.

The handler manager is referenced through the global at `0x005436D8`.
Its two tree roots are separated by command family.

## Handler-node layout

Each registration node is `0x14` bytes:

| Offset | Meaning |
| --- | --- |
| `+0x00` | left child |
| `+0x04` | right child |
| `+0x08` | handler-name string pointer |
| `+0x0C` | handler target/object pointer |
| `+0x10` | auxiliary integer; registration glue passes `-1` |

## Dispatch

`func_000D024C` is the FSCommand dispatch path. It parses the requested
handler name, searches the FS tree, and, when a node matches, invokes the
registered target through its interface/vtable entry. A missing handler follows
the diagnostic path containing `No FS handler found`.

`func_000D041C` is the parallel LoadVariables dispatch path. It searches the
LV tree, invokes the registered target, and returns the produced result. A
missing handler follows the `No LV handler found` diagnostic path.

`func_000D066C` enumerates the FS/LV handler lists for diagnostics.

This resolves the static blocker previously recorded in
`program-03-05`: registration is now connected to the actual script-call
dispatch path.

## Debug-menu bindings

The registration glue at `0x001CEC48-0x001CECB8` establishes:

| Native name | AIP channel |
| --- | --- |
| `GetStartScreenFromMain` | LoadVariables |
| `DEBUG_GetDebugMenuData` | LoadVariables |
| `DEBUG_OnAdvance` | FSCommand |
| `DEBUG_OnRealFE` | FSCommand |

The matching unregister glue is at `0x001CECBC-0x001CECFC`.

Retail already contains `menu/debugmenu.big` with
`debugMenu.apt` / `debugMenu.const`, so the menu's mere presence is **not**
unique to the debug build. The new result is the recovered native dispatch
semantics and a much stronger cross-build map.

The exact APT bytecode instruction sites that issue these requests remain a
separate decoding task.

## Cross-build layout

The ULES00270 reference BOOT.BIN SHA-256 is
`8ff90a628346c67c929ff9f494a3806ef1bcfb41788db9330885348eda49f1b4`.

Its ELF has 62 sections and entry `0x0034DF24`. Its primary section sizes are:

- `.text`: `0x4F64A4`
- `.data`: `0x5C760`
- `.bss`: `0x355A4`

Those three sizes exactly match the tracked retail BOOT.BIN report. This makes
the debug/review build a high-value address-level reference, but matching
addresses must still be validated per function before promotion to CONFIRMED.

## Evidence

Machine-readable evidence lives in
`analysis/resources/debug-build-aip-dispatch.json`.


## Concrete debug-menu handler targets

The debug/review build's static initializer at
`0x001CF2D8-0x001CF39C` resolves the registration targets all the way to
concrete handler functions:

| Native name | Descriptor | Implementation |
| --- | ---: | ---: |
| `GetStartScreenFromMain` | `0x00581D54` | `0x001CED00` |
| `DEBUG_GetDebugMenuData` | `0x00581D64` | `0x001CED2C` |
| `DEBUG_OnAdvance` | `0x00581D74` | `0x001CF1A0` |
| `DEBUG_OnRealFE` | `0x00581D84` | `0x001CF2A0` |

The initializer writes those descriptor addresses into the global slots later
passed to the AIP registration helpers. Each descriptor has the concrete
handler function pointer at `+0x0C`.

### `DEBUG_GetDebugMenuData`

`0x001CED2C` is the real data-producing handler. Its output schema is now
recoverable directly from the native calls:

- `iNumElements = 3`
- `aBoxNames` receives three localized labels:
  `TL_Select_Boxer`, `TL_Select_Boxer`, `TL_Select_Venue`
- paired selector arrays:
  - `aBoxStrings0` / `aBoxIDs0`
  - `aBoxStrings1` / `aBoxIDs1`
  - `aBoxStrings2` / `aBoxIDs2`
- `aDefaultIDs = [25, 17, 9]`

The first two selector families are populated from boxer data; the third is
populated from venue data using `Venue_%d` keys.

### `DEBUG_OnAdvance`

`0x001CF1A0` parses `iBox0`, `iBox1`, and `iBox2`, obtains the proven
fight-session singleton through `func_001B3EA8`, applies the two boxer
selections through separate corner calls, applies the third selection through
a distinct session setter consistent with the venue slot, and then executes the
fight/front-end transition sequence.

This makes the surviving debug menu a concrete developer quick-fight setup
path rather than merely an orphaned UI asset.

### `DEBUG_OnRealFE`

`0x001CF2A0` calls the front-end command path with the strings
`ChangeScreen`, `_root`, and `MAINMENU`, providing the route back to the
normal front end.
