# Reference ISO workspace

Task 4 converts the exact `ULUS10066-v1.00` image into a deterministic local research workspace without committing copyrighted payloads.

## Layout

```text
workspace/
├── original/   # byte-exact ISO files; read-only after extraction
├── working/    # decoded and reconstructed intermediate files
├── modified/   # intentional edits used by later rebuild tasks
└── manifests/
    └── workspace.json
```

`original/` is authoritative. Later codecs and rebuild tools read from `original/`, write decoded material to `working/`, and consume intentional replacements from `modified/`. They must not modify `original/` in place.

## Extraction

```bash
fnr3-re extract-image \
  "/path/to/Fight Night Round 3 (USA).iso" \
  "/local/path/fnr3-workspace" \
  --revision-config config/revisions/ulus10066-v1.00.json
```

Use `--force` only to transactionally replace an existing workspace. The existing directory is preserved unless the complete replacement succeeds.

The dedicated entry point performs extraction followed by verification:

```bash
python tools/build_reference_workspace.py \
  "/path/to/Fight Night Round 3 (USA).iso" \
  "/local/path/fnr3-workspace"
```

## Manifest contract

`manifests/workspace.json` records:

- locked revision ID and source ISO identity;
- ISO volume identifier, logical sector size, and declared sector count;
- every directory in deterministic discovery order;
- every file path, LBA, byte offset, byte size, SHA-256, discovery order, and broad resource classification.

Manifest JSON uses sorted keys, fixed indentation, UTF-8, and a terminal newline. Two extractions of the same image must produce byte-identical manifests.

## Safety rules

The scanner rejects:

- invalid or truncated primary volume descriptors;
- disagreeing little-endian and big-endian ISO9660 fields;
- extents outside the declared volume;
- duplicate case-insensitive paths;
- unsafe identifiers or traversal components;
- reused directory extents;
- overlapping allocated file or directory extents;
- unsupported multi-extent files.

The exact revision validator runs before extraction. A wrong region, modified image, stale copy, or malformed `PARAM.SFO` cannot create a trusted workspace.

## Verification

```bash
fnr3-re verify-workspace /local/path/fnr3-workspace
```

Verification checks required directories, manifest structure, every original file's size and SHA-256, read-only permissions, missing directories, symbolic links, and unexpected files.

## Repository boundary

The workspace path must remain outside the repository or under an ignored local directory. ROMs, original executables, extracted archives, assets, saves, RAM captures, screenshots, and recorded audio are not committed. Only tools, schemas, tests, normalized evidence, and documentation belong in Git.
