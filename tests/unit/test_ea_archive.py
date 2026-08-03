from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from fnr3_re.ea_archive import (
    EaArchiveError,
    build_ea_archive,
    extract_ea_archive,
    parse_ea_archive,
    rebuild_ea_archive,
)


def make_archive(
    *,
    magic: bytes = b"BIGF",
    first_offset: int = 0x30,
    second_offset: int = 0x40,
    total_size: int = 0x42,
) -> bytes:
    header = bytearray()
    header.extend(magic)
    header.extend(total_size.to_bytes(4, "little"))
    header.extend((2).to_bytes(4, "big"))
    header.extend((0x30).to_bytes(4, "big"))
    header.extend(first_offset.to_bytes(4, "big"))
    header.extend((1).to_bytes(4, "big"))
    header.extend(b"a.bin\x00")
    header.extend(second_offset.to_bytes(4, "big"))
    header.extend((2).to_bytes(4, "big"))
    header.extend(b"dir/b.bin\x00")
    assert len(header) == 0x30
    output = bytearray(total_size)
    output[: len(header)] = header
    output[first_offset : first_offset + 1] = b"A"
    output[second_offset : second_offset + 2] = b"BB"
    return bytes(output)


def test_parses_bigf_directory_and_infers_alignment() -> None:
    archive = parse_ea_archive(make_archive())

    assert archive.magic == b"BIGF"
    assert archive.total_size == 0x42
    assert archive.header_size == 0x30
    assert archive.alignment == 0x10
    observed = [
        (member.name, member.offset, member.size, member.data)
        for member in archive.members
    ]
    assert observed == [
        ("a.bin", 0x30, 1, b"A"),
        ("dir/b.bin", 0x40, 2, b"BB"),
    ]
    assert archive.members[0].sha256 == hashlib.sha256(b"A").hexdigest()


def test_parses_big4_with_observed_sixty_four_byte_alignment() -> None:
    payload = make_archive(
        magic=b"BIG4",
        first_offset=0x40,
        second_offset=0x80,
        total_size=0x82,
    )
    archive = parse_ea_archive(payload)

    assert archive.magic == b"BIG4"
    assert archive.alignment == 0x40
    assert archive.members[0].offset == 0x40
    assert archive.members[1].offset == 0x80


def test_builder_is_deterministic_and_round_trips_both_magics() -> None:
    members = (("a.bin", b"A"), ("dir/b.bin", b"BB"))

    for magic, alignment in ((b"BIGF", 0x10), (b"BIG4", 0x40)):
        first = build_ea_archive(members, magic=magic, alignment=alignment)
        second = build_ea_archive(members, magic=magic, alignment=alignment)
        parsed = parse_ea_archive(first)

        assert first == second
        assert parsed.magic == magic
        assert parsed.alignment == alignment
        assert [(member.name, member.data) for member in parsed.members] == list(members)
        assert int.from_bytes(first[4:8], "little") == len(first)
        assert int.from_bytes(first[8:12], "big") == 2


def test_no_change_rebuild_is_byte_exact() -> None:
    payload = make_archive()
    archive = parse_ea_archive(payload)

    assert rebuild_ea_archive(archive) == payload


def test_guarded_replacement_preserves_order_magic_and_alignment() -> None:
    archive = parse_ea_archive(make_archive())
    expected = {"dir/b.bin": hashlib.sha256(b"BB").hexdigest()}

    rebuilt = rebuild_ea_archive(
        archive,
        {"dir/b.bin": b"replacement"},
        expected_sha256=expected,
    )
    parsed = parse_ea_archive(rebuilt)

    assert parsed.magic == b"BIGF"
    assert parsed.alignment == 0x10
    assert [member.name for member in parsed.members] == ["a.bin", "dir/b.bin"]
    assert parsed.members[0].data == b"A"
    assert parsed.members[1].data == b"replacement"


def test_replacement_rejects_unknown_or_stale_members() -> None:
    archive = parse_ea_archive(make_archive())

    with pytest.raises(EaArchiveError, match="replacement member does not exist"):
        rebuild_ea_archive(archive, {"missing.bin": b"x"})
    with pytest.raises(EaArchiveError, match="original member hash mismatch"):
        rebuild_ea_archive(
            archive,
            {"a.bin": b"x"},
            expected_sha256={"a.bin": "0" * 64},
        )


def test_extraction_is_transactional_and_path_safe(tmp_path: Path) -> None:
    archive = parse_ea_archive(make_archive())
    destination = tmp_path / "archive"

    manifest = extract_ea_archive(archive, destination)

    assert (destination / "a.bin").read_bytes() == b"A"
    assert (destination / "dir" / "b.bin").read_bytes() == b"BB"
    assert manifest[0]["name"] == "a.bin"
    assert manifest[1]["name"] == "dir/b.bin"
    with pytest.raises(FileExistsError):
        extract_ea_archive(archive, destination)

    extract_ea_archive(archive, destination, force=True)
    assert (destination / "dir" / "b.bin").read_bytes() == b"BB"


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (b"", "archive header is truncated"),
        (b"NOPE" + b"\x00" * 12, "unsupported EA archive magic"),
        (make_archive()[:-1], "archive size mismatch"),
        (
            make_archive()[:8] + (3).to_bytes(4, "big") + make_archive()[12:],
            "directory record is truncated",
        ),
        (
            make_archive()[:12] + (0x20).to_bytes(4, "big") + make_archive()[16:],
            "directory record is truncated",
        ),
    ],
)
def test_parser_rejects_malformed_headers(payload: bytes, message: str) -> None:
    with pytest.raises(EaArchiveError, match=message):
        parse_ea_archive(payload)


def test_builder_rejects_duplicate_member_names() -> None:
    with pytest.raises(EaArchiveError, match="duplicate archive member"):
        build_ea_archive((("a.bin", b"A"), ("A.BIN", b"B")))


def test_parser_rejects_unsafe_and_overlapping_members() -> None:
    unsafe = bytearray(make_archive())
    unsafe[24:30] = b"../x\x00\x00"
    overlapping = bytearray(make_archive())
    overlapping[30:34] = (0x30).to_bytes(4, "big")

    with pytest.raises(EaArchiveError, match="unsafe archive member path"):
        parse_ea_archive(bytes(unsafe))
    with pytest.raises(EaArchiveError, match="overlapping member payloads"):
        parse_ea_archive(bytes(overlapping))
