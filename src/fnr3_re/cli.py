from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from uuid import uuid4

from .ea_archive import EaArchive, extract_ea_archive, parse_ea_archive
from .iso import build_workspace, verify_workspace
from .manifests import WorkspaceValidationResult
from .module_map import build_workspace_module_map
from .package_gate import ValidationResult, validate_package, validate_registry
from .ppsspp_bundle import verify_ppsspp_bundle
from .psp_modules import analyze_psp_modules, write_psp_analysis_run
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

    module_parser = subparsers.add_parser("module-map")
    module_parser.add_argument("workspace", type=Path)
    module_parser.add_argument("--output", type=Path)
    module_parser.add_argument("--force", action="store_true")
    module_parser.add_argument("--json", action="store_true", dest="as_json")

    psp_parser = subparsers.add_parser("analyze-psp-modules")
    psp_parser.add_argument("workspace", type=Path)
    psp_parser.add_argument("--nid-db", action="append", type=Path, default=[])
    psp_parser.add_argument("--allow-unpinned-toolkit", action="store_true")
    psp_parser.add_argument("--json", action="store_true", dest="as_json")

    bundle_parser = subparsers.add_parser("ppsspp-bundle")
    bundle_subparsers = bundle_parser.add_subparsers(
        dest="ppsspp_bundle_command", required=True
    )
    bundle_verify_parser = bundle_subparsers.add_parser("verify")
    bundle_verify_parser.add_argument("path", type=Path)
    bundle_verify_parser.add_argument("--json", action="store_true", dest="as_json")

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
    if args.command == "module-map":
        module_map = build_workspace_module_map(args.workspace)
        encoded = module_map.to_json()
        if args.output is not None:
            _write_binary_output(args.output, encoded.encode("utf-8"), force=args.force)
        if args.as_json or args.output is None:
            print(encoded, end="")
        else:
            print(f"wrote: {args.output} ({len(module_map.modules)} modules)")
        return 0
    if args.command == "analyze-psp-modules":
        run = analyze_psp_modules(
            args.workspace,
            nid_db_paths=tuple(args.nid_db),
            allow_unpinned_toolkit=args.allow_unpinned_toolkit,
        )
        evidence_path = write_psp_analysis_run(run)
        analyzed = sum(module.status == "analyzed" for module in run.modules)
        needs_decryption = sum(
            module.status == "needs_decryption" for module in run.modules
        )
        failed = sum(module.status == "failed" for module in run.modules)
        if args.as_json:
            print(
                json.dumps(
                    {
                        "analyzed": analyzed,
                        "evidence_path": str(evidence_path),
                        "failed": failed,
                        "needs_decryption": needs_decryption,
                        "revision_locked": run.toolchain.revision_locked,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                end="",
            )
        else:
            print(
                "psp-analysis: "
                f"analyzed={analyzed} "
                f"needs-decryption={needs_decryption} "
                f"failed={failed} evidence={evidence_path}"
            )
        return 0
    if args.command == "ppsspp-bundle":
        identity = verify_ppsspp_bundle(args.path)
        if args.as_json:
            print(
                json.dumps(
                    {
                        "headless_sha256": identity.headless_sha256,
                        "host": identity.host,
                        "port": identity.port,
                        "revision": identity.revision,
                        "sdl_sha256": identity.sdl_sha256,
                        "xvfb_sha256": identity.xvfb_sha256,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                end="",
            )
        else:
            print(
                f"valid PPSSPP debugger bundle: {identity.revision} "
                f"({identity.host}:{identity.port})"
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
