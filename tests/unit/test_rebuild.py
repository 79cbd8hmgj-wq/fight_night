from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from fnr3_re.iso import build_workspace
from fnr3_re.rebuild import (
    BuildError,
    BuildPlan,
    BytePatch,
    load_build_plan,
    rebuild_image,
)
from fnr3_re.revision import ReferenceRevision
from tests.support.psp_iso import SECTOR_SIZE, write_reference

BOOT_PATH = "PSP_GAME/SYSDIR/BOOT.BIN"
BOOT_LBA = 25


def prepare_workspace(
    tmp_path: Path,
) -> tuple[Path, Path, ReferenceRevision, bytes]:
    reference, revision, image = write_reference(tmp_path)
    workspace = tmp_path / "workspace"
    build_workspace(reference, workspace, revision)
    return reference, workspace, revision, image


def test_no_change_rebuild_is_byte_exact_and_deterministic(tmp_path: Path) -> None:
    reference, workspace, revision, image = prepare_workspace(tmp_path)
    first_output = tmp_path / "first.iso"
    second_output = tmp_path / "second.iso"

    first = rebuild_image(
        reference,
        workspace,
        first_output,
        revision,
        BuildPlan.empty("fixture-v1"),
    )
    second = rebuild_image(
        reference,
        workspace,
        second_output,
        revision,
        BuildPlan.empty("fixture-v1"),
    )

    assert first_output.read_bytes() == image
    assert second_output.read_bytes() == image
    assert first.to_json() == second.to_json()
    assert first.no_change
    assert first.changed_files == ()
    assert first.output_sha256 == hashlib.sha256(image).hexdigest()
    assert first.output_sha256 == first.source_sha256


def test_guarded_byte_patch_changes_only_the_expected_iso_range(tmp_path: Path) -> None:
    reference, workspace, revision, image = prepare_workspace(tmp_path)
    output = tmp_path / "patched.iso"
    plan = BuildPlan(
        revision_id="fixture-v1",
        patches=(
            BytePatch(
                patch_id="boot-byte",
                path=BOOT_PATH,
                file_offset=5,
                expected=b"C",
                replacement=b"X",
            ),
        ),
    )

    report = rebuild_image(reference, workspace, output, revision, plan)
    rebuilt = output.read_bytes()
    iso_offset = BOOT_LBA * SECTOR_SIZE + 5

    assert rebuilt[:iso_offset] == image[:iso_offset]
    assert rebuilt[iso_offset] == ord("X")
    assert rebuilt[iso_offset + 1 :] == image[iso_offset + 1 :]
    assert not report.no_change
    assert len(report.changed_files) == 1
    assert report.changed_files[0].path == BOOT_PATH
    assert report.changed_files[0].ranges[0].file_offset == 5
    assert report.changed_files[0].ranges[0].iso_offset == iso_offset
    assert report.changed_files[0].ranges[0].expected_hex == "43"
    assert report.changed_files[0].ranges[0].replacement_hex == "58"


def test_empty_plan_reverts_to_reference_after_a_patched_build(tmp_path: Path) -> None:
    reference, workspace, revision, image = prepare_workspace(tmp_path)
    patched_output = tmp_path / "patched.iso"
    reverted_output = tmp_path / "reverted.iso"
    patch = BytePatch(
        patch_id="boot-byte",
        path=BOOT_PATH,
        file_offset=5,
        expected=b"C",
        replacement=b"X",
    )

    rebuild_image(
        reference,
        workspace,
        patched_output,
        revision,
        BuildPlan(revision_id="fixture-v1", patches=(patch,)),
    )
    reverted = rebuild_image(
        reference,
        workspace,
        reverted_output,
        revision,
        BuildPlan.empty("fixture-v1"),
    )

    assert patched_output.read_bytes() != image
    assert reverted_output.read_bytes() == image
    assert reverted.no_change


