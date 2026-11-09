"""C-подобные языки -> IR: C, C++, Java, C#, JavaScript, TypeScript, Go, Rust, PHP, Kotlin, Swift, Dart, Scala."""
from __future__ import annotations
import re
from collections import namedtuple
from typing import List, Tuple, Optional
from .ir import *

Tok = namedtuple("Tok", "k t s e line")

MULTI_OPS = sorted(
    ["===", "!==", "<<=", ">>=", ">>>", "...", "..<", "?.", "??", "=>", "->", "==", "!=", "<=", ">=", "&&", "||", "++", "--",
     "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<", ">>", "::", ":=", "<-", "..", "?:", "!!", "**"],
    key=len, reverse=True)
ASI_LANGS = {"javascript", "typescript", "go", "kotlin", "swift", "scala"}
NUM_RX = re.compile(r"0[xXbBoO][0-9a-fA-F_]+[a-zA-Z]*|\d[\d_]*(?:\.(?!\.)\d*)?(?:[eE][+-]?\d+)?[a-zA-Z]*")
ID_RX = re.compile(r"[^\W\d]\w*|\$\w*", re.U)
LIFETIME_RX = re.compile(r"'[A-Za-z_]\w*")
CHAR_RX = re.compile(r"'(?:\\.|[^\\'\n])'")


def lex(src: str, lang: str):
    n = len(src)
    i, line = 0, 1
    toks: List[Tok] = []
    clean = list(src)
    cmap = {}
    bol = True

    def blank(a, b):
        for k in range(a, b):
            if clean[k] != "\n":
                clean[k] = " "

    def note(text, ln):
        text = text.strip()
        if text:
            cmap[ln] = text

    while i < n:
        c = src[i]
        if c == "\n":
            line += 1; i += 1; bol = True
            continue
        if c in " \t\r":
            i += 1
            continue
        if c == "#" and lang in ("c", "cpp", "csharp") and bol:
            j = i
            while j < n and src[j] != "\n":
                if src[j] == "\\" and j + 1 < n and src[j + 1] == "\n":
                    line += 1; j += 1
                j += 1
            blank(i, j); i = j
            continue
        if c == "#" and lang == "rust" and src.startswith(("#[", "#!["), i):
            depth, j = 0, i
            while j < n:
                if src[j] == "[": depth += 1
                elif src[j] == "]":
                    depth -= 1
                    if depth == 0:
                        j += 1; break
                j += 1
            blank(i, j); i = j
            continue
        if lang == "php":
            for tag in ("<?php", "<?=", "?>"):
                if src.startswith(tag, i):
                    blank(i, i + len(tag)); i += len(tag); break
            else:
                tag = None
            if tag:
                continue
            if c == "#" and not src.startswith("#[", i):
                j = src.find("\n", i); j = n if j < 0 else j
                note(src[i + 1:j], line); blank(i, j); i = j
                continue
        if src.startswith("//", i):
            j = src.find("\n", i); j = n if j < 0 else j
            note(src[i:j].lstrip("/").lstrip("!"), line); blank(i, j); i = j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2); j = n if j < 0 else j + 2
            chunk = src[i:j]
            for k, ln_txt in enumerate(chunk.split("\n")):
                note(ln_txt.strip().lstrip("/*").rstrip("*/").strip().lstrip("*").strip(), line + k)
            line += chunk.count("\n")
            blank(i, j); i = j
            continue
        bol = False
        start, sl = i, line
        if c == '"' or c == "`" or (c == "'" and not CHAR_RX.match(src, i) and not (lang == "rust" and LIFETIME_RX.match(src, i))):
            q = c
            if src.startswith('"""', i):
                j = src.find('"""', i + 3); j = n if j < 0 else j + 3
                line += src.count("\n", i, j)
            else:
                verbatim = lang == "csharp" and i > 0 and src[i - 1] == "@"
                multiline = q == "`"
                j = i + 1
                while j < n:
                    ch = src[j]
                    if ch == "\\" and not verbatim and q != "`" or (ch == "\\" and q == "`" and lang == "javascript"):
                        j += 2; continue
                    if ch == q:
                        if verbatim and src[j + 1:j + 2] == '"':
                            j += 2; continue
                        break
                    if ch == "\n":
                        line += 1
                        if not (verbatim or multiline):
                            break
                    j += 1
                j = min(j + 1, n)
            toks.append(Tok("str", src[start:j], start, j, sl)); i = j
            continue
        if c == "'":
            m = CHAR_RX.match(src, i)
            if m:
                toks.append(Tok("str", m.group(), i, m.end(), line)); i = m.end(); continue
            m = LIFETIME_RX.match(src, i)
            if m:
                toks.append(Tok("id", m.group(), i, m.end(), line)); i = m.end(); continue
        if c.isdigit():
            m = NUM_RX.match(src, i)
            toks.append(Tok("num", m.group(), i, m.end(), line)); i = m.end(); continue
        m = ID_RX.match(src, i)
        if m and m.group():
            toks.append(Tok("id", m.group(), i, m.end(), line)); i = m.end(); continue
        for op in MULTI_OPS:
            if src.startswith(op, i):
                toks.append(Tok("op", op, i, i + len(op), line)); i += len(op); break
        else:
            toks.append(Tok("op", c, i, i + 1, line)); i += 1
    return toks, "".join(clean), cmap


