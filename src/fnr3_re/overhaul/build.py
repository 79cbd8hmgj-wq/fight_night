"""Overhaul Alpha 1's mod/patch build layer.

This module does **not** reimplement byte-guarded patching, revision
verification, or ISO reconstruction -- that machinery already exists and
is fully tested in :mod:`fnr3_re.revision` and :mod:`fnr3_re.rebuild`
(``BytePatch`` verifies expected original bytes before writing and fails
closed on mismatch; ``rebuild_image`` re-verifies the reference image's
hash, the workspace's own file hashes, and every patched extent's hash
before ever touching an output file, using an atomic temp-file-then-replace
write). This module only wires that existing machinery to Alpha 1's own
build plan.

## "Revert cleanly"

There is nothing to revert in the destructive sense: ``rebuild_image``
never mutates the reference image or the workspace in place -- it always
reads a pristine, hash-verified reference image and writes a brand new
output file. "Revert" is therefore just "rebuild the baseline again"
(:func:`generate_baseline`), which is byte-for-byte the reference image
(``rebuild_image`` asserts this itself: a no-patch build's output hash
must equal ``revision.iso_sha256``, or it raises).

## Why the Alpha 1 build plan is currently empty

This pass performed substantial static RE (see
``docs/overhaul/alpha1/README.md``) but did not establish a safe,
evidence-backed byte-level patch site for any of the still-unresolved
original gameplay formulas (stamina cost, damage/hit-resolution, the AI
decision loop, the per-round judging formula). Per this milestone's own
instructions ("do not patch unidentified fields... do not overwrite
unresolved original behavior blindly"), the Alpha 1 build plan
intentionally has zero patches this pass rather than guessing at any.
The overhaul's own new stamina/damage/AI/judging logic (``fnr3_re.overhaul.
stamina`` etc.) is implemented and tested as a standalone rules engine,
ready to be wired in via real patches once a safe injection point is
proven for each.
"""

from __future__ import annotations

from pathlib import Path

from fnr3_re.rebuild import BuildPlan, BuildReport, load_build_plan, rebuild_image
from fnr3_re.revision import ReferenceRevision, load_reference_revision

ALPHA1_REVISION_PATH = Path("config/revisions/ulus10066-v1.00.json")
ALPHA1_BUILD_PLAN_PATH = Path("config/overhaul/alpha1/build_plan.json")


def load_alpha1_revision(revision_path: Path = ALPHA1_REVISION_PATH) -> ReferenceRevision:
    return load_reference_revision(revision_path)


def load_alpha1_build_plan(plan_path: Path = ALPHA1_BUILD_PLAN_PATH) -> BuildPlan:
    return load_build_plan(plan_path)


def generate_baseline(
    reference_image: Path,
    workspace: Path,
    output: Path,
    *,
    revision_path: Path = ALPHA1_REVISION_PATH,
    force: bool = False,
) -> BuildReport:
    """Rebuild the unmodified baseline (zero patches applied)."""

    revision = load_alpha1_revision(revision_path)
    empty_plan = BuildPlan.empty(revision.revision_id)
    return rebuild_image(reference_image, workspace, output, revision, empty_plan, force=force)


def generate_alpha_build(
    reference_image: Path,
    workspace: Path,
    output: Path,
    *,
    revision_path: Path = ALPHA1_REVISION_PATH,
    plan_path: Path = ALPHA1_BUILD_PLAN_PATH,
    force: bool = False,
) -> BuildReport:
    """Rebuild the Alpha 1 overhaul build (applies ``build_plan.json``)."""

    revision = load_alpha1_revision(revision_path)
    plan = load_alpha1_build_plan(plan_path)
    return rebuild_image(reference_image, workspace, output, revision, plan, force=force)