def test_stale_guard_and_invalid_patch_abort_before_output(tmp_path: Path) -> None:
    reference, workspace, revision, _image = prepare_workspace(tmp_path)

    invalid_patches = [
        (
            BytePatch("stale", BOOT_PATH, 5, b"Z", b"X"),
            "expected original bytes differ",
        ),
        (
            BytePatch("unknown", "missing.bin", 0, b"A", b"B"),
            "patch file does not exist",
        ),
        (
            BytePatch("range", BOOT_PATH, 999, b"A", b"B"),
            "patch range is outside file",
        ),
        (
            BytePatch("length", BOOT_PATH, 0, b"A", b"BB"),
            "replacement length differs",
        ),
    ]
    for index, (patch, message) in enumerate(invalid_patches):
        output = tmp_path / f"invalid-{index}.iso"
        with pytest.raises(BuildError, match=message):
            rebuild_image(
                reference,
                workspace,
                output,
                revision,
                BuildPlan(revision_id="fixture-v1", patches=(patch,)),
            )
        assert not output.exists()


def test_overlapping_or_duplicate_patches_are_rejected(tmp_path: Path) -> None:
    reference, workspace, revision, _image = prepare_workspace(tmp_path)
    output = tmp_path / "invalid.iso"
    overlapping = BuildPlan(
        revision_id="fixture-v1",
        patches=(
            BytePatch("first", BOOT_PATH, 0, b"BO", b"XY"),
            BytePatch("second", BOOT_PATH, 1, b"OO", b"ZZ"),
        ),
    )

    with pytest.raises(BuildError, match="overlapping patches"):
        rebuild_image(reference, workspace, output, revision, overlapping)
    with pytest.raises(ValueError, match="duplicate patch id"):
        BuildPlan(
            revision_id="fixture-v1",
            patches=(
                BytePatch("same", BOOT_PATH, 0, b"B", b"X"),
                BytePatch("same", BOOT_PATH, 1, b"O", b"Y"),
            ),
        )
    assert not output.exists()


def test_existing_output_requires_force_and_is_replaced_atomically(tmp_path: Path) -> None:
    reference, workspace, revision, image = prepare_workspace(tmp_path)
    output = tmp_path / "rebuilt.iso"
    output.write_bytes(b"existing")

    with pytest.raises(FileExistsError):
        rebuild_image(
            reference,
            workspace,
            output,
            revision,
            BuildPlan.empty("fixture-v1"),
        )
    assert output.read_bytes() == b"existing"

    rebuild_image(
        reference,
        workspace,
        output,
        revision,
        BuildPlan.empty("fixture-v1"),
        force=True,
    )
    assert output.read_bytes() == image


def test_plan_json_is_strict_and_deterministic(tmp_path: Path) -> None:
    path = tmp_path / "plan.json"
    path.write_text(
        json.dumps(
            {
                "patches": [
                    {
                        "expected_hex": "43",
                        "file_offset": 5,
                        "id": "boot-byte",
                        "path": BOOT_PATH,
                        "replacement_hex": "58",
                    }
                ],
                "revision_id": "fixture-v1",
                "schema_version": 1,
            }
        ),
        encoding="utf-8",
    )

    plan = load_build_plan(path)

    assert plan.patches[0].expected == b"C"
    assert plan.patches[0].replacement == b"X"
    assert json.loads(plan.to_json())["patches"][0]["id"] == "boot-byte"
    assert plan.to_json().endswith("\n")


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"schema_version": 2, "revision_id": "fixture-v1", "patches": []},
        {"schema_version": 1, "revision_id": "fixture-v1", "patches": "bad"},
        {
            "schema_version": 1,
            "revision_id": "fixture-v1",
            "patches": [
                {
                    "id": "bad",
                    "path": BOOT_PATH,
                    "file_offset": 0,
                    "expected_hex": "0",
                    "replacement_hex": "00",
                }
            ],
        },
    ],
)
def test_plan_json_rejects_invalid_payloads(tmp_path: Path, payload: object) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="invalid build plan"):
        load_build_plan(path)
