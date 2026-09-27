# Fighter combat state machine (debug ULES00270)

This package records a debug-build static reconstruction used to narrow the
retail FNR3 overhaul search. It does **not** claim that the listed addresses
are retail ULUS10066 hook addresses.

Source artifact:

- ULES00270 debug/review `BOOT.BIN`
- SHA-256 `8ff90a628346c67c929ff9f494a3806ef1bcfb41788db9330885348eda49f1b4`

Machine-readable evidence is in:

`analysis/resources/debug-fight-state-machine.json`

## Fighter runtime object

`0x000409FC` constructs a large per-fighter runtime object. Two owned
subsystems are now directly bounded:

- `owner+0x1F4` -> 0x7C-byte movement state machine, constructed by
  `0x00064158`;
- `owner+0x21C` -> 0x74-byte combat/action state controller, constructed by
  `0x00034458(controller, 14)`.

The combat controller allocates 14 state-pointer slots. `0x00034C98` reads a
state object's `+0x08` field and stores the state pointer into the array at
that index, proving `state+0x08` is the state ID.

Recovered state IDs:

| ID | State |
|---:|---|
| 0 | DRONE_STATE_IDLE |
| 3 | DRONE_DEFEND_PREPARE |
| 4 | DRONE_DEFENDING |
| 5 | DRONE_ATTACKING |
| 6 | DRONE_KNOCKDOWN_ATTACK |
| 7 | DRONE_FEINTING |
| 8 | DRONE_TAUNTING |
| 9 | DRONE_ILLEGAL_PUNCH |
| 10 | DRONE_SIGNATURE_PUNCH |
| 11 | DRONE_COUNTER_PUNCH |
| 12 | DRONE_BREAKCLINCH |
| 13 | DRONE_CLINCH |

IDs 1 and 2 are not instantiated by this constructor and remain unnamed.

## State object ABI

Concrete states share a common prefix:

```text
+0x00/+0x04  transition/internal state
+0x08        state ID
+0x0C/+0x10  initialized to -1 by common constructors
+0x14        member-function table pointer
+0x18        owning fighter runtime object
+0x1C        copy of owner+0x28
+0x20        copy of owner+0x2C
+0x24        copy of owner+0x30
```

The member-function table entries are eight-byte records containing a signed
`this` adjustment and a function pointer.

The important table slot is `+0x18`: the central fighter update invokes that
slot on the current combat state and also on the separate movement state
machine.

Transition helpers also bound the later table slots:

- `0x000426C4` sets the transition flag and invokes table `+0x78`;
- `0x00042694` clears it and invokes table `+0x80`.

Enter/exit naming for those two callbacks is probable rather than an original
symbol claim.

## Per-fighter update

`0x00041450` is the strongest static fight-loop boundary recovered so far.

At `0x000417B0` it follows:

```text
fighter+0x21C
  -> combat controller+0x54
  -> current combat state+0x14
  -> member-function slot +0x18
  -> state update
```

At `0x000417D0` it then follows:

```text
fighter+0x1F4
  -> movement state+0x14
  -> member-function slot +0x18
  -> movement update
```

Therefore one call to `0x00041450` advances both the fighter's current combat
action and movement state.

### Why there is no direct JAL caller

`0x00041450` is itself installed as a virtual/member-function method at
`+0x104` in multiple fighter-class tables:

- table base `0x0057B4EC`
- table base `0x0057B6CC`
- table base `0x0057B8AC`
- table base `0x0057BA8C`

Each has `0x00041450` at table `+0x104`.

This explains why a direct `jal 0x41450` search finds nothing. The next static
step is to identify the manager/container that invokes fighter virtual slot
`+0x104`; that should expose the outer fight tick that updates both fighters.

## State update targets

Useful concrete per-state update functions include:

