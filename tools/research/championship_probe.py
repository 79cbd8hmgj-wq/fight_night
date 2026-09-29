from __future__ import annotations

import json
from pathlib import Path
import struct

import rabbitizer
from pspdisasm.elf32 import parse_elf32

TARGETS = [
    "GetRankingInformation",
    "aCurrentBeltHolders",
    "GetMyCareerStatsInfo",
    "aiTitleBeltsWon",
    "aiTitleBeltsDefended",
    "aiTitleBeltsLost",
    "aiTitleBeltsForfeited",
    "GetTrophyCaseInfo",
    "GetTrophyInfo",
    "GetViewAwardInfo",
    "strTrophyName",
    "strTrophyOwner",
    "strTimesDefended",
    "iTrophyID",
    "aTrophyIDs",
    "aTrophyTypes",
    "GetIndividualContractInfo",
    "strFightType",
    "INFO_Awards_0",
    "INFO_Awards_1",
    "INFO_Awards_7",
    "INFO_Awards_15",
    "INFO_Awards_16",
    "INFO_Awards_20",
    "INFO_Awards_21",
    "INFO_Awards_22",
    "INFO_Awards_28",
    "INFO_Awards_Unknown",
]

def offset_to_vaddr(elf, offset: int) -> int | None:
    for ph in elf.program_headers:
        if ph.type == 1 and ph.offset <= offset < ph.offset + ph.filesz:
            return ph.vaddr + (offset - ph.offset)
    for sec in elf.sections:
        if sec.type != 8 and sec.offset <= offset < sec.offset + sec.size:
            return sec.addr + (offset - sec.offset)
    return None

