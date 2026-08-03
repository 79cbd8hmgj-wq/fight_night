from __future__ import annotations

import os
from pathlib import Path

import pytest

from fnr3_re.iso import build_workspace
from fnr3_re.rebuild import BuildPlan, rebuild_image
from fnr3_re.revision import load_reference_revision

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_CONFIG = ROOT / "config" / "revisions" / "ulus10066-v1.00.json"
CHUNK_SIZE = 1024 * 1024


@pytest.mark.skipif(
    "FNR3_REFERENCE_ISO" not in os.environ,
    reason="FNR3_REFERENCE_ISO is not configured",
)
def test_reference_no_change_rebuild_is_byte_exact(tmp_path: Path) -> None:
    reference = Path(os.environ["FNR3_REFERENCE_ISO"])
    revision = load_reference_revision(REFERENCE_CONFIG)
    workspace = tmp_path / "workspace"
    output = tmp_path / "rebuilt.iso"

    workspace_manifest = build_workspace(reference, workspace, revision)
    report = rebuild_image(
        reference,
        workspace,
        output,
        revision,
        BuildPlan.empty(revision.revision_id),
    )

    assert len(workspace_manifest.files) == 653
    assert len(workspace_manifest.directories) == 71
    assert output.stat().st_size == revision.iso_size
    assert report.no_change
    assert report.changed_files == ()
    assert report.output_sha256 == revision.iso_sha256
    assert files_are_equal(output, reference)


def files_are_equal(first: Path, second: Path) -> bool:
    if first.stat().st_size != second.stat().st_size:
        return False
    with first.open("rb") as first_stream, second.open("rb") as second_stream:
        while True:
            first_chunk = first_stream.read(CHUNK_SIZE)
            second_chunk = second_stream.read(CHUNK_SIZE)
            if first_chunk != second_chunk:
                return False
            if not first_chunk:
                return True
