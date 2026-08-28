from __future__ import annotations

from fnr3_re.psp_sfo import build_param_sfo_strings, build_runtime_param_sfo
from fnr3_re.revision import ReferenceRevision, parse_param_sfo


def _revision() -> ReferenceRevision:
    return ReferenceRevision(
        revision_id="ULUS10066-v1.00",
        disc_id="ULUS10066",
        disc_version="1.00",
        title="EA SPORTS™ FIGHT NIGHT Round 3",
        psp_system_version="2.60",
        iso_size=1_137_737_728,
        iso_sha256="b11da5afe208d9791eecd9f6a44d0f57946f7d9de165b7d8dd22f5ee740f4ee2",
    )


def test_runtime_param_sfo_round_trips_locked_identity() -> None:
    payload = build_runtime_param_sfo(_revision())
    parsed = parse_param_sfo(payload)

    assert parsed == {
        "DISC_ID": "ULUS10066",
        "DISC_VERSION": "1.00",
        "PSP_SYSTEM_VER": "2.60",
        "TITLE": "EA SPORTS™ FIGHT NIGHT Round 3",
    }


def test_runtime_param_sfo_is_byte_deterministic() -> None:
    assert build_runtime_param_sfo(_revision()) == build_runtime_param_sfo(_revision())


def test_param_sfo_writer_rejects_embedded_nul() -> None:
    try:
        build_param_sfo_strings({"TITLE": "bad\x00title"})
    except ValueError as exc:
        assert str(exc) == "PARAM.SFO values must not contain NUL"
    else:
        raise AssertionError("embedded NUL was accepted")


def test_param_sfo_writer_rejects_empty_key() -> None:
    try:
        build_param_sfo_strings({"": "value"})
    except ValueError as exc:
        assert str(exc) == "PARAM.SFO keys must be non-empty"
    else:
        raise AssertionError("empty PARAM.SFO key was accepted")
