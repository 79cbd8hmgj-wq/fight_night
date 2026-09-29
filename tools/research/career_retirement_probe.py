from __future__ import annotations

import json
from pathlib import Path
import struct

import rabbitizer
from pspdisasm.elf32 import parse_elf32


TARGET_STRINGS = (
    "iRetired",
    "iRetireContractID",
    "GetNextEventState",
    "GetCareerCentralInfo",
)

# Existing evidence places the Career Mode/contract implementation in this
# retail BOOT.BIN neighborhood. Keep the scan bounded to avoid noisy global
# offset-zero stores.
CAREER_START = 0x00190000
CAREER_END = 0x00210000


def sign16(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def words_for_section(raw: bytes, section):
    end = section.offset + section.size - (section.size % 4)
    for off in range(section.offset, end, 4):
        yield section.addr + (off - section.offset), struct.unpack_from("<I", raw, off)[0]


def vaddr_word(raw: bytes, elf, address: int) -> int | None:
    off = elf.vaddr_to_offset(address)
    if off is None or off + 4 > len(raw):
        return None
    return struct.unpack_from("<I", raw, off)[0]


def offset_to_vaddr(elf, offset: int) -> int | None:
    for ph in elf.program_headers:
        if ph.type == 1 and ph.offset <= offset < ph.offset + ph.filesz:
            return ph.vaddr + (offset - ph.offset)
    for sec in elf.sections:
        if sec.type != 8 and sec.offset <= offset < sec.offset + sec.size:
            return sec.addr + (offset - sec.offset)
    return None


def is_stack_prologue(word: int) -> bool:
    op = word >> 26
    rs = (word >> 21) & 0x1F
    rt = (word >> 16) & 0x1F
    return op == 0x09 and rs == 29 and rt == 29 and sign16(word & 0xFFFF) < 0


def function_bounds(raw: bytes, elf, address: int) -> tuple[int, int]:
    start = address & ~3
    for candidate in range(start, max(-4, start - 0x1000), -4):
        word = vaddr_word(raw, elf, candidate)
        if word is not None and is_stack_prologue(word):
            start = candidate
            break

    cursor = max(address, start)
    limit = min(start + 0x2000, address + 0x1800)
    while cursor < limit:
        word = vaddr_word(raw, elf, cursor)
        if word == 0x03E00008:
            return start, cursor + 8
        cursor += 4
    return start, min(start + 0x800, limit)


def disasm_range(raw: bytes, elf, start: int, end: int, limit: int = 100) -> list[str]:
    rows: list[str] = []
    for addr in range(start, end, 4):
        word = vaddr_word(raw, elf, addr)
        if word is None:
            break
        ins = rabbitizer.Instruction(word, category=rabbitizer.InstrCategory.R4000ALLEGREX)
        ins.vram = addr
        rows.append(f"0x{addr:08X}: {word:08X}  {ins.disassemble()}")
        if len(rows) >= limit:
            rows.append("...TRUNCATED...")
            break
    return rows


def references_to_address(raw: bytes, elf, target: int) -> list[int]:
    refs: set[int] = set()
    low = target & 0xFFFF
    hi_ori = (target >> 16) & 0xFFFF
    hi_addiu = ((target + 0x8000) >> 16) & 0xFFFF

    for sec in elf.sections:
        if sec.kind != "executable" or sec.size < 8:
            continue
        words = list(words_for_section(raw, sec))
        for i, (_, word) in enumerate(words):
            if (word >> 26) != 0x0F:
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
                if op2 == 0x0D and imm == hi_ori and imm2 == low:
                    refs.add(addr2)
                elif op2 == 0x09 and imm == hi_addiu and imm2 == low:
                    refs.add(addr2)
    return sorted(refs)



def written_register(word: int) -> int | None:
    op = word >> 26
    if op == 0:
        funct = word & 0x3F
        if funct in {0x08, 0x0C, 0x0D}:  # jr/syscall/break
            return None
        return (word >> 11) & 0x1F
    if op in {
        0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
        0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26,
    }:
        return (word >> 16) & 0x1F
    if op == 0x03:  # jal
        return 31
    return None


def propagated_source_register(word: int) -> int | None:
    if (word >> 26) != 0:
        return None
    rs = (word >> 21) & 0x1F
    rt = (word >> 16) & 0x1F
    funct = word & 0x3F
    if funct in {0x21, 0x25}:  # addu/or pseudo-move forms
        if rt == 0:
            return rs
        if rs == 0:
            return rt
    return None


def loaded_constant(word: int) -> int | None:
    op = word >> 26
    rs = (word >> 21) & 0x1F
    imm = word & 0xFFFF
    if rs != 0:
        return None
    if op == 0x09:
        return sign16(imm)
    if op == 0x0D:
        return imm
    return None


def strict_profile_zero_writers(raw: bytes, elf) -> list[dict]:
    rows = []
    caller_saved = {2, 3, 4, 5, 6, 7, *range(8, 16), 24, 25, 31}
    for sec in elf.sections:
        if sec.kind != "executable":
            continue
        profile_regs: set[int] = set()
        constants: dict[int, int] = {}
        current_start = sec.addr
        for addr, word in words_for_section(raw, sec):
            if not (CAREER_START <= addr < CAREER_END):
                continue
            if is_stack_prologue(word):
                profile_regs.clear()
                constants.clear()
                current_start = addr

            op = word >> 26
            rs = (word >> 21) & 0x1F
            rt = (word >> 16) & 0x1F
            imm = word & 0xFFFF

            if op == 0x28 and imm == 0 and rs in profile_regs:
                start, end = function_bounds(raw, elf, addr)
                rows.append(
                    {
                        "address": f"0x{addr:08X}",
                        "function_start": f"0x{start:08X}",
                        "base_reg": rs,
                        "value_reg": rt,
                        "known_value": constants.get(rt),
                        "context": disasm_range(
                            raw,
                            elf,
                            max(start, addr - 0x90),
                            min(end, addr + 0x80),
                            120,
                        ),
                    }
                )

            dest = written_register(word)
            source = propagated_source_register(word)
            const = loaded_constant(word)

            if op == 0x23 and imm == 0x003C:
                profile_regs.discard(rt)
                profile_regs.add(rt)
            elif dest is not None:
                was_profile_alias = source in profile_regs if source is not None else False
                profile_regs.discard(dest)
                if was_profile_alias:
                    profile_regs.add(dest)

            if dest is not None:
                constants.pop(dest, None)
                if const is not None:
                    constants[dest] = const
                elif source is not None and source in constants:
                    constants[dest] = constants[source]

            if op == 0x03:
                for reg in caller_saved:
                    profile_regs.discard(reg)
                    constants.pop(reg, None)

            if word == 0x03E00008:
                profile_regs.clear()
                constants.clear()
                current_start = addr + 8
    return rows

def main() -> None:
    raw = Path("BOOT.BIN").read_bytes()
    elf = parse_elf32(raw)

    string_xrefs = []
    for target in TARGET_STRINGS:
        needle = target.encode("ascii") + b"\0"
        pos = 0
        while True:
            off = raw.find(needle, pos)
            if off < 0:
                break
            va = offset_to_vaddr(elf, off)
            refs = references_to_address(raw, elf, va) if va is not None else []
            entries = []
            for ref in refs:
                start, end = function_bounds(raw, elf, ref)
                entries.append(
                    {
                        "xref": f"0x{ref:08X}",
                        "function_start": f"0x{start:08X}",
                        "context": disasm_range(
                            raw,
                            elf,
                            max(start, ref - 0x50),
                            min(end, ref + 0x80),
                            70,
                        ),
                    }
                )
            string_xrefs.append(
                {
                    "string": target,
                    "vaddr": f"0x{va:08X}" if va is not None else None,
                    "references": entries,
                }
            )
            pos = off + 1

    # Inventory direct byte stores to +0 in the career/contract implementation.
    # The retired flag is profile+0x00, but +0 stores on unrelated objects also
    # exist, so these are candidates rather than semantic claims.
    zero_byte_stores = []
    for sec in elf.sections:
        if sec.kind != "executable":
            continue
        for addr, word in words_for_section(raw, sec):
            if not (CAREER_START <= addr < CAREER_END):
                continue
            if (word >> 26) != 0x28 or (word & 0xFFFF) != 0:
                continue
            start, end = function_bounds(raw, elf, addr)
            zero_byte_stores.append(
                {
                    "address": f"0x{addr:08X}",
                    "base_reg": (word >> 21) & 0x1F,
                    "value_reg": (word >> 16) & 0x1F,
                    "function_start": f"0x{start:08X}",
                    "context": disasm_range(
                        raw,
                        elf,
                        max(start, addr - 0x50),
                        min(end, addr + 0x70),
                        80,
                    ),
                }
            )

    # Stronger structural candidates: function loads a pointer from +0x3C
    # (the proven Career Central profile-pointer field) and later stores a byte
    # to +0 through that same register. This only matches direct same-register
    # dataflow and intentionally misses transformed/aliased cases.
    profile_direct_writers = []
    for sec in elf.sections:
        if sec.kind != "executable":
            continue
        words = list(words_for_section(raw, sec))
        for i, (addr, word) in enumerate(words):
            if not (CAREER_START <= addr < CAREER_END):
                continue
            if (word >> 26) != 0x23 or (word & 0xFFFF) != 0x003C:
                continue
            profile_reg = (word >> 16) & 0x1F
            start, end = function_bounds(raw, elf, addr)
            for j in range(i + 1, min(i + 96, len(words))):
                addr2, word2 = words[j]
                if addr2 >= end:
                    break
                if (word2 >> 26) != 0x28 or (word2 & 0xFFFF) != 0:
                    continue
                if ((word2 >> 21) & 0x1F) != profile_reg:
                    continue
                profile_direct_writers.append(
                    {
                        "profile_load": f"0x{addr:08X}",
                        "store": f"0x{addr2:08X}",
                        "profile_reg": profile_reg,
                        "value_reg": (word2 >> 16) & 0x1F,
                        "function_start": f"0x{start:08X}",
                        "context": disasm_range(
                            raw,
                            elf,
                            max(start, addr2 - 0x80),
                            min(end, addr2 + 0x80),
                            110,
                        ),
                    }
                )

    focused = {}
    for address in (
        0x001CFE54,
        0x001D235C,
        0x001A2C98,
        0x001FF3A0,
        0x001FF6C0,
    ):
        start, end = function_bounds(raw, elf, address)
        focused[f"0x{address:08X}"] = {
            "function_start": f"0x{start:08X}",
            "function_end": f"0x{end:08X}",
            "assembly": disasm_range(raw, elf, start, end, 180),
        }

    print("CAREER_RETIREMENT_PROBE_BEGIN")
    print(
        json.dumps(
            {
                "string_xrefs": string_xrefs,
                "strict_profile_zero_writers": strict_profile_zero_writers(raw, elf),
                "profile_direct_writers": profile_direct_writers,
                "zero_byte_store_candidates": zero_byte_stores[:80],
                "zero_byte_store_candidate_count": len(zero_byte_stores),
                "focused_functions": focused,
            },
            indent=2,
        )
    )
    print("CAREER_RETIREMENT_PROBE_END")


if __name__ == "__main__":
    main()
