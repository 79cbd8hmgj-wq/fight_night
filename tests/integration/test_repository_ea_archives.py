from __future__ import annotations

from pathlib import Path

from fnr3_re.ea_archive import parse_ea_archive, rebuild_ea_archive
from fnr3_re.refpack import decompress_refpack

ROOT = Path(__file__).resolve().parents[2]


def test_tracked_bigf_ui_archive_matches_observed_contract() -> None:
    path = ROOT / "components" / "alpha.big"
    payload = path.read_bytes()
    archive = parse_ea_archive(payload)

    assert archive.magic == b"BIGF"
    assert archive.total_size == 4_784
    assert archive.header_size == 0x58
    assert archive.alignment == 0x10
    assert [member.name for member in archive.members] == [
        "alpha.apt",
        "alpha.const",
        "alpha.o",
        "alpha.msh",
    ]
    assert [(member.offset, member.size) for member in archive.members] == [
        (0x60, 0x308),
        (0x370, 0xFF),
        (0x470, 0x95D),
        (0xDD0, 0x4E0),
    ]
    assert rebuild_ea_archive(archive) == payload


def test_tracked_big4_database_archive_matches_observed_contract() -> None:
    path = ROOT / "preload" / "db.viv"
    payload = path.read_bytes()
    archive = parse_ea_archive(payload)

    assert archive.magic == b"BIG4"
    assert archive.total_size == 21_854
    assert archive.header_size == 0xE7
    assert archive.header_tail == b"L266\x15\x05\x00\x01"
    assert archive.alignment == 0x40
    assert [member.name for member in archive.members] == [
        "xdbboxr.adf",
        "xdbvenue.adf",
        "xdbalias.adf",
        "xdbevent.adf",
        "xdbhmtwn.adf",
        "xdbstore.adf",
        "xdbpref.adf",
        "xdbrivl.adf",
        "xdbtrain.adf",
        "xdbcutpn.adf",
    ]
    assert [(member.offset, member.size) for member in archive.members] == [
        (0x100, 0xC2D),
        (0xD40, 0x221),
        (0xF80, 0x363),
        (0x1300, 0x100),
        (0x1400, 0x325),
        (0x1740, 0x200C),
        (0x3780, 0x119),
        (0x38C0, 0x644),
        (0x3F40, 0xC81),
        (0x4C00, 0x95E),
    ]
    assert all(member.refpack_compressed for member in archive.members)
    assert len(decompress_refpack(archive.members[0].data)) == 9_704
    assert rebuild_ea_archive(archive) == payload
