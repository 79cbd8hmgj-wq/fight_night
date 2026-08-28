from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast
from uuid import uuid4

from .ea_archive import EaArchive, extract_ea_archive, parse_ea_archive
from .iso import build_workspace, verify_workspace
from .manifests import WorkspaceValidationResult
from .module_map import build_workspace_module_map
from .package_gate import ValidationResult, validate_package, validate_registry
from .ppsspp_bundle import (
    FNR3_DEBUGGER_BUNDLE_PROFILE,
    DebuggerBundleIdentity,
    verify_ppsspp_bundle,
)
from .psp_modules import analyze_psp_modules, write_psp_analysis_run
from .rebuild import BuildPlan, load_build_plan, rebuild_image
from .refpack import compress_refpack, decompress_refpack
from .revision import ImageValidationResult, hash_file, load_reference_revision, validate_image
from .runtime_bootstrap import (
    Task9EBootstrapReport,
    load_bootstrap_input_trace,
    prepare_task9e_bootstrap,
)
from .runtime_image import (
    RuntimeImageReport,
    load_runtime_payload_manifest,
    prepare_runtime_image,
)
from .save_runtime_9e import (
    Task9ECaptureInputs,
    Task9EFirstDivergence,
    Task9EPlanError,
    Task9ERuntimeSource,
    hash_savedata_slot,
    load_payload_lifetime_contract,
    load_task9e_plan,
    prepare_corrupted_savedata,
    run_task9e_capture,
    write_task9e_runtime_evidence,
)

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_TASK9E_PLAN = (
    _REPOSITORY_ROOT / "analysis" / "save" / "checkpoint-9e-runtime-capture-plan.json"
)
_DEFAULT_TASK9E_PAYLOAD = (
    _REPOSITORY_ROOT / "analysis" / "save" / "save-payload-lifetime.json"
)
_DEFAULT_REVISION_CONFIG = (
    _REPOSITORY_ROOT / "config" / "revisions" / "ulus10066-v1.00.json"
)
_DEFAULT_RUNTIME_PAYLOAD = (
    _REPOSITORY_ROOT / "config" / "runtime" / "ulus10066-repository-payload.json"
)
_RUNTIME_IMAGE_REPORT = "runtime-image.json"
_RUNTIME_ISO_NAME = "fight-night-runtime.iso"
_SHA256_LENGTH = 64


@dataclass(frozen=True, slots=True)
class Task9ECliSummary:
    valid: bool
    capture_id: str
    callback_target: int | None
    first_divergence: str | None
    evidence_path: Path

    def to_mapping(self) -> dict[str, object]:
        return {
            "callback_target": self.callback_target,
            "capture_id": self.capture_id,
            "evidence_path": str(self.evidence_path),
            "first_divergence": self.first_divergence,
            "valid": self.valid,
        }


@dataclass(frozen=True, slots=True)
class _BootstrapRecord:
    report: Task9EBootstrapReport
    state: Path
    memstick: Path
    savedata_slot: Path


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

    runtime_parser = subparsers.add_parser("prepare-fnr3-runtime")
    runtime_parser.add_argument("repository_root", type=Path)
    runtime_parser.add_argument("output_root", type=Path)
    runtime_parser.add_argument("--bundle", required=True, type=Path)
    runtime_parser.add_argument(
        "--payload-manifest",
        type=Path,
        default=_DEFAULT_RUNTIME_PAYLOAD,
    )
    runtime_parser.add_argument("--force", action="store_true")
    runtime_parser.add_argument("--json", action="store_true", dest="as_json")

    bootstrap_parser = subparsers.add_parser("bootstrap-save-9e")
    bootstrap_parser.add_argument("runtime_root", type=Path)
    bootstrap_parser.add_argument("--bundle", required=True, type=Path)
    bootstrap_parser.add_argument("--trace", required=True, type=Path)
    bootstrap_parser.add_argument("--json", action="store_true", dest="as_json")

    capture_parser = subparsers.add_parser("capture-save-9e")
    capture_parser.add_argument("workspace", type=Path)
    capture_parser.add_argument("--bundle", required=True, type=Path)
    capture_parser.add_argument("--iso", type=Path)
    capture_parser.add_argument("--state", type=Path)
    capture_parser.add_argument("--savedata-slot", type=Path)
    capture_parser.add_argument("--runtime-root", type=Path)
    capture_parser.add_argument("--bootstrap-report", type=Path)
    capture_parser.add_argument("--plan", type=Path, default=_DEFAULT_TASK9E_PLAN)
    capture_parser.add_argument(
        "--payload-lifetime",
        type=Path,
        default=_DEFAULT_TASK9E_PAYLOAD,
    )
    capture_parser.add_argument("--capture-id")
    capture_parser.add_argument("--json", action="store_true", dest="as_json")

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


