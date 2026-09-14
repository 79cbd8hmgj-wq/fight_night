"""Generic JSON load/save for simple flat tunables dataclasses.

Kept separate from the tunables dataclasses themselves so that "tunable
overhaul parameters" (data) and "how tunables are stored" (this small bit
of I/O machinery) stay in different files, per this milestone's
instruction to separate tunable parameters from patching/build machinery
where feasible.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")


def save_tunables(tunables: Any, path: Path) -> None:
    path.write_text(
        json.dumps(asdict(tunables), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_tunables(cls: type[T], path: Path) -> T:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid tunables file {path}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError(f"tunables file {path} root must be an object")
    return cls(**payload)
