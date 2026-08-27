from __future__ import annotations

import json
from pathlib import Path
from types import ModuleType, SimpleNamespace

from fnr3_re.psp_evidence import build_psp_evidence_manifest
from fnr3_re.psp_modules import PspAnalysisRun, PspModuleCandidate, PspModuleRun
from fnr3_re.psp_toolchain import PspToolchainInfo

TOOLKIT_REVISION = "b3a07f4d0880b7933f87a9557b5e0aa3f364fa5a"
REFERENCE_SHA256 = "b11da5afe208d9791eecd9f6a44d0f57946f7d9de165b7d8dd22f5ee740f4ee2"


def _sample_run(tmp_path: Path) -> PspAnalysisRun:
    candidate = PspModuleCandidate(
        workspace_path="PSP_GAME/SYSDIR/BOOT.BIN",
        local_path=tmp_path / "BOOT.BIN",
        sha256="a" * 64,
        size=0x500,
        iso_lba=321,
        iso_byte_offset=321 * 2048,
        classification="executable",
        is_boot=True,
    )
    model = SimpleNamespace(
        input_kind="elf",
        executable_kind="prx",
        needs_decryption=False,
        elf_header=SimpleNamespace(file_type=0xFFA0, entry=0x100),
        program_headers=[
            SimpleNamespace(
                index=0,
                type=1,
                offset=0x100,
                vaddr=0,
                filesz=0x400,
                memsz=0x500,
                flags=5,
                align=0x1000,
            ),
            SimpleNamespace(
                index=1,
                type=1,
                offset=0x500,
                vaddr=0x1000,
                filesz=0x80,
                memsz=0x100,
                flags=6,
                align=0x1000,
            ),
        ],
        sections=[
            SimpleNamespace(
                index=1,
                name=".text",
                type=1,
                flags=6,
                addr=0x100,
                offset=0x100,
                size=0x300,
                addralign=16,
                kind="executable",
            ),
            SimpleNamespace(
                index=2,
                name=".data",
                type=1,
                flags=3,
                addr=0x1000,
                offset=0x500,
                size=0x80,
                addralign=16,
                kind="writable",
            ),
        ],
        module_info=SimpleNamespace(name="FNR3", address=0x20),
        imports=[
            SimpleNamespace(
                name="sceKernelLibrary",
                functions=[SimpleNamespace(nid=1)],
                variables=[SimpleNamespace(nid=2)],
            )
        ],
        exports=[
            SimpleNamespace(
                name="FNR3",
                functions=[SimpleNamespace(nid=3)],
                variables=[],
            )
        ],
        relocations=[
            SimpleNamespace(type=2, type_name="R_MIPS_32", source="section"),
            SimpleNamespace(type=2, type_name="R_MIPS_32", source="prxreloc2"),
        ],
        warnings=["model warning"],
    )
    placement = SimpleNamespace(
        load_address=0x08804000,
        original_image_base=0,
        image_size=0x800,
        image_end=0x08804800,
        alignment=0x1000,
        placement_kind="boot_inferred",
        placement_confidence=0.95,
        runtime_address_claim=True,
        requires_relocation=True,
        placement_evidence=["PSP low-allocation boot default"],
    )
    disassembly = SimpleNamespace(
        functions=[
            SimpleNamespace(
                name="func_08804040",
                address=0x08804040,
                size=0x24,
                section=".text",
                instruction_count=9,
                assembly="sensitive assembly body",
                instructions=[SimpleNamespace(word=0xDEADBEEF)],
            )
        ],
        symbols=[
            SimpleNamespace(
                name="sym",
                address=0x08804100,
                section=".text",
                kind="function",
                source="spimdisasm",
            )
        ],
        references=[
            SimpleNamespace(source_address=0x08804040, target_address=0x08804100)
        ],
        warnings=["disassembly warning"],
        raw_data=b"forbidden raw bytes",
    )
    advanced = SimpleNamespace(
        function_confidence=[
            SimpleNamespace(name="func_08804040", address=0x08804040, score=0.85)
        ],
        call_edges=[
            SimpleNamespace(source_address=0x08804040, target_address=0x08804080)
        ],
        jump_tables=[],
    )
    module = PspModuleRun(
        candidate=candidate,
        status="analyzed",
        needs_decryption=False,
        model=model,
        placement=placement,
        disassembly=disassembly,
        advanced=advanced,
    )
    links = SimpleNamespace(
        modules=["FNR3"],
        resolutions=[SimpleNamespace(nid=1)],
        links=[SimpleNamespace(nid=1)],
        propagated_symbols=[SimpleNamespace(name="sceKernelFoo")],
        warnings=["link warning"],
    )
    toolchain = PspToolchainInfo(
        module=ModuleType("fake_pspdisasm"),
        repository="https://github.com/79cbd8hmgj-wq/PSP-disassembly-tool.git",
        expected_revision=TOOLKIT_REVISION,
        observed_revision=TOOLKIT_REVISION,
        package_version="0.9.0",
        revision_locked=True,
    )
    return PspAnalysisRun(
        workspace=tmp_path,
        toolchain=toolchain,
        modules=(module,),
        links=links,
    )