def _validate_capture_cli_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.command != "capture-save-9e":
        return
    retail_values = (args.iso, args.state, args.savedata_slot)
    repository_values = (args.runtime_root, args.bootstrap_report)
    retail_any = any(value is not None for value in retail_values)
    retail_all = all(value is not None for value in retail_values)
    repository_any = any(value is not None for value in repository_values)
    repository_all = all(value is not None for value in repository_values)
    if retail_any and repository_any:
        parser.error(
            "capture-save-9e retail and repository runtime arguments are mutually exclusive"
        )
    if retail_any and not retail_all:
        parser.error("retail mode requires --iso, --state, and --savedata-slot")
    if repository_any and not repository_all:
        parser.error("repository mode requires --runtime-root and --bootstrap-report")
    if not retail_all and not repository_all:
        parser.error("capture-save-9e requires one complete runtime source mode")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _validate_capture_cli_args(parser, args)
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
    if args.command == "prepare-fnr3-runtime":
        try:
            runtime_report = _execute_prepare_fnr3_runtime(
                repository_root=args.repository_root,
                output_root=args.output_root,
                bundle=args.bundle,
                payload_manifest_path=args.payload_manifest,
                force=args.force,
            )
        except (OSError, RuntimeError, ValueError) as exc:
            _print_command_error("prepare-fnr3-runtime", exc)
            return 1
        if args.as_json:
            print(runtime_report.to_json(), end="")
        else:
            print(
                "runtime: "
                f"revision={runtime_report.revision_id} "
                f"sha256={runtime_report.runtime_iso_sha256} "
                f"files={len(runtime_report.files)}"
            )
        return 0
    if args.command == "bootstrap-save-9e":
        try:
            bootstrap_result = _execute_bootstrap_save_9e(
                runtime_root=args.runtime_root,
                bundle=args.bundle,
                trace_path=args.trace,
            )
        except (OSError, RuntimeError, ValueError) as exc:
            _print_command_error("bootstrap-save-9e", exc)
            return 1
        if args.as_json:
            print(bootstrap_result.to_json(), end="")
        else:
            print(
                "task9e-bootstrap: "
                f"revision={bootstrap_result.revision_id} "
                f"save={bootstrap_result.savedata_slot_name} "
                f"state={bootstrap_result.state_sha256}"
            )
        return 0
    if args.command == "capture-save-9e":
        try:
            summary = _execute_capture_save_9e(
                workspace=args.workspace,
                bundle=args.bundle,
                iso=args.iso,
                state=args.state,
                savedata_slot=args.savedata_slot,
                runtime_root=args.runtime_root,
                bootstrap_report=args.bootstrap_report,
                plan_path=args.plan,
                payload_lifetime_path=args.payload_lifetime,
                capture_id=args.capture_id,
            )
        except (OSError, RuntimeError, ValueError) as exc:
            _print_command_error("capture-save-9e", exc)
            return 1
        if args.as_json:
            print(json.dumps(summary.to_mapping(), indent=2, sort_keys=True) + "\n", end="")
        else:
            callback = (
                "none"
                if summary.callback_target is None
                else f"0x{summary.callback_target:08X}"
            )
            divergence = summary.first_divergence or "none"
            print(
                "task9e: "
                f"valid={str(summary.valid).lower()} "
                f"capture={summary.capture_id} "
                f"callback={callback} "
                f"divergence={divergence} "
                f"evidence={summary.evidence_path}"
            )
        return 0 if summary.valid else 1
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


