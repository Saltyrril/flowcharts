"""Ассемблер (x86 Intel/AT&T, ARM, AArch64, MIPS, RISC-V, AVR, 6502, 68k) -> IR.

Переходы по меткам изображаются соединителями (ГОСТ 19.701-90, п. 3.4.1), условные переходы –
символом «Решение», вызовы – «Предопределённый процесс».
"""
from __future__ import annotations
import re
from typing import List, Tuple, Dict
from .ir import *

RET = {"ret", "retn", "retf", "retq", "iret", "iretd", "iretq", "rts", "rti", "reti", "sysret", "eret", "leave_ret", "retw"}
HALT = {"hlt", "halt", "stp", "wfi_halt"}
UNCOND = {"jmp", "b", "br", "j", "bra", "rjmp", "ljmp", "goto", "jmpl", "jra", "jmps", "jmpf", "ajmp", "sjmp"}
CALL = {"call", "calll", "callq", "bl", "blx", "jal", "rcall", "jsr", "bsr", "lcall", "acall", "icall", "invoke", "callf"}
LOOPS = {"loop", "loope", "loopz", "loopne", "loopnz"}

# мнемоника -> символ сравнения либо готовое условие по флагу
COND: Dict[str, str] = {}
def _add(names, sym):
    for n in names.split():
        COND[n] = sym
_add("je jz beq breq", "==");  _add("jne jnz bne brne", "!=")
_add("jg jnle bgt", ">");      _add("jge jnl bge brge", ">=")
_add("jl jnge blt brlt", "<"); _add("jle jng ble", "<=")
_add("ja jnbe bhi bgtu", ">"); _add("jae jnb jnc bcs bhs brsh bgeu", ">=")
_add("jb jnae jc bcc blo brlo bltu", "<"); _add("jbe jna bls bleu", "<=")
_add("beqz cbz", "==");  _add("bnez cbnz", "!=")
_add("blez", "<=");      _add("bgtz", ">");  _add("bltz", "<"); _add("bgez", ">=")
FLAGS = {"jo": "OF = 1", "jno": "OF = 0", "js": "SF = 1", "jns": "SF = 0", "jp": "PF = 1", "jnp": "PF = 0",
         "jpe": "PF = 1", "jpo": "PF = 0", "jcxz": "CX = 0", "jecxz": "ECX = 0", "jrcxz": "RCX = 0",
         "bmi": "N = 1", "bpl": "N = 0", "bvs": "V = 1", "bvc": "V = 0", "brmi": "N = 1", "brpl": "N = 0",
         "brvs": "V = 1", "brvc": "V = 0", "brcs": "C = 1", "brcc": "C = 0", "brhs": "H = 1", "brhc": "H = 0",
         "brts": "T = 1", "brtc": "T = 0", "brie": "I = 1", "brid": "I = 0"}
TWO_REG = {"beq", "bne", "blt", "bge", "bgt", "ble", "bltu", "bgeu", "bgtu", "bleu"}
ZERO_BR = {"beqz", "bnez", "blez", "bgtz", "bltz", "bgez", "cbz", "cbnz"}
CMP_LIKE = {"cmp", "cmpl", "cmpq", "cmpw", "cmpb", "cp", "cpi", "cpc", "cmn", "cpx", "cpy", "cmpa", "cmpi", "cmpd", "cmps"}
TEST_LIKE = {"test", "testl", "testq", "testw", "testb", "tst", "bit"}
ARITH = {"sub", "subs", "add", "adds", "dec", "inc", "and", "ands", "or", "orr", "orrs", "xor", "eor", "eors", "neg",
         "shl", "shr", "sar", "sal", "subl", "addl", "decl", "incl", "andl", "orl", "xorl", "subq", "addq", "decq",
         "incq", "dbra", "dec_", "lsl", "lsr", "asr", "sbc", "adc", "sbb", "subi", "dex", "dey", "inx", "iny"}
DIRECTIVES = {"section", "segment", "ends", "global", "globl", "extern", "extrn", "public", "org", "bits", "use16", "use32",
              "assume", "include", "includelib", "model", "stack", "end", "align", "title", "page", "format", "entry",
              "macro", "endm", "equ", "db", "dw", "dd", "dq", "dt", "resb", "resw", "resd", "resq", "times", "struc",
              "ideal", "name", "label", "cpu", "default", "dfsg", "byte", "word", "long", "quad", "ascii", "asciz",
              "string", "space", "data", "code", "text", "bss", "dseg", "cseg", "eseg", "processor", "list", "nolist",
              "device", "def", "cseg", "dseg", "eseg", "set", "syntax", "arch", "thumb", "arm", "type", "size", "file",
              "ident", "comm", "lcomm", "weak", "hidden", "p2align", "option", "mem", "incbin", "export", "import"}
