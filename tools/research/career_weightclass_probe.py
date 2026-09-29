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


def offset_to_vaddr(elf, offset):
    for ph in elf.program_headers:
        if ph.type == 1 and ph.offset <= offset < ph.offset + ph.filesz:
            return ph.vaddr + (offset - ph.offset)
    for sec in elf.sections:
        if sec.type != 8 and sec.offset <= offset < sec.offset + sec.size:
            return sec.addr + (offset - sec.offset)
    return None


def refs_to_address(raw, elf, target):
    refs=set()
    low=target & 0xFFFF
    hi_ori=(target >> 16) & 0xFFFF
    hi_addiu=((target + 0x8000) >> 16) & 0xFFFF
    for sec in elf.sections:
        if sec.kind != "executable":
            continue
        ws=list(words(raw,sec))
        for i,(addr,w) in enumerate(ws):
            if (w >> 26) != 0x0F:
                continue
            rt=(w >> 16)&31
            imm=w&0xFFFF
            if imm not in (hi_ori,hi_addiu):
                continue
            for addr2,w2 in ws[i+1:i+13]:
                op2=w2>>26
                rs2=(w2>>21)&31
                rt2=(w2>>16)&31
                imm2=w2&0xFFFF
                if rs2 != rt or rt2 != rt:
                    continue
                if op2 == 0x0D and imm == hi_ori and imm2 == low:
                    refs.add(addr2)
                elif op2 == 0x09 and imm == hi_addiu and imm2 == low:
                    refs.add(addr2)
    return sorted(refs)


def string_xrefs(raw, elf, names):
    out={}
    for name in names:
        needle=name.encode("ascii")+b"\0"
        hits=[]
        pos=0
        while True:
            off=raw.find(needle,pos)
            if off < 0:
                break
            va=offset_to_vaddr(elf,off)
            refs=refs_to_address(raw,elf,va) if va is not None else []
            hits.append({
                "file_offset":f"0x{off:X}",
                "vaddr":f"0x{va:08X}" if va is not None else None,
                "refs":[{
                    "address":f"0x{x:08X}",
                    "function_start":f"0x{bounds(raw,elf,x)[0]:08X}",
                    "context":disasm(raw,elf,max(bounds(raw,elf,x)[0],x-0x28),min(bounds(raw,elf,x)[1],x+0x38),32),
                } for x in refs],
            })
            pos=off+1
        out[name]=hits
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

    weight_change_strings=string_xrefs(raw,elf,[
        "INFO_Weightclass_Change_Yes",
        "INFO_Weightclass_Change_No",
    ])

    print("CAREER_WEIGHTCLASS_PROBE_BEGIN")
    print(json.dumps({
        "slot_weight_class_field_accesses":field_accesses,
        "callers":callers,
        "focused_ranges":focused,
        "weight_change_string_xrefs":weight_change_strings,
    },indent=2))
    print("CAREER_WEIGHTCLASS_PROBE_END")


if __name__=="__main__":
    main()
