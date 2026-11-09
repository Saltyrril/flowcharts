"""Раскладка блок-схемы по ГОСТ 19.701-90.

Результат – список графических примитивов (многоугольники, линии, текст), общий для SVG- и PNG-вывода.
Ось каждого блока – x = 0, вход блока – (0, 0), выход – (0, exit_y).
"""
from __future__ import annotations
import math
import textwrap
from typing import List, Optional
from .ir import *

FS = 13          # размер шрифта, px
CW = 7.7         # средняя ширина символа, px
LH = 17          # межстрочный интервал
W = 232          # стандартная ширина символа
HW = W / 2
DHW = 124        # полуширина символа «Решение»
GAP = 30         # вертикальный зазор между символами
HGAP = 46        # горизонтальный зазор между ветвями
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


# ------------------------------------------------------------------ примитивы
def shift_prim(p, dx, dy):
    k = p[0]
    if k == "poly":
        return (k, [(x + dx, y + dy) for x, y in p[1]])
    if k == "ellipse":
        return (k, p[1] + dx, p[2] + dy, p[3], p[4])
    if k == "stadium":
        return (k, p[1] + dx, p[2] + dy, p[3] + dx, p[4] + dy)
    if k == "line":
        return (k, [(x + dx, y + dy) for x, y in p[1]], p[2], p[3])
    if k == "text":
        return (k, p[1] + dx, p[2] + dy) + tuple(p[3:])
    return p


def line(pts, arrow=False, dashed=False):
    return ("line", list(pts), arrow, dashed)


def text(x, y, s, anchor="middle", size=FS, style=""):
    return ("text", x, y, s, size, anchor, style)


def wrap(s: str, maxc: int, maxlines: int = 12) -> List[str]:
    lines: List[str] = []
    for para in str(s).split("\n"):
        ls = textwrap.wrap(para.rstrip(), width=max(4, maxc), break_long_words=True, break_on_hyphens=False,
                           replace_whitespace=False) or [""]
        lines += ls
    if len(lines) > maxlines:
        lines = lines[:maxlines]
        lines[-1] = lines[-1][:max(1, maxc - 1)] + "…"
    return lines


def text_lines(lines, cx, cy, anchor="middle", size=FS):
    n = len(lines)
    y0 = cy - (n - 1) * LH / 2
    return [text(cx, y0 + k * LH, ln, anchor, size) for k, ln in enumerate(lines)]


class Block:
    """Блок раскладки. ent – id первого символа; exits – [(id, порт, подпись)] живых выходов; edges – связи внутри блока."""
    __slots__ = ("prims", "left", "right", "height", "exit_y", "recv", "ent", "exits", "edges")

    def __init__(self, prims=None, left=0.0, right=0.0, height=0.0, exit_y: Optional[float] = 0.0, recv=False,
                 ent=None, exits=None, edges=None):
        self.prims = prims or []
        self.left, self.right, self.height, self.exit_y, self.recv = left, right, height, exit_y, recv
        self.ent, self.exits, self.edges = ent, exits or [], edges or []

    def shifted(self, dx, dy):
        return [shift_prim(p, dx, dy) for p in self.prims]

    @property
    def empty(self):
        return not self.prims


def leaf(prims, hw, h, alive=True, recv=False):
    return Block(prims, hw, hw, h, h if alive else None, recv)


# ------------------------------------------------------------------ символы
def n_process(txt, predef=False, left_align=False):
    lines = wrap(txt, int((W - 22) / CW), 14)
    h = max(44, len(lines) * LH + 18)
    prims = [("poly", [(-HW, 0), (HW, 0), (HW, h), (-HW, h)])]
    if predef:
        prims += [line([(-HW + 13, 0), (-HW + 13, h)]), line([(HW - 13, 0), (HW - 13, h)])]
    if left_align:
        prims += text_lines(lines, -HW + 10, h / 2, "start")
    else:
        prims += text_lines(lines, 0, h / 2)
    return leaf(prims, HW, h)