PREFIXES = {"rep", "repe", "repz", "repne", "repnz", "lock", "bnd", "notrack"}
DATA_DEF = re.compile(r"^[\w$.@?]+\s+(?:db|dw|dd|dq|dt|equ|=|resb|resw|resd|resq|rest|struc|segment|ends|label|byte|word|"
                      r"dword|qword|sbyte|sword|sdword|real4|real8|proc|endp)\b", re.I)
LABEL_RX = re.compile(r"^\s*((?:\.?[A-Za-z_$.@?][\w$.@?]*)|\d+)\s*:(?!=)")
SUFFIX_OK = {"mov", "cmp", "test", "add", "sub", "and", "or", "xor", "inc", "dec", "neg", "shl", "shr", "sar", "call", "ret", "push", "pop", "lea"}


def _strip_comment(raw: str) -> Tuple[str, str]:
    quote = None
    for i, ch in enumerate(raw):
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
        elif ch == ";":
            return raw[:i], raw[i + 1:].strip()
        elif raw.startswith("//", i):
            return raw[:i], raw[i + 2:].strip()
        elif ch == "@" and (i == 0 or raw[i - 1].isspace()):
            return raw[:i], raw[i + 1:].strip()
        elif ch == "#" and (raw[:i].strip() == "" or raw[i + 1:i + 2] in ("", " ", "\t")):
            return raw[:i], raw[i + 1:].strip()
    return raw, ""


def _base(mn: str) -> str:
    if mn in SUFFIX_OK or mn in CMP_LIKE or mn in TEST_LIKE or mn in ARITH:
        return mn
    if len(mn) > 2 and mn[-1] in "bwlq" and mn[:-1] in SUFFIX_OK:
        return mn[:-1]
    return mn


def _ops(s: str) -> List[str]:
    out, cur, depth = [], "", 0
    for ch in s:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


class E:
    __slots__ = ("kind", "name", "mn", "ops", "comment", "line", "pre")
    def __init__(self, kind, name="", mn="", ops="", comment="", line=0, pre=""):
        self.kind, self.name, self.mn, self.ops, self.comment, self.line, self.pre = kind, name, mn, ops, comment, line, pre