def _print_command_error(command: str, exc: Exception) -> None:
    message = str(exc).splitlines()[0] if str(exc) else type(exc).__name__
    print(f"{command}: {message}", file=sys.stderr)


def _execute_prepare_fnr3_runtime(
    *,
    repository_root: Path,
    output_root: Path,
    bundle: Path,
    payload_manifest_path: Path,
    force: bool,
) -> RuntimeImageReport:
    revision = load_reference_revision(_DEFAULT_REVISION_CONFIG)
    manifest = load_runtime_payload_manifest(payload_manifest_path)
    verify_ppsspp_bundle(bundle, profile=FNR3_DEBUGGER_BUNDLE_PROFILE)
    return prepare_runtime_image(
        repository_root,
        output_root,
        manifest,
        revision,
        force=force,
    )


def _execute_bootstrap_save_9e(
    *,
    runtime_root: Path,
    bundle: Path,
    trace_path: Path,
) -> Task9EBootstrapReport:
    root, _runtime_iso, runtime_source = _load_repository_runtime(runtime_root)
    verify_ppsspp_bundle(bundle, profile=FNR3_DEBUGGER_BUNDLE_PROFILE)
    plan = load_task9e_plan(_DEFAULT_TASK9E_PLAN)
    trace = load_bootstrap_input_trace(trace_path)
    return prepare_task9e_bootstrap(
        root,
        bundle,
        trace,
        plan,
        runtime_source,
        bundle_profile=FNR3_DEBUGGER_BUNDLE_PROFILE,
    )


def _validate_capture_id(capture_id: str | None) -> str:
    resolved = capture_id or f"capture-{uuid4().hex}"
    if not resolved.strip() or resolved != resolved.strip():
        raise Task9EPlanError("capture id must be non-empty without surrounding whitespace")
    if Path(resolved).name != resolved or resolved in {".", ".."}:
        raise Task9EPlanError("capture id must be one normal path component")
    return resolved


def _format_first_divergence(divergence: Task9EFirstDivergence | None) -> str | None:
    if divergence is None:
        return None
    observation = divergence.observation_id or "none"
    field = divergence.field or "none"
    return f"{divergence.fact}:{observation}:{field}"


