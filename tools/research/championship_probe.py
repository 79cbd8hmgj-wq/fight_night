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
            if op != 0x28 or not (0x1B <= imm <= 0x40):  # SB
                continue
            start, end = function_bounds(raw, elf, addr)
            title_state_writes.append({
                "address": f"0x{addr:08X}",
                "field_offset": f"0x{imm:02X}",
                "function_start": f"0x{start:08X}",
                "context": disasm_range(raw, elf, max(start, addr - 0x28), min(end, addr + 0x38)),
            })

    manual_targets = [0x00196DC4, 0x001948C0, 0x0019BB68, 0x0019CFF8]
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
        "champion_transfer_full": disasm_range(raw, elf, 0x00196DC4, 0x00197018),
        "result_title_transfer_region": disasm_range(raw, elf, 0x0019CB00, 0x0019CDA0),
        "ranking_belt_region": disasm_range(raw, elf, 0x001E2B70, 0x001E2D20),
        "career_stats_title_region": disasm_range(raw, elf, 0x001E2580, 0x001E2888),
        "trophy_title_region": disasm_range(raw, elf, 0x001FE400, 0x001FE850),
        "division_mapping_helper": disasm_range(raw, elf, 0x0019527C, 0x00195340),
        "career_slot_to_weight_class": disasm_range(raw, elf, 0x001929C4, 0x00192A40),
        "title_record_getter": disasm_range(raw, elf, 0x00192930, 0x001929C4),
        "title_gate_helper": disasm_range(raw, elf, 0x001971A0, 0x00197280),
    }

    def read_c_string(address: int) -> str | None:
        off = elf.vaddr_to_offset(address)
        if off is None:
            return None
        end = raw.find(b"\\0", off, min(len(raw), off + 256))
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

    print("CHAMPIONSHIP_PROBE_BEGIN")
    print(json.dumps({
        "targets": rows,
        "functions": list(functions.values()),
        "champion_halfword_writes": champion_writes,
        "title_state_byte_writes": title_state_writes,
        "manual_functions": manual_functions,
        "focused_ranges": focused_ranges,
    }, indent=2))
    print("CHAMPIONSHIP_PROBE_END")

if __name__ == "__main__":
    main()
