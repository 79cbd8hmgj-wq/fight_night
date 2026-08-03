# Exact-layout ISO rebuild pipeline

Task 6 proves a deterministic reconstruction boundary without repacking or relocating the original filesystem.

## Build model

The builder requires four trusted inputs:

1. The exact `ULUS10066-v1.00` reference ISO.
2. A verified immutable workspace produced by Task 4.
3. The locked revision configuration.
4. A versioned build plan containing zero or more guarded byte patches.

A no-change build copies the complete reference image, verifies every manifest extent against the reference and immutable workspace, reparses the result, and requires the final SHA-256 to equal the locked retail hash.

```bash
fnr3-re rebuild-image \
  "/path/to/Fight Night Round 3 (USA).iso" \
  "/local/path/fnr3-workspace" \
  "/local/path/fnr3-rebuilt.iso" \
  --revision-config config/revisions/ulus10066-v1.00.json \
  --plan config/build-plans/no-change.json
```

The default report is written beside the output as:

```text
fnr3-rebuilt.iso.build.json
```

A custom report path can be supplied with `--report`. Existing output or report files require `--force` and are replaced as one transactional pair.

## Guarded byte patches

Task 6 deliberately permits only fixed-size, revision-guarded patches:

```json
{
  "schema_version": 1,
  "revision_id": "ULUS10066-v1.00",
  "patches": [
    {
      "id": "example-patch",
      "path": "PSP_GAME/SYSDIR/BOOT.BIN",
      "file_offset": 4096,
      "expected_hex": "00000000",
      "replacement_hex": "01000000"
    }
  ]
}
```

Before any output is written, the builder requires:

- the plan revision to match the locked image revision;
- the target path to exist in the exact workspace manifest;
- the immutable source file size and SHA-256 to match its manifest;
- the reference ISO extent to match the same manifest hash;
- expected and replacement byte counts to be equal;
- the patch range to remain inside the original file;
- the expected bytes to match exactly;
- patch IDs to be unique;
- patches within a file not to overlap.

A stale guard, wrong image, changed workspace, invalid range, unknown path, duplicate ID, overlap, or length-changing replacement fails before the output or report is created.

## Build report

The deterministic JSON report records:

- revision ID;
- reference SHA-256;
- canonical build-plan SHA-256;
- output SHA-256 and byte size;
- whether the build is a no-change build;
- each changed file's source and output SHA-256;
- every patch ID, file-relative offset, ISO-relative offset, length, expected bytes, and replacement bytes.

A clean rebuild with the no-change plan is also the authoritative rollback procedure for all Task 6 patches.

## Current boundary

Task 6 preserves the original ISO layout and only changes bytes inside existing file extents. It does not yet:

- grow or shrink a file;
- relocate extents;
- rebuild ISO directory records;
- add or remove files;
- automatically reinsert decoded RefPack or BIG/VIV resources;
- claim a PPSSPP boot, fight, save, or reload result.

Those capabilities require later evidence-backed rebuild manifests and runtime validation. The fixed-size boundary is intentional: it proves guarded patching and exact rollback before introducing relocation or metadata changes.

## Retail integration gate

When `FNR3_REFERENCE_ISO` points to the validated retail image, the environment-gated integration test:

1. extracts and verifies all 653 files and 71 directories;
2. performs a no-change rebuild;
3. verifies the exact retail size and SHA-256;
4. confirms the changed-file list is empty.

The ISO and local workspace remain outside Git. No copyrighted payload is uploaded to CI or committed to the repository.
