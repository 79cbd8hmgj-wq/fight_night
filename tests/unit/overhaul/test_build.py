from __future__ import annotations

from pathlib import Path

from fnr3_re.overhaul.build import (
    ALPHA1_BUILD_PLAN_PATH,
    ALPHA1_REVISION_PATH,
    load_alpha1_build_plan,
    load_alpha1_revision,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_alpha1_revision_loads_and_matches_the_tracked_ulus10066_revision() -> None:
    revision = load_alpha1_revision(REPO_ROOT / ALPHA1_REVISION_PATH)
    assert revision.revision_id == "ULUS10066-v1.00"
    assert revision.disc_id == "ULUS10066"


def test_alpha1_build_plan_loads_and_is_currently_empty() -> None:
    plan = load_alpha1_build_plan(REPO_ROOT / ALPHA1_BUILD_PLAN_PATH)
    assert plan.revision_id == "ULUS10066-v1.00"
    # Intentionally empty this pass -- see fnr3_re.overhaul.build's module
    # docstring for why no byte patch was safe to add yet.
    assert plan.patches == ()


def test_alpha1_build_plan_revision_matches_alpha1_revision() -> None:
    revision = load_alpha1_revision(REPO_ROOT / ALPHA1_REVISION_PATH)
    plan = load_alpha1_build_plan(REPO_ROOT / ALPHA1_BUILD_PLAN_PATH)
    assert plan.revision_id == revision.revision_id
