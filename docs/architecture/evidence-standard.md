# Evidence Standard

## Confidence labels

### CONFIRMED

A semantic claim proven by exact code or data plus at least one controlled runtime observation, deterministic reconstruction, write/read breakpoint, input/output experiment, save diff, or rebuilt-game test.

### PROBABLE

Strong static evidence and consistent runtime behavior exist, but a reverse control, lifecycle proof, or independent deterministic check is missing.

### CANDIDATE

A plausible function, field, table, object, module owner, or interpretation that still requires controlled validation.

### REJECTED

A previous candidate contradicted by exact binary evidence, runtime evidence, a reverse control, or lifecycle behavior.

## Minimum claim record

Every normalized claim must identify:

- supported source revision;
- owning executable, PRX, archive, or resource;
- address type and value where applicable;
- evidence type;
- confidence label;
- bounded question being answered;
- positive case;
- reverse control or reason it is pending;
- lifecycle coverage or reason it is pending;
- exact hashes for relevant code or data regions;
- conclusion and remaining unknowns.

## Prohibited confirmation sources

The following are insufficient by themselves for `CONFIRMED`:

- decompiler pseudocode;
- function or variable names inferred from strings;
- visual similarity;
- a single uncontrolled memory value;
- one caller without writer or lifecycle analysis;
- a guide, wiki, or external roster list;
- behavior observed only in a scripted tutorial path;
- a patch that appears to work without guarded source verification.

## Address discipline

Never conflate:

- PPSSPP runtime address;
- module-relative virtual address;
- ELF virtual address;
- ELF file offset;
- stored PRX offset;
- archive member offset;
- ISO byte offset;
- ISO LBA.

Normalized evidence must state the address type explicitly. Conversions require a revision-locked module or archive map.

## Runtime experiment requirements

A strong runtime experiment records:

1. exact game and executable hashes;
2. emulator version and relevant settings;
3. save or state hash;
4. game mode and participants;
5. triggering input or event;
6. breakpoint or watchpoint address;
7. selected registers and memory;
8. expected and observed transition;
9. reverse control;
10. initialization, repeated-use, reset, and destruction boundaries when applicable.

Raw debugger packets, RAM dumps, screenshots, saves, and recorded input files remain local and ignored. Only concise normalized evidence enters Git.

## Functional reconstruction standard

Reconstructed code must preserve observed:

- input and output types;
- ordering and side effects;
- clamping and saturation;
- signedness and widths;
- integer or floating-point rounding;
- randomness and seed inputs;
- state ownership and lifetime;
- player and CPU differences;
- normal, tutorial, career, title, training, and scripted paths.

Unknowns must remain explicit. A readable guess is not a reconstruction.

## Replacement-boundary standard

Every future replacement must document:

- exact hook or replaced call;
- ABI and register/stack expectations;
- original overwritten bytes or records;
- new storage and lifetime;
- module and memory budget;
- failure behavior;
- original fallback;
- rollback procedure;
- tests proving neutral equivalence before new behavior is enabled.
