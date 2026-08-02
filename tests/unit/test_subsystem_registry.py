from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "config" / "subsystem_registry.json"
REQUIRED_SYSTEM_FIELDS = {
    "id",
    "name",
    "scope_class",
    "owners",
    "dependencies",
    "consumers",
    "status",
    "blocking_unknowns",
    "package_path",
    "phase2_features",
}


def load_registry() -> dict[str, Any]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_registry_is_deterministically_formatted() -> None:
    raw = REGISTRY_PATH.read_text(encoding="utf-8")
    parsed = json.loads(raw)
    expected = (
        json.dumps(parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    )
    assert raw == expected


def test_registry_covers_every_master_plan_program() -> None:
    registry = load_registry()
    systems = registry["systems"]
    assert isinstance(systems, list)
    program_numbers = {
        system["program"]
        for system in systems
        if isinstance(system, dict) and isinstance(system.get("program"), int)
    }
    assert program_numbers == set(range(31))


def test_system_ids_are_unique_and_required_fields_exist() -> None:
    registry = load_registry()
    systems = registry["systems"]
    assert isinstance(systems, list)
    ids: list[str] = []
    for system in systems:
        assert isinstance(system, dict)
        assert REQUIRED_SYSTEM_FIELDS <= system.keys()
        system_id = system["id"]
        assert isinstance(system_id, str) and system_id
        ids.append(system_id)
    assert len(ids) == len(set(ids))


def test_scope_classes_statuses_and_package_paths_are_valid() -> None:
    registry = load_registry()
    allowed_classes = set(registry["allowed_scope_classes"])
    allowed_classification = set(registry["allowed_classification_statuses"])
    allowed_statuses = set(registry["allowed_package_statuses"])
    systems = registry["systems"]
    assert isinstance(systems, list)
    for system in systems:
        assert system["scope_class"] in allowed_classes
        assert system["classification_status"] in allowed_classification
        assert system["status"] in allowed_statuses
        package_path = system["package_path"]
        assert isinstance(package_path, str) and package_path
        assert not package_path.startswith("/")
        assert ".." not in Path(package_path).parts


def test_dependencies_and_consumers_reference_registered_systems() -> None:
    registry = load_registry()
    systems = registry["systems"]
    assert isinstance(systems, list)
    registered = {system["id"] for system in systems}
    for system in systems:
        for field in ("dependencies", "consumers"):
            references = system[field]
            assert isinstance(references, list)
            missing = set(references) - registered
            assert not missing, f"{system['id']} has unknown {field}: {sorted(missing)}"


def test_phase2_features_are_unique_and_use_registered_dependencies() -> None:
    registry = load_registry()
    systems = registry["systems"]
    features = registry["phase2_features"]
    assert isinstance(systems, list)
    assert isinstance(features, list)
    registered_systems = {system["id"] for system in systems}
    feature_ids = [feature["id"] for feature in features]
    assert len(feature_ids) == len(set(feature_ids))
    for feature in features:
        assert isinstance(feature["id"], str) and feature["id"]
        requires = feature["requires"]
        assert isinstance(requires, list) and requires
        missing = set(requires) - registered_systems
        assert not missing, f"{feature['id']} requires unknown systems: {sorted(missing)}"


def test_every_system_feature_reference_is_registered() -> None:
    registry = load_registry()
    systems = registry["systems"]
    features = registry["phase2_features"]
    assert isinstance(systems, list)
    assert isinstance(features, list)
    registered_features = {feature["id"] for feature in features}
    for system in systems:
        references = system["phase2_features"]
        assert isinstance(references, list)
        missing = set(references) - registered_features
        assert not missing, (
            f"{system['id']} links to unregistered Phase II features: {sorted(missing)}"
        )


def test_phase2_is_blocked_and_phase2_programs_are_not_complete() -> None:
    registry = load_registry()
    project = registry["project"]
    systems = registry["systems"]
    assert isinstance(project, dict)
    assert project["current_phase"] == "I"
    assert project["phase2_gate"] == "blocked"
    for system in systems:
        if system["phase"] == "II":
            assert system["status"] == "blocked"


def test_owners_and_blockers_are_meaningful() -> None:
    registry = load_registry()
    systems = registry["systems"]
    assert isinstance(systems, list)
    for system in systems:
        owners = system["owners"]
        blockers = system["blocking_unknowns"]
        assert isinstance(owners, list) and owners
        assert all(isinstance(owner, str) and owner not in {"?", "unknown"} for owner in owners)
        assert isinstance(blockers, list) and blockers
        assert all(
            isinstance(blocker, str) and blocker not in {"unproven", "unknown"}
            for blocker in blockers
        )


def test_dependency_consumer_links_are_bidirectional() -> None:
    registry = load_registry()
    systems = registry["systems"]
    assert isinstance(systems, list)
    by_id = {system["id"]: system for system in systems}
    for system in systems:
        for dependency_id in system["dependencies"]:
            dependency = by_id[dependency_id]
            assert system["id"] in dependency["consumers"], (
                f"{dependency_id} is missing reverse consumer {system['id']}"
            )
        for consumer_id in system["consumers"]:
            consumer = by_id[consumer_id]
            assert system["id"] in consumer["dependencies"], (
                f"{consumer_id} is not dependent on {system['id']}"
            )


def test_every_phase2_feature_includes_foundation_and_release_gates() -> None:
    registry = load_registry()
    features = registry["phase2_features"]
    assert isinstance(features, list)
    required = {
        "program-00",
        "program-01",
        "program-02",
        "program-03",
        "program-29",
        "program-30",
    }
    for feature in features:
        missing = required - set(feature["requires"])
        assert not missing, f"{feature['id']} omits global gates: {sorted(missing)}"


EXACT_DECOMPILATION_GATE = (
    "Before overhaul implementation begins, every system modified by the overhaul—and "
    "every system that owns, stores, calls, displays, saves, or consumes its data—must "
    "be functionally reverse-engineered to a verified replacement boundary."
)


def test_exact_decompilation_gate_is_locked_in_docs_and_registry() -> None:
    registry = load_registry()
    assert registry["decompilation_gate"] == EXACT_DECOMPILATION_GATE
    gate_doc = (ROOT / "docs" / "architecture" / "decompilation-gate.md").read_text(
        encoding="utf-8"
    )
    assert EXACT_DECOMPILATION_GATE in gate_doc
