from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .evidence import EvidenceClaim

LOCKED_DECOMPILATION_GATE = (
    "Before overhaul implementation begins, every system modified by the overhaul—and "
    "every system that owns, stores, calls, displays, saves, or consumes its data—must "
    "be functionally reverse-engineered to a verified replacement boundary."
)

REQUIRED_PACKAGE_FILES = frozenset(
    {
        "README.md",
        "status.json",
        "ownership.json",
        "symbols.csv",
        "fields.csv",
        "enums.csv",
        "callers.csv",
        "consumers.csv",
        "evidence.jsonl",
        "lifecycle.md",
        "original-behavior.md",
        "replacement-boundary.md",
        "risks.md",
        "verification.md",
    }
)
REQUIRED_LIFECYCLE_PHASES = frozenset(
    {"initialization", "first_use", "repeated_use", "reset", "destruction", "alternate_path"}
)


@dataclass(frozen=True, slots=True)
class ValidationResult:
    package: Path
    valid: bool
    diagnostics: tuple[str, ...]

    def to_json(self) -> str:
        return json.dumps(
            {
                "diagnostics": list(self.diagnostics),
                "package": str(self.package),
                "valid": self.valid,
            },
            indent=2,
            sort_keys=True,
        ) + "\n"


def validate_package(package: Path) -> ValidationResult:
    diagnostics: set[str] = set()
    if not package.is_dir():
        diagnostics.add("package directory does not exist")
        return _result(package, diagnostics)

    present = {item.name for item in package.iterdir() if item.is_file()}
    for missing in REQUIRED_PACKAGE_FILES - present:
        diagnostics.add(f"missing package file: {missing}")

    status = _load_json_object(package / "status.json", diagnostics, "status.json")
    if status is not None:
        _validate_complete_status(status, diagnostics)

    evidence_path = package / "evidence.jsonl"
    if evidence_path.is_file():
        _validate_evidence_jsonl(evidence_path, diagnostics)

    return _result(package, diagnostics)


def _validate_complete_status(status: Mapping[str, Any], diagnostics: set[str]) -> None:
    if status.get("status") != "complete":
        diagnostics.add("package status is not complete")
    blockers = status.get("blocking_unknowns")
    if not isinstance(blockers, list):
        diagnostics.add("blocking_unknowns must be a list")
    elif blockers:
        diagnostics.add("blocking unknowns remain: " + ", ".join(str(item) for item in blockers))

    lifecycle = status.get("lifecycle_evidence")
    if not isinstance(lifecycle, Mapping):
        for phase in REQUIRED_LIFECYCLE_PHASES:
            diagnostics.add(f"missing lifecycle evidence: {phase}")
    else:
        for phase in REQUIRED_LIFECYCLE_PHASES:
            if lifecycle.get(phase) is not True:
                diagnostics.add(f"missing lifecycle evidence: {phase}")

    tests = status.get("tests")
    if not isinstance(tests, list) or not tests:
        diagnostics.add("original-behavior tests are missing")
    consumers = status.get("consumer_inventory")
    if not isinstance(consumers, list) or not consumers:
        diagnostics.add("consumer inventory is empty")
    for key in ("fallback", "rollback"):
        value = status.get(key)
        if not isinstance(value, str) or not value.strip():
            diagnostics.add(f"{key} is missing")


