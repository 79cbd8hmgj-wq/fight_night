from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from fnr3_re.ppsspp_bundle import (
    DebuggerBundleProfile,
    PpssppBundleError,
    verify_ppsspp_bundle,
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_bundle(root: Path) -> DebuggerBundleProfile:
    root.mkdir()
    (root / "bin").mkdir()
    files = {
        root / "PPSSPPSDL": b"fixture-sdl",
        root / "PPSSPPHeadless": b"fixture-headless",
        root / "bin" / "Xvfb": b"fixture-xvfb",
        root / "launch-debug.sh": b"#!/bin/sh\nexit 0\n",
        root / "ppsspp_ws.py": b"#!/usr/bin/env python3\n",
    }
    for path, payload in files.items():
        path.write_bytes(payload)
        path.chmod(0o755)
    (root / "ppsspp-resolved-revision.txt").write_text(
        "fixture-revision\n", encoding="utf-8"
    )
    (root / "ppsspp-debug.ini").write_text(
        """[General]
RemoteDebuggerOnStartup = True
RemoteDebuggerLocal = True
RemoteISOPort = 56244
""",
        encoding="utf-8",
    )
    return DebuggerBundleProfile(
        revision="fixture-revision",
        sdl_sha256=_sha256(files[root / "PPSSPPSDL"]),
        headless_sha256=_sha256(files[root / "PPSSPPHeadless"]),
        xvfb_sha256=_sha256(files[root / "bin" / "Xvfb"]),
        default_port=56244,
    )


def test_verifies_exact_external_debugger_bundle(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    profile = _write_bundle(bundle)

    identity = verify_ppsspp_bundle(bundle, profile=profile)

    assert identity.root == bundle.resolve()
    assert identity.revision == "fixture-revision"
    assert identity.sdl_sha256 == profile.sdl_sha256
    assert identity.headless_sha256 == profile.headless_sha256
    assert identity.xvfb_sha256 == profile.xvfb_sha256
    assert identity.launcher_path == (bundle / "launch-debug.sh").resolve()
    assert identity.client_path == (bundle / "ppsspp_ws.py").resolve()
    assert identity.host == "127.0.0.1"
    assert identity.port == 56244


def test_rejects_wrong_revision_or_binary_hash(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    profile = _write_bundle(bundle)

    (bundle / "ppsspp-resolved-revision.txt").write_text("wrong\n", encoding="utf-8")
    with pytest.raises(PpssppBundleError, match="revision"):
        verify_ppsspp_bundle(bundle, profile=profile)

    (bundle / "ppsspp-resolved-revision.txt").write_text(
        "fixture-revision\n", encoding="utf-8"
    )
    (bundle / "PPSSPPSDL").write_bytes(b"changed")
    with pytest.raises(PpssppBundleError, match="PPSSPPSDL hash mismatch"):
        verify_ppsspp_bundle(bundle, profile=profile)


def test_rejects_missing_or_symlinked_required_paths(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    profile = _write_bundle(bundle)

    (bundle / "ppsspp_ws.py").unlink()
    with pytest.raises(PpssppBundleError, match="required bundle file"):
        verify_ppsspp_bundle(bundle, profile=profile)

    (bundle / "ppsspp_ws.py").symlink_to(bundle / "launch-debug.sh")
    with pytest.raises(PpssppBundleError, match="symlink"):
        verify_ppsspp_bundle(bundle, profile=profile)


def test_rejects_nonlocal_or_malformed_debugger_configuration(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    profile = _write_bundle(bundle)
    config = bundle / "ppsspp-debug.ini"

    config.write_text(
        """[General]
RemoteDebuggerOnStartup = True
RemoteDebuggerLocal = False
RemoteISOPort = 56244
""",
        encoding="utf-8",
    )
    with pytest.raises(PpssppBundleError, match="local-only"):
        verify_ppsspp_bundle(bundle, profile=profile)

    config.write_text(
        """[General]
RemoteDebuggerOnStartup = True
RemoteDebuggerLocal = True
RemoteISOPort = not-a-port
""",
        encoding="utf-8",
    )
    with pytest.raises(PpssppBundleError, match="RemoteISOPort"):
        verify_ppsspp_bundle(bundle, profile=profile)


def test_rejects_unexpected_bundle_port_for_locked_profile(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    profile = _write_bundle(bundle)
    (bundle / "ppsspp-debug.ini").write_text(
        """[General]
RemoteDebuggerOnStartup = True
RemoteDebuggerLocal = True
RemoteISOPort = 56245
""",
        encoding="utf-8",
    )

    with pytest.raises(PpssppBundleError, match="expected debugger port"):
        verify_ppsspp_bundle(bundle, profile=profile)
