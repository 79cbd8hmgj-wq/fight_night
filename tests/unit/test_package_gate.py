from __future__ import annotations

import json
from pathlib import Path

from fnr3_re.package_gate import validate_package, validate_registry


REQUIRED_PACKAGE_FILES = {
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


def write_complete_package(path: Path) -> None:
    path.mkdir(parents=True)
    status = {
        "system_id": "program-07",
        "scope_class": "A",
        "status": "complete",
        "blocking_unknowns": [],
        "lifecycle_evidence": {
            "initialization": True,
            "first_use": True,
            "repeated_use": True,
            "reset": True,
            "destruction": True,
            "alternate_path": True,
        },
        "tests": ["tests/unit/test_stamina_original.py"],
        "fallback": "Call the original stamina routine.",
        "rollback": "Restore the guarded original call bytes.",
        "consumer_inventory": ["fight", "AI", "HUD"],
    }
    for name in REQUIRED_PACKAGE_FILES:
        target = path / name
        if name == "status.json":
            target.write_text(json.dumps(status, sort_keys=True) + "\n", encoding="utf-8")
        elif name.endswith(".csv"):
            target.write_text("id,name\n1,example\n", encoding="utf-8")
        elif name == "evidence.jsonl":
            target.write_text(
                json.dumps(
                    {
                        "claim_id": "stamina-field",
                        "question": "Which field stores current stamina?",
                        "source_revision": "ULUS10066-v1.00",
                        "module": "BOOT.BIN",
                        "confidence": "CONFIRMED",
                        "evidence_types": ["exact_binary", "runtime_capture"],
                        "addresses": [{"address_type": "runtime", "value": 0x08810000}],
                        "conclusion": "Confirmed field.",
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
        else:
            target.write_text(f"# {name}\n\nDocumented.\n", encoding="utf-8")


def test_incomplete_package_reports_specific_sorted_diagnostics(tmp_path: Path) -> None:
    package = tmp_path / "stamina"
    package.mkdir()
    (package / "status.json").write_text(
        json.dumps(
            {
                "system_id": "program-07",
                "scope_class": "A",
                "status": "complete",
                "blocking_unknowns": ["AI reader unresolved"],
                "lifecycle_evidence": {"initialization": True},
                "tests": [],
                "fallback": "",
                "rollback": "",
                "consumer_inventory": [],
            }
        ),
        encoding="utf-8",
    )

    result = validate_package(package)

    assert not result.valid
    assert result.diagnostics == tuple(sorted(result.diagnostics))
    assert "blocking unknowns remain: AI reader unresolved" in result.diagnostics
    assert "consumer inventory is empty" in result.diagnostics
    assert "fallback is missing" in result.diagnostics
    assert "original-behavior tests are missing" in result.diagnostics
    assert "rollback is missing" in result.diagnostics
    assert any(item.startswith("missing package file:") for item in result.diagnostics)
    assert any(item.startswith("missing lifecycle evidence:") for item in result.diagnostics)


def test_complete_package_passes_deterministically(tmp_path: Path) -> None:
    package = tmp_path / "stamina"
    write_complete_package(package)

    first = validate_package(package)
    second = validate_package(package)

    assert first.valid
    assert first.diagnostics == ()
    assert first.to_json() == second.to_json()
    assert json.loads(first.to_json()) == {
        "diagnostics": [],
        "package": str(package),
        "valid": True,
    }


def test_registry_validation_uses_task1_contract(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    registry = tmp_path / "registry.json"
    registry.write_text(
        (root / "config" / "subsystem_registry.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    result = validate_registry(registry)
    assert result.valid

    payload = json.loads(registry.read_text(encoding="utf-8"))
    payload["systems"][0]["dependencies"] = ["missing-system"]
    registry.write_text(json.dumps(payload), encoding="utf-8")
    result = validate_registry(registry)
    assert not result.valid
    assert "program-00 has unknown dependency: missing-system" in result.diagnostics


def test_registry_validation_rejects_one_way_dependency_links(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    registry = tmp_path / "registry.json"
    payload = json.loads(
        (root / "config" / "subsystem_registry.json").read_text(encoding="utf-8")
    )
    payload["systems"][0]["consumers"].remove("program-01")
    registry.write_text(json.dumps(payload), encoding="utf-8")

    result = validate_registry(registry)

    assert not result.valid
    assert "program-00 is missing reverse consumer: program-01" in result.diagnostics


def test_registry_validation_rejects_phase2_feature_without_global_gate(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    registry = tmp_path / "registry.json"
    payload = json.loads(
        (root / "config" / "subsystem_registry.json").read_text(encoding="utf-8")
    )
    payload["phase2_features"][0]["requires"].remove("program-02")
    registry.write_text(json.dumps(payload), encoding="utf-8")

    result = validate_registry(registry)

    assert not result.valid
    assert "combat omits global gate: program-02" in result.diagnostics


def test_registry_validation_rejects_modified_decompilation_gate(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    registry = tmp_path / "registry.json"
    payload = json.loads(
        (root / "config" / "subsystem_registry.json").read_text(encoding="utf-8")
    )
    payload["decompilation_gate"] = "A weaker rule."
    registry.write_text(json.dumps(payload), encoding="utf-8")

    result = validate_registry(registry)

    assert not result.valid
    assert "registry decompilation gate does not match the locked rule" in result.diagnostics
