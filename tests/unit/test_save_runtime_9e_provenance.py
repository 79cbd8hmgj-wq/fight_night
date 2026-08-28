from __future__ import annotations

import pytest

from fnr3_re.save_runtime_9e import Task9EPlanError, Task9ERuntimeSource

_LOCKED_RETAIL_SHA256 = "b11da5afe208d9791eecd9f6a44d0f57946f7d9de165b7d8dd22f5ee740f4ee2"
_LOCKED_BOOT_SHA256 = "906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9"
_RUNTIME_SHA256 = "1" * 64
_MANIFEST_SHA256 = "2" * 64


def test_repository_runtime_source_preserves_distinct_retail_and_runtime_identity() -> None:
    source = Task9ERuntimeSource.repository_image(
        revision_id="ULUS10066-v1.00",
        retail_iso_sha256=_LOCKED_RETAIL_SHA256,
        runtime_iso_sha256=_RUNTIME_SHA256,
        payload_manifest_sha256=_MANIFEST_SHA256,
        boot_sha256=_LOCKED_BOOT_SHA256,
    )

    assert source.source_mode == "repository_runtime_image"
    assert source.runtime_iso_sha256 == _RUNTIME_SHA256
    assert source.runtime_iso_sha256 != source.retail_iso_sha256
    assert source.payload_manifest_sha256 == _MANIFEST_SHA256


def test_retail_runtime_source_uses_retail_hash_as_runtime_identity() -> None:
    source = Task9ERuntimeSource.retail_iso(
        revision_id="ULUS10066-v1.00",
        retail_iso_sha256=_LOCKED_RETAIL_SHA256,
        boot_sha256=_LOCKED_BOOT_SHA256,
    )

    assert source.source_mode == "retail_iso"
    assert source.runtime_iso_sha256 == _LOCKED_RETAIL_SHA256
    assert source.payload_manifest_sha256 is None


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("revision_id", "ULES00000-v1.00", "revision"),
        ("retail_iso_sha256", "not-a-hash", "SHA-256"),
        ("runtime_iso_sha256", "not-a-hash", "SHA-256"),
        ("payload_manifest_sha256", "not-a-hash", "SHA-256"),
        ("boot_sha256", "3" * 64, "BOOT"),
    ],
)
def test_repository_runtime_source_rejects_invalid_provenance(
    field: str,
    value: str,
    match: str,
) -> None:
    values = {
        "revision_id": "ULUS10066-v1.00",
        "retail_iso_sha256": _LOCKED_RETAIL_SHA256,
        "runtime_iso_sha256": _RUNTIME_SHA256,
        "payload_manifest_sha256": _MANIFEST_SHA256,
        "boot_sha256": _LOCKED_BOOT_SHA256,
    }
    values[field] = value

    with pytest.raises(Task9EPlanError, match=match):
        Task9ERuntimeSource.repository_image(**values)


def test_repository_runtime_source_rejects_retail_hash_reuse() -> None:
    with pytest.raises(Task9EPlanError, match="distinct"):
        Task9ERuntimeSource.repository_image(
            revision_id="ULUS10066-v1.00",
            retail_iso_sha256=_LOCKED_RETAIL_SHA256,
            runtime_iso_sha256=_LOCKED_RETAIL_SHA256,
            payload_manifest_sha256=_MANIFEST_SHA256,
            boot_sha256=_LOCKED_BOOT_SHA256,
        )
