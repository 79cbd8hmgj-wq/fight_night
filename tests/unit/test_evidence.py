from __future__ import annotations

import json

import pytest

from fnr3_re.evidence import (
    Address,
    AddressType,
    BinaryRegion,
    Confidence,
    EvidenceClaim,
    EvidenceType,
    RuntimeCapture,
    dump_json,
)


def test_address_rejects_negative_values() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        Address(AddressType.RUNTIME, -1)


def test_confirmed_claim_rejects_decompiler_only_evidence() -> None:
    with pytest.raises(ValueError, match="independent evidence"):
        EvidenceClaim(
            claim_id="stamina-field",
            question="Which field stores current stamina?",
            source_revision="ULUS10066-v1.00",
            module="BOOT.BIN",
            confidence=Confidence.CONFIRMED,
            evidence_types=(EvidenceType.DECOMPILER,),
            addresses=(Address(AddressType.ELF_VIRTUAL, 0x08804000),),
            conclusion="Candidate field at +0x20.",
        )


def test_confirmed_claim_requires_exact_binary_evidence() -> None:
    with pytest.raises(ValueError, match="exact binary"):
        EvidenceClaim(
            claim_id="stamina-field",
            question="Which field stores current stamina?",
            source_revision="ULUS10066-v1.00",
            module="BOOT.BIN",
            confidence=Confidence.CONFIRMED,
            evidence_types=(EvidenceType.RUNTIME_CAPTURE,),
            addresses=(Address(AddressType.RUNTIME, 0x08804000),),
            conclusion="Runtime-only interpretation.",
        )


def test_claim_requires_at_least_one_typed_address() -> None:
    with pytest.raises(ValueError, match="typed address"):
        EvidenceClaim(
            claim_id="stamina-field",
            question="Which field stores current stamina?",
            source_revision="ULUS10066-v1.00",
            module="BOOT.BIN",
            confidence=Confidence.CANDIDATE,
            evidence_types=(EvidenceType.DECOMPILER,),
            addresses=(),
            conclusion="Unlocated candidate.",
        )


def test_confirmed_claim_serializes_deterministically() -> None:
    claim = EvidenceClaim(
        claim_id="jab-writer",
        question="Which instruction deducts jab stamina?",
        source_revision="ULUS10066-v1.00",
        module="BOOT.BIN",
        confidence=Confidence.CONFIRMED,
        evidence_types=(EvidenceType.EXACT_BINARY, EvidenceType.RUNTIME_CAPTURE),
        addresses=(Address(AddressType.RUNTIME, 0x08812340),),
        conclusion="The writer subtracts the resolved jab cost.",
        remaining_unknowns=("AI difficulty modifier",),
        binary_regions=(
            BinaryRegion(
                module="BOOT.BIN",
                address=Address(AddressType.ELF_FILE_OFFSET, 0x12340),
                size=16,
                sha256="a" * 64,
            ),
        ),
        runtime_captures=(
            RuntimeCapture(
                emulator="PPSSPP-test",
                state_sha256="b" * 64,
                breakpoint=Address(AddressType.RUNTIME, 0x08812340),
                registers=(("a0", 100), ("v0", 92)),
                memory=((0x09ABC000, "64000000"),),
            ),
        ),
    )

    first = dump_json(claim)
    second = dump_json(claim)
    assert first == second
    assert first.endswith("\n")
    parsed = json.loads(first)
    assert parsed["claim_id"] == "jab-writer"
    assert parsed["confidence"] == "CONFIRMED"
    assert parsed["addresses"][0] == {"address_type": "runtime", "value": 0x08812340}
    assert parsed["runtime_captures"][0]["registers"] == [["a0", 100], ["v0", 92]]


def test_binary_region_validates_sha256_and_size() -> None:
    with pytest.raises(ValueError, match="64 lowercase hexadecimal"):
        BinaryRegion(
            module="BOOT.BIN",
            address=Address(AddressType.ELF_FILE_OFFSET, 0),
            size=4,
            sha256="BAD",
        )
    with pytest.raises(ValueError, match="positive"):
        BinaryRegion(
            module="BOOT.BIN",
            address=Address(AddressType.ELF_FILE_OFFSET, 0),
            size=0,
            sha256="c" * 64,
        )


def test_claim_from_mapping_preserves_nested_binary_and_runtime_evidence() -> None:
    claim = EvidenceClaim.from_mapping(
        {
            "claim_id": "jab-writer",
            "question": "Which instruction deducts jab stamina?",
            "source_revision": "ULUS10066-v1.00",
            "module": "BOOT.BIN",
            "confidence": "CONFIRMED",
            "evidence_types": ["exact_binary", "runtime_capture"],
            "addresses": [{"address_type": "runtime", "value": 0x08812340}],
            "conclusion": "The writer subtracts the resolved jab cost.",
            "remaining_unknowns": ["AI difficulty modifier"],
            "binary_regions": [
                {
                    "module": "BOOT.BIN",
                    "address": {"address_type": "elf_file_offset", "value": 0x12340},
                    "size": 16,
                    "sha256": "a" * 64,
                }
            ],
            "runtime_captures": [
                {
                    "emulator": "PPSSPP-test",
                    "state_sha256": "b" * 64,
                    "breakpoint": {"address_type": "runtime", "value": 0x08812340},
                    "registers": [["a0", 100], ["v0", 92]],
                    "memory": [[0x09ABC000, "64000000"]],
                }
            ],
        }
    )

    assert claim.binary_regions[0].size == 16
    assert claim.runtime_captures[0].registers == (("a0", 100), ("v0", 92))
    assert claim.remaining_unknowns == ("AI difficulty modifier",)
