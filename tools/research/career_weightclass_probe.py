from __future__ import annotations

import json
from pathlib import Path
import struct

import rabbitizer
from pspdisasm.elf32 import parse_elf32


def sign16(v: int) -> int:
    return v - 0x10000 if v & 0x8000 else v


def words(raw, sec):
    end = sec.offset + sec.size - (sec.size % 4)
    for off in range(sec.offset, end, 4):
        yield sec.addr + (off - sec.offset), struct.unpack_from("<I", raw, off)[0]


def vword(raw, elf, addr):
    off = elf.vaddr_to_offset(addr)
    if off is None or off + 4 > len(raw):
        return None
    return struct.unpack_from("<I", raw, off)[0]


def is_prologue(w: int) -> bool:
    return ((w >> 26) == 0x09 and ((w >> 21) & 31) == 29 and
            ((w >> 16) & 31) == 29 and sign16(w & 0xFFFF) < 0)


def bounds(raw, elf, addr):
    start = addr & ~3
    for p in range(start, max(-4, start - 0x800), -4):
        w = vword(raw, elf, p)
        if w is not None and is_prologue(w):
            start = p
            break
    end = min(start + 0x1200, addr + 0x1000)
    p = max(addr, start)
    while p < end:
        if vword(raw, elf, p) == 0x03E00008:
            return start, p + 8
        p += 4
    return start, min(end, start + 0x600)


def disasm(raw, elf, start, end, limit=120):
    out = []
    for addr in range(start, end, 4):
        w = vword(raw, elf, addr)
        if w is None:
            break
        ins = rabbitizer.Instruction(w, category=rabbitizer.InstrCategory.R4000ALLEGREX)
        ins.vram = addr
        out.append(f"0x{addr:08X}: {w:08X}  {ins.disassemble()}")
        if len(out) >= limit:
            out.append("...TRUNCATED...")
            break
    return out


def jal_callers(raw, elf, target):
    out=[]
    for sec in elf.sections:
        if sec.kind != "executable":
            continue
        for addr,w in words(raw, sec):
            if (w >> 26) != 0x03:
                continue
            dest=((addr+4)&0xF0000000)|((w&0x03FFFFFF)<<2)
            if dest != target:
                continue
            s,e=bounds(raw,elf,addr)
            out.append({
                "call_site":f"0x{addr:08X}",
                "caller_start":f"0x{s:08X}",
                "context":disasm(raw,elf,max(s,addr-0x38),min(e,addr+0x50),56),
            })
    return out


def main():
    raw=Path("BOOT.BIN").read_bytes()
    elf=parse_elf32(raw)

    # The three persistent career-slot -> absolute-weight-class bytes.
    field_accesses=[]
    for sec in elf.sections:
        if sec.kind != "executable":
            continue
        for addr,w in words(raw,sec):
            if not (0x00190000 <= addr < 0x00210000):
                continue
            op=w>>26
            imm=w&0xFFFF
            if imm not in (0x2D,0x2E,0x2F):
                continue
            opname={0x20:"LB",0x24:"LBU",0x28:"SB"}.get(op)
            if opname is None:
                continue
            s,e=bounds(raw,elf,addr)
            field_accesses.append({
                "address":f"0x{addr:08X}",
                "op":opname,
                "offset":f"0x{imm:02X}",
                "function_start":f"0x{s:08X}",
                "context":disasm(raw,elf,max(s,addr-0x48),min(e,addr+0x68),72),
            })

    targets=[0x0019527C,0x001929C4,0x00196DC4,0x0019DFE8]
    callers={f"0x{x:08X}":jal_callers(raw,elf,x) for x in targets}

    focused={
        "division_window_update_region":disasm(raw,elf,0x00195000,0x00195430,320),
        "title_transfer":disasm(raw,elf,0x00196DC4,0x00197018,180),
        "expired_title_processing":disasm(raw,elf,0x0019DFE8,0x0019E790,420),
        "slot_to_class_getter":disasm(raw,elf,0x001929C4,0x001929D4,16),
    }

    print("CAREER_WEIGHTCLASS_PROBE_BEGIN")
    print(json.dumps({
        "slot_weight_class_field_accesses":field_accesses,
        "callers":callers,
        "focused_ranges":focused,
    },indent=2))
    print("CAREER_WEIGHTCLASS_PROBE_END")


if __name__=="__main__":
    main()
