from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

import fnr3_re.psp_modules as psp_modules
from fnr3_re.psp_modules import PspModuleCandidate, analyze_psp_modules
from fnr3_re.psp_toolchain import PspToolchainInfo

TOOLKIT_REVISION = "b3a07f4d0880b7933f87a9557b5e0aa3f364fa5a"


@dataclass(slots=True)
class _ModuleInfo:
    address: int


@dataclass(slots=True)
class _Model:
    needs_decryption: bool = False
    module_info: _ModuleInfo = field(default_factory=lambda: _ModuleInfo(0x20))


@dataclass(slots=True)
class _PlacementInput:
    path: str
    is_boot: bool
    model: _Model


@dataclass(slots=True)
class _Placement:
    path: str
    load_address: int
    placement_kind: str
    requires_relocation: bool
    alignment: int = 0x10


@dataclass(slots=True)
class _Function:
    address: int


@dataclass(slots=True)
class _Disassembly:
    functions: list[_Function]


@dataclass(slots=True)
class _ModuleAnalysisInput:
    model: _Model
    disassembly: _Disassembly | None = None


@dataclass(slots=True)
class _RelocatedView:
    model: _Model


@dataclass(slots=True)
class _Links:
    model_addresses: tuple[int, ...]
    function_addresses: tuple[int, ...]
    database: object | None


class _Toolkit(ModuleType):
    ModulePlacementInput: type[_PlacementInput]
    ModuleAnalysisInput: type[_ModuleAnalysisInput]

    def __init__(self) -> None:
        super().__init__("fake_pspdisasm")
        self.ModulePlacementInput = _PlacementInput
        self.ModuleAnalysisInput = _ModuleAnalysisInput
        self.loaded_nid_paths: tuple[Path, ...] = ()

    def analyze_file(self, path: Path) -> _Model:
        return _Model()

    def plan_module_placements(self, inputs: list[_PlacementInput]) -> list[_Placement]:
        return [
            _Placement(
                path=item.path,
                load_address=0x08804000 + index * 0x10000,
                placement_kind="boot_inferred" if item.is_boot else "analysis",
                requires_relocation=True,
            )
            for index, item in enumerate(inputs)
        ]

    def disassemble_file(
        self,
        path: Path,
        *,
        load_address: int | None = None,
    ) -> _Disassembly:
        base = 0x1000 if load_address is None else load_address
        return _Disassembly(functions=[_Function(base + 0x40)])

    def analyze_advanced(self, model: _Model, disassembly: _Disassembly) -> object:
        return SimpleNamespace(source_model=model, source_disassembly=disassembly)

    def build_relocated_load_view(
        self,
        data: bytes,
        elf: object,
        model: _Model,
        *,
        load_address: int,
    ) -> _RelocatedView:
        assert data == b"fixture"
        assert elf is not None
        return _RelocatedView(model=_Model(module_info=_ModuleInfo(load_address + 0x20)))

    def load_nid_databases(self, paths: tuple[Path, ...]) -> object:
        self.loaded_nid_paths = paths
        return SimpleNamespace(paths=paths)

    def link_modules(
        self,
        modules: list[_ModuleAnalysisInput],
        database: object | None = None,
    ) -> _Links:
        model_addresses = tuple(item.model.module_info.address for item in modules)
        function_addresses = tuple(
            item.disassembly.functions[0].address
            for item in modules
            if item.disassembly is not None
        )
        return _Links(model_addresses, function_addresses, database)


def _candidate(tmp_path: Path, name: str, *, is_boot: bool) -> PspModuleCandidate:
    local_path = tmp_path / name
    local_path.write_bytes(b"fixture")
    workspace_path = (
        "PSP_GAME/SYSDIR/BOOT.BIN" if is_boot else f"PSP_GAME/USRDIR/{name}"
    )
    return PspModuleCandidate(
        workspace_path=workspace_path,
        local_path=local_path,
        sha256="f" * 64,
        size=7,
        iso_lba=100,
        iso_byte_offset=100 * 2048,
        classification="executable",
        is_boot=is_boot,
    )


def _install(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[_Toolkit, tuple[PspModuleCandidate, ...]]:
    toolkit = _Toolkit()
    candidates = (
        _candidate(tmp_path, "BOOT.BIN", is_boot=True),
        _candidate(tmp_path, "SECOND.PRX", is_boot=False),
    )
    info = PspToolchainInfo(
        module=toolkit,
        repository="https://github.com/79cbd8hmgj-wq/PSP-disassembly-tool.git",
        expected_revision=TOOLKIT_REVISION,
        observed_revision=TOOLKIT_REVISION,
        package_version="0.9.0",
        revision_locked=True,
    )
    monkeypatch.setattr(
        psp_modules,
        "discover_psp_module_candidates",
        lambda workspace: candidates,
    )
    monkeypatch.setattr(
        psp_modules,
        "load_psp_toolchain",
        lambda *, allow_unpinned: info,
    )
    parser_module = SimpleNamespace(parse_elf32=lambda data: SimpleNamespace(raw_data=data))
    monkeypatch.setattr(
        psp_modules,
        "import_module",
        lambda name: parser_module,
        raising=False,
    )
    return toolkit, candidates


def test_link_inputs_share_planned_runtime_addresses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install(tmp_path, monkeypatch)

    run = analyze_psp_modules(tmp_path)

    assert isinstance(run.links, _Links)
    assert run.links.model_addresses == (0x08804020, 0x08814020)
    assert run.links.function_addresses == (0x08804040, 0x08814040)


def test_structural_linking_runs_without_nid_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toolkit, _ = _install(tmp_path, monkeypatch)

    run = analyze_psp_modules(tmp_path, nid_db_paths=())

    assert isinstance(run.links, _Links)
    assert run.links.database is None
    assert toolkit.loaded_nid_paths == ()


def test_optional_nid_database_is_forwarded_to_linker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toolkit, _ = _install(tmp_path, monkeypatch)
    nid_path = tmp_path / "nids.json"
    nid_path.write_text("{}", encoding="utf-8")

    run = analyze_psp_modules(tmp_path, nid_db_paths=(nid_path,))

    assert isinstance(run.links, _Links)
    assert run.links.database is not None
    assert toolkit.loaded_nid_paths == (nid_path,)