def _execute_capture_save_9e(
    *,
    workspace: Path,
    bundle: Path,
    iso: Path | None,
    state: Path | None,
    savedata_slot: Path | None,
    runtime_root: Path | None,
    bootstrap_report: Path | None,
    plan_path: Path,
    payload_lifetime_path: Path,
    capture_id: str | None,
) -> Task9ECliSummary:
    resolved_capture_id = _validate_capture_id(capture_id)
    plan = load_task9e_plan(plan_path)
    contract = load_payload_lifetime_contract(payload_lifetime_path)
    revision = load_reference_revision(_DEFAULT_REVISION_CONFIG)
    bundle_identity = verify_ppsspp_bundle(bundle, profile=FNR3_DEBUGGER_BUNDLE_PROFILE)
    if revision.revision_id != plan.revision_id:
        raise Task9EPlanError("revision configuration does not match the Task 9E plan")
    if contract.source_revision != plan.revision_id:
        raise Task9EPlanError("payload lifetime revision does not match the Task 9E plan")

    capture_root = (
        workspace / "working" / "runtime" / "task-9e" / resolved_capture_id
    )
    with tempfile.TemporaryDirectory(prefix=f"fnr3-task9e-{resolved_capture_id}-") as temp:
        temp_root = Path(temp)
        if runtime_root is not None:
            if bootstrap_report is None or any(
                value is not None for value in (iso, state, savedata_slot)
            ):
                raise Task9EPlanError("invalid repository capture source arguments")
            source_root, runtime_iso, runtime_source = _load_repository_runtime(runtime_root)
            bootstrap = _load_bootstrap_record(
                source_root,
                bootstrap_report,
                runtime_source,
                bundle_identity,
            )
            success_memstick, success_slot = _copy_successful_control_memstick(
                bootstrap,
                temp_root / "successful-memstick",
            )
            corrupted_memstick = temp_root / "corrupted-memstick"
            corrupted_slot = (
                corrupted_memstick
                / "PSP"
                / "SAVEDATA"
                / bootstrap.report.savedata_slot_name
            )
            corrupted_slot.parent.mkdir(parents=True)
            mutation = prepare_corrupted_savedata(
                success_slot,
                corrupted_slot,
                contract,
            )
            capture_iso = runtime_iso
            capture_state = bootstrap.state
        else:
            if (
                bootstrap_report is not None
                or iso is None
                or state is None
                or savedata_slot is None
            ):
                raise Task9EPlanError("invalid retail capture source arguments")
            runtime_source = Task9ERuntimeSource.retail_iso(
                revision_id=revision.revision_id,
                retail_iso_sha256=revision.iso_sha256,
                boot_sha256=plan.boot_sha256,
            )
            success_memstick = _infer_memstick_root(savedata_slot)
            success_slot = savedata_slot
            corrupted_memstick = temp_root / "corrupted-memstick"
            corrupted_slot = corrupted_memstick / "PSP" / "SAVEDATA" / savedata_slot.name
            corrupted_slot.parent.mkdir(parents=True)
            mutation = prepare_corrupted_savedata(
                savedata_slot,
                corrupted_slot,
                contract,
            )
            capture_iso = iso
            capture_state = state

        success_inputs = Task9ECaptureInputs(
            workspace=workspace,
            bundle_root=bundle,
            iso=capture_iso,
            state=capture_state,
            savedata_slot=success_slot,
            plan=plan,
            payload_contract=contract,
            revision=revision,
            control_id="successful_load",
            bundle_profile=FNR3_DEBUGGER_BUNDLE_PROFILE,
            runtime_source=runtime_source,
            memstick_root=success_memstick,
        )
        corrupted_inputs = Task9ECaptureInputs(
            workspace=workspace,
            bundle_root=bundle,
            iso=capture_iso,
            state=capture_state,
            savedata_slot=corrupted_slot,
            plan=plan,
            payload_contract=contract,
            revision=revision,
            control_id="corrupted_copy_control",
            bundle_profile=FNR3_DEBUGGER_BUNDLE_PROFILE,
            runtime_source=runtime_source,
            memstick_root=corrupted_memstick,
        )
        evidence = run_task9e_capture(
            success_inputs,
            corrupted_inputs,
            mutation=mutation,
        )
        evidence_path = write_task9e_runtime_evidence(
            workspace,
            evidence,
            capture_root,
        )

    callback = evidence.successful.callback
    callback_target = None if callback is None else callback.target.value
    return Task9ECliSummary(
        valid=evidence.successful.valid and evidence.corrupted.valid,
        capture_id=resolved_capture_id,
        callback_target=callback_target,
        first_divergence=_format_first_divergence(evidence.first_divergence),
        evidence_path=evidence_path,
    )


def _infer_memstick_root(savedata_slot: Path) -> Path:
    if savedata_slot.is_symlink():
        raise Task9EPlanError("savedata slot must not be a symlink")
    if savedata_slot.parent.name != "SAVEDATA" or savedata_slot.parent.parent.name != "PSP":
        raise Task9EPlanError("savedata slot must be under <memstick>/PSP/SAVEDATA")
    root = savedata_slot.parent.parent.parent
    if root.is_symlink():
        raise Task9EPlanError("memstick root must not be a symlink")
    return root