| State | Update |
|---|---|
| DRONE_ATTACKING | `0x0005B58C` |
| DRONE_TAUNTING | `0x00059230` |
| DRONE_FEINTING | `0x0005C878` |
| DRONE_COUNTER_PUNCH | `0x0005CD54` |
| DRONE_DEFENDING | `0x0005F41C` |
| DRONE_CLINCH | `0x0005FBB4` |
| DRONE_STATE_IDLE | `0x00061B50` |
| DRONE_KNOCKDOWN_ATTACK | `0x00061E08` |
| DRONE_MOVEMENT | `0x00064220` |

The movement update has a distinct switch over movement substate values 0..8,
which independently confirms that movement is a separate state machine.

## Overhaul impact

This replaces the previous broad "search around DRONE strings" plan with a
bounded execution architecture:

```text
outer fight manager (still to recover)
    -> fighter virtual +0x104
       -> 0x00041450 per-fighter update
          -> current combat-state update
          -> movement-state update
```

Immediate static targets are:

1. recover the outer caller of virtual slot `+0x104`;
2. trace `DRONE_ATTACKING` into punch execution, stamina cost and hit
   resolution;
3. trace `DRONE_KNOCKDOWN_ATTACK` into knockdown/KO/TKO decisions;
4. correlate action-state transitions with the known AI attack-power
   consumers.

`0x00041450` is a strong **debug-build** hook boundary. It is not yet a safe
retail patch site; ULUS10066 transfer/matching and original-instruction/ABI
verification are still required.


## Outer owner and call chain

The next two caller layers are also recovered.

`0x000352F4` is the direct virtual-update invoker. It loads
`fighter+0x64`, selects the member-function entry at table `+0x100`, and
invokes the function pointer at entry `+0x04`. For the fighter class tables
above that pointer is `0x00041450`. `0x000350B4` is a thin wrapper around
this call.

A larger high-level boxer object is constructed by `0x000A01EC`. It installs
member-function table `0x0057D03C` at object `+0x18` and owns the fighter
runtime pointer at `+0x2A0`.

Its virtual update method is `0x000A0894` (table entry `+0x28`, function
pointer `+0x2C`). At `0x000A0E80` it calls:

```text
0x000350B4(object+0x2A0)
  -> 0x000352F4
     -> fighter virtual table +0x100
        -> 0x00041450
```

`0x0009D084` populates `object+0x2A0`. At
`0x0009D22C-0x0009D23C` it calls `0x00054608` using selected boxer/XDB
data and stores the returned fighter runtime pointer at `+0x2A0`.

`0x000859B4` bridges fight-session setup to these high-level boxer objects:
it reads the fight-session singleton and selected boxer IDs, allocates 0x2D0
byte objects, constructs them with `0x000A01EC`, stores them in the owning
manager, then invokes `0x0009D084` to create each object's fighter runtime.

This gives the current bounded chain:

```text
fight-session boxer selections
  -> 0x000859B4 boxer-owner setup
     -> 0x000A01EC high-level boxer object
        -> 0x0009D084 / 0x00054608 fighter-runtime creation
        -> 0x000A0894 high-level update
           -> 0x000350B4
              -> 0x000352F4
                 -> 0x00041450 fighter tick
                    -> combat state update
                    -> movement state update
```

## Corrected false gameplay leads

Three prior string-xref avenues were presentation-side rather than direct
gameplay owners:

- `aiPunchesThrown` is part of the `GetMyCareerStatsInfo` output-key
  cluster with `aiPunchesLanded`, `aiPunchAccuracy`, rank and career
  record fields. Its owner is a front-end data builder, not proof of the
  hit-resolution pipeline.
- `astrTKOTime` is part of `GetCareerHistoryInfo`/list output alongside
  opponent name, fight result and rounds lasted. Its xref is not the KO/TKO
  decision routine.
- both `iStamina` strings are rating-presentation keys: one in SelectBoxer
  and one in Get/Update/SetCreateRatingsInfo. They do not identify the
  in-fight stamina field or formula.

These strings remain useful schema/UI evidence, but are no longer used as
primary combat-code leads.