def _validate_evidence_jsonl(path: Path, diagnostics: set[str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        diagnostics.add("evidence.jsonl is empty")
        return
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            diagnostics.add(f"evidence.jsonl line {line_number} is empty")
            continue
        try:
            payload = json.loads(line)
            if not isinstance(payload, Mapping):
                raise ValueError("claim must be an object")
            EvidenceClaim.from_mapping(payload)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            diagnostics.add(f"invalid evidence.jsonl line {line_number}: {exc}")


def validate_registry(path: Path) -> ValidationResult:
    diagnostics: set[str] = set()
    registry = _load_json_object(path, diagnostics, "registry")
    if registry is None:
        return _result(path, diagnostics)

    if registry.get("decompilation_gate") != LOCKED_DECOMPILATION_GATE:
        diagnostics.add("registry decompilation gate does not match the locked rule")

    systems_raw = registry.get("systems")
    if not isinstance(systems_raw, list):
        diagnostics.add("registry systems must be a list")
        return _result(path, diagnostics)
    systems = [item for item in systems_raw if isinstance(item, Mapping)]
    if len(systems) != len(systems_raw):
        diagnostics.add("registry systems must contain objects")

    ids = [item.get("id") for item in systems]
    string_ids = [item for item in ids if isinstance(item, str) and item]
    if len(string_ids) != len(ids):
        diagnostics.add("every registry system requires a non-empty id")
    if len(string_ids) != len(set(string_ids)):
        diagnostics.add("registry system ids must be unique")
    registered = set(string_ids)

    allowed_classes = _string_set(registry.get("allowed_scope_classes"))
    allowed_statuses = _string_set(registry.get("allowed_package_statuses"))
    feature_raw = registry.get("phase2_features")
    features = feature_raw if isinstance(feature_raw, list) else []
    feature_ids = {
        item.get("id")
        for item in features
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }
    by_id = {
        system_id: system
        for system in systems
        if isinstance((system_id := system.get("id")), str)
    }

    for system in systems:
        system_id = system.get("id")
        if not isinstance(system_id, str):
            continue
        if system.get("scope_class") not in allowed_classes:
            diagnostics.add(f"{system_id} has unknown scope class: {system.get('scope_class')}")
        if system.get("status") not in allowed_statuses:
            diagnostics.add(f"{system_id} has unknown status: {system.get('status')}")
        for relation in ("dependencies", "consumers"):
            values = system.get(relation)
            if not isinstance(values, list):
                diagnostics.add(f"{system_id} {relation} must be a list")
                continue
            for value in values:
                if value not in registered:
                    singular = {"dependencies": "dependency", "consumers": "consumer"}[relation]
                    diagnostics.add(f"{system_id} has unknown {singular}: {value}")
        linked_features = system.get("phase2_features")
        if not isinstance(linked_features, list):
            diagnostics.add(f"{system_id} phase2_features must be a list")
        else:
            for feature in linked_features:
                if feature not in feature_ids:
                    diagnostics.add(f"{system_id} has unknown Phase II feature: {feature}")

        dependencies = system.get("dependencies")
        if isinstance(dependencies, list):
            for dependency_id in dependencies:
                dependency = by_id.get(dependency_id)
                if dependency is None:
                    continue
                consumers = dependency.get("consumers")
                if not isinstance(consumers, list) or system_id not in consumers:
                    diagnostics.add(f"{dependency_id} is missing reverse consumer: {system_id}")
        consumers = system.get("consumers")
        if isinstance(consumers, list):
            for consumer_id in consumers:
                consumer = by_id.get(consumer_id)
                if consumer is None:
                    continue
                dependencies = consumer.get("dependencies")
                if not isinstance(dependencies, list) or system_id not in dependencies:
                    diagnostics.add(f"{consumer_id} is missing reverse dependency: {system_id}")

    global_gates = {
        "program-00",
        "program-01",
        "program-02",
        "program-03",
        "program-29",
        "program-30",
    }
    for feature in features:
        if not isinstance(feature, Mapping):
            diagnostics.add("Phase II features must contain objects")
            continue
        feature_id = feature.get("id")
        requires = feature.get("requires")
        if not isinstance(feature_id, str) or not feature_id:
            diagnostics.add("Phase II feature requires a non-empty id")
            continue
        if not isinstance(requires, list) or not requires:
            diagnostics.add(f"{feature_id} requires a non-empty dependency list")
            continue
        for dependency in requires:
            if dependency not in registered:
                diagnostics.add(f"{feature_id} requires unknown system: {dependency}")
        for missing_gate in sorted(global_gates - set(requires)):
            diagnostics.add(f"{feature_id} omits global gate: {missing_gate}")

    project = registry.get("project")
    if not isinstance(project, Mapping):
        diagnostics.add("registry project must be an object")
    else:
        if project.get("current_phase") != "I":
            diagnostics.add("registry current phase must be I")
        if project.get("phase2_gate") != "blocked":
            diagnostics.add("registry Phase II gate must be blocked")

    return _result(path, diagnostics)


def _load_json_object(
    path: Path, diagnostics: set[str], label: str
) -> Mapping[str, Any] | None:
    if not path.is_file():
        diagnostics.add(f"{label} is missing")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        diagnostics.add(f"invalid {label}: {exc}")
        return None
    if not isinstance(payload, Mapping):
        diagnostics.add(f"{label} must be an object")
        return None
    return payload


def _string_set(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str)}


def _result(path: Path, diagnostics: set[str]) -> ValidationResult:
    ordered = tuple(sorted(diagnostics))
    return ValidationResult(package=path, valid=not ordered, diagnostics=ordered)