def _load_json_object(path: Path, label: str) -> Mapping[str, object]:
    if path.is_symlink() or not path.is_file():
        raise Task9EPlanError(f"{label} must be a regular non-symlink file")
    try:
        decoded: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Task9EPlanError(f"unable to read {label}: {exc}") from exc
    if not isinstance(decoded, Mapping):
        raise Task9EPlanError(f"{label} root must be a JSON object")
    return cast(Mapping[str, object], decoded)


def _required_string(payload: Mapping[str, object], key: str, label: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise Task9EPlanError(f"{label} {key} must be a non-empty string")
    return value


def _required_sha256(payload: Mapping[str, object], key: str, label: str) -> str:
    value = _required_string(payload, key, label)
    if len(value) != _SHA256_LENGTH or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise Task9EPlanError(f"{label} {key} must be lowercase SHA-256")
    return value


def _load_repository_runtime(
    runtime_root: Path,
) -> tuple[Path, Path, Task9ERuntimeSource]:
    if runtime_root.is_symlink():
        raise Task9EPlanError("runtime root must not be a symlink")
    try:
        root = runtime_root.resolve(strict=True)
    except OSError as exc:
        raise Task9EPlanError("runtime root does not exist") from exc
    if not root.is_dir():
        raise Task9EPlanError("runtime root must be a directory")
    payload = _load_json_object(root / _RUNTIME_IMAGE_REPORT, "runtime-image report")
    if payload.get("schema_version") != 1:
        raise Task9EPlanError("runtime-image report has unsupported schema_version")
    if payload.get("source_mode") != "repository_runtime_image":
        raise Task9EPlanError("runtime-image report is not repository runtime provenance")
    source = Task9ERuntimeSource.repository_image(
        revision_id=_required_string(payload, "revision_id", "runtime-image report"),
        retail_iso_sha256=_required_sha256(
            payload, "retail_iso_sha256", "runtime-image report"
        ),
        runtime_iso_sha256=_required_sha256(
            payload, "runtime_iso_sha256", "runtime-image report"
        ),
        payload_manifest_sha256=_required_sha256(
            payload, "payload_manifest_sha256", "runtime-image report"
        ),
        boot_sha256=_required_sha256(payload, "boot_sha256", "runtime-image report"),
    )
    runtime_iso = root / _RUNTIME_ISO_NAME
    if runtime_iso.is_symlink() or not runtime_iso.is_file():
        raise Task9EPlanError("runtime ISO must be a regular non-symlink file")
    if hash_file(runtime_iso) != source.runtime_iso_sha256:
        raise Task9EPlanError("runtime ISO hash does not match runtime-image report")
    return root, runtime_iso, source


def _safe_runtime_relative(root: Path, value: str, label: str, *, directory: bool) -> Path:
    if "\\" in value:
        raise Task9EPlanError(f"{label} must use a safe relative POSIX path")
    relative = PurePosixPath(value)
    if relative.is_absolute() or not relative.parts or any(
        part in {"", ".", ".."} for part in relative.parts
    ):
        raise Task9EPlanError(f"{label} must be a safe relative path")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise Task9EPlanError(f"{label} path contains a symlink")
    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise Task9EPlanError(f"{label} does not resolve safely under runtime root") from exc
    if directory and not resolved.is_dir():
        raise Task9EPlanError(f"{label} must resolve to a directory")
    if not directory and not resolved.is_file():
        raise Task9EPlanError(f"{label} must resolve to a file")
    return resolved


def _inventory_sha256(slot: Path) -> str:
    normalized = [
        {
            "relative_path": entry.relative_path,
            "sha256": entry.sha256,
            "size": entry.size,
        }
        for entry in hash_savedata_slot(slot)
    ]
    encoded = json.dumps(normalized, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_bootstrap_record(
    runtime_root: Path,
    report_path: Path,
    runtime_source: Task9ERuntimeSource,
    bundle: DebuggerBundleIdentity,
) -> _BootstrapRecord:
    payload = _load_json_object(report_path, "Task 9E bootstrap report")
    if payload.get("schema_version") != 1:
        raise Task9EPlanError("Task 9E bootstrap report has unsupported schema_version")
    report = Task9EBootstrapReport(
        schema_version=1,
        revision_id=_required_string(payload, "revision_id", "bootstrap report"),
        runtime_iso_sha256=_required_sha256(
            payload, "runtime_iso_sha256", "bootstrap report"
        ),
        payload_manifest_sha256=_required_sha256(
            payload, "payload_manifest_sha256", "bootstrap report"
        ),
        bundle_revision=_required_string(payload, "bundle_revision", "bootstrap report"),
        bundle_sdl_sha256=_required_sha256(
            payload, "bundle_sdl_sha256", "bootstrap report"
        ),
        savedata_slot_name=_required_string(
            payload, "savedata_slot_name", "bootstrap report"
        ),
        savedata_inventory_sha256=_required_sha256(
            payload, "savedata_inventory_sha256", "bootstrap report"
        ),
        state_sha256=_required_sha256(payload, "state_sha256", "bootstrap report"),
        input_trace_sha256=_required_sha256(
            payload, "input_trace_sha256", "bootstrap report"
        ),
        state_relative_path=_required_string(
            payload, "state_relative_path", "bootstrap report"
        ),
        memstick_relative_path=_required_string(
            payload, "memstick_relative_path", "bootstrap report"
        ),
    )
    if report.revision_id != runtime_source.revision_id:
        raise Task9EPlanError("bootstrap revision does not match runtime provenance")
    if report.runtime_iso_sha256 != runtime_source.runtime_iso_sha256:
        raise Task9EPlanError("bootstrap runtime hash does not match runtime provenance")
    if report.payload_manifest_sha256 != runtime_source.payload_manifest_sha256:
        raise Task9EPlanError("bootstrap payload hash does not match runtime provenance")
    if report.bundle_revision != bundle.revision or report.bundle_sdl_sha256 != bundle.sdl_sha256:
        raise Task9EPlanError("bootstrap debugger bundle identity does not match current bundle")
    if Path(report.savedata_slot_name).name != report.savedata_slot_name:
        raise Task9EPlanError("bootstrap savedata slot name is unsafe")

    state = _safe_runtime_relative(
        runtime_root,
        report.state_relative_path,
        "bootstrap state",
        directory=False,
    )
    memstick = _safe_runtime_relative(
        runtime_root,
        report.memstick_relative_path,
        "bootstrap memstick",
        directory=True,
    )
    slot = memstick / "PSP" / "SAVEDATA" / report.savedata_slot_name
    if slot.is_symlink() or not slot.is_dir():
        raise Task9EPlanError("bootstrap savedata slot is missing or unsafe")
    if hash_file(state) != report.state_sha256:
        raise Task9EPlanError("bootstrap state hash does not match report")
    if _inventory_sha256(slot) != report.savedata_inventory_sha256:
        raise Task9EPlanError("bootstrap savedata inventory does not match report")
    return _BootstrapRecord(report=report, state=state, memstick=memstick, savedata_slot=slot)


def _copy_successful_control_memstick(
    bootstrap: _BootstrapRecord,
    destination: Path,
) -> tuple[Path, Path]:
    if destination.exists() or destination.is_symlink():
        raise Task9EPlanError("successful control memstick destination already exists")
    destination.mkdir()
    slot = destination / "PSP" / "SAVEDATA" / bootstrap.report.savedata_slot_name
    slot.parent.mkdir(parents=True)
    shutil.copytree(bootstrap.savedata_slot, slot)
    if _inventory_sha256(slot) != bootstrap.report.savedata_inventory_sha256:
        raise Task9EPlanError("successful control save copy changed during preparation")
    return destination, slot


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
