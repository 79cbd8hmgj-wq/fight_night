from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any

from .psp_modules import FNR3_ISO_SHA256, FNR3_REVISION_ID, PspAnalysisRun, PspModuleRun


@dataclass(frozen=True, slots=True)
class AddressValue:
    type: str
    value: int


@dataclass(frozen=True, slots=True)
class PspModuleEvidenceManifest:
    schema_version: int
    fight_night_revision_id: str
    reference_iso_sha256: str
    workspace_manifest_sha256: str
    toolkit: dict[str, object]
    modules: tuple[dict[str, object], ...]
    links: dict[str, object]
    warnings: tuple[str, ...]

    def to_json(self) -> str:
        return json.dumps(
            asdict(self),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        ) + "\n"


def _sequence(value: object) -> list[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _warnings(value: object) -> list[str]:
    return sorted({str(item) for item in _sequence(value) if str(item).strip()})


def _library_entry_count(libraries: object) -> int:
    count = 0
    for library in _sequence(libraries):
        count += len(_sequence(getattr(library, "functions", [])))
        count += len(_sequence(getattr(library, "variables", [])))
    return count


def _library_summaries(libraries: object) -> list[dict[str, object]]:
    summaries = [
        {
            "function_count": len(_sequence(getattr(library, "functions", []))),
            "name": str(getattr(library, "name", "")),
            "variable_count": len(_sequence(getattr(library, "variables", []))),
        }
        for library in _sequence(libraries)
    ]
    return sorted(
        summaries,
        key=lambda item: (
            str(item["name"]).casefold(),
            int(item["function_count"]),
            int(item["variable_count"]),
        ),
    )


def _program_header_summaries(model: object | None) -> list[dict[str, object]]:
    if model is None:
        return []
    records = []
    for header in _sequence(getattr(model, "program_headers", [])):
        records.append(
            {
                "align": int(getattr(header, "align", 0)),
                "file_offset": AddressValue(
                    "elf_file_offset",
                    int(getattr(header, "offset", 0)),
                ),
                "filesz": int(getattr(header, "filesz", 0)),
                "flags": int(getattr(header, "flags", 0)),
                "index": int(getattr(header, "index", 0)),
                "memsz": int(getattr(header, "memsz", 0)),
                "type": int(getattr(header, "type", 0)),
                "vaddr": AddressValue("elf_vaddr", int(getattr(header, "vaddr", 0))),
            }
        )
    return sorted(records, key=lambda item: int(item["index"]))


def _section_summaries(model: object | None) -> list[dict[str, object]]:
    if model is None:
        return []
    records = []
    for section in _sequence(getattr(model, "sections", [])):
        records.append(
            {
                "address": AddressValue(
                    "elf_vaddr",
                    int(getattr(section, "addr", 0)),
                ),
                "addralign": int(getattr(section, "addralign", 0)),
                "file_offset": AddressValue(
                    "elf_file_offset",
                    int(getattr(section, "offset", 0)),
                ),
                "flags": int(getattr(section, "flags", 0)),
                "index": int(getattr(section, "index", 0)),
                "kind": str(getattr(section, "kind", "")),
                "name": str(getattr(section, "name", "")),
                "size": int(getattr(section, "size", 0)),
                "type": int(getattr(section, "type", 0)),
            }
        )
    return sorted(records, key=lambda item: int(item["index"]))


def _function_summaries(disassembly: object | None) -> list[dict[str, object]]:
    if disassembly is None:
        return []
    records = []
    for function in _sequence(getattr(disassembly, "functions", [])):
        records.append(
            {
                "address": AddressValue(
                    "runtime_address",
                    int(getattr(function, "address", 0)),
                ),
                "instruction_count": int(getattr(function, "instruction_count", 0)),
                "name": str(getattr(function, "name", "")),
                "section": str(getattr(function, "section", "")),
                "size": int(getattr(function, "size", 0)),
            }
        )
    return sorted(
        records,
        key=lambda item: (
            int(item["address"].value),
            str(item["name"]),
        ),
    )


def _symbol_summaries(disassembly: object | None) -> list[dict[str, object]]:
    if disassembly is None:
        return []
    records = []
    for symbol in _sequence(getattr(disassembly, "symbols", [])):
        section = getattr(symbol, "section", None)
        records.append(
            {
                "address": AddressValue(
                    "runtime_address",
                    int(getattr(symbol, "address", 0)),
                ),
                "kind": str(getattr(symbol, "kind", "")),
                "name": str(getattr(symbol, "name", "")),
                "section": str(section) if section is not None else None,
                "source": str(getattr(symbol, "source", "")),
            }
        )
    return sorted(
        records,
        key=lambda item: (
            int(item["address"].value),
            str(item["name"]),
            str(item["kind"]),
        ),
    )


def _relocation_summary(model: object | None) -> list[dict[str, object]]:
    if model is None:
        return []
    counts: Counter[tuple[str, int, str]] = Counter()
    for relocation in _sequence(getattr(model, "relocations", [])):
        key = (
            str(getattr(relocation, "source", "section")),
            int(getattr(relocation, "type", 0)),
            str(getattr(relocation, "type_name", "")),
        )
        counts[key] += 1
    return [
        {
            "count": count,
            "source": source,
            "type": relocation_type,
            "type_name": type_name,
        }
        for (source, relocation_type, type_name), count in sorted(counts.items())
    ]


def _module_warnings(run: PspModuleRun) -> tuple[str, ...]:
    values: set[str] = set()
    if run.error:
        values.add(run.error)
    for source in (run.model, run.disassembly, run.advanced, run.typing):
        if source is None:
            continue
        values.update(_warnings(getattr(source, "warnings", [])))
    return tuple(sorted(values))


def _placement_payload(run: PspModuleRun) -> dict[str, object] | None:
    placement = run.placement
    if placement is None:
        return None
    return {
        "alignment": int(getattr(placement, "alignment", 0)),
        "evidence": tuple(
            str(item) for item in _sequence(getattr(placement, "placement_evidence", []))
        ),
        "image_end": AddressValue(
            "runtime_address",
            int(getattr(placement, "image_end", 0)),
        ),
        "image_size": int(getattr(placement, "image_size", 0)),
        "kind": str(getattr(placement, "placement_kind", "unknown")),
        "load_address": AddressValue(
            "runtime_address",
            int(getattr(placement, "load_address", 0)),
        ),
        "original_image_base": AddressValue(
            "elf_virtual_address",
            int(getattr(placement, "original_image_base", 0)),
        ),
        "requires_relocation": bool(getattr(placement, "requires_relocation", False)),
        "runtime_address_claim": bool(
            getattr(placement, "runtime_address_claim", False)
        ),
        "tool_confidence": float(
            getattr(placement, "placement_confidence", 0.0)
        ),
    }


def _module_payload(run: PspModuleRun) -> dict[str, object]:
    candidate = run.candidate
    model = run.model
    disassembly = run.disassembly
    advanced = run.advanced
    header = getattr(model, "elf_header", None) if model is not None else None
    module_info = getattr(model, "module_info", None) if model is not None else None

    elf_entry: AddressValue | None = None
    elf_type: int | None = None
    if header is not None:
        elf_entry = AddressValue("elf_virtual_address", int(getattr(header, "entry", 0)))
        elf_type = int(getattr(header, "file_type", 0))

    counts = {
        "advanced_call_edges": len(
            _sequence(getattr(advanced, "call_edges", [])) if advanced is not None else []
        ),
        "advanced_function_confidence": len(
            _sequence(getattr(advanced, "function_confidence", []))
            if advanced is not None
            else []
        ),
        "exports": _library_entry_count(
            getattr(model, "exports", []) if model is not None else []
        ),
        "functions": len(
            _sequence(getattr(disassembly, "functions", []))
            if disassembly is not None
            else []
        ),
        "imports": _library_entry_count(
            getattr(model, "imports", []) if model is not None else []
        ),
        "program_headers": len(
            _sequence(getattr(model, "program_headers", [])) if model is not None else []
        ),
        "references": len(
            _sequence(getattr(disassembly, "references", []))
            if disassembly is not None
            else []
        ),
        "relocations": len(
            _sequence(getattr(model, "relocations", [])) if model is not None else []
        ),
        "sections": len(
            _sequence(getattr(model, "sections", [])) if model is not None else []
        ),
        "symbols": len(
            _sequence(getattr(disassembly, "symbols", []))
            if disassembly is not None
            else []
        ),
    }

    imports = getattr(model, "imports", []) if model is not None else []
    exports = getattr(model, "exports", []) if model is not None else []
    return {
        "classification": candidate.classification,
        "counts": counts,
        "elf_entry": elf_entry,
        "elf_type": elf_type,
        "executable_kind": (
            str(getattr(model, "executable_kind", "")) if model is not None else None
        ),
        "functions": _function_summaries(disassembly),
        "input_kind": str(getattr(model, "input_kind", "")) if model is not None else None,
        "is_boot": candidate.is_boot,
        "iso_byte_offset": AddressValue("iso_byte_offset", candidate.iso_byte_offset),
        "iso_lba": AddressValue("iso_lba", candidate.iso_lba),
        "libraries": {
            "exports": _library_summaries(exports),
            "imports": _library_summaries(imports),
        },
        "module_name": (
            str(getattr(module_info, "name", "")) if module_info is not None else None
        ),
        "needs_decryption": run.needs_decryption,
        "placement": _placement_payload(run),
        "program_headers": _program_header_summaries(model),
        "relocation_summary": _relocation_summary(model),
        "sections": _section_summaries(model),
        "sha256": candidate.sha256,
        "size": candidate.size,
        "status": run.status,
        "symbols": _symbol_summaries(disassembly),
        "warnings": _module_warnings(run),
        "workspace_path": candidate.workspace_path,
    }


def _links_payload(links: object | None) -> dict[str, object]:
    if links is None:
        return {
            "modules": 0,
            "propagated_symbols": 0,
            "resolutions": 0,
            "resolved_links": 0,
            "warnings": (),
        }
    return {
        "modules": len(_sequence(getattr(links, "modules", []))),
        "propagated_symbols": len(
            _sequence(getattr(links, "propagated_symbols", []))
        ),
        "resolutions": len(_sequence(getattr(links, "resolutions", []))),
        "resolved_links": len(_sequence(getattr(links, "links", []))),
        "warnings": tuple(_warnings(getattr(links, "warnings", []))),
    }


def build_psp_evidence_manifest(
    run: PspAnalysisRun,
    *,
    workspace_manifest_sha256: str,
) -> PspModuleEvidenceManifest:
    modules = tuple(
        _module_payload(module)
        for module in sorted(run.modules, key=lambda item: item.candidate.workspace_path.casefold())
    )
    links = _links_payload(run.links)
    warnings = sorted(
        {
            warning
            for module in run.modules
            for warning in _module_warnings(module)
        }
        | set(_warnings(getattr(run.links, "warnings", []) if run.links is not None else []))
    )
    toolchain = run.toolchain
    toolkit: dict[str, object] = {
        "expected_revision": toolchain.expected_revision,
        "observed_revision": toolchain.observed_revision,
        "package_version": toolchain.package_version,
        "repository": toolchain.repository,
        "revision_locked": toolchain.revision_locked,
    }
    return PspModuleEvidenceManifest(
        schema_version=1,
        fight_night_revision_id=FNR3_REVISION_ID,
        reference_iso_sha256=FNR3_ISO_SHA256,
        workspace_manifest_sha256=workspace_manifest_sha256,
        toolkit=toolkit,
        modules=modules,
        links=links,
        warnings=tuple(warnings),
    )