def sign16(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value

def words_for_section(raw: bytes, section):
    end = section.offset + section.size - (section.size % 4)
    for off in range(section.offset, end, 4):
        yield section.addr + (off - section.offset), struct.unpack_from("<I", raw, off)[0]

def references_to_address(raw: bytes, elf, target: int) -> list[int]:
    refs: set[int] = set()
    low = target & 0xFFFF
    hi_ori = (target >> 16) & 0xFFFF
    hi_addiu = ((target + 0x8000) >> 16) & 0xFFFF

    for sec in elf.sections:
        if sec.kind != "executable" or sec.size < 8:
            continue
        words = list(words_for_section(raw, sec))
        for i, (addr, word) in enumerate(words):
            op = word >> 26
            if op != 0x0F:  # LUI
                continue
            rt = (word >> 16) & 0x1F
            imm = word & 0xFFFF
            if imm not in {hi_ori, hi_addiu}:
                continue
            for j in range(i + 1, min(i + 13, len(words))):
                addr2, word2 = words[j]
                op2 = word2 >> 26
                rs2 = (word2 >> 21) & 0x1F
                rt2 = (word2 >> 16) & 0x1F
                imm2 = word2 & 0xFFFF
                if rs2 != rt or rt2 != rt:
                    continue
                if op2 == 0x0D and imm == hi_ori and imm2 == low:  # ORI
                    refs.add(addr2)
                elif op2 == 0x09 and imm == hi_addiu and imm2 == low:  # ADDIU
                    refs.add(addr2)
    return sorted(refs)

def vaddr_word(raw: bytes, elf, address: int) -> int | None:
    off = elf.vaddr_to_offset(address)
    if off is None or off + 4 > len(raw):
        return None
    return struct.unpack_from("<I", raw, off)[0]

def is_stack_prologue(word: int) -> bool:
    op = word >> 26
    rs = (word >> 21) & 0x1F
    rt = (word >> 16) & 0x1F
    imm = sign16(word & 0xFFFF)
    return op == 0x09 and rs == 29 and rt == 29 and imm < 0

def function_bounds(raw: bytes, elf, address: int) -> tuple[int, int]:
    start = address & ~3
    for candidate in range(start, max(-4, start - 0x1000), -4):
        word = vaddr_word(raw, elf, candidate)
        if word is not None and is_stack_prologue(word):
            start = candidate
            break

    end = min(start + 0x2000, address + 0x1800)
    cursor = max(address, start)
    while cursor < end:
        word = vaddr_word(raw, elf, cursor)
        if word == 0x03E00008:  # jr $ra
            return start, cursor + 8
        cursor += 4
    return start, min(end, start + 0x800)

def disasm_range(raw: bytes, elf, start: int, end: int) -> list[str]:
    rows = []
    for addr in range(start, end, 4):
        word = vaddr_word(raw, elf, addr)
        if word is None:
            break
        ins = rabbitizer.Instruction(word, category=rabbitizer.InstrCategory.R4000ALLEGREX)
        ins.vram = addr
        rows.append(f"0x{addr:08X}: {word:08X}  {ins.disassemble()}")
        if len(rows) >= 320:
            rows.append("...TRUNCATED...")
            break
    return rows

def pointer_locations(raw: bytes, elf, target: int) -> list[int]:
    needle = struct.pack("<I", target)
    out = []
    start = 0
    while True:
        off = raw.find(needle, start)
        if off < 0:
            break
        va = offset_to_vaddr(elf, off)
        if va is not None:
            out.append(va)
        start = off + 1
    return out[:64]

def main() -> None:
    path = Path("BOOT.BIN")
    raw = path.read_bytes()
    elf = parse_elf32(raw)

    rows = []
    all_xrefs: set[int] = set()
    for target in TARGETS:
        needle = target.encode("ascii") + b"\0"
        locs = []
        pos = 0
        while True:
            off = raw.find(needle, pos)
            if off < 0:
                break
            va = offset_to_vaddr(elf, off)
            direct = references_to_address(raw, elf, va) if va is not None else []
            for x in direct:
                all_xrefs.add(x)
            locs.append({
                "file_offset": f"0x{off:X}",
                "vaddr": f"0x{va:08X}" if va is not None else None,
                "direct_code_xrefs": [f"0x{x:08X}" for x in direct],
                "pointer_locations": [f"0x{x:08X}" for x in pointer_locations(raw, elf, va)] if va is not None else [],
            })
            pos = off + 1
        rows.append({"target": target, "locations": locs})

    functions = {}
    for xref in sorted(all_xrefs):
        start, end = function_bounds(raw, elf, xref)
        key = (start, end)
        if key not in functions:
            functions[key] = {
                "start": f"0x{start:08X}",
                "end": f"0x{end:08X}",
                "xrefs": [],
                "assembly": disasm_range(raw, elf, start, end),
            }
        functions[key]["xrefs"].append(f"0x{xref:08X}")

    # Find all direct halfword writes to the six persistent champion slots.
    champion_write_offsets = {0x50, 0x52, 0x54, 0x56, 0x58, 0x5A}
    champion_writes = []
    seen_bounds = set()
    for sec in elf.sections:
        if sec.kind != "executable" or sec.size < 4:
            continue
        for addr, word in words_for_section(raw, sec):
            op = word >> 26
            imm = word & 0xFFFF
            if op != 0x29 or imm not in champion_write_offsets:  # SH
                continue
            start, end = function_bounds(raw, elf, addr)
            key = (start, end)
            context_start = max(start, addr - 0x50)
            context_end = min(end, addr + 0x70)
            champion_writes.append({
                "address": f"0x{addr:08X}",
                "field_offset": f"0x{imm:02X}",
                "function_start": f"0x{start:08X}",
                "function_end": f"0x{end:08X}",
                "context": disasm_range(raw, elf, context_start, context_end),
            })
            seen_bounds.add(key)

    # Also inventory direct byte writes to the title/trophy-state neighborhood.
    title_state_writes = []
    for sec in elf.sections:
        if sec.kind != "executable" or sec.size < 4:
            continue
        for addr, word in words_for_section(raw, sec):
            op = word >> 26
            imm = word & 0xFFFF
            if op != 0x28 or not (0x15 <= imm <= 0x41):  # SB
                continue
            start, end = function_bounds(raw, elf, addr)
            title_state_writes.append({
                "address": f"0x{addr:08X}",
                "field_offset": f"0x{imm:02X}",
                "function_start": f"0x{start:08X}",
                "context": disasm_range(raw, elf, max(start, addr - 0x28), min(end, addr + 0x38)),
            })

    manual_targets = [0x00194518, 0x00195564, 0x001A10B8, 0x001A1280, 0x001A2C98, 0x001A3FBC, 0x001A4F50, 0x00196DC4, 0x001948C0, 0x0019AAAC, 0x0019BB68, 0x0019CFF8, 0x0019DFE8, 0x001FF120, 0x001FF1B4, 0x00202904, 0x002029A4, 0x00202A84, 0x00202EF4]
    manual_functions = []
    for target in manual_targets:
        start, end = function_bounds(raw, elf, target)
        callers = []
        for sec in elf.sections:
            if sec.kind != "executable" or sec.size < 4:
                continue
            for addr, word in words_for_section(raw, sec):
                if (word >> 26) != 0x03:  # JAL
                    continue
                dest = ((addr + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)
                if dest == target:
                    caller_start, caller_end = function_bounds(raw, elf, addr)
                    callers.append({
                        "call_site": f"0x{addr:08X}",
                        "caller_start": f"0x{caller_start:08X}",
                        "caller_end": f"0x{caller_end:08X}",
                        "context": disasm_range(raw, elf, max(caller_start, addr - 0x40), min(caller_end, addr + 0x50)),
                    })
        manual_functions.append({
            "target": f"0x{target:08X}",
            "start": f"0x{start:08X}",
            "end": f"0x{end:08X}",
            "callers": callers,
            "assembly": disasm_range(raw, elf, start, end),
        })

    focused_ranges = {
        "population_matchmaking_full": disasm_range(raw, elf, 0x00195564, 0x00195810),
        "contract_eligibility_full": disasm_range(raw, elf, 0x001A3FBC, 0x001A4F50),
        "special_contract_scheduler_full": disasm_range(raw, elf, 0x001A4F50, 0x001A5594),
        "champion_transfer_full": disasm_range(raw, elf, 0x00196DC4, 0x00197018),
        "result_title_transfer_region": disasm_range(raw, elf, 0x0019CB00, 0x0019CDA0),
        "result_title_transfer_full": disasm_range(raw, elf, 0x0019CC20, 0x0019CFF8),
        "title_state_helper_1A0E58": disasm_range(raw, elf, 0x001A0E58, 0x001A0E70),
        "title_state_helper_1A0E70": disasm_range(raw, elf, 0x001A0E70, 0x001A1280),
        "title_state_helper_1A1280": disasm_range(raw, elf, 0x001A1280, 0x001A1500),
        "contract_type_resolver": disasm_range(raw, elf, 0x001A2C98, 0x001A2D70),
        "ranking_belt_region": disasm_range(raw, elf, 0x001E2B70, 0x001E2D20),
        "career_stats_title_region": disasm_range(raw, elf, 0x001E2580, 0x001E2888),
        "trophy_title_region": disasm_range(raw, elf, 0x001FE400, 0x001FE850),
        "forfeit_title_tail_a": disasm_range(raw, elf, 0x0019E4D0, 0x0019E630),
        "forfeit_title_tail_b": disasm_range(raw, elf, 0x0019E620, 0x0019E790),
        "division_mapping_helper": disasm_range(raw, elf, 0x0019527C, 0x00195340),
        "career_slot_to_weight_class": disasm_range(raw, elf, 0x001929C4, 0x00192A40),
        "title_record_getter": disasm_range(raw, elf, 0x00192930, 0x001929C4),
        "title_gate_helper": disasm_range(raw, elf, 0x001971A0, 0x00197280),
        "contract_info_region": disasm_range(raw, elf, 0x001FF0D0, 0x001FF430),
        "award_label_region": disasm_range(raw, elf, 0x00202880, 0x00203020),
        "division_change_tail": disasm_range(raw, elf, 0x00195340, 0x00195430),
        "match_descriptor_predicate_a": disasm_range(raw, elf, 0x001A2400, 0x001A2460),
        "match_descriptor_predicate_b": disasm_range(raw, elf, 0x001A2460, 0x001A24C4),
        "match_descriptor_value_helper": disasm_range(raw, elf, 0x001A248C, 0x001A24C4),
        "match_descriptor_reciprocal": disasm_range(raw, elf, 0x001A24C4, 0x001A25A0),
        "population_matchmaking_scheduler": disasm_range(raw, elf, 0x00195564, 0x00195810),
        "special_contract_scheduler": disasm_range(raw, elf, 0x001A4F50, 0x001A5594),
        "shared_result_entry": disasm_range(raw, elf, 0x0019AAAC, 0x0019AD40),
        "shared_result_title_dispatch": disasm_range(raw, elf, 0x0019AD40, 0x0019B2C0),
        "shared_progression_dispatch": disasm_range(raw, elf, 0x0019AAAC, 0x0019B2C0),
        "title_counter_gate_0": disasm_range(raw, elf, 0x0019B180, 0x0019B350),
        "title_counter_gate_1": disasm_range(raw, elf, 0x0019B380, 0x0019B4F0),
        "title_counter_gate_2": disasm_range(raw, elf, 0x0019B540, 0x0019B690),
        "title_counter_gate_3": disasm_range(raw, elf, 0x0019B700, 0x0019B870),
        "title_counter_gate_4": disasm_range(raw, elf, 0x0019B8E0, 0x0019BA30),
        "shared_progression_title_counters_a": disasm_range(raw, elf, 0x0019B2C0, 0x0019B390),
        "shared_progression_title_counters_b": disasm_range(raw, elf, 0x0019B460, 0x0019B530),
        "shared_progression_title_counters_c": disasm_range(raw, elf, 0x0019B600, 0x0019B6D0),
        "shared_progression_title_counters_d": disasm_range(raw, elf, 0x0019B7D0, 0x0019B8A0),
        "shared_progression_title_counters_e": disasm_range(raw, elf, 0x0019B9B0, 0x0019BA80),
        "contract_eligibility_head": disasm_range(raw, elf, 0x001A3FBC, 0x001A44BC),
        "contract_eligibility_tail": disasm_range(raw, elf, 0x001A44BC, 0x001A49BC),
    }

    def read_c_string(address: int) -> str | None:
        off = elf.vaddr_to_offset(address)
        if off is None:
            fallback = address + 0x100
            off = fallback if 0 <= fallback < len(raw) else None
        if off is None:
            return None
        end = raw.find(b"\0", off, min(len(raw), off + 256))
        if end < 0:
            return None
        try:
            return raw[off:end].decode("utf-8")
        except UnicodeDecodeError:
            return None

    named_string_addresses = [
        0x0050BB58, 0x0050BB70, 0x0050BB78, 0x0050BB88, 0x0050BB9C, 0x0050BBB0,
        0x0050BBC8, 0x0050BBD8, 0x0050BBF0, 0x0050BC04, 0x0050BC1C, 0x0050BC2C,
        0x0050BC3C, 0x0050BC4C, 0x0050BC54, 0x0050BC60, 0x0050BC74, 0x0050BC80,
        0x0050BC8C, 0x0050BC94, 0x0050BC9C, 0x0050BCA0, 0x0050BCA4, 0x0050BCA8,
        0x0050BCD0, 0x0050BCE0, 0x0050BCEC, 0x0050BD00, 0x0050BD10, 0x0050BD1C,
        0x0050BD28, 0x0050D698, 0x0050D6AC, 0x0050D6BC, 0x0050D6FC,
        0x0050D748, 0x0050D758, 0x0050D768, 0x0050D778, 0x0050D788, 0x0050D798,
        0x0050D7A8, 0x0050D7BC, 0x0050D7D8, 0x0050D8B8, 0x0050D8CC,
        0x0050D8E0, 0x0050D8F8, 0x0050D904, 0x0050D918, 0x0050D924,
        0x0050D938, 0x0050D948, 0x0050D95C, 0x0050D964, 0x0050D96C,
        0x0050D978, 0x0050D98C, 0x0050D9A8, 0x0050D9B8,
    ]
    named_strings = {
        f"0x{address:08X}": read_c_string(address)
        for address in named_string_addresses
    }

    # Stored contract type -> post-fight career/title dispatch in 0x0019AAAC.
    result_contract_jump_table = []
    for index in range(25):
        address = 0x00508478 + index * 4
        target = vaddr_word(raw, elf, address)
        result_contract_jump_table.append({
            "contract_type": index + 2,
            "jump_target": f"0x{target:08X}" if target is not None else None,
            "case_assembly": disasm_range(raw, elf, target, min(target + 0xA0, 0x0019BB68)) if target is not None else [],
        })

    # Contract-type -> title-state/counter dispatch after the shared result prelude.
    title_counter_jump_table = []
    for index in range(20):
        address = 0x005084E0 + index * 4
        target = vaddr_word(raw, elf, address)
        title_counter_jump_table.append({
            "contract_type": index + 3,
            "jump_target": f"0x{target:08X}" if target is not None else None,
            "case_assembly": disasm_range(raw, elf, target, min(target + 0xC0, 0x0019BB68)) if target is not None else [],
        })

    # Contract-type -> eligibility precheck switch in 0x001A3FBC.
    eligibility_jump_table = []
    for index in range(27):
        address = 0x00508A08 + index * 4
        target = vaddr_word(raw, elf, address)
        eligibility_jump_table.append({
            "contract_type": index + 1,
            "jump_target": f"0x{target:08X}" if target is not None else None,
            "case_assembly": disasm_range(raw, elf, target, min(target + 0x90, 0x001A4684)) if target is not None else [],
        })

    # Contract-type -> special/live-contract scheduler switch in 0x001A4F50.
    scheduler_jump_table = []
    for index in range(26):
        address = 0x00508C60 + index * 4
        target = vaddr_word(raw, elf, address)
        scheduler_jump_table.append({
            "contract_type": index + 2,
            "jump_target": f"0x{target:08X}" if target is not None else None,
            "case_assembly": disasm_range(raw, elf, target, min(target + 0xA0, 0x001A5594)) if target is not None else [],
        })

    # Contract-type -> award-label switch used by individual contract info.
    award_jump_table = []
    for index in range(20):
        address = 0x0050E498 + index * 4
        off = elf.vaddr_to_offset(address)
        target = struct.unpack_from("<I", raw, off)[0] if off is not None else 0
        award_jump_table.append({
            "contract_type": index + 3,
            "jump_target": f"0x{target:08X}",
        })

    contract_label_addresses = [
        0x0050DF38, 0x0050DF48, 0x0050DF58, 0x0050DF68, 0x0050DF78,
        0x0050DF88, 0x0050DF98, 0x0050DFA8, 0x0050DFB8, 0x0050DFC8,
        0x0050DFD8, 0x0050DFE8, 0x0050DFF8, 0x0050E008, 0x0050E018,
        0x0050E028, 0x0050E038, 0x0050E048, 0x0050E058, 0x0050E068,
        0x0050E078, 0x0050E088, 0x0050E098, 0x0050E0A8, 0x0050E0B8,
        0x0050E0C8, 0x0050E0D8,
    ]
    contract_label_address_strings = {
        f"0x{address:08X}": read_c_string(address)
        for address in contract_label_addresses
    }

    # Title-stat byte writers in the career-system address range. These are
    # kept separate from profile award-state bytes (+0x1C..+0x20).
    title_stat_writes = []
    for sec in elf.sections:
        if sec.kind != "executable" or sec.size < 4:
            continue
        for addr, word in words_for_section(raw, sec):
            if not (0x00190000 <= addr < 0x001B0000):
                continue
            op = word >> 26
            imm = word & 0xFFFF
            if op != 0x28 or imm not in {0x15, 0x16, 0x17, 0x18}:
                continue
            start, end = function_bounds(raw, elf, addr)
            title_stat_writes.append({
                "address": f"0x{addr:08X}",
                "field_offset": f"0x{imm:02X}",
                "function_start": f"0x{start:08X}",
                "context": disasm_range(raw, elf, max(start, addr - 0x40), min(end, addr + 0x50)),
            })

    # Computed accesses to progression-record title-stat offsets. Direct SB/LB
    # scans miss the common pattern "addiu ptr, record, +0x17; lbu/sb 0(ptr)".
    title_stat_pointer_adjusts = []
    for sec in elf.sections:
        if sec.kind != "executable" or sec.size < 4:
            continue
        for addr, word in words_for_section(raw, sec):
            if not (0x00190000 <= addr < 0x001B0000):
                continue
            op = word >> 26
            imm = word & 0xFFFF
            if op != 0x09 or imm not in {0x15, 0x16, 0x17, 0x18}:  # ADDIU
                continue
            rs = (word >> 21) & 0x1F
            rt = (word >> 16) & 0x1F
            start, end = function_bounds(raw, elf, addr)
            title_stat_pointer_adjusts.append({
                "address": f"0x{addr:08X}",
                "offset": f"0x{imm:02X}",
                "base_reg": rs,
                "dest_reg": rt,
                "function_start": f"0x{start:08X}",
                "context": disasm_range(raw, elf, max(start, addr - 0x30), min(end, addr + 0x40)),
            })

    def scan_string_region(start_vaddr: int, end_vaddr: int) -> list[dict[str, str]]:
        rows = []
        start_off = elf.vaddr_to_offset(start_vaddr)
        end_off = elf.vaddr_to_offset(end_vaddr)
        if start_off is None or end_off is None:
            return rows
        end_off = min(len(raw), end_off)
        off = start_off
        while off < end_off:
            while off < end_off and not (0x20 <= raw[off] <= 0x7E):
                off += 1
            if off >= end_off:
                break
            begin = off
            while off < end_off and 0x20 <= raw[off] <= 0x7E:
                off += 1
            if off < end_off and raw[off] == 0 and off - begin >= 4:
                try:
                    value = raw[begin:off].decode("ascii")
                except UnicodeDecodeError:
                    value = ""
                if value:
                    rows.append({
                        "vaddr": f"0x{(start_vaddr + (begin - start_off)):08X}",
                        "value": value,
                    })
            off += 1
        return rows

    contract_label_strings = scan_string_region(0x0050DEC0, 0x0050E100)
    contract_detail_strings = scan_string_region(0x0050E820, 0x0050EC20)

    def local_string_refs(start: int, end: int) -> list[dict[str, str]]:
        refs: dict[int, str] = {}
        words = []
        for addr in range(start, end, 4):
            word = vaddr_word(raw, elf, addr)
            if word is None:
                continue
            words.append((addr, word))
        for i, (addr, word) in enumerate(words):
            if (word >> 26) != 0x0F:  # LUI
                continue
            rt = (word >> 16) & 0x1F
            hi = word & 0xFFFF
            for j in range(i + 1, min(i + 6, len(words))):
                addr2, w2 = words[j]
                op2 = w2 >> 26
                rs2 = (w2 >> 21) & 0x1F
                rt2 = (w2 >> 16) & 0x1F
                if rs2 != rt or rt2 != rt:
                    continue
                imm = w2 & 0xFFFF
                target = None
                if op2 == 0x09:  # ADDIU
                    target = ((hi << 16) + sign16(imm)) & 0xFFFFFFFF
                elif op2 == 0x0D:  # ORI
                    target = ((hi << 16) | imm) & 0xFFFFFFFF
                if target is None:
                    continue
                value = read_c_string(target)
                if value is not None and value and all((ord(ch) >= 0x20 or ch in "\\t") for ch in value):
                    refs[target] = value
        return [{"address": f"0x{k:08X}", "value": v} for k, v in sorted(refs.items())]

    contract_cases = []
    for index in range(20):
        type_id = index + 3
        target = vaddr_word(raw, elf, 0x0050E498 + index * 4)
        if target is None:
            continue
        contract_cases.append({
            "type_id": type_id,
            "target": f"0x{target:08X}",
            "string_refs": local_string_refs(target, target + 0x120),
            "assembly": disasm_range(raw, elf, target, target + 0x120),
        })
    title_gate_table = []
    for i in range(20):
        dest = vaddr_word(raw, elf, 0x00508220 + i * 4)
        title_gate_table.append({
            "state": i + 3,
            "target": f"0x{dest:08X}" if dest is not None else None,
            "value": 1 if dest == 0x001971D0 else (0 if dest == 0x001971D8 else None),
        })
    secondary_gate_table = []
    for i in range(8):
        dest = vaddr_word(raw, elf, 0x00508270 + i * 4)
        secondary_gate_table.append({
            "state": i + 2,
            "target": f"0x{dest:08X}" if dest is not None else None,
            "value": 1 if dest == 0x00197210 else (0 if dest == 0x00197218 else None),
        })

    eligibility_cases = []
    for index in range(27):
        type_id = index + 1
        target = vaddr_word(raw, elf, 0x00508A08 + index * 4)
        if target is None:
            continue
        eligibility_cases.append({
            "type_id": type_id,
            "target": f"0x{target:08X}",
            "assembly": disasm_range(raw, elf, target, min(target + 0xC0, 0x001A4684)),
        })


    # Find title-counter mutations tied specifically to the progression-record getter
    # 0x001928F0.  This avoids confusing profile/stack bytes at the same small
    # offsets (+0x15..+0x18) with progression-record title statistics.
    progression_title_counter_sequences = []
    for sec in elf.sections:
        if sec.kind != "executable" or sec.size < 4:
            continue
        words = list(words_for_section(raw, sec))
        for i, (addr, word) in enumerate(words):
            if not (0x00190000 <= addr < 0x001B0000):
                continue
            if (word >> 26) != 0x03:  # JAL
                continue
            dest = ((addr + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)
            if dest != 0x001928F0:
                continue
            window = words[max(0, i - 5): min(len(words), i + 28)]
            interesting = False
            for _waddr, w in window:
                op = w >> 26
                imm = w & 0xFFFF
                # load/store/addiu family using the four title-stat offsets.
                if imm in {0x15, 0x16, 0x17, 0x18} and op in {
                    0x08, 0x09, 0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2B
                }:
                    interesting = True
                    break
            if interesting:
                progression_title_counter_sequences.append({
                    "getter_call": f"0x{addr:08X}",
                    "function_start": f"0x{function_bounds(raw, elf, addr)[0]:08X}",
                    "context": disasm_range(
                        raw, elf,
                        max(function_bounds(raw, elf, addr)[0], addr - 0x18),
                        min(function_bounds(raw, elf, addr)[1], addr + 0x70),
                    ),
                })

    semantic_terms = [
        b"eliminator", b"challenger", b"contender", b"mandatory",
        b"title shot", b"championship", b"defend", b"forfeit",
    ]
    semantic_string_hits = {}
    lower_raw = raw.lower()
    for term in semantic_terms:
        hits = []
        pos = 0
        while True:
            off = lower_raw.find(term, pos)
            if off < 0:
                break
            start = off
            while start > 0 and 0x20 <= raw[start - 1] <= 0x7E:
                start -= 1
            end = off
            while end < len(raw) and 0x20 <= raw[end] <= 0x7E:
                end += 1
            try:
                value = raw[start:end].decode("ascii")
            except UnicodeDecodeError:
                value = None
            hits.append({
                "file_offset": f"0x{off:X}",
                "vaddr": (
                    f"0x{offset_to_vaddr(elf, off):08X}"
                    if offset_to_vaddr(elf, off) is not None else None
                ),
                "string": value,
            })
            pos = off + len(term)
        semantic_string_hits[term.decode("ascii")] = hits[:64]


    # Candidate semantics for progression record+0x13, which the weekly world
    # tick decrements.  Collect getter-tied accesses so post-fight setters can
    # be distinguished from unrelated objects that also have a +0x13 byte.
    progression_cooldown_sequences = []
    for sec in elf.sections:
        if sec.kind != "executable" or sec.size < 4:
            continue
        words = list(words_for_section(raw, sec))
        for i, (addr, word) in enumerate(words):
            if not (0x00190000 <= addr < 0x001B8000):
                continue
            if (word >> 26) != 0x03:
                continue
            dest = ((addr + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)
            if dest != 0x001928F0:
                continue
            window = words[max(0, i - 6): min(len(words), i + 24)]
            if not any((w & 0xFFFF) == 0x13 for _wa, w in window):
                continue
            progression_cooldown_sequences.append({
                "getter_call": f"0x{addr:08X}",
                "function_start": f"0x{function_bounds(raw, elf, addr)[0]:08X}",
                "context": disasm_range(
                    raw, elf,
                    max(function_bounds(raw, elf, addr)[0], addr - 0x20),
                    min(function_bounds(raw, elf, addr)[1], addr + 0x68),
                ),
            })

    print("CHAMPIONSHIP_PROBE_BEGIN")
    print(json.dumps({
        "targets": rows,
        "functions": list(functions.values()),
        "champion_halfword_writes": champion_writes,
        "title_state_byte_writes": title_state_writes,
        "manual_functions": manual_functions,
        "focused_ranges": focused_ranges,
        "named_strings": named_strings,
        "result_contract_jump_table": result_contract_jump_table,
        "title_counter_jump_table": title_counter_jump_table,
        "eligibility_jump_table": eligibility_jump_table,
        "scheduler_jump_table": scheduler_jump_table,
        "contract_label_address_strings": contract_label_address_strings,
        "contract_label_strings": contract_label_strings,
        "contract_detail_strings": contract_detail_strings,
        "contract_cases": contract_cases,
        "title_gate_table": title_gate_table,
        "secondary_gate_table": secondary_gate_table,
        "eligibility_cases": eligibility_cases,
        "title_stat_writes": title_stat_writes,
        "title_stat_pointer_adjusts": title_stat_pointer_adjusts,
        "progression_title_counter_sequences": progression_title_counter_sequences,
        "progression_cooldown_sequences": progression_cooldown_sequences,
        "semantic_string_hits": semantic_string_hits,
    }, indent=2))
    print("CHAMPIONSHIP_PROBE_END")

if __name__ == "__main__":
    main()