def parse_asm(src: str, o: Options) -> Tuple[List[Chart], List[str]]:
    src = re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group()), src, flags=re.S)
    entries: List[E] = []
    pending_comments: List[str] = []
    warns: List[str] = []
    num_counter: Dict[str, int] = {}
    for ln, raw in enumerate(src.splitlines(), 1):
        code, comment = _strip_comment(raw.rstrip())
        code = code.strip()
        if not code:
            if comment:
                pending_comments.append(comment)
            elif not raw.strip():
                pending_comments = pending_comments if pending_comments else []
            continue
        while True:
            m = LABEL_RX.match(code)
            if not m:
                break
            name = m.group(1)
            if name.isdigit():
                num_counter[name] = num_counter.get(name, 0) + 1
                name = f"{name}#{num_counter[name]}"
            entries.append(E("label", name=name, line=ln, comment=comment, pre="\n".join(pending_comments)))
            pending_comments = []
            code = code[m.end():].strip()
        if not code:
            continue
        mp = re.match(r"^([\w$.@?]+)\s+(proc|endp)\b", code, re.I)
        if mp:
            entries.append(E("proc" if mp.group(2).lower() == "proc" else "endp", name=mp.group(1), line=ln,
                             pre="\n".join(pending_comments)))
            pending_comments = []
            continue
        if DATA_DEF.match(code):
            pending_comments = []
            continue
        parts = code.split(None, 1)
        mn = parts[0].lower()
        rest = parts[1].strip() if len(parts) > 1 else ""
        if mn.startswith(".") or mn.startswith("%") or (mn in DIRECTIVES and mn not in ("name", "label", "string", "set", "type", "size", "default", "mem", "def", "export", "import")):
            continue
        shown_mn = parts[0]
        if mn in PREFIXES and rest:
            p2 = rest.split(None, 1)
            shown_mn = f"{parts[0]} {p2[0]}"
            mn = p2[0].lower()
            rest = p2[1].strip() if len(p2) > 1 else ""
        entries.append(E("instr", mn=mn, ops=rest, name=shown_mn, comment=comment, line=ln, pre="\n".join(pending_comments)))
        pending_comments = []

    # --- разрешение числовых локальных меток 1b / 1f
    label_positions = [(i, e.name) for i, e in enumerate(entries) if e.kind == "label"]
    for idx, e in enumerate(entries):
        if e.kind != "instr":
            continue
        m = re.search(r"\b(\d+)([bf])\s*$", e.ops)
        if m and (e.mn in UNCOND or e.mn in COND or e.mn in CALL or e.mn in LOOPS):
            num, d = m.group(1), m.group(2)
            cand = [(i, n) for i, n in label_positions if n.startswith(num + "#")]
            if d == "b":
                cand = [c for c in cand if c[0] < idx]
                tgt = cand[-1][1] if cand else None
            else:
                cand = [c for c in cand if c[0] > idx]
                tgt = cand[0][1] if cand else None
            if tgt:
                e.ops = e.ops[:m.start()] + tgt

    labels = {e.name for e in entries if e.kind == "label"} | {e.name for e in entries if e.kind == "proc"}

    def target_of(e: E) -> str:
        ops = _ops(e.ops)
        t = ops[-1] if ops else ""
        t = re.sub(r"^(short|near|far|ptr|offset|dword|qword|word|byte)\s+", "", t, flags=re.I)
        t = re.sub(r"^(short|near|far)\s+", "", t, flags=re.I)
        return t.strip().lstrip("*")

    jump_targets, call_targets = set(), set()
    for e in entries:
        if e.kind != "instr":
            continue
        if e.mn in UNCOND or e.mn in COND or e.mn in FLAGS or e.mn in LOOPS:
            jump_targets.add(target_of(e))
        elif e.mn in CALL:
            call_targets.add(target_of(e))

    # --- разбиение на схемы
    segments: List[Tuple[str, List[E]]] = []
    has_proc = any(e.kind == "proc" for e in entries)
    cur_name, cur = None, []
    if has_proc:
        outside: List[E] = []
        inproc = None
        for e in entries:
            if e.kind == "proc":
                inproc = (e.name, [E("label", name=e.name, pre=e.pre, line=e.line)])
                continue
            if e.kind == "endp":
                if inproc:
                    segments.append((inproc[0], inproc[1]))
                inproc = None
                continue
            (inproc[1] if inproc else outside).append(e)
        if inproc:
            segments.append(inproc)
        if any(x.kind == "instr" for x in outside):
            segments.insert(0, (None, outside))
    else:
        for e in entries:
            if e.kind == "label" and e.name in call_targets and e.name != "":
                if cur:
                    segments.append((cur_name, cur))
                cur_name, cur = e.name, [e]
            else:
                cur.append(e)
        if cur:
            segments.append((cur_name, cur))

    charts: List[Chart] = []
    for name, ents in segments:
        if not any(x.kind == "instr" for x in ents):
            continue
        first_label = next((x for x in ents if x.kind == "label"), None)
        if name is None:
            entry = next((x.name for x in ents if x.kind == "label" and x.name.lower() in ("main", "_start", "start", "_main")), None)
            name = entry or "Основная программа"
            kind = "program"
            comment = ents[0].pre if ents and ents[0].kind == "label" else ""
        else:
            kind = "function"
            comment = first_label.pre if first_label else ""
        body = _convert(ents, labels, jump_targets, o, name)
        ch = Chart(name=name, body=body, signature=name if kind == "function" else "", comment=comment, kind=kind)
        ch.line = first_label.line if first_label and first_label.line else (ents[0].line if ents else 0)
        charts.append(ch)
    return charts, warns


def _imm(x: str) -> str:
    return x[1:] if x.startswith("#") and len(x) > 1 else x


