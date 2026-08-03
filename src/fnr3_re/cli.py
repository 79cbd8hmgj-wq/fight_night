from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from .iso import build_workspace, verify_workspace
from .manifests import WorkspaceValidationResult
from .package_gate import ValidationResult, validate_package, validate_registry
from .revision import ImageValidationResult, load_reference_revision, validate_image


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fnr3-re")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate-package", "validate-registry"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("path", type=Path)
        subparser.add_argument("--json", action="store_true", dest="as_json")

    image_parser = subparsers.add_parser("validate-image")
    image_parser.add_argument("path", type=Path)
    image_parser.add_argument("--revision-config", required=True, type=Path)
    image_parser.add_argument("--json", action="store_true", dest="as_json")

    extract_parser = subparsers.add_parser("extract-image")
    extract_parser.add_argument("image", type=Path)
    extract_parser.add_argument("workspace", type=Path)
    extract_parser.add_argument("--revision-config", required=True, type=Path)
    extract_parser.add_argument("--force", action="store_true")
    extract_parser.add_argument("--json", action="store_true", dest="as_json")

    workspace_parser = subparsers.add_parser("verify-workspace")
    workspace_parser.add_argument("path", type=Path)
    workspace_parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "validate-image":
        image_result = validate_image(args.path, load_reference_revision(args.revision_config))
        _print_image_result(image_result, args.as_json)
        return 0 if image_result.valid else 1
    if args.command == "extract-image":
        manifest = build_workspace(
            args.image,
            args.workspace,
            load_reference_revision(args.revision_config),
            force=args.force,
        )
        if args.as_json:
            print(manifest.to_json(), end="")
        else:
            print(
                f"extracted: {args.workspace} "
                f"({len(manifest.files)} files, {len(manifest.directories)} directories)"
            )
        return 0
    if args.command == "verify-workspace":
        workspace_result = verify_workspace(args.path)
        _print_workspace_result(workspace_result, args.as_json)
        return 0 if workspace_result.valid else 1

    validation_result: ValidationResult
    if args.command == "validate-package":
        validation_result = validate_package(args.path)
    else:
        validation_result = validate_registry(args.path)
    _print_validation_result(validation_result, args.as_json)
    return 0 if validation_result.valid else 1


def _print_validation_result(result: ValidationResult, as_json: bool) -> None:
    if as_json:
        print(result.to_json(), end="")
    elif result.valid:
        print(f"valid: {result.package}")
    else:
        print(f"invalid: {result.package}")
        for diagnostic in result.diagnostics:
            print(f"- {diagnostic}")


def _print_image_result(result: ImageValidationResult, as_json: bool) -> None:
    if as_json:
        print(result.to_json(), end="")
    elif result.valid:
        print(f"valid: {result.image} ({result.revision_id})")
    else:
        print(f"invalid: {result.image}")
        for diagnostic in result.diagnostics:
            print(f"- {diagnostic}")


def _print_workspace_result(result: WorkspaceValidationResult, as_json: bool) -> None:
    if as_json:
        print(result.to_json(), end="")
    elif result.valid:
        print(f"valid: {result.workspace}")
    else:
        print(f"invalid: {result.workspace}")
        for diagnostic in result.diagnostics:
            print(f"- {diagnostic}")


if __name__ == "__main__":
    raise SystemExit(main())
