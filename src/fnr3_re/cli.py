from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from uuid import uuid4

from .ea_archive import EaArchive, extract_ea_archive, parse_ea_archive
from .iso import build_workspace, verify_workspace
from .manifests import WorkspaceValidationResult
from .package_gate import ValidationResult, validate_package, validate_registry
from .rebuild import BuildPlan, load_build_plan, rebuild_image
from .refpack import compress_refpack, decompress_refpack
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

    rebuild_parser = subparsers.add_parser("rebuild-image")
    rebuild_parser.add_argument("reference", type=Path)
    rebuild_parser.add_argument("workspace", type=Path)
    rebuild_parser.add_argument("output", type=Path)
    rebuild_parser.add_argument("--revision-config", required=True, type=Path)
    rebuild_parser.add_argument("--plan", type=Path)
    rebuild_parser.add_argument("--report", type=Path)
    rebuild_parser.add_argument("--force", action="store_true")
    rebuild_parser.add_argument("--json", action="store_true", dest="as_json")

    for command in ("refpack-decode", "refpack-encode"):
        codec_parser = subparsers.add_parser(command)
        codec_parser.add_argument("source", type=Path)
        codec_parser.add_argument("destination", type=Path)
        codec_parser.add_argument("--force", action="store_true")

    archive_list_parser = subparsers.add_parser("archive-list")
    archive_list_parser.add_argument("path", type=Path)
    archive_list_parser.add_argument("--json", action="store_true", dest="as_json")

    archive_extract_parser = subparsers.add_parser("archive-extract")
    archive_extract_parser.add_argument("path", type=Path)
    archive_extract_parser.add_argument("destination", type=Path)
    archive_extract_parser.add_argument("--force", action="store_true")
    archive_extract_parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "validate-image":
        image_result = validate_image(args.path, load_reference_revision(args.revision_config))
        _print_image_result(image_result, args.as_json)
        return 0 if image_result.valid else 1
    if args.command == "extract-image":
        workspace_manifest = build_workspace(
            args.image,
            args.workspace,
            load_reference_revision(args.revision_config),
            force=args.force,
        )
        if args.as_json:
            print(workspace_manifest.to_json(), end="")
        else:
            print(
                f"extracted: {args.workspace} "
                f"({len(workspace_manifest.files)} files, "
                f"{len(workspace_manifest.directories)} directories)"
            )
        return 0
    if args.command == "verify-workspace":
        workspace_result = verify_workspace(args.path)
        _print_workspace_result(workspace_result, args.as_json)
        return 0 if workspace_result.valid else 1
    if args.command == "rebuild-image":
        revision = load_reference_revision(args.revision_config)
        plan = load_build_plan(args.plan) if args.plan is not None else BuildPlan.empty(
            revision.revision_id
        )
        build_report = rebuild_image(
            args.reference,
            args.workspace,
            args.output,
            revision,
            plan,
            force=args.force,
            report_path=args.report,
        )
        if args.as_json:
            print(build_report.to_json(), end="")
        else:
            state = "no-change" if build_report.no_change else "patched"
            print(
                f"rebuilt: {args.output} ({state}, "
                f"sha256 {build_report.output_sha256})"
            )
        return 0
    if args.command in {"refpack-decode", "refpack-encode"}:
        source = args.source.read_bytes()
        output = (
            decompress_refpack(source)
            if args.command == "refpack-decode"
            else compress_refpack(source)
        )
        _write_binary_output(args.destination, output, force=args.force)
        print(f"wrote: {args.destination} ({len(output)} bytes)")
        return 0
    if args.command == "archive-list":
        archive = parse_ea_archive(args.path.read_bytes())
        if args.as_json:
            print(_archive_listing_json(archive), end="")
        else:
            print(
                f"{archive.magic.decode('ascii')}: {len(archive.members)} members, "
                f"alignment 0x{archive.alignment:x}"
            )
            for member in archive.members:
                marker = " RefPack" if member.refpack_compressed else ""
                print(
                    f"{member.order:04d} 0x{member.offset:08x} "
                    f"{member.size:10d}{marker:8s} {member.name}"
                )
        return 0
    if args.command == "archive-extract":
        archive = parse_ea_archive(args.path.read_bytes())
        archive_manifest = extract_ea_archive(
            archive, args.destination, force=args.force
        )
        if args.as_json:
            print(json.dumps(archive_manifest, indent=2, sort_keys=True), end="\n")
        else:
            print(
                f"extracted: {args.destination} ({len(archive_manifest)} members)"
            )
        return 0

    validation_result: ValidationResult
    if args.command == "validate-package":
        validation_result = validate_package(args.path)
    else:
        validation_result = validate_registry(args.path)
    _print_validation_result(validation_result, args.as_json)
    return 0 if validation_result.valid else 1


def _write_binary_output(destination: Path, payload: bytes, *, force: bool) -> None:
    if destination.exists() and not force:
        raise FileExistsError(f"output already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp-{uuid4().hex}")
    try:
        temporary.write_bytes(payload)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def _archive_listing_json(archive: EaArchive) -> str:
    return (
        json.dumps(
            {
                "alignment": archive.alignment,
                "header_size": archive.header_size,
                "magic": archive.magic.decode("ascii"),
                "members": [
                    {
                        "name": member.name,
                        "offset": member.offset,
                        "order": member.order,
                        "refpack_compressed": member.refpack_compressed,
                        "sha256": member.sha256,
                        "size": member.size,
                    }
                    for member in archive.members
                ],
                "total_size": archive.total_size,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


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
