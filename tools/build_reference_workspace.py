from __future__ import annotations

import argparse
from pathlib import Path

from fnr3_re.iso import build_workspace, verify_workspace
from fnr3_re.revision import load_reference_revision

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVISION = ROOT / "config" / "revisions" / "ulus10066-v1.00.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate ULUS10066 and create a deterministic local research workspace."
    )
    parser.add_argument("image", type=Path)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--revision-config", type=Path, default=DEFAULT_REVISION)
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest = build_workspace(
        args.image,
        args.workspace,
        load_reference_revision(args.revision_config),
        force=args.force,
    )
    verification = verify_workspace(args.workspace)
    if not verification.valid:
        for diagnostic in verification.diagnostics:
            print(f"- {diagnostic}")
        return 1
    print(
        f"workspace ready: {args.workspace} "
        f"({len(manifest.files)} files, {len(manifest.directories)} directories)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
