"""Промежуточное представление (IR) программы и нормализация текста операторов."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class Options:
    gost_assign: bool = True      # «=» -> «:=», «i++» -> «i := i + 1», убрать типы в объявлениях
    keep_decl: bool = False       # показывать объявления переменных без инициализации
    merge: int = 1                # макс. число простых операторов в одном блоке «Процесс» (1 = не объединять)
    asm_group: int = 6            # макс. число ассемблерных команд в одном блоке
    asm_comments: bool = False    # добавлять комментарии из исходника в блоки ассемблера
    show_comment: bool = True     # рисовать символ «Комментарий» (сигнатура + описание функции)
    detail: str = "full"          # full | calls (структура + вызовы) | structure (только циклы/условия/переходы)
    expand: int = 0               # глубина «разворачивания» вызовов пользовательских функций внутрь схемы (0 = выкл.)


# ---------------------------------------------------------------- узлы IR
@dataclass
class Proc:
    text: str
    kind: str = "stmt"            # stmt (будет уточнён) | process | io | predef | asm


@dataclass
class If:
    cond: str
    then: list
    els: list


@dataclass
class Loop:
    top: Optional[str]            # текст верхней границы цикла («пока ...», «для ...»)
    bottom: Optional[str]         # текст нижней границы («пока ...», «до ...»)
    body: list


@dataclass
class Switch:
    expr: str
    cases: List[Tuple[str, list]]


@dataclass
class Ret:
    text: str


@dataclass
class Jump:
    kind: str                     # break | continue | goto
    target: str = ""


@dataclass
class Label:
    name: str


@dataclass
class Chart:
    name: str
    body: list
    signature: str = ""
    comment: str = ""
    kind: str = "function"        # function | program


# ---------------------------------------------------------------- утилиты текста
def collapse(s: str) -> str:
    return " ".join(s.split())


def strip_outer_parens(s: str) -> str:
    s = s.strip()
    while s.startswith("(") and s.endswith(")"):
        depth = 0
        ok = True
        for i, ch in enumerate(s):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and i != len(s) - 1:
                    ok = False
                    break
        if ok:
            s = s[1:-1].strip()
        else:
            break
    return s


def scan_top(s: str):
    """Итератор (индекс, символ, глубина) по символам вне строк и скобок-глубины."""
    depth = 0
    quote = None
    i = 0
    while i < len(s):
        ch = s[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
        else:
            if ch in "\"'`":
                quote = ch
            elif ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            else:
                yield i, ch, depth
            if ch in "([{" or ch in ")]}":
                pass
        i += 1


def split_top(s: str, sep: str) -> List[str]:
    parts, cur = [], 0
    for i, ch, d in scan_top(s):
        if ch == sep and d == 0:
            parts.append(s[cur:i])
            cur = i + 1
    parts.append(s[cur:])
    return parts


def has_top_op(s: str) -> bool:
    for i, ch, d in scan_top(s):
        if d == 0 and (ch.isspace() or ch in "+-*/%&|^<>?:"):
            return True
    return False


def gostify(t: str) -> str:
    """Первое присваивание верхнего уровня: «=» -> «:=»."""
    if ":=" in t:
        return t
    for i, ch, d in scan_top(t):
        if ch == "=" and d == 0:
            prev = t[i - 1] if i > 0 else ""
            nxt = t[i + 1] if i + 1 < len(t) else ""
            if prev in "=!<>+-*/%&|^:" or nxt in "=>":
                continue
            return (t[:i].rstrip() + " := " + t[i + 1:].lstrip()).strip()
    return t


NOT_TYPE = {"return", "throw", "new", "delete", "goto", "else", "case", "print", "echo", "await",
            "yield", "go", "defer", "del", "assert", "import", "export", "raise", "exit", "using",
            "break", "continue", "typeof", "sizeof", "do", "in", "is", "as", "not", "and", "or"}
_MOD = r"(?:(?:const|final|static|unsigned|signed|long|short|register|volatile|let|var|val|mut|auto|extern|readonly)\s+)*"
_TYPE = r"[A-Za-z_][\w:<>\[\]\*&\.\?$]*"
_DECL_RX = re.compile(
    r"^" + _MOD + _TYPE + r"(?:\s*[\*&]+\s*|\s+)[A-Za-z_$][\w$]*(?:\[[^\]]*\])*"
    r"(?:\s*,\s*[\*&]*\s*[A-Za-z_$][\w$]*(?:\[[^\]]*\])*)*$")
_STRIP_A = re.compile(r"^(?:let|var|val|mut)\s+(?:mut\s+)?([^=:]+?)\s*(?::\s*[^=]+?)?\s*=(?![=>])\s*(.*)$", re.S)
_STRIP_C = re.compile(r"^(?:const|final|static)\s+([A-Za-z_$][\w$]*)\s*(?::\s*[^=]+?)?\s*=(?![=>])\s*(.*)$", re.S)
_STRIP_B = re.compile(r"^" + _MOD + _TYPE + r"(?:\s*[\*&]+\s*|\s+)([\*&]*[A-Za-z_$][\w$]*(?:\[[^\]]*\])*)\s*=(?![=>])\s*(.*)$", re.S)
_AUG_RX = re.compile(r"(?<![=!<>])(\+|-|\*|/|%|&|\||\^|<<|>>)=(?!=)")
_INC_RX = re.compile(r"^(?:(\+\+|--)\s*([\w$.\[\]>*-]+)|([\w$.\[\]>*-]+)\s*(\+\+|--))$")


def strip_type(t: str) -> str:
    first = t.split(None, 1)[0] if t.split() else ""
    if first in NOT_TYPE:
        return t
    for rx in (_STRIP_A, _STRIP_C, _STRIP_B):
        m = rx.match(t)
        if m:
            name = m.group(1).strip()
            if first in NOT_TYPE or name in NOT_TYPE:
                return t
            return f"{name} = {m.group(2).strip()}"
    return t


def aug_assign(t: str) -> str:
    for i, ch, d in scan_top(t):
        if d == 0 and ch == "=" and i > 0:
            m = _AUG_RX.match(t, i - 1) or _AUG_RX.match(t, i - 2)
            if m and m.end() == i + 1:
                lhs = t[:m.start()].strip()
                rhs = t[m.end():].strip()
                if not lhs or "(" in lhs and ")" not in lhs:
                    return t
                if has_top_op(rhs) and not (rhs.startswith("(") and rhs.endswith(")") and strip_outer_parens(rhs) != rhs):
                    rhs = f"({rhs})"
                return f"{lhs} = {lhs} {m.group(1)} {rhs}"
    return t


def incdec(t: str) -> str:
    m = _INC_RX.match(t)
    if not m:
        return t
    op = m.group(1) or m.group(4)
    lhs = m.group(2) or m.group(3)
    return f"{lhs} = {lhs} {'+' if op == '++' else '-'} 1"


_MULTI_HEAD = re.compile(r"^" + _MOD + _TYPE + r"(?:\s*[\*&]+\s*|\s+)(?=[\*&]*[A-Za-z_$])")
_DECLARATOR = re.compile(r"^[\*&]*[A-Za-z_$][\w$]*(?:\[[^\]]*\])*(?:\s*=(?![=>])\s*.+)?$", re.S)


def multi_decl(t: str) -> Optional[str]:
    """«int a[N], i, s = 0» -> «s = 0» (оставляем только инициализации)."""
    m = _MULTI_HEAD.match(t)
    if not m or t.split()[0] in NOT_TYPE:
        return None
    parts = [p.strip() for p in split_top(t[m.end():], ",")]
    if len(parts) < 2 or not all(_DECLARATOR.match(p) for p in parts):
        return None
    inits = [p.lstrip("*&").strip() for p in parts if "=" in p]
    return "; ".join(inits) if inits else ""


def norm_stmt(text: str, o: Options) -> Optional[str]:
    t = collapse(text).rstrip(";").strip()
    if not t:
        return None
    if o.gost_assign:
        md = multi_decl(t)
        if md is not None:
            if not md:
                return None if not o.keep_decl else t
            t = md
    if not o.keep_decl and _DECL_RX.match(t) and t.split()[0] not in NOT_TYPE:
        return None
    if o.gost_assign:
        t = strip_type(t)
        t = aug_assign(t)
        t = incdec(t)
        t = gostify(t)
    return t


def norm_head(text: str, o: Options) -> str:
    """Заголовок цикла for: «i = 0; i < n; i++» -> «i := 0; i < n; i := i + 1»."""
    parts = split_top(text, ";")
    if len(parts) == 3 and o.gost_assign:
        a = norm_stmt(parts[0], Options(gost_assign=True, keep_decl=True)) or ""
        c = collapse(parts[1])
        d = norm_stmt(parts[2], Options(gost_assign=True, keep_decl=True)) or ""
        return "; ".join(x for x in (a, c, d))
    return collapse(text)


# ---------------------------------------------------------------- классификация
IO_RX = re.compile(
    r"(?<![\w$.])(?:printf|fprintf|puts|fputs|putchar|cout|println|print|echo|writeln|write|scanf|fscanf|"
    r"fgets|gets|getchar|cin|readln|read|readLine|readline|input|nextInt|nextLine|nextDouble|nextFloat|"
    r"Scanln|Scanf|Scan|Sscanf|Printf|Println|Print|prompt|alert|WriteLine|ReadLine|Write|Read|"
    r"cerr|clog|getline|var_dump|print_r|printfn|readInt|readlnInt)\b"
    r"|System\.out|System\.in|console\.(?:log|error|warn|info)|fmt\.(?:Print|Scan|Fprint|Sprint)\w*|Console\.(?:Write|Read)\w*"
    r"|(?<![\w$])(?:print|println)!")


def carry(new, old):
    """Перенести номера строк исходника на новый узел."""
    if hasattr(old, "line"):
        new.line = old.line
        new.end = getattr(old, "end", old.line)
    if hasattr(old, "src"):
        new.src = old.src
    return new


def classify_and_fix(chart_body: list, o: Options, user_rx) -> list:
    out = []
    for n in chart_body:
        if isinstance(n, Proc):
            if n.kind == "stmt":
                t = norm_stmt(n.text, o)
                if t is None:
                    continue
                if IO_RX.search(t):
                    n = carry(Proc(t, "io"), n)
                elif user_rx is not None and user_rx.search(t):
                    n = carry(Proc(t, "predef"), n)
                else:
                    n = carry(Proc(t, "process"), n)
            out.append(n)
        elif isinstance(n, If):
            n.then = classify_and_fix(n.then, o, user_rx)
            n.els = classify_and_fix(n.els, o, user_rx)
            out.append(n)
        elif isinstance(n, Loop):
            n.body = classify_and_fix(n.body, o, user_rx)
            out.append(n)
        elif isinstance(n, Switch):
            n.cases = [(l, classify_and_fix(b, o, user_rx)) for l, b in n.cases]
            out.append(n)
        else:
            out.append(n)
    return merge_procs(out, o)


def merge_procs(items: list, o: Options) -> list:
    if o.merge <= 1:
        return items
    out = []
    for n in items:
        if (isinstance(n, Proc) and n.kind == "process" and out and isinstance(out[-1], Proc)
                and out[-1].kind == "process" and out[-1].text.count("\n") + 1 < o.merge):
            merged = Proc(out[-1].text + "\n" + n.text, "process")
            merged.line = getattr(out[-1], "line", 0)
            merged.end = getattr(n, "end", getattr(n, "line", 0))
            out[-1] = merged
        else:
            out.append(n)
    return out


def short_name(n: str) -> str:
    return n.replace("::", ".").split(".")[-1]


def finalize(charts: List[Chart], o: Options, extra_names=()) -> List[Chart]:
    names = sorted({short_name(c.name) for c in charts if c.kind == "function"} | set(extra_names), key=len, reverse=True)
    user_rx = None
    if names:
        user_rx = re.compile(r"(?<![\w$])(?:" + "|".join(re.escape(x) for x in names) + r")\s*\(")
    for c in charts:
        c.body = classify_and_fix(c.body, o, user_rx)
    return charts


# ---------------------------------------------------------------- уровни детализации и «разворачивание» вызовов
import copy


def _drop_simple(body: list, keep_calls: bool) -> list:
    out = []
    for n in body:
        if isinstance(n, Proc):
            if n.kind == "predef" and keep_calls:
                out.append(n)
            continue
        if isinstance(n, If):
            n.then, n.els = _drop_simple(n.then, keep_calls), _drop_simple(n.els, keep_calls)
        elif isinstance(n, Loop):
            n.body = _drop_simple(n.body, keep_calls)
        elif isinstance(n, Switch):
            n.cases = [(l, _drop_simple(b, keep_calls)) for l, b in n.cases]
        out.append(n)
    return out


def apply_detail(charts: List[Chart], o: Options) -> None:
    if o.detail in ("calls", "structure"):
        for c in charts:
            c.body = _drop_simple(c.body, keep_calls=(o.detail == "calls"))


_CALL_RX = re.compile(r"(?<![\w$])([A-Za-z_$][\w$]*)\s*\(")


def _convert_returns(body: list, fname: str, label: str, state: dict, top: bool = True) -> list:
    out = []
    for idx, n in enumerate(body):
        if isinstance(n, Ret) and n.text.startswith("возврат"):
            expr = n.text[len("возврат"):].strip()
            last = top and idx == len(body) - 1
            if expr:
                p = Proc(f"{fname} := {expr}", "process")
                carry(p, n)
                out.append(p)
            if not last:
                j = Jump("goto", label)
                carry(j, n)
                out.append(j)
                state["used"] = True
            continue
        if isinstance(n, If):
            n.then = _convert_returns(n.then, fname, label, state, False)
            n.els = _convert_returns(n.els, fname, label, state, False)
        elif isinstance(n, Loop):
            n.body = _convert_returns(n.body, fname, label, state, False)
        elif isinstance(n, Switch):
            n.cases = [(l, _convert_returns(b, fname, label, state, False)) for l, b in n.cases]
        out.append(n)
    return out


def _tag_src(body: list, fid: int) -> None:
    for n in body:
        if not hasattr(n, "src"):
            n.src = fid
        if isinstance(n, If):
            _tag_src(n.then, fid); _tag_src(n.els, fid)
        elif isinstance(n, Loop):
            _tag_src(n.body, fid)
        elif isinstance(n, Switch):
            for _, b in n.cases:
                _tag_src(b, fid)


def expand_charts(files_charts: List[List[Chart]], o: Options, ids=None) -> None:
    """Подставить тела вызываемых функций (того же проекта) в места вызова. files_charts[i] – схемы i-го файла;
    ids[i] – номер файла в проекте (для подсветки строк чужого файла)."""
    if o.expand <= 0:
        return
    ids = ids or list(range(len(files_charts)))
    orig = {id(c): copy.deepcopy(c.body) for fc in files_charts for c in fc}
    glob = {}
    local = []
    for fc in files_charts:
        m = {}
        for c in fc:
            if c.kind == "function":
                m.setdefault(short_name(c.name), c)
                glob.setdefault(short_name(c.name), c)
        local.append(m)
    counter = {}

    def walk(body, lmap, depth, stack):
        out = []
        for n in body:
            if isinstance(n, Proc) and n.kind == "predef" and depth > 0:
                callee = None
                for m in _CALL_RX.finditer(n.text):
                    cand = lmap.get(m.group(1)) or glob.get(m.group(1))
                    if cand is not None and id(cand) not in stack:
                        callee = cand
                        break
                if callee is not None:
                    out.append(n)
                    fn = short_name(callee.name)
                    counter[fn] = counter.get(fn, 0) + 1
                    label = f"возврат из {fn}" + (f" ({counter[fn]})" if counter[fn] > 1 else "")
                    inner = copy.deepcopy(orig[id(callee)])
                    cmap = next((lm for lm, fc in zip(local, files_charts) if callee in fc), lmap)
                    inner = walk(inner, cmap, depth - 1, stack | {id(callee)})
                    state = {"used": False}
                    inner = _convert_returns(inner, fn, label, state)
                    if state["used"]:
                        inner.append(Label(label))
                    fid = next((ids[k] for k, fc in enumerate(files_charts) if callee in fc), None)
                    if fid is not None:
                        _tag_src(inner, fid)
                    out.extend(inner)
                    continue
            if isinstance(n, If):
                n.then, n.els = walk(n.then, lmap, depth, stack), walk(n.els, lmap, depth, stack)
            elif isinstance(n, Loop):
                n.body = walk(n.body, lmap, depth, stack)
            elif isinstance(n, Switch):
                n.cases = [(l, walk(b, lmap, depth, stack)) for l, b in n.cases]
            out.append(n)
        return out

    for lmap, fc in zip(local, files_charts):
        for c in fc:
            c.body = walk(c.body, lmap, o.expand, frozenset([id(c)]))