CONTROL = {"if", "for", "while", "switch", "catch", "return", "sizeof", "do", "else", "try", "foreach", "when", "match",
           "elif", "elseif", "synchronized", "lock", "using", "await", "typeof", "defer", "go", "throw", "new", "with"}
MODIFIERS = {"public", "private", "protected", "static", "final", "abstract", "sealed", "partial", "export", "default", "async",
             "unsafe", "pub", "open", "internal", "data", "inline", "virtual", "explicit", "constexpr", "override", "extern",
             "readonly", "const", "mutating", "suspend", "operator", "infix", "tailrec", "external", "native", "synchronized",
             "@", "template", "friend", "noexcept", "declare", "fileprivate", "lazy", "required", "convenience", "final", "#"}
CLASSLIKE = {"class", "struct", "interface", "enum", "namespace", "union", "impl", "trait", "object", "module", "mod", "record",
             "protocol", "extension", "companion", "actor", "package"}
DEFKW = {"fn", "fun", "func", "function", "def", "sub"}
WRAP_KW = {"synchronized", "lock", "using", "unsafe", "checked", "unchecked", "fixed", "autoreleasepool", "scope", "with"}
SKIP_START = {"import", "package", "include", "typedef", "use", "namespace", "using", "require_once", "include_once", "typealias",
              "export_from", "extern"}
EXIT_RX = re.compile(r"^(?:exit|abort|_exit|quick_exit|panic|die|os\.Exit|System\.exit|process\.exit|Environment\.Exit|fatalError|"
                     r"std::exit|log\.Fatal\w*|exit!)\b\s*\(?")
CONT_OPS = set("+ - * / % = == != < > <= >= && || & | ^ , . ( [ { ? : => -> :: ?. ?? += -= *= /= %= &= |= ^= << >> === !== := <- ~ !".split()) - {"!"}
LEAD_OPS = {".", "?.", "&&", "||", "?", ":", "=>", "->", "??", "=", "==", "!=", ")", "]", "+", "*", "/", "%", "<", ">", "&", "|", "^", "::", "<=", ">=", ","}


