from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_python_project_enables_strict_quality_gates() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert config["project"]["requires-python"] == ">=3.11"
    assert config["project"]["scripts"]["fnr3-re"] == "fnr3_re.cli:main"
    assert config["tool"]["mypy"]["strict"] is True
    assert set(config["tool"]["ruff"]["lint"]["select"]) >= {"E", "F", "I", "UP", "B"}
    dev_dependencies = config["project"]["optional-dependencies"]["dev"]
    assert {dependency.split(">=")[0] for dependency in dev_dependencies} >= {
        "mypy",
        "pytest",
        "ruff",
    }


def test_python_ci_runs_tests_lint_and_type_checks() -> None:
    workflow = ROOT / ".github" / "workflows" / "python-ci.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "pull_request:" in text
    assert 'python-version: "3.11"' in text
    assert 'pip install -e ".[dev]"' in text
    assert "python -m pytest" in text
    assert "python -m ruff check" in text
    assert "python -m mypy" in text
