"""Pascal / Delphi / Free Pascal -> IR."""
from __future__ import annotations
import re
from collections import namedtuple
from typing import List, Tuple
from .ir import *

PTok = namedtuple("PTok", "k t low s e line")
TOKEN_RE = re.compile(r"""(?P<ws>\s+)|(?P<c1>\{[^}]*\})|(?P<c2>\(\*.*?\*\))|(?P<c3>//[^\n]*)|(?P<str>'(?:[^']|'')*')|"""
                      r"""(?P<op>:=|<>|<=|>=|\.\.|[^\w\s])|(?P<id>[A-Za-z_]\w*)|(?P<num>\$[0-9A-Fa-f]+|\d+(?:\.\d+)?)""", re.S)
SECTIONS = {"var", "const", "type", "label", "threadvar", "resourcestring"}
ROUT = {"procedure", "function", "constructor", "destructor"}
STOP_DECL = SECTIONS | ROUT | {"begin", "implementation", "initialization", "finalization", "uses", "interface"}
DIRS = {"forward", "external", "overload", "inline", "assembler", "virtual", "override", "cdecl", "stdcall", "register", "pascal",
        "safecall", "far", "near", "export", "reintroduce", "abstract", "static", "dynamic"}


class Pascal:
    def __init__(self, src: str, o: Options):
        self.o = o
        self.toks: List[PTok] = []
        clean = list(src)
        self.comments = {}
        line = 1
        for m in TOKEN_RE.finditer(src):
            k = m.lastgroup
            text = m.group()
            if k == "ws":
                line += text.count("\n")
                continue
            if k in ("c1", "c2", "c3"):
                body = text.strip("{}()*/ ").strip()
                for q, part in enumerate(text.split("\n")):
                    self.comments[line + q] = part.strip("{}()*/ ").strip()
                for x in range(m.start(), m.end()):
                    if clean[x] != "\n":
                        clean[x] = " "
                line += text.count("\n")
                continue
            self.toks.append(PTok(k, text, text.lower(), m.start(), m.end(), line))
            line += text.count("\n")
        self.clean = "".join(clean)
        self.n = len(self.toks)
        self.i = 0
        self.charts: List[Chart] = []
        self.main: list = []
        self.main_name = ""

    def low(self, k=0):
        j = self.i + k
        return self.toks[j].low if 0 <= j < self.n else ""

    def txt(self, a, b):
        if b <= a:
            return ""
        return collapse(self.clean[self.toks[a].s:self.toks[b - 1].e])

    def skip_to_semicolon(self):
        while self.i < self.n and self.low() != ";":
            self.i += 1
        self.i += 1

    def skip_decl_section(self):
        self.i += 1
        depth = 0
        while self.i < self.n:
            lw = self.low()
            if depth == 0 and lw in STOP_DECL:
                break
            if lw in ("record", "object") or (lw == "class" and self.low(1) not in (";", "of")):
                depth += 1
            elif lw == "end" and depth > 0:
                depth -= 1
            self.i += 1

    def doc_above(self, line):
        buf, k = [], line - 1
        while k in self.comments:
            buf.append(self.comments[k]); k -= 1
        buf.reverse()
        return "\n".join(x for x in buf if x)

    def p_routine(self, prefix):
        header_line = self.toks[self.i].line
        self.i += 1
        a = self.i
        while self.i < self.n and (self.toks[self.i].k == "id" or self.low() == "."):
            self.i += 1
        name = self.txt(a, self.i).replace(" ", "")
        params = ""
        if self.low() == "(":
            depth, j = 0, self.i
            while j < self.n:
                if self.low_at(j) == "(": depth += 1
                elif self.low_at(j) == ")":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            params = self.txt(self.i + 1, j)
            self.i = j + 1
        res = ""
        if self.low() == ":":
            b = self.i + 1
            while self.i < self.n and self.low() != ";":
                self.i += 1
            res = self.txt(b, self.i)
        self.skip_to_semicolon()
        forward = False
        while self.low() in DIRS:
            if self.low() in ("forward", "external", "abstract"):
                forward = True
            self.skip_to_semicolon()
        if forward:
            return
        full = ".".join(prefix + [name]) if prefix else name
        while True:
            lw = self.low()
            if lw in SECTIONS:
                self.skip_decl_section()
            elif lw in ROUT:
                self.p_routine(prefix + [name])
            else:
                break
        if self.low() != "begin":
            return
        body = self.p_compound()
        if self.low() == ";":
            self.i += 1
        sig = f"{full}({params})" + (f": {res}" if res else "")
        ch = Chart(name=full, body=body, signature=sig, comment=self.doc_above(header_line), kind="function")
        ch.line = header_line
        self.charts.append(ch)

    def low_at(self, j):
        return self.toks[j].low if 0 <= j < self.n else ""

    def p_compound(self) -> list:
        self.i += 1   # begin
        body = self.p_stmts({"end"})
        if self.low() == "end":
            self.i += 1
        return body

    def p_stmts(self, stops) -> list:
        out = []
        while self.i < self.n:
            while self.low() == ";":
                self.i += 1
            if self.i >= self.n or self.low() in stops:
                break
            before = self.i
            st = self.p_stmt()
            if self.i == before:
                self.i += 1                       # гарантия прогресса
            if st is None:
                continue
            out.extend(st if isinstance(st, list) else [st])
        return out

    def until(self, *words) -> str:
        a, depth = self.i, 0
        while self.i < self.n:
            lw = self.low()
            if lw in ("(", "["):
                depth += 1
            elif lw in (")", "]"):
                depth -= 1
            elif depth == 0 and lw in words:
                break
            self.i += 1
        return self.txt(a, self.i)

    def p_body(self) -> list:
        st = self.p_stmt()
        if st is None:
            return []
        return st if isinstance(st, list) else [st]

    def p_stmt(self):
        if self.i >= self.n:
            return None
        start = self.toks[self.i].line
        r = self._p_stmt()
        if r is None:
            return r
        end = self.toks[min(self.i, self.n) - 1].line if self.n and self.i > 0 else start
        for n in (r if isinstance(r, list) else [r]):
            if not hasattr(n, "line"):
                n.line = start
                n.end = end if isinstance(n, (Proc, Ret, Jump)) else start
        return r

    def _p_stmt(self):
        lw = self.low()
        t = self.toks[self.i]
        if lw == "begin":
            return self.p_compound()
        if lw == "if":
            self.i += 1
            cond = self.until("then")
            self.i += 1
            then = self.p_body()
            els = []
            if self.low() == "else":
                self.i += 1
                els = self.p_body()
            return If(strip_outer_parens(cond), then, els)
        if lw == "while":
            self.i += 1
            cond = self.until("do")
            self.i += 1
            return Loop("пока " + strip_outer_parens(cond), None, self.p_body())
        if lw == "for":
            self.i += 1
            head = self.until("do")
            self.i += 1
            return Loop("для " + head, None, self.p_body())
        if lw == "repeat":
            self.i += 1
            body = self.p_stmts({"until"})
            cond = ""
            if self.low() == "until":
                self.i += 1
                cond = self.until(";", "end", "else")
            return Loop(None, "до " + strip_outer_parens(cond), body)
        if lw == "case":
            self.i += 1
            expr = self.until("of")
            self.i += 1
            cases = []
            while self.i < self.n and self.low() != "end":
                while self.low() == ";":
                    self.i += 1
                if self.low() == "end":
                    break
                if self.low() == "else":
                    self.i += 1
                    cases.append(("иначе", self.p_stmts({"end"})))
                    break
                before = self.i
                label = self.until(":")
                self.i += 1
                cases.append((label, self.p_body()))
                if self.i <= before:
                    self.i = before + 1
            if self.low() == "end":
                self.i += 1
            return Switch(expr, cases)
        if lw == "with":
            self.i += 1
            head = self.until("do")
            self.i += 1
            h = Proc("with " + head)
            h.line = h.end = t.line
            return [h] + self.p_body()
        if lw == "try":
            self.i += 1
            body = self.p_stmts({"except", "finally", "end"})
            extra = []
            if self.low() == "except":
                self.i += 1
                h = self.p_stmts({"end", "finally"})
                extra = [If("Исключение?", h, [])]
            if self.low() == "finally":
                self.i += 1
                extra += self.p_stmts({"end"})
            if self.low() == "end":
                self.i += 1
            return body + extra
        if lw == "on" and self.toks[self.i].k == "id":
            self.i += 1
            head = self.until("do")
            self.i += 1
            return If(f"Исключение {head}?", self.p_body(), [])
        if lw == "goto":
            self.i += 1
            a = self.i
            self.i += 1
            return Jump("goto", self.txt(a, self.i))
        if lw in ("break", "continue"):
            self.i += 1
            return Jump(lw)
        if lw in ("exit", "halt") or lw == "raise":
            a = self.i
            self.simple_end()
            text = self.txt(a, self.i)
            return Ret(("выход" if lw == "exit" else text) if lw != "exit" or "(" not in text else "выход " + text[4:].strip("() "))
        if t.k == "id" and self.low(1) == ":" and self.low(2) != "=" and lw not in ("else",):
            self.i += 2
            return Label(t.t)
        a = self.i
        self.simple_end()
        text = self.txt(a, self.i)
        return Proc(text) if text else None

    def simple_end(self):
        depth = 0
        while self.i < self.n:
            lw = self.low()
            if lw in ("(", "["):
                depth += 1
            elif lw in (")", "]"):
                depth -= 1
            elif depth == 0 and lw in (";", "end", "else", "until", "except", "finally"):
                break
            self.i += 1

    def run(self):
        while self.i < self.n:
            lw = self.low()
            if lw in ROUT:
                self.p_routine([])
            elif lw == "begin":
                self.main = self.p_compound()
                if self.low() == ".":
                    self.i += 1
            elif lw in ("program", "unit"):
                a = self.i + 1
                self.i += 1
                if self.toks[self.i].k == "id" if self.i < self.n else False:
                    self.main_name = self.toks[self.i].t
                self.skip_to_semicolon()
            elif lw in SECTIONS or lw in ("uses", "interface", "implementation", "initialization", "finalization"):
                self.skip_decl_section() if lw in SECTIONS or lw == "uses" else self.__setattr__("i", self.i + 1)
            else:
                self.i += 1
        funcs = sorted(self.charts, key=lambda c: getattr(c, "line", 0))
        out = []
        if self.main:
            out.append(Chart(name=self.main_name or "Основная программа", body=self.main, kind="program"))
        return out + funcs, []


def parse_pascal(src: str, o: Options):
    return Pascal(src, o).run()
