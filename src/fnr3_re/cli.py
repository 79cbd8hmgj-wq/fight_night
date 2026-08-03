from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from .package_gate import ValidationResult, validate_package, validate_registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fnr3-re")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate-package", "validate-registry"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("path", type=Path)
        subparser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result: ValidationResult
    if args.command == "validate-package":
        result = validate_package(args.path)
    else:
        result = validate_registry(args.path)

    if args.as_json:
        print(result.to_json(), end="")
    elif result.valid:
        print(f"valid: {result.package}")
    else:
        print(f"invalid: {result.package}")
        for diagnostic in result.diagnostics:
            print(f"- {diagnostic}")
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
