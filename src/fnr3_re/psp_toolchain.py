from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import import_module, metadata
from types import ModuleType
from typing import Any

EXPECTED_PSPDISASM_REPOSITORY = "https://github.com/79cbd8hmgj-wq/PSP-disassembly-tool.git"
EXPECTED_PSPDISASM_REVISION = "b3a07f4d0880b7933f87a9557b5e0aa3f364fa5a"
EXPECTED_PSPDISASM_VERSION = "0.9.0"


class PspToolchainError(RuntimeError):
    """Raised when the optional PSP analysis toolchain is absent or untrusted."""


@dataclass(frozen=True, slots=True)
class PspToolchainInfo:
    module: ModuleType
    repository: str
    expected_revision: str
    observed_revision: str | None
    package_version: str
    revision_locked: bool


def _direct_url_info(distribution: metadata.Distribution) -> tuple[str | None, str | None]:
    raw = distribution.read_text("direct_url.json")
    if raw is None:
        return None, None
    try:
        payload: Any = json.loads(raw)
    except json.JSONDecodeError:
        return None, None
    if not isinstance(payload, dict):
        return None, None
    url = payload.get("url")
    observed_url = url if isinstance(url, str) else None
    vcs_info = payload.get("vcs_info")
    if not isinstance(vcs_info, dict):
        return observed_url, None
    commit_id = vcs_info.get("commit_id")
    observed_revision = commit_id if isinstance(commit_id, str) else None
    return observed_url, observed_revision


def load_psp_toolchain(*, allow_unpinned: bool) -> PspToolchainInfo:
    try:
        imported = import_module("pspdisasm")
        distribution = metadata.distribution("pspdisasm")
    except (ModuleNotFoundError, metadata.PackageNotFoundError) as exc:
        raise PspToolchainError(
            "PSP module analysis requires the optional psp-analysis dependency"
        ) from exc

    observed_url, observed_revision = _direct_url_info(distribution)
    revision_locked = (
        distribution.version == EXPECTED_PSPDISASM_VERSION
        and observed_revision == EXPECTED_PSPDISASM_REVISION
        and observed_url == EXPECTED_PSPDISASM_REPOSITORY
    )
    if not revision_locked and not allow_unpinned:
        raise PspToolchainError(
            "pspdisasm does not match the locked Phase 7G baseline; install fnr3-re "
            "with the psp-analysis extra or use --allow-unpinned-toolkit for "
            "exploratory local analysis"
        )

    return PspToolchainInfo(
        module=imported,
        repository=EXPECTED_PSPDISASM_REPOSITORY,
        expected_revision=EXPECTED_PSPDISASM_REVISION,
        observed_revision=observed_revision,
        package_version=distribution.version,
        revision_locked=revision_locked,
    )
