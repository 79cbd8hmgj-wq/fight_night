from __future__ import annotations

import configparser
import hashlib
from dataclasses import dataclass
from pathlib import Path


class PpssppBundleError(ValueError):
    """Raised when an external PPSSPP debugger bundle is invalid or untrusted."""


@dataclass(frozen=True, slots=True)
class DebuggerBundleProfile:
    revision: str
    sdl_sha256: str
    headless_sha256: str
    xvfb_sha256: str
    default_port: int


@dataclass(frozen=True, slots=True)
class DebuggerBundleIdentity:
    root: Path
    revision: str
    sdl_path: Path
    sdl_sha256: str
    headless_path: Path
    headless_sha256: str
    xvfb_path: Path
    xvfb_sha256: str
    launcher_path: Path
    client_path: Path
    config_path: Path
    host: str
    port: int


FNR3_DEBUGGER_BUNDLE_PROFILE = DebuggerBundleProfile(
    revision="fa50bb1976065c4f8b1b47af227d367fe9771555",
    sdl_sha256="143d0d8f89ff5cbe5e65d66efe447a1f0510e376685a7f217cbb581fcf323c06",
    headless_sha256="623a661cd5b26a34194faf3896925c9da48eb20107306435a959472b3a0813f6",
    xvfb_sha256="2c7f5a9534410fed5092d782a69ca7ffd9fce80e98b81ffe4944d703dd11d3b1",
    default_port=56244,
)


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _required_file(root: Path, relative: str) -> Path:
    path = root / relative
    if path.is_symlink():
        raise PpssppBundleError(f"required bundle file must not be a symlink: {relative}")
    if not path.is_file():
        raise PpssppBundleError(f"required bundle file is missing: {relative}")
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise PpssppBundleError(f"required bundle file escapes bundle root: {relative}") from exc
    return resolved


def _require_hash(path: Path, expected: str, label: str) -> str:
    observed = _hash_file(path)
    if observed != expected:
        raise PpssppBundleError(
            f"{label} hash mismatch: expected {expected}, observed {observed}"
        )
    return observed


def _read_debugger_port(config_path: Path, expected_port: int) -> int:
    parser = configparser.ConfigParser()
    try:
        with config_path.open("r", encoding="utf-8") as stream:
            parser.read_file(stream)
    except (OSError, configparser.Error) as exc:
        raise PpssppBundleError(f"invalid ppsspp-debug.ini: {exc}") from exc
    if not parser.has_section("General"):
        raise PpssppBundleError("ppsspp-debug.ini is missing [General]")
    try:
        on_startup = parser.getboolean("General", "RemoteDebuggerOnStartup")
        local_only = parser.getboolean("General", "RemoteDebuggerLocal")
        port = parser.getint("General", "RemoteISOPort")
    except (ValueError, configparser.Error) as exc:
        raise PpssppBundleError(f"invalid RemoteISOPort/debugger configuration: {exc}") from exc
    if not on_startup:
        raise PpssppBundleError("remote debugger must start automatically")
    if not local_only:
        raise PpssppBundleError("remote debugger must be local-only")
    if not 1 <= port <= 65535:
        raise PpssppBundleError("RemoteISOPort must be between 1 and 65535")
    if port != expected_port:
        raise PpssppBundleError(
            f"expected debugger port {expected_port}, observed {port}"
        )
    return port


def verify_ppsspp_bundle(
    root: Path,
    *,
    profile: DebuggerBundleProfile = FNR3_DEBUGGER_BUNDLE_PROFILE,
) -> DebuggerBundleIdentity:
    if root.is_symlink():
        raise PpssppBundleError("bundle root must not be a symlink")
    resolved_root = root.expanduser().resolve()
    if not resolved_root.is_dir():
        raise PpssppBundleError(f"bundle root is not a directory: {root}")

    revision_path = _required_file(resolved_root, "ppsspp-resolved-revision.txt")
    sdl_path = _required_file(resolved_root, "PPSSPPSDL")
    headless_path = _required_file(resolved_root, "PPSSPPHeadless")
    xvfb_path = _required_file(resolved_root, "bin/Xvfb")
    launcher_path = _required_file(resolved_root, "launch-debug.sh")
    client_path = _required_file(resolved_root, "ppsspp_ws.py")
    config_path = _required_file(resolved_root, "ppsspp-debug.ini")

    revision = revision_path.read_text(encoding="utf-8").strip()
    if revision != profile.revision:
        raise PpssppBundleError(
            f"PPSSPP revision mismatch: expected {profile.revision}, observed {revision}"
        )

    sdl_sha256 = _require_hash(sdl_path, profile.sdl_sha256, "PPSSPPSDL")
    headless_sha256 = _require_hash(
        headless_path, profile.headless_sha256, "PPSSPPHeadless"
    )
    xvfb_sha256 = _require_hash(xvfb_path, profile.xvfb_sha256, "Xvfb")
    port = _read_debugger_port(config_path, profile.default_port)

    return DebuggerBundleIdentity(
        root=resolved_root,
        revision=revision,
        sdl_path=sdl_path,
        sdl_sha256=sdl_sha256,
        headless_path=headless_path,
        headless_sha256=headless_sha256,
        xvfb_path=xvfb_path,
        xvfb_sha256=xvfb_sha256,
        launcher_path=launcher_path,
        client_path=client_path,
        config_path=config_path,
        host="127.0.0.1",
        port=port,
    )