def n_io(txt):
    s = 20
    lines = wrap(txt, int((W - 2 * s - 6) / CW), 12)
    h = max(44, len(lines) * LH + 18)
    prims = [("poly", [(-HW + s, 0), (HW, 0), (HW - s, h), (-HW, h)])] + text_lines(lines, 0, h / 2)
    return leaf(prims, HW, h)


def n_decision(txt):
    words = str(txt).split() or [""]
    longest = max(len(w) for w in words)
    dhw = DHW
    # длинное слово не должно разрываться: при необходимости расширяем ромб
    if longest * CW + 8 > 0.62 * 2 * dhw:
        dhw = min(260, math.ceil((longest * CW + 8) / 0.62 / 2))
    best = None
    for maxc in range(max(10, min(longest, 40)), 50):
        lines = wrap(txt, maxc, 8)
        tw = max(len(l) for l in lines) * CW + 8
        th = len(lines) * LH + 6
        if tw / (2 * dhw) >= 0.80:
            continue
        H = th / (1 - tw / (2 * dhw))
        if best is None or H < best[0] - 1:
            best = (H, lines)
    if best is None:
        lines = wrap(txt, max(10, longest), 8)
        best = (len(lines) * LH * 3.2, lines)
    H = max(72, math.ceil(best[0]))
    prims = [("poly", [(0, 0), (dhw, H / 2), (0, H), (-dhw, H / 2)])] + text_lines(best[1], 0, H / 2)
    return Block(prims, dhw, dhw, H, H)


def n_term(txt, alive=True):
    lines = wrap(txt, int((W - 30) / CW), 6)
    tw = max(len(l) for l in lines) * CW + 44
    w = min(W, max(150, tw))
    h = max(38, len(lines) * LH + 14)
    prims = [("stadium", -w / 2, 0, w / 2, h)] + text_lines(lines, 0, h / 2)
    return Block(prims, w / 2, w / 2, h, h if alive else None)


def n_loop(txt, top=True):
    c = 15
    lines = wrap(txt, int((W - 2 * c - 4) / CW), 8)
    h = max(40, len(lines) * LH + 16)
    if top:
        pts = [(-HW + c, 0), (HW - c, 0), (HW, c), (HW, h), (-HW, h), (-HW, c)]
    else:
        pts = [(-HW, 0), (HW, 0), (HW, h - c), (HW - c, h), (-HW + c, h), (-HW, h - c)]
    return leaf([("poly", pts)] + text_lines(lines, 0, h / 2), HW, h)


def n_conn(label, note="", alive=True, recv=False):
    r = 17
    prims = [("ellipse", 0, r, r, r), text(0, r, str(label), "middle", 12)]
    right = r
    if note:
        n = note if len(note) <= 28 else note[:27] + "…"
        prims.append(text(r + 8, r, n, "start", 11, "note"))
        right = r + 8 + len(n) * CW * 0.85
    return Block(prims, r, right, 2 * r, 2 * r if alive else None, recv)


# ------------------------------------------------------------------ последовательность
def seq_blocks(blocks: List[Block]) -> Block:
    prims: list = []
    edges: list = []
    left = right = 0.0
    cur_h = 0.0
    exit_y: Optional[float] = 0.0
    alive = True
    first = True
    ent = None
    exits: list = []
    for b in blocks:
        if b.empty and b.height == 0:
            continue
        if not first and not alive:
            if not b.recv:
                continue                     # недостижимый код
            top = cur_h + GAP * 1.4
        elif first:
            top = 0.0
            ent = b.ent
        else:
            top = max(exit_y, cur_h) + GAP
            prims.append(line([(0, exit_y), (0, top)], arrow=True))
            for sid, port, lb in exits:
                edges.append({"f": sid, "p": port, "t": b.ent, "lb": lb})
        prims += b.shifted(0, top)
        edges += b.edges
        left, right = max(left, b.left), max(right, b.right)
        cur_h = max(cur_h, top + b.height)
        if b.exit_y is None:
            alive, exits = False, []
        else:
            alive, exit_y, exits = True, top + b.exit_y, list(b.exits)
        first = False
    return Block(prims, left, right, cur_h, exit_y if alive else None, ent=ent, exits=exits if alive else [], edges=edges)


