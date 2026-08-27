from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from fnr3_re.psp_toolchain import (
    EXPECTED_PSPDISASM_REVISION,
    PspToolchainError,
    load_psp_toolchain,
)


class _FakeDistribution:
    def __init__(self, *, version: str, commit_id: str | None) -> None:
        self.version = version
        self._commit_id = commit_id

    def read_text(self, filename: str) -> str | None:
        if filename != "direct_url.json" or self._commit_id is None:
            return None
        return json.dumps(
            {
                "url": "https://github.com/79cbd8hmgj-wq/PSP-disassembly-tool.git",
                "vcs_info": {
                    "commit_id": self._commit_id,
                    "vcs": "git",
                },
            }
        )


def _install_fake_toolchain(monkeypatch: pytest.MonkeyPatch, *, version: str, commit_id: str | None) -> object:
    module = SimpleNamespace(__version__=version)
    monkeypatch.setattr("fnr3_re.psp_toolchain.import_module", lambda name: module)
    monkeypatch.setattr(
        "fnr3_re.psp_toolchain.metadata.distribution",
        lambda name: _FakeDistribution(version=version, commit_id=commit_id),
    )
    return module


def test_missing_toolkit_is_actionable(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(name: str) -> object:
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("fnr3_re.psp_toolchain.import_module", missing)
    with pytest.raises(PspToolchainError, match="psp-analysis"):
        load_psp_toolchain(allow_unpinned=False)


def test_exact_revision_is_locked(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _install_fake_toolchain(
        monkeypatch,
        version="0.9.0",
        commit_id=EXPECTED_PSPDISASM_REVISION,
    )
    info = load_psp_toolchain(allow_unpinned=False)

    assert info.module is module
    assert info.package_version == "0.9.0"
    assert info.observed_revision == EXPECTED_PSPDISASM_REVISION
    assert info.revision_locked is True


def test_mismatched_revision_is_rejected_in_strict_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_toolchain(monkeypatch, version="0.9.0", commit_id="1" * 40)

    with pytest.raises(PspToolchainError, match="locked Phase 7G baseline"):
        load_psp_toolchain(allow_unpinned=False)


def test_unpinned_install_requires_explicit_override(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_toolchain(monkeypatch, version="0.9.0", commit_id=None)

    with pytest.raises(PspToolchainError, match="locked Phase 7G baseline"):
        load_psp_toolchain(allow_unpinned=False)

    info = load_psp_toolchain(allow_unpinned=True)
    assert info.revision_locked is False
    assert info.observed_revision is None
