from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath

_REVISION_ID = "ULUS10066-v1.00"
_LOCKED_BOOT_SHA256 = "906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9"

_USRDIR_FILES = (
    "beanim.viv",
    "beload.zlb",
    "bootfonts.txt",
    "bootfonttable.txt",
    "empty.big",
    "feanim.viv",
    "feload.zlb",
    "fonttable.txt",
    "main.big",
    "mainbe.big",
    "mainsystem.big",
    "pad1.pad",
    "realfonts.txt",
    "scranim.viv",
)

_USRDIR_ROOTS = (
    "careermodebe",
    "careermodefe1",
    "careermodefe2",
    "components",
    "contract",
    "data",
    "enviro",
    "fighthype",
    "framework",
    "gamemodesFE",
    "gamemodesbe",
    "hud",
    "icons",
    "menu",
    "mycornerfe",
    "pausemenu",
    "playNowBE",
    "playnowfe",
    "preload",
    "profilemanager",
    "rivalChallenge",
    "rivalChallengeBE",
    "scripts",
    "system",
)


def _git_blob_sha1(root: Path, relative: PurePosixPath) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "hash-object", "--no-filters", "--", relative.as_posix()],
        check=False,
        capture_output=True,
        text=True,
        timeout=30.0,
    )
    digest = result.stdout.strip()
    if result.returncode != 0 or len(digest) != 40:
        diagnostic = result.stderr.strip()
        raise RuntimeError(f"git hash-object failed for {relative.as_posix()}: {diagnostic}")
    return digest


def _entry(root: Path, source: PurePosixPath, destination: PurePosixPath) -> dict[str, object]:
    source_path = root.joinpath(*source.parts)
    if source_path.is_symlink():
        raise RuntimeError(f"payload source is a symlink: {source.as_posix()}")
    if not source_path.is_file():
        raise RuntimeError(f"payload source is missing: {source.as_posix()}")

    role = "padding" if source.suffix.casefold() == ".pad" else "game_data"
    if destination.as_posix().startswith("PSP_GAME/SYSDIR/"):
        role = "metadata"
    if destination.name in {"BOOT.BIN", "EBOOT.BIN"} and destination.parent.name == "SYSDIR":
        role = "executable"

    item: dict[str, object] = {
        "source": source.as_posix(),
        "destination": destination.as_posix(),
        "size": source_path.stat().st_size,
        "git_blob_sha1": _git_blob_sha1(root, source),
        "role": role,
    }
    if source.as_posix() == "BOOT.BIN":
        digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if digest != _LOCKED_BOOT_SHA256:
            raise RuntimeError("BOOT.BIN does not match the locked Fight Night executable")
        item["sha256"] = digest
    return item


def _tree_entries(
    root: Path,
    source_root: PurePosixPath,
    destination_root: PurePosixPath,
) -> list[dict[str, object]]:
    directory = root.joinpath(*source_root.parts)
    if directory.is_symlink() or not directory.is_dir():
        raise RuntimeError(f"payload source root is missing or invalid: {source_root.as_posix()}")
    entries: list[dict[str, object]] = []
    for path in sorted(directory.rglob("*"), key=lambda item: item.as_posix().casefold()):
        if path.is_symlink():
            relative_path = path.relative_to(root).as_posix()
            raise RuntimeError(f"payload tree contains a symlink: {relative_path}")
        if not path.is_file():
            continue
        relative = PurePosixPath(path.relative_to(root).as_posix())
        within_root = relative.relative_to(source_root)
        destination = destination_root / within_root
        entries.append(_entry(root, relative, destination))
    if not entries:
        raise RuntimeError(f"payload source root contains no files: {source_root.as_posix()}")
    return entries


def generate_manifest(repository_root: Path) -> dict[str, object]:
    root = repository_root.resolve(strict=True)
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError("repository root must be a normal directory")

    entries = [
        _entry(root, PurePosixPath("BOOT.BIN"), PurePosixPath("PSP_GAME/SYSDIR/BOOT.BIN")),
        _entry(root, PurePosixPath("EBOOT.BIN"), PurePosixPath("PSP_GAME/SYSDIR/EBOOT.BIN")),
    ]
    entries.extend(
        _tree_entries(
            root,
            PurePosixPath("UPDATE"),
            PurePosixPath("PSP_GAME/SYSDIR/UPDATE"),
        )
    )
    for filename in _USRDIR_FILES:
        source = PurePosixPath(filename)
        entries.append(_entry(root, source, PurePosixPath("PSP_GAME/USRDIR") / source))
    for root_name in _USRDIR_ROOTS:
        source_root = PurePosixPath(root_name)
        entries.extend(
            _tree_entries(
                root,
                source_root,
                PurePosixPath("PSP_GAME/USRDIR") / source_root,
            )
        )

    source_keys = [str(entry["source"]).casefold() for entry in entries]
    destination_keys = [str(entry["destination"]).casefold() for entry in entries]
    if len(source_keys) != len(set(source_keys)):
        raise RuntimeError("generated payload manifest contains duplicate source paths")
    if len(destination_keys) != len(set(destination_keys)):
        raise RuntimeError("generated payload manifest contains duplicate destination paths")

    return {
        "schema_version": 1,
        "revision_id": _REVISION_ID,
        "entries": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the reviewed Fight Night runtime allowlist"
    )
    parser.add_argument("repository_root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    payload = generate_manifest(args.repository_root)
    output: Path = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    total_size = sum(int(entry["size"]) for entry in payload["entries"])
    print(f"runtime-payload: files={len(payload['entries'])} bytes={total_size} output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