def test_manifest_is_deterministic_and_has_no_timestamp(tmp_path: Path) -> None:
    run = _sample_run(tmp_path)

    first = build_psp_evidence_manifest(run, workspace_manifest_sha256="b" * 64).to_json()
    second = build_psp_evidence_manifest(run, workspace_manifest_sha256="b" * 64).to_json()

    assert first == second
    assert "timestamp" not in first


def test_tool_confidence_stays_separate_from_fight_night_evidence(tmp_path: Path) -> None:
    payload = json.loads(
        build_psp_evidence_manifest(
            _sample_run(tmp_path),
            workspace_manifest_sha256="b" * 64,
        ).to_json()
    )

    placement = payload["modules"][0]["placement"]
    assert placement["tool_confidence"] == 0.95
    assert placement["load_address"] == {
        "type": "runtime_address",
        "value": 0x08804000,
    }
    assert "fight_night_confidence" not in placement
    assert payload["fight_night_revision_id"] == "ULUS10066-v1.00"
    assert payload["reference_iso_sha256"] == REFERENCE_SHA256


def test_manifest_preserves_address_domains_and_compact_counts(tmp_path: Path) -> None:
    payload = json.loads(
        build_psp_evidence_manifest(
            _sample_run(tmp_path),
            workspace_manifest_sha256="b" * 64,
        ).to_json()
    )
    module = payload["modules"][0]

    assert module["iso_lba"] == {"type": "iso_lba", "value": 321}
    assert module["iso_byte_offset"] == {
        "type": "iso_byte_offset",
        "value": 321 * 2048,
    }
    assert module["elf_entry"] == {"type": "elf_virtual_address", "value": 0x100}
    assert module["counts"]["imports"] == 2
    assert module["counts"]["exports"] == 1
    assert module["counts"]["relocations"] == 2
    assert module["counts"]["functions"] == 1
    assert payload["links"]["resolved_links"] == 1


def test_manifest_contains_required_compact_structural_summaries(tmp_path: Path) -> None:
    payload = json.loads(
        build_psp_evidence_manifest(
            _sample_run(tmp_path),
            workspace_manifest_sha256="b" * 64,
        ).to_json()
    )
    module = payload["modules"][0]

    assert module["program_headers"][0] == {
        "align": 0x1000,
        "file_offset": {"type": "elf_file_offset", "value": 0x100},
        "filesz": 0x400,
        "flags": 5,
        "index": 0,
        "memsz": 0x500,
        "type": 1,
        "vaddr": {"type": "elf_vaddr", "value": 0},
    }
    assert module["sections"][0] == {
        "address": {"type": "elf_vaddr", "value": 0x100},
        "addralign": 16,
        "file_offset": {"type": "elf_file_offset", "value": 0x100},
        "flags": 6,
        "index": 1,
        "kind": "executable",
        "name": ".text",
        "size": 0x300,
        "type": 1,
    }
    assert module["functions"] == [
        {
            "address": {"type": "runtime_address", "value": 0x08804040},
            "instruction_count": 9,
            "name": "func_08804040",
            "section": ".text",
            "size": 0x24,
        }
    ]
    assert module["symbols"] == [
        {
            "address": {"type": "runtime_address", "value": 0x08804100},
            "kind": "function",
            "name": "sym",
            "section": ".text",
            "source": "spimdisasm",
        }
    ]
    assert module["libraries"] == {
        "exports": [{"function_count": 1, "name": "FNR3", "variable_count": 0}],
        "imports": [
            {
                "function_count": 1,
                "name": "sceKernelLibrary",
                "variable_count": 1,
            }
        ],
    }
    assert module["relocation_summary"] == [
        {"count": 1, "source": "prxreloc2", "type": 2, "type_name": "R_MIPS_32"},
        {"count": 1, "source": "section", "type": 2, "type_name": "R_MIPS_32"},
    ]


def test_manifest_contains_no_assembly_raw_bytes_or_instruction_words(tmp_path: Path) -> None:
    encoded = build_psp_evidence_manifest(
        _sample_run(tmp_path),
        workspace_manifest_sha256="b" * 64,
    ).to_json()

    assert "sensitive assembly body" not in encoded
    assert "forbidden raw bytes" not in encoded
    assert "DEADBEEF" not in encoded
    assert '"assembly"' not in encoded
    assert '"raw_data"' not in encoded