def _cond_text(mn: str, ops: List[str], setter) -> str:
    code = COND.get(mn)
    if mn in FLAGS:
        return FLAGS[mn]
    if mn in ZERO_BR and ops:
        return f"{ops[0]} {code} 0"
    if mn in TWO_REG and len(ops) >= 3:
        return f"{ops[0]} {code} {ops[1]}"
    if setter is not None and code:
        smn, sops = setter
        b = _base(smn)
        so = _ops(sops)
        if b in CMP_LIKE or smn in CMP_LIKE:
            if len(so) >= 2:
                a, bb = so[0], so[1]
                if all(x[:1] in "%$" for x in (a, bb)):   # AT&T: операнды в обратном порядке
                    a, bb = bb, a
                return f"{_imm(a)} {code} {_imm(bb)}"
            if len(so) == 1:
                reg = {"cpx": "X", "cpy": "Y"}.get(smn, "A")
                return f"{reg} {code} {_imm(so[0])}"
        if b in TEST_LIKE or smn in TEST_LIKE:
            if len(so) >= 2:
                a, bb = so[0], so[1]
                if a == bb:
                    return f"{a} {code} 0"
                return f"({a} & {bb}) {code} 0"
        if smn in ARITH or b in ARITH:
            dst = so[0] if so else {"dex": "X", "dey": "Y", "inx": "X", "iny": "Y"}.get(smn, "результат")
            if smn in ("dex", "inx"):
                dst = "X"
            if smn in ("dey", "iny"):
                dst = "Y"
            return f"{dst} {code} 0"
    return f"условие «{mn}»"


def _convert(ents: List[E], labels, jump_targets, o: Options, chart_name: str) -> list:
    stmts: list = []
    group: List[str] = []
    group_cmp: List[bool] = []
    setter = None

    glines: List[int] = []

    def put(node, line, end=None):
        node.line = line
        node.end = end if end is not None else line
        stmts.append(node)

    def flush():
        if group:
            put(Proc("\n".join(group), "asm"), glines[0], glines[-1])
            group.clear()
            group_cmp.clear()
            glines.clear()

    def text_of(e: E) -> str:
        t = (e.name + (" " + e.ops if e.ops else "")).strip()
        if o.asm_comments and e.comment:
            t += "  ; " + e.comment
        return t

    def tgt(e: E) -> str:
        ops = _ops(e.ops)
        t = ops[-1] if ops else ""
        t = re.sub(r"^(short|near|far|ptr|offset)\s+", "", t, flags=re.I)
        return t.strip().lstrip("*")

    for e in ents:
        if e.kind == "label":
            flush()
            if e.name in jump_targets and e.name != chart_name:
                put(Label(e.name), e.line)
            continue
        if e.kind != "instr":
            continue
        mn = e.mn
        ops = _ops(e.ops)
        low = e.ops.lower().replace(" ", "")
        is_ret = (mn in RET or (mn == "bx" and low == "lr") or (mn == "jr" and low in ("$ra", "ra")) or
                  (mn == "mov" and low in ("pc,lr", "pc,r14")) or (mn == "pop" and "pc" in low.strip("{}").split(",")) or
                  (mn == "ldp" and False))
        if is_ret:
            flush()
            put(Ret("возврат" if mn != "pop" else text_of(e)), e.line)
            continue
        if mn in HALT:
            flush()
            put(Ret("останов"), e.line)
            continue
        if mn in COND or mn in FLAGS:
            t = tgt(e)
            if not t or t not in labels:
                flush()
                put(Proc(text_of(e), "predef"), e.line)
                continue
            first_line = e.line
            if group and group_cmp and group_cmp[-1]:
                group.pop(); group_cmp.pop(); first_line = glines.pop()
            flush()
            j = Jump("goto", t)
            j.line = j.end = e.line
            put(If(_cond_text(mn, ops, setter), [j], []), first_line, e.line)
            continue
        if mn in LOOPS:
            t = tgt(e)
            flush()
            cond = "(E)CX := (E)CX - 1; (E)CX != 0" + {"loope": " и ZF = 1", "loopz": " и ZF = 1", "loopne": " и ZF = 0", "loopnz": " и ZF = 0"}.get(mn, "")
            j = Jump("goto", t)
            j.line = j.end = e.line
            put(If(cond, [j], []), e.line)
            continue
        if mn in UNCOND:
            t = tgt(e)
            flush()
            if t in labels:
                put(Jump("goto", t), e.line)
            else:
                put(Ret(f"переход: {t}" if t else text_of(e)), e.line)
            continue
        if mn in CALL:
            flush()
            put(Proc(text_of(e), "predef"), e.line)
            continue
        base = _base(mn)
        is_cmp = (base in CMP_LIKE or mn in CMP_LIKE or base in TEST_LIKE or mn in TEST_LIKE)
        if is_cmp or mn in ARITH or base in ARITH:
            setter = (mn, e.ops)
        group.append(text_of(e))
        group_cmp.append(is_cmp)
        glines.append(e.line)
        if len(group) >= max(1, o.asm_group):
            flush()
    flush()
    return stmts