class CLike:
    def __init__(self, src: str, lang: str, o: Options):
        self.src, self.lang, self.o = src, lang, o
        self.toks, self.clean, self.cmap = lex(src, lang)
        self.n = len(self.toks)
        self.i = 0
        self.asi = lang in ASI_LANGS
        self.prefix: List[str] = []
        self.charts: List[Chart] = []
        self.warns: List[str] = []
        self.eof = Tok("eof", "", len(src), len(src), (self.toks[-1].line if self.toks else 1))

    # ---------------------------------------------------------------- базовые операции
    def peek(self, k=0) -> Tok:
        j = self.i + k
        return self.toks[j] if 0 <= j < self.n else self.eof

    def is_op(self, t, k=0):
        x = self.peek(k)
        return x.k == "op" and x.t == t

    def is_id(self, t, k=0):
        x = self.peek(k)
        return x.k == "id" and x.t == t

    def txt(self, a: int, b: int) -> str:
        if b <= a:
            return ""
        return collapse(self._summarize(self.toks[a].s, self.toks[b - 1].e))

    def _summarize(self, s: int, e: int) -> str:
        seg = self.clean[s:e]
        out, depth, start = [], 0, 0
        i, q = 0, None
        while i < len(seg):
            ch = seg[i]
            if q:
                if ch == "\\":
                    i += 2; continue
                if ch == q:
                    q = None
            elif ch in "\"'`":
                q = ch
            elif ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    inner = seg[start:i + 1]
                    if len(inner) > 40 and "\n" in inner:
                        out.append((start, i + 1))
            i += 1
        res, last = [], 0
        for a, b in out:
            res.append(seg[last:a]); res.append("{…}"); last = b
        res.append(seg[last:])
        return "".join(res)

    def match_close(self, j: int) -> int:
        """j — индекс открывающей скобки; вернуть индекс парной закрывающей."""
        pairs = {"(": ")", "[": "]", "{": "}"}
        stack = [pairs[self.toks[j].t]]
        j += 1
        while j < self.n and stack:
            t = self.toks[j]
            if t.k == "op":
                if t.t in pairs:
                    stack.append(pairs[t.t])
                elif t.t in (")", "]", "}"):
                    if t.t == stack[-1]:
                        stack.pop()
                        if not stack:
                            return j
            j += 1
        return min(j, self.n - 1)

    def boundary(self, a: Tok, b: Tok) -> bool:
        if b.line <= a.line:
            return False
        if a.k == "op" and a.t in CONT_OPS:
            return False
        if b.k == "op" and b.t in LEAD_OPS:
            return False
        if b.k == "id" and b.t in ("else", "catch", "finally", "where", "as", "in", "is", "and", "or"):
            return False
        return True

    def scan_end(self, comma_end=False) -> int:
        """Конец простого оператора: индекс (искл.) последнего токена. Съедает завершающий ';'."""
        depth, j = 0, self.i
        while j < self.n:
            t = self.toks[j]
            if t.k == "op":
                if t.t in "([{":
                    depth += 1
                elif t.t in ")]}":
                    if depth == 0:
                        break
                    depth -= 1
                elif t.t == ";" and depth == 0:
                    end = j
                    self.i = j + 1
                    return end
                elif t.t == "," and depth == 0 and comma_end:
                    break
            j += 1
            if self.asi and depth == 0 and j < self.n and self.boundary(t, self.toks[j]):
                break
        end = j
        self.i = j
        return end

    def read_cond(self) -> str:
        """Условие после if/while: в скобках либо до '{' (Go/Rust/Swift)."""
        if self.lang not in ("go", "rust", "swift") and self.is_op("("):
            c = self.match_close(self.i)
            text = self.txt(self.i + 1, c)
            self.i = c + 1
            return strip_outer_parens(text)
        j, depth = self.i, 0
        while j < self.n:
            t = self.toks[j]
            if t.k == "op":
                if t.t in "([":
                    depth += 1
                elif t.t in ")]":
                    depth -= 1
                elif t.t == "{" and depth == 0:
                    break
                elif t.t == ";" and depth == 0 and self.lang != "go":
                    break
            j += 1
        text = self.txt(self.i, j)
        self.i = j
        return strip_outer_parens(text)

    # ---------------------------------------------------------------- операторы
    def parse_stmts(self, stop=None) -> list:
        out = []
        while self.i < self.n:
            t = self.peek()
            if t.k == "op" and t.t == "}":
                break
            if stop and stop(t):
                break
            before = self.i
            st = self.parse_stmt()
            if self.i == before:
                self.i += 1                       # гарантия прогресса
            if st is None:
                continue
            if isinstance(st, list):
                out.extend(st)
            else:
                out.append(st)
        return out

    def parse_block(self) -> list:
        if self.is_op("{"):
            self.i += 1
            body = self.parse_stmts()
            if self.is_op("}"):
                self.i += 1
            return body
        return self.parse_body()

    def parse_body(self) -> list:
        if self.is_op("{"):
            return self.parse_block()
        st = self.parse_stmt()
        if st is None:
            return []
        return st if isinstance(st, list) else [st]

    def parse_stmt(self, comma_end=False):
        start = self.peek().line
        r = self._parse_stmt(comma_end)
        if r is None:
            return r
        end = self.toks[self.i - 1].line if 0 < self.i <= self.n else start
        for n in (r if isinstance(r, list) else [r]):
            if not hasattr(n, "line"):
                n.line = start
                n.end = end if isinstance(n, (Proc, Ret, Jump)) else start
        return r

    def _mk(self, node, line=None):
        node.line = node.end = line if line is not None else self.peek().line
        return node

    def _parse_stmt(self, comma_end=False):
        t = self.peek()
        if t.k == "eof":
            self.i = self.n
            return None
        if t.k == "op":
            if t.t == ";":
                self.i += 1
                return None
            if t.t == "{":
                return self.parse_block()
            if t.t == "}":
                self.i += 1
                return None
            if t.t == "@" or (t.t == "[" and self.lang == "csharp"):
                self.skip_attribute()
                return None
        if t.k == "id":
            kw, lang = t.t, self.lang
            nxt = self.peek(1)
            if kw in ("if", "elseif") and not (lang in ("kotlin",) and False):
                return self.p_if()
            if kw == "while":
                self.i += 1
                cond = self.read_cond()
                return Loop("пока " + cond, None, self.parse_body())
            if kw == "do" and lang != "swift":
                return self.p_do()
            if kw == "do" and lang == "swift":
                return self.p_try()
            if kw == "repeat" and lang == "swift":
                self.i += 1
                body = self.parse_block()
                if self.is_id("while"):
                    self.i += 1
                    cond = self.read_cond()
                    return Loop(None, "пока " + cond, body)
                return body
            if kw in ("for", "foreach"):
                return self.p_for()
            if kw == "loop" and lang == "rust" and nxt.t == "{":
                self.i += 1
                return Loop("пока true", None, self.parse_block())
            if kw == "switch" or (kw == "select" and lang == "go" and nxt.t == "{"):
                return self.p_switch()
            if (kw == "match" and lang == "rust") or (kw == "when" and lang == "kotlin"):
                return self.p_arrow_switch()
            if kw == "try" and lang != "rust":
                return self.p_try()
            if kw == "guard" and lang == "swift":
                self.i += 1
                cond = self.read_cond()
                cond = re.sub(r"\s+else$", "", cond)
                if self.is_id("else"):
                    self.i += 1
                body = self.parse_block()
                return If(cond, [], body)
            if kw == "return":
                self.i += 1
                a = self.i
                e = self.scan_end(comma_end)
                expr = self.txt(a, e)
                return Ret("возврат " + expr if expr else "возврат")
            if kw in ("throw", "raise") and lang != "kotlin_x":
                self.i += 1
                a = self.i
                e = self.scan_end(comma_end)
                return Ret("throw " + self.txt(a, e))
            if kw == "break":
                self.i += 1
                self.scan_end(comma_end)
                return Jump("break")
            if kw == "continue":
                self.i += 1
                self.scan_end(comma_end)
                return Jump("continue")
            if kw == "goto":
                self.i += 1
                a = self.i
                e = self.scan_end(comma_end)
                return Jump("goto", self.txt(a, e))
            if kw == "defer" and lang in ("go", "swift") and nxt.t == "{":
                self.i += 1
                return [self._mk(Proc("defer"), t.line)] + self.parse_block()
            if kw in ("case", "default") and not (self.is_op("(", 1)):
                while self.i < self.n and not self.is_op(":") and not self.is_op("}"):
                    self.i += 1
                if self.is_op(":"):
                    self.i += 1
                return None
            # метка  ident :
            if (nxt.k == "op" and nxt.t == ":" and kw not in ("default", "public", "private", "protected", "case", "else")
                    and lang in ("c", "cpp", "csharp", "go", "java", "javascript", "typescript", "swift", "rust", "php", "dart", "kotlin")
                    and self.peek(2).t != ":"):
                self.i += 2
                return Label(kw)
        return self.p_simple(comma_end)

    def skip_attribute(self):
        if self.is_op("@"):
            self.i += 1
            while self.peek().k == "id" or self.is_op("."):
                self.i += 1
            if self.is_op("("):
                self.i = self.match_close(self.i) + 1
        elif self.is_op("["):
            self.i = self.match_close(self.i) + 1

    def p_if(self):
        ln = self.peek().line
        self.i += 1
        cond = self.read_cond()
        pre = []
        if self.lang == "go" and ";" in [x for x in split_top(cond, ";")][0:0] or (self.lang in ("go",) and len(split_top(cond, ";")) == 2):
            a, b = split_top(cond, ";")
            pre = [self._mk(Proc(a.strip()), ln)]
            cond = b.strip()
        then = self.parse_body()
        els = []
        if self.is_id("else"):
            self.i += 1
            if self.is_id("if"):
                r = self.p_if()
                els = r if isinstance(r, list) else [r]
            else:
                els = self.parse_body()
        elif self.is_id("elseif") or (self.is_id("else") and self.is_id("if", 1)):
            r = self.p_if()
            els = r if isinstance(r, list) else [r]
        node = self._mk(If(cond, then, els), ln)
        return pre + [node] if pre else node

    def p_do(self):
        self.i += 1
        body = self.parse_body()
        cond = "true"
        if self.is_id("while"):
            self.i += 1
            cond = self.read_cond()
            if self.is_op(";"):
                self.i += 1
        return Loop(None, "пока " + cond, body)

    def p_for(self):
        self.i += 1
        if self.is_id("await"):
            self.i += 1
        if self.is_op("(") and self.lang not in ("go", "rust", "swift"):
            c = self.match_close(self.i)
            head = self.txt(self.i + 1, c)
            self.i = c + 1
        else:
            j, depth = self.i, 0
            while j < self.n:
                t = self.toks[j]
                if t.k == "op":
                    if t.t in "([":
                        depth += 1
                    elif t.t in ")]":
                        depth -= 1
                    elif t.t == "{" and depth == 0:
                        break
                j += 1
            head = self.txt(self.i, j)
            self.i = j
        parts = split_top(head, ";")
        if len(parts) >= 3:
            if not any(p.strip() for p in parts):
                top = "пока true"
            else:
                top = "для " + norm_head("; ".join(x.strip() for x in parts[:3]), self.o)
        elif self.lang in ("go",) and "range" not in head and head.strip() and not re.search(r"\bin\b", head):
            top = "пока " + head.strip()
        elif not head.strip():
            top = "пока true"
        else:
            top = "для " + collapse(head)
        return Loop(top, None, self.parse_body())

    def p_try(self):
        self.i += 1
        if self.is_op("("):                  # try-with-resources
            self.i = self.match_close(self.i) + 1
        body = self.parse_block()
        catches = []
        fin: list = []
        while self.is_id("catch") or self.is_id("finally") or self.is_id("except"):
            if self.is_id("finally"):
                self.i += 1
                fin = self.parse_block()
                continue
            self.i += 1
            ctype = ""
            if self.is_op("("):
                c = self.match_close(self.i)
                ctype = self.txt(self.i + 1, c)
                self.i = c + 1
            cb = self.parse_block()
            catches.append((ctype, cb))
        els: list = []
        for ctype, cb in reversed(catches):
            els = [If("Исключение" + (": " + ctype if ctype else "") + "?", cb, els)]
        return body + els + fin

    def p_switch(self):
        kw = self.peek().t
        self.i += 1
        expr = ""
        if kw == "select":
            expr = "select"
        else:
            if self.is_op("{"):
                expr = ""
            else:
                expr = self.read_cond()
        pre = []
        if self.lang == "go" and len(split_top(expr, ";")) == 2:
            a, b = split_top(expr, ";")
            pre = [self._mk(Proc(a.strip()))]
            expr = b.strip()
        if not self.is_op("{"):
            return pre or None
        self.i += 1
        cases, pending = [], []
        while self.i < self.n and not self.is_op("}"):
            t = self.peek()
            if t.k == "id" and t.t in ("case", "default"):
                self.i += 1
                if t.t == "case":
                    j, depth = self.i, 0
                    while j < self.n:
                        x = self.toks[j]
                        if x.k == "op":
                            if x.t in "([{":
                                depth += 1
                            elif x.t in ")]}":
                                depth -= 1
                            elif depth == 0 and x.t in (":", "->"):
                                break
                        j += 1
                    label = self.txt(self.i, j)
                    self.i = j
                else:
                    label = "иначе"
                arrow = self.is_op("->")
                if self.is_op(":") or arrow:
                    self.i += 1
                if arrow:
                    body = self.parse_body()
                    cases.append((", ".join(pending + [label]), body)); pending = []
                    continue
                pending.append(label)
                body = self.parse_stmts(lambda x: x.k == "id" and x.t in ("case", "default"))
                if body and isinstance(body[-1], Jump) and body[-1].kind == "break":
                    body.pop()
                if not body and not self.is_op("}"):
                    continue
                cases.append((", ".join(pending), body)); pending = []
            else:
                before = self.i
                self.parse_stmt()
                if self.i == before:
                    self.i += 1
        if pending:
            cases.append((", ".join(pending), []))
        if self.is_op("}"):
            self.i += 1
        return pre + [Switch(expr or "выбор по условиям", cases)]

    def p_arrow_switch(self):
        self.i += 1
        expr = ""
        if not self.is_op("{"):
            expr = self.read_cond()
        if not self.is_op("{"):
            return None
        self.i += 1
        cases = []
        while self.i < self.n and not self.is_op("}"):
            j, depth = self.i, 0
            while j < self.n:
                x = self.toks[j]
                if x.k == "op":
                    if x.t in "([{":
                        depth += 1
                    elif x.t in ")]}":
                        depth -= 1
                    elif depth == 0 and x.t in ("->", "=>"):
                        break
                j += 1
            label = self.txt(self.i, j)
            self.i = min(j + 1, self.n)
            if j >= self.n:
                break
            if label.strip() in ("else", "_"):
                label = "иначе"
            if self.is_op("{"):
                body = self.parse_block()
            else:
                st = self.parse_stmt(comma_end=True)
                body = [] if st is None else (st if isinstance(st, list) else [st])
            if self.is_op(","):
                self.i += 1
            cases.append((label, body))
        if self.is_op("}"):
            self.i += 1
        return Switch(expr or "выбор", cases)

    # ---------------------------------------------------------------- простые операторы и определения
    def find_brace_header(self) -> Optional[int]:
        j, depth = self.i, 0
        first = self.peek()
        defstart = first.k == "id" and (first.t in DEFKW or (first.t in MODIFIERS and any(
            self.peek(k).t in DEFKW for k in range(1, 5))))
        while j < self.n:
            t = self.toks[j]
            if t.k == "op":
                if t.t in "([":
                    depth += 1
                elif t.t in ")]":
                    if depth == 0:
                        return None
                    depth -= 1
                elif depth == 0:
                    if t.t == "{":
                        return j
                    if t.t == ";" or t.t == "}":
                        return None
                    if t.t in ("=", ":=", "+=", "-=", "*=", "/=") and not defstart:
                        if self.is_func_literal(j + 1):
                            pass
                        else:
                            return None
            if self.asi and depth == 0 and j + 1 < self.n and self.boundary(t, self.toks[j + 1]):
                return None
            j += 1
        return None

    def is_func_literal(self, j: int) -> bool:
        if j < self.n and self.toks[j].t == "async":
            j += 1
        if j >= self.n:
            return False
        t = self.toks[j]
        if t.t == "function":
            return True
        if t.t == "(":
            c = self.match_close(j)
            return c + 1 < self.n and self.toks[c + 1].t == "=>"
        if t.k == "id" and j + 1 < self.n and self.toks[j + 1].t == "=>":
            return True
        return False

    def first_keyword(self, a: int, b: int) -> Optional[int]:
        k = a
        while k < b:
            t = self.toks[k]
            if t.k == "op" and t.t in ("@", "#"):
                k += 1
                while k < b and (self.toks[k].k == "id" or self.toks[k].t == "."):
                    k += 1
                if k < b and self.toks[k].t == "(":
                    k = self.match_close(k) + 1
                continue
            if t.k == "op" and t.t == "[" and self.lang == "csharp":
                k = self.match_close(k) + 1
                continue
            if t.k == "id" and t.t == "template" and k + 1 < b and self.toks[k + 1].t == "<":
                depth, k = 0, k + 1
                while k < b:
                    if self.toks[k].t == "<": depth += 1
                    elif self.toks[k].t == ">":
                        depth -= 1
                        if depth == 0:
                            k += 1; break
                    k += 1
                continue
            if t.k == "id" and t.t in MODIFIERS and t.t not in ("extern",):
                k += 1
                continue
            return k
        return None

    def class_name(self, k: int, b: int) -> str:
        kw = self.toks[k].t
        j = k + 1
        if j < b and self.toks[j].t == "<":
            depth = 0
            while j < b:
                if self.toks[j].t == "<": depth += 1
                elif self.toks[j].t == ">":
                    depth -= 1
                    if depth == 0:
                        j += 1; break
                j += 1
        if kw == "impl":
            names = [self.toks[x].t for x in range(j, b) if self.toks[x].k == "id"]
            if "for" in names:
                idx = names.index("for")
                return names[idx + 1] if idx + 1 < len(names) else names[0]
            return names[0] if names else ""
        for x in range(j, b):
            if self.toks[x].k == "id" and self.toks[x].t not in ("class", "struct", "interface"):
                return self.toks[x].t
        return ""

    def func_info(self, a: int, b: int):
        p = None
        depth = 0
        for k in range(a, b):
            t = self.toks[k]
            if t.k == "op":
                if t.t == "(" and depth == 0:
                    p = k
                    break
                if t.t in "[<" and False:
                    depth += 1
        if p is None:
            return None
        kwi = None
        for k in range(a, p):
            if self.toks[k].k == "id" and self.toks[k].t in DEFKW:
                kwi = k
                break
        prefix = ""
        if kwi is not None:
            if self.lang == "go" and self.toks[kwi].t == "func" and p == kwi + 1:
                rc = self.match_close(p)
                ids = [self.toks[x].t for x in range(p + 1, rc) if self.toks[x].k == "id"]
                prefix = ids[-1] if ids else ""
                q = rc + 1
                if q < b and self.toks[q].k == "id":
                    name = self.toks[q].t
                    p = q + 1
                else:
                    return None
            else:
                if p - 1 <= kwi or self.toks[p - 1].k != "id":
                    return None
                name = self.toks[p - 1].t
        else:
            if p == a:
                return None
            tk = self.toks[p - 1]
            if tk.k == "id":
                if tk.t in CONTROL or tk.t in ("function", "def", "fn", "func"):
                    return None
                name = tk.t
                k = p - 1
                while k - 2 >= a and self.toks[k - 1].t in ("::", ".") and self.toks[k - 2].k == "id":
                    name = self.toks[k - 2].t + "." + name
                    k -= 2
            elif tk.k == "op" and p - 2 >= a and self.toks[p - 2].t == "operator":
                name = "operator" + tk.t
            else:
                return None
            if any(self.toks[x].t in ("=", ":=") and self.toks[x].k == "op" for x in range(a, p - 1)):
                return None
            first = self.toks[a]
            if first.k == "id" and first.t in CONTROL:
                return None
        pc = self.match_close(p)
        params = self.txt(p + 1, pc)
        if prefix:
            name = prefix + "." + name
        return name, params

    def doc_above(self, line: int) -> str:
        buf = []
        k = line - 1
        while k in self.cmap:
            buf.append(self.cmap[k])
            k -= 1
        buf.reverse()
        return "\n".join(buf)

    def register(self, name, params, header_line, body):
        qn = ".".join(self.prefix + [name])
        ch = Chart(name=qn, body=body, signature=f"{qn}({params})", comment=self.doc_above(header_line), kind="function")
        ch.line = header_line
        self.charts.append(ch)

    def p_simple(self, comma_end=False):
        start = self.i
        first = self.peek()
        b = None if comma_end else self.find_brace_header()
        if b is not None:
            k = self.first_keyword(start, b)
            kt = self.toks[k] if k is not None else None
            if kt is not None and ((kt.t in CLASSLIKE and kt.k == "id") or (kt.t == "type" and any(self.toks[x].t in ("struct", "interface") for x in range(start, b))) or
                                  (kt.t == "extern" and b > k + 1 and self.toks[k + 1].k == "str")):
                name = self.class_name(k, b) if kt.t != "extern" and kt.t != "type" else (self.toks[k + 1].t if kt.t == "type" else "")
                self.i = b
                self.prefix.append(name) if name else None
                self.i = b + 1
                self.parse_stmts()          # содержимое класса: интересны только методы
                if self.is_op("}"):
                    self.i += 1
                if name:
                    self.prefix.pop()
                return None
            info = self.func_info(start, b) if kt is None or kt.t not in CONTROL or kt.t in DEFKW else None
            lit = None
            if info is None:
                lt = [x for x in range(start, b) if self.toks[x].t == "=" or self.toks[x].t == ":="]
                if lt and self.is_func_literal(lt[0] + 1) and self.toks[lt[0] - 1].k == "id":
                    lit = (self.toks[lt[0] - 1].t, "")
                    hdr_params = ""
                    pidx = [x for x in range(lt[0] + 1, b) if self.toks[x].t == "("]
                    if pidx:
                        hdr_params = self.txt(pidx[0] + 1, self.match_close(pidx[0]))
                    lit = (lit[0], hdr_params)
            if info or lit:
                name, params = info or lit
                self.i = b
                body = self.parse_block()
                self.register(name, params, self.toks[start].line, body)
                return None
            if kt is not None and kt.t in WRAP_KW:
                head = self.txt(start, b)
                self.i = b
                body = self.parse_block()
                return [self._mk(Proc(head), self.toks[start].line)] + body
            # блок неизвестного вида (get { }, init { }, static { }) – пропустить
            self.i = self.match_close(b) + 1
            if self.is_op(";"):
                self.i += 1
            return None
        a = self.i
        e = self.scan_end(comma_end)
        text = self.txt(a, e)
        if not text:
            return None
        w0 = first.t if first.k == "id" else ""
        if w0 in SKIP_START and not (w0 == "using" and self.peek(1).t == "("):
            return None
        if w0 in CLASSLIKE and w0 not in ("object",) and first.k == "id":
            return None
        if w0 == "type" and self.peek(1).k == "id" and self.lang in ("go", "rust", "typescript"):
            return None
        if EXIT_RX.match(text):
            return Ret(text)
        if self._proto(text):
            return None
        return Proc(text)

    _PROTO = re.compile(r"^[\w\s\*&:<>,\[\]\.$]+\s+[\*&]*\w+\s*\([^()]*\)\s*(?:const)?$")

    def _proto(self, text: str) -> bool:
        w = text.split(None, 1)[0] if text.split() else ""
        if w in ("new", "await", "delete", "yield", "co_await", "echo", "print", "return", "throw", "go", "defer", "else", "case"):
            return False
        if "=" in text or "->" in text and False:
            return False
        return bool(self._PROTO.match(text)) and len(text.split("(")[0].split()) >= 2 and self.lang in ("c", "cpp", "java", "csharp", "php", "dart")

    # ---------------------------------------------------------------- результат
    def run(self, program_name="Основная программа") -> Tuple[List[Chart], List[str]]:
        top = self.parse_stmts_toplevel()
        funcs = sorted(self.charts, key=lambda c: getattr(c, "line", 0))
        out: List[Chart] = []
        keep_top = self.lang in ("javascript", "typescript", "php", "swift", "python") or not funcs
        if top and keep_top:
            out.append(Chart(name=program_name, body=top, kind="program"))
        return out + funcs, self.warns

    def parse_stmts_toplevel(self) -> list:
        out = []
        while self.i < self.n:
            before = self.i
            out.extend(self.parse_stmts())
            if self.is_op("}"):
                self.i += 1
            if self.i == before:
                self.i += 1
        return out


def parse_clike(src: str, lang: str, o: Options):
    return CLike(src, lang, o).run()