class Ctx:
    def __init__(self, kind):
        self.kind = kind
        self.break_n = None
        self.cont_n = None


def collect_gotos(stmts, acc=None):
    acc = set() if acc is None else acc
    for s in stmts:
        if isinstance(s, Jump) and s.kind == "goto":
            acc.add(s.target)
        elif isinstance(s, If):
            collect_gotos(s.then, acc); collect_gotos(s.els, acc)
        elif isinstance(s, Loop):
            collect_gotos(s.body, acc)
        elif isinstance(s, Switch):
            for _, b in s.cases:
                collect_gotos(b, acc)
    return acc


class Builder:
    def __init__(self, o: Options):
        self.o = o
        self.stack: List[Ctx] = []
        self.conn_n = 0
        self.loop_n = 0
        self.goto_nums = {}
        self.gotos = set()
        self.warns: List[str] = []
        self.sid_n = 0
        self.lines = {}          # id символа -> (строка, конец) исходника

    def mark(self, b: Block, kind: str, txt: str, s=None, line=None, end=None) -> str:
        """Пометить примитивы блока как символ схемы (для подсветки и редактора)."""
        self.sid_n += 1
        sid = f"s{self.sid_n}"
        b.prims = [("mark", "b", sid, kind, str(txt))] + b.prims + [("mark", "e", sid)]
        ln = line if line is not None else getattr(s, "line", 0)
        en = end if end is not None else getattr(s, "end", ln)
        if ln:
            self.lines[sid] = (ln, en or ln, getattr(s, "src", None))
        b.ent = sid
        b.exits = [(sid, "b", "")] if b.exit_y is not None else []
        return sid

    def sym(self, b: Block, kind: str, txt: str, s=None, line=None) -> Block:
        self.mark(b, kind, txt, s, line)
        return b

    def new_conn(self):
        self.conn_n += 1
        return str(self.conn_n)

    def goto_num(self, name):
        if name not in self.goto_nums:
            self.goto_nums[name] = self.new_conn()
        return self.goto_nums[name]

    def loop_name(self):
        n = self.loop_n
        self.loop_n += 1
        return LETTERS[n % 26] + (str(n // 26) if n >= 26 else "")

    def seq(self, stmts) -> Block:
        blocks = []
        for s in stmts:
            blocks.extend(self.stmt(s))
        return seq_blocks(blocks)

    # ---------------------------------------------------------------- операторы
    def stmt(self, s) -> List[Block]:
        if isinstance(s, Proc):
            if s.kind == "predef":
                return [self.sym(n_process(s.text, predef=True), "predef", s.text, s)]
            if s.kind == "io":
                return [self.sym(n_io(s.text), "io", s.text, s)]
            return [self.sym(n_process(s.text, left_align=(s.kind == "asm")), "process", s.text, s)]
        if isinstance(s, If):
            return [self.if_block(s)]
        if isinstance(s, Loop):
            return self.loop_block(s)
        if isinstance(s, Switch):
            return self.switch_block(s)
        if isinstance(s, Ret):
            return [self.sym(n_term(s.text, alive=False), "term", s.text, s)]
        if isinstance(s, Jump):
            if s.kind == "goto":
                return [self.sym(n_conn(self.goto_num(s.target), s.target, alive=False), "conn", self.goto_num(s.target), s)]
            ctxs = [c for c in reversed(self.stack) if (s.kind == "break" or c.kind == "loop")]
            if not ctxs:
                self.warns.append(f"{s.kind} вне цикла")
                return [self.sym(n_term(s.kind, alive=False), "term", s.kind, s)]
            c = ctxs[0]
            if s.kind == "break":
                if c.break_n is None:
                    c.break_n = self.new_conn()
                note = "выход из цикла" if c.kind == "loop" else "выход из выбора"
                return [self.sym(n_conn(c.break_n, note, alive=False), "conn", c.break_n, s)]
            if c.cont_n is None:
                c.cont_n = self.new_conn()
            return [self.sym(n_conn(c.cont_n, "следующая итерация", alive=False), "conn", c.cont_n, s)]
        if isinstance(s, Label):
            if s.name in self.gotos:
                return [self.sym(n_conn(self.goto_num(s.name), s.name, recv=True), "conn", self.goto_num(s.name), s)]
            return []
        return []

    def if_block(self, s: If) -> Block:
        d = n_decision(s.cond)
        dh = d.height
        DHW = d.left
        sid = self.mark(d, "decision", s.cond, s)
        bt, be = self.seq(s.then), self.seq(s.els)
        t_alive, e_alive = bt.exit_y is not None, be.exit_y is not None
        by = dh + GAP
        prims = list(d.prims)
        edges = bt.edges + be.edges
        t_empty, e_empty = bt.empty, be.empty

        def lab(x, y, s_, anchor):
            return text(x, y, s_, anchor, 12)

        # ----- обе ветви непустые и обе живы (или обе завершаются): «да» слева, «нет» справа
        if not t_empty and not e_empty and t_alive == e_alive:
            xl = -max(bt.right + HGAP / 2, DHW + 22)
            xr = max(be.left + HGAP / 2, DHW + 22)
            prims += [line([(-DHW, dh / 2), (xl, dh / 2), (xl, by)], arrow=True),
                      line([(DHW, dh / 2), (xr, dh / 2), (xr, by)], arrow=True),
                      lab(-DHW - 4, dh / 2 - 8, "да", "end"), lab(DHW + 4, dh / 2 - 8, "нет", "start")]
            prims += bt.shifted(xl, by) + be.shifted(xr, by)
            edges += [{"f": sid, "p": "l", "t": bt.ent, "lb": "да"}, {"f": sid, "p": "r", "t": be.ent, "lb": "нет"}]
            left = max(DHW, -xl + bt.left)
            right = max(DHW, xr + be.right)
            heights = max(by + bt.height, by + be.height)
            if t_alive or e_alive:
                merge_y = max([by + b.height for b, a in ((bt, t_alive), (be, e_alive)) if a]) + GAP
                for b, x, a in ((bt, xl, t_alive), (be, xr, e_alive)):
                    if a:
                        prims.append(line([(x, by + b.exit_y), (x, merge_y), (0, merge_y)]))
                return Block(prims, left, right, max(heights, merge_y), merge_y, ent=sid,
                             exits=bt.exits + be.exits, edges=edges)
            return Block(prims, left, right, heights, None, ent=sid, exits=[], edges=edges)

        # ----- одна ветвь «основная» (под символом), другая – сбоку справа
        if t_empty and e_empty:
            main, side, main_lab, side_lab = bt, be, "да", "нет"
        elif t_alive != e_alive:
            if t_alive:
                main, side, main_lab, side_lab = bt, be, "да", "нет"
            else:
                main, side, main_lab, side_lab = be, bt, "нет", "да"
        else:  # одна пустая, другая непустая (обе живы)
            if t_empty:
                main, side, main_lab, side_lab = be, bt, "нет", "да"
            else:
                main, side, main_lab, side_lab = bt, be, "да", "нет"
        side_is_bypass = side.empty
        if side_is_bypass:
            xs = max(DHW + 24, main.right + 26)
        else:
            xs = max(DHW + 24, main.right + HGAP + side.left)
        prims += [lab(DHW + 4, dh / 2 - 8, side_lab, "start")]
        prims.append(line([(DHW, dh / 2), (xs, dh / 2)] + ([(xs, by)] if not side_is_bypass else []), arrow=not side_is_bypass))
        if not side_is_bypass:
            prims += side.shifted(xs, by)
            edges.append({"f": sid, "p": "r", "t": side.ent, "lb": side_lab})
        main_empty = main.empty
        prims.append(lab(6, dh + 14, main_lab, "start"))
        if not main_empty:
            prims.append(line([(0, dh), (0, by)], arrow=True))
            prims += main.shifted(0, by)
            edges.append({"f": sid, "p": "b", "t": main.ent, "lb": main_lab})
            m_exit = by + main.exit_y
            m_h = by + main.height
            exits = list(main.exits)
        else:
            m_exit, m_h = dh, dh
            exits = [(sid, "b", main_lab)]
        side_h = (by + side.height) if not side_is_bypass else 0
        left = max(DHW, main.left)
        right = max(DHW, main.right, (xs + side.right) if not side_is_bypass else xs)
        if side_is_bypass:
            merge_y = max(m_h, m_exit) + GAP
            prims.append(line([(0, m_exit), (0, merge_y)]))
            prims.append(line([(xs, dh / 2), (xs, merge_y), (0, merge_y)]))
            exits.append((sid, "r", side_lab))
            return Block(prims, left, right, merge_y, merge_y, ent=sid, exits=exits, edges=edges)
        if side.exit_y is not None:
            exits += side.exits
        return Block(prims, left, right, max(m_h, side_h, dh), m_exit, ent=sid, exits=exits, edges=edges)

    def loop_block(self, s: Loop) -> List[Block]:
        ctx = Ctx("loop")
        name = self.loop_name()
        body_stmts = list(s.body)
        while body_stmts and isinstance(body_stmts[-1], Jump) and body_stmts[-1].kind == "continue":
            body_stmts.pop()
        self.stack.append(ctx)
        body = self.seq(body_stmts)
        self.stack.pop()
        top_txt = f"{name} {s.top}" if s.top else name
        bot_txt = f"{name} {s.bottom}" if s.bottom else name
        top = n_loop(top_txt, True)
        bottom = n_loop(bot_txt, False)
        self.mark(top, "looptop", top_txt, s)
        ln = getattr(s, "line", 0)
        self.mark(bottom, "loopbot", bot_txt, s, line=ln, end=ln)
        parts = [top]
        if not body.empty:
            parts.append(body)
        if ctx.cont_n is not None:
            parts.append(self.sym(n_conn(ctx.cont_n, "следующая итерация", recv=True), "conn", ctx.cont_n, s))
        body_alive = body.empty or body.exit_y is not None or ctx.cont_n is not None
        if not body_alive:
            bottom.recv = True
        parts.append(bottom)
        if ctx.break_n is not None:
            parts.append(self.sym(n_conn(ctx.break_n, "выход из цикла", recv=True), "conn", ctx.break_n, s))
        return [seq_blocks(parts)]

    def switch_block(self, s: Switch) -> List[Block]:
        ctx = Ctx("switch")
        d = n_decision(s.expr)
        dh = d.height
        DHW = d.left
        sid = self.mark(d, "decision", s.expr, s)
        self.stack.append(ctx)
        branches = [(self.fit(lbl), self.seq(body)) for lbl, body in s.cases]
        self.stack.pop()
        if not any(l == "иначе" for l, _ in branches):
            branches.append(("иначе", Block()))
        xs, cur, prev = [], 0.0, None
        for lbl, b in branches:
            l, r = max(b.left, 70), max(b.right, 70)
            cur = 0.0 if prev is None else xs[-1] + prev + HGAP + l
            xs.append(cur)
            prev = r
        shift = -(xs[0] + xs[-1]) / 2
        xs = [x + shift for x in xs]
        bus_y = dh + 14
        by = bus_y + GAP
        prims = list(d.prims)
        prims.append(line([(0, dh), (0, bus_y)]))
        prims.append(line([(min(xs), bus_y), (max(xs), bus_y)]))
        left = right = DHW
        alive_ends = []
        edges: list = []
        exits: list = []
        heights = by
        for (lbl, b), x in zip(branches, xs):
            prims.append(line([(x, bus_y), (x, by)], arrow=not b.empty))
            prims.append(text(x + 5, bus_y + 12, lbl, "start", 12))
            prims += b.shifted(x, by)
            edges += b.edges
            if b.empty:
                exits.append((sid, "b", lbl))
            else:
                edges.append({"f": sid, "p": "b", "t": b.ent, "lb": lbl})
            left, right = max(left, -x + b.left, -x + 70), max(right, x + b.right, x + 70)
            heights = max(heights, by + b.height)
            if b.exit_y is not None:
                alive_ends.append((x, by + b.exit_y, by + b.height))
                if not b.empty:
                    exits += b.exits
        out = []
        if alive_ends:
            merge_y = max(h for _, _, h in alive_ends) + GAP
            for x, ey, _ in alive_ends:
                prims.append(line([(x, ey), (x, merge_y), (0, merge_y)]))
            blk = Block(prims, left, right, max(merge_y, heights), merge_y, ent=sid, exits=exits, edges=edges)
        else:
            blk = Block(prims, left, right, heights, None, ent=sid, exits=[], edges=edges)
        out.append(blk)
        if ctx.break_n is not None:
            out.append(self.sym(n_conn(ctx.break_n, "выход из выбора", recv=True), "conn", ctx.break_n, s))
        return [seq_blocks(out)]

    @staticmethod
    def fit(lbl, n=26):
        return lbl if len(lbl) <= n else lbl[:n - 1] + "…"


# ------------------------------------------------------------------ схема целиком
class Rendered:
    def __init__(self, name, prims, width, height):
        self.name, self.prims, self.width, self.height = name, prims, width, height


def prim_bbox(prims):
    xs, ys = [], []
    for p in prims:
        k = p[0]
        if k == "poly" or k == "line":
            for x, y in p[1]:
                xs.append(x); ys.append(y)
        elif k == "ellipse":
            xs += [p[1] - p[3], p[1] + p[3]]; ys += [p[2] - p[4], p[2] + p[4]]
        elif k == "stadium":
            xs += [p[1], p[3]]; ys += [p[2], p[4]]
        elif k == "text":
            w = len(p[3]) * CW * p[4] / FS
            x = p[1]
            a = p[5]
            x0 = x - w / 2 if a == "middle" else (x if a == "start" else x - w)
            xs += [x0, x0 + w]; ys += [p[2] - 8, p[2] + 8]
    return min(xs), min(ys), max(xs), max(ys)


def comment_prims(lines, start: Block):
    """Символ «Комментарий» (ГОСТ 19.701-90, 3.4.3): скобка + пунктирная линия к символу."""
    wrapped = []
    for l in lines:
        wrapped += wrap(l, 40, 8)
    wrapped = wrapped[:14]
    n = len(wrapped)
    h = n * LH + 10
    sx = start.right + 40
    mid = start.height / 2
    y0, y1 = mid - h / 2, mid + h / 2
    inner = [line([(sx + 10, y0), (sx, y0), (sx, y1), (sx + 10, y1)])] + text_lines(wrapped, sx + 18, mid, "start")
    dashed = line([(start.right, mid), (sx, mid)], dashed=True)
    width = max(len(l) for l in wrapped) * CW + 18
    return inner, dashed, sx + 18 + width, "\n".join(wrapped)


def extract_model(prims, lines_map, caption, width, height):
    """Граф схемы для редактора: символы (по меткам) с координатами и текстом."""
    nodes, cur = [], None
    for p in prims:
        if p[0] == "mark":
            if p[1] == "b":
                cur = {"id": p[2], "k": p[3], "text": p[4], "shape": None, "texts": [], "note": ""}
            else:
                if cur is not None:
                    nodes.append(cur)
                cur = None
            continue
        if cur is None:
            continue
        k = p[0]
        if k in ("poly", "ellipse", "stadium") and cur["shape"] is None:
            cur["shape"] = p
        elif k == "line" and cur["k"] == "comment":
            cur["shape"] = p
        elif k == "text":
            if p[6] == "note":
                cur["note"] = p[3]
            else:
                cur["texts"].append(p)
    out = []
    for n in nodes:
        sh = n["shape"]
        if sh is None:
            continue
        if sh[0] == "poly" or sh[0] == "line":
            xs = [x for x, _ in sh[1]]; ys = [y for _, y in sh[1]]
            x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        elif sh[0] == "ellipse":
            x0, y0, x1, y1 = sh[1] - sh[3], sh[2] - sh[4], sh[1] + sh[3], sh[2] + sh[4]
        else:
            x0, y0, x1, y1 = sh[1], sh[2], sh[3], sh[4]
        d = {"id": n["id"], "k": n["k"], "x": round(x0, 1), "y": round(y0, 1), "w": round(x1 - x0, 1), "h": round(y1 - y0, 1),
             "text": n["text"], "note": n["note"]}
        if n["texts"] and n["texts"][0][5] == "start":
            d["align"] = "left"
        if n["k"] == "comment":
            tw = max((len(t[3]) for t in n["texts"]), default=1) * CW + 18
            d["w"] = round(tw, 1)
        ln = lines_map.get(n["id"])
        if ln:
            d["l"], d["e"] = ln[0], ln[1]
            if len(ln) > 2 and ln[2] is not None:
                d["f"] = ln[2]
        out.append(d)
    return out


def build_chart(chart: Chart, o: Options) -> Rendered:
    b = Builder(o)
    b.gotos = collect_gotos(chart.body)
    start = n_term("начало")
    b.mark(start, "term", "начало", line=getattr(chart, "line", 0) or None)
    cm_edge = None
    cm_prims = None
    lines = []
    if o.show_comment:
        if chart.signature:
            lines.append(chart.signature)
        for l in (chart.comment or "").split("\n"):
            if l.strip():
                lines.append("// " + l.strip())
    if lines:
        inner, dashed, extra_right, ctext = comment_prims(lines, start)
        cb = Block(inner)
        csid = b.mark(cb, "comment", ctext)
        start = Block(start.prims + cb.prims + [dashed], start.left, extra_right, start.height, start.exit_y,
                      ent=start.ent, exits=start.exits, edges=[{"f": start.ent, "p": "r", "t": csid, "lb": "", "d": 1}])
    body = b.seq(chart.body)
    blocks = [start] + ([body] if not body.empty else [])
    s1 = seq_blocks(blocks)
    if s1.exit_y is not None:
        end = n_term("конец")
        b.mark(end, "term", "конец")
        s1 = seq_blocks([s1, end])
    prims = list(s1.prims)
    x0, y0, x1, y1 = prim_bbox(prims)
    caption = f"Блок-схема: {chart.name}"
    cap_w = len(caption) * CW * 1.05
    margin = 28
    width = max(x1 - x0, cap_w) + 2 * margin
    cx_shift = -x0 + margin + (width - 2 * margin - (x1 - x0)) / 2
    prims = [shift_prim(p, cx_shift, -y0 + margin) for p in prims]
    height = (y1 - y0) + 2 * margin + 38
    prims.append(text(width / 2, height - 22, caption, "middle", 14, "caption"))
    r = Rendered(chart.name, prims, math.ceil(width), math.ceil(height))
    r.warns = b.warns
    r.lines = b.lines
    r.model = {"w": r.width, "h": r.height, "caption": caption,
               "nodes": extract_model(prims, b.lines, caption, r.width, r.height), "edges": s1.edges}
    return r
