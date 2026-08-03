from __future__ import annotations

import json
from pathlib import Path

from fnr3_re.module_map import ModuleKind, build_repository_module_map

ROOT = Path(__file__).resolve().parents[2]


def test_tracked_repository_module_map_is_deterministic() -> None:
    module_map = build_repository_module_map(ROOT)

    assert module_map.revision_id == "tracked-repository-samples"
    assert [module.path for module in module_map.modules] == ["BOOT.BIN", "EBOOT.BIN"]
    assert [module.kind for module in module_map.modules] == [
        ModuleKind.PLAIN_ELF,
        ModuleKind.PSP_CONTAINER,
    ]
    boot, eboot = module_map.modules
    assert boot.entry_point == eboot.entry_point == 0x34DECC
    assert boot.file_size == eboot.container_elf_size == 7_270_664
    assert eboot.file_size == eboot.container_psp_size == 7_271_008
    assert boot.runtime_base is None
    assert eboot.runtime_base is None
    assert boot.address_mapping_status == "static_elf_mapped_iso_offset_pending"
    assert eboot.address_mapping_status == "packed_container_requires_decrypted_elf"

    encoded = module_map.to_json()
    assert encoded == build_repository_module_map(ROOT).to_json()
    decoded = json.loads(encoded)
    assert decoded["modules"][0]["sections"]
    assert decoded["modules"][1]["sections"] == []
