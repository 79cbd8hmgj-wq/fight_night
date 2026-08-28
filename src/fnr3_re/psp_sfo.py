from __future__ import annotations

from collections.abc import Mapping

from .revision import ReferenceRevision

_PSF_VERSION = 0x00000101
_STRING_TYPE = 0x0204
_RUNTIME_KEYS = ("DISC_ID", "DISC_VERSION", "PSP_SYSTEM_VER", "TITLE")


def build_runtime_param_sfo(revision: ReferenceRevision) -> bytes:
    values = {
        "DISC_ID": revision.disc_id,
        "DISC_VERSION": revision.disc_version,
        "PSP_SYSTEM_VER": revision.psp_system_version,
        "TITLE": revision.title,
    }
    return build_param_sfo_strings({key: values[key] for key in _RUNTIME_KEYS})


def build_param_sfo_strings(values: Mapping[str, str]) -> bytes:
    keys = bytearray()
    data = bytearray()
    entries: list[tuple[int, int, int]] = []

    for key, value in values.items():
        if not isinstance(key, str) or not key:
            raise ValueError("PARAM.SFO keys must be non-empty")
        if "\x00" in key:
            raise ValueError("PARAM.SFO keys must not contain NUL")
        if not isinstance(value, str):
            raise ValueError("PARAM.SFO values must be strings")
        if "\x00" in value:
            raise ValueError("PARAM.SFO values must not contain NUL")

        key_offset = len(keys)
        keys.extend(key.encode("utf-8"))
        keys.append(0)

        while len(data) % 4:
            data.append(0)
        value_offset = len(data)
        encoded_value = value.encode("utf-8") + b"\x00"
        data.extend(encoded_value)
        entries.append((key_offset, value_offset, len(encoded_value)))

    key_table_offset = 20 + 16 * len(entries)
    data_table_offset = _align_four(key_table_offset + len(keys))
    payload = bytearray(data_table_offset + len(data))
    payload[0:4] = b"\x00PSF"
    payload[4:8] = _PSF_VERSION.to_bytes(4, "little")
    payload[8:12] = key_table_offset.to_bytes(4, "little")
    payload[12:16] = data_table_offset.to_bytes(4, "little")
    payload[16:20] = len(entries).to_bytes(4, "little")

    for index, (key_offset, value_offset, value_length) in enumerate(entries):
        entry_offset = 20 + index * 16
        payload[entry_offset : entry_offset + 2] = key_offset.to_bytes(2, "little")
        payload[entry_offset + 2 : entry_offset + 4] = _STRING_TYPE.to_bytes(2, "little")
        payload[entry_offset + 4 : entry_offset + 8] = value_length.to_bytes(4, "little")
        payload[entry_offset + 8 : entry_offset + 12] = value_length.to_bytes(4, "little")
        payload[entry_offset + 12 : entry_offset + 16] = value_offset.to_bytes(4, "little")

    payload[key_table_offset : key_table_offset + len(keys)] = keys
    payload[data_table_offset : data_table_offset + len(data)] = data
    return bytes(payload)


def _align_four(value: int) -> int:
    return (value + 3) & ~3
