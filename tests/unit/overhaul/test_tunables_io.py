from __future__ import annotations

from pathlib import Path

import pytest

from fnr3_re.overhaul.ai import AIPolicyTunables
from fnr3_re.overhaul.damage import DamageTunables
from fnr3_re.overhaul.judging import JudgingTunables
from fnr3_re.overhaul.stamina import StaminaTunables

REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = REPO_ROOT / "config" / "overhaul" / "alpha1"


def test_stamina_tunables_round_trip(tmp_path: Path) -> None:
    tunables = StaminaTunables(base_capacity=120.0)
    path = tmp_path / "stamina.json"
    tunables.save(path)
    loaded = StaminaTunables.load(path)
    assert loaded.base_capacity == 120.0
    assert loaded.resolved_action_costs() == tunables.resolved_action_costs()


def test_damage_tunables_round_trip(tmp_path: Path) -> None:
    tunables = DamageTunables(base_health=150.0)
    path = tmp_path / "damage.json"
    tunables.save(path)
    assert DamageTunables.load(path) == tunables


def test_judging_tunables_round_trip_preserves_bias_as_tuple(tmp_path: Path) -> None:
    tunables = JudgingTunables(per_judge_bias=(0.1, -0.2, 0.0))
    path = tmp_path / "judging.json"
    tunables.save(path)
    loaded = JudgingTunables.load(path)
    assert loaded.per_judge_bias == (0.1, -0.2, 0.0)
    assert isinstance(loaded.per_judge_bias, tuple)


def test_ai_policy_tunables_round_trip(tmp_path: Path) -> None:
    tunables = AIPolicyTunables(low_stamina_fraction=0.4)
    path = tmp_path / "ai.json"
    tunables.save(path)
    assert AIPolicyTunables.load(path) == tunables


@pytest.mark.parametrize(
    "filename,cls",
    [
        ("stamina_tunables.json", StaminaTunables),
        ("damage_tunables.json", DamageTunables),
        ("judging_tunables.json", JudgingTunables),
        ("ai_policy_tunables.json", AIPolicyTunables),
    ],
)
def test_repository_tunable_configs_load_cleanly(filename: str, cls: type) -> None:
    path = CONFIG_DIR / filename
    assert path.is_file(), f"missing tunables config: {path}"
    loaded = cls.load(path)  # type: ignore[attr-defined]
    assert loaded is not None
