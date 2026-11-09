"""Python -> IR (через стандартный модуль ast)."""
from __future__ import annotations
import ast
from typing import List, Tuple
from .ir import *


def parse_python(src: str, o: Options) -> Tuple[List[Chart], List[str]]:
    tree = ast.parse(src)
    lines = src.splitlines()
    charts: List[Chart] = []
    warns: List[str] = []
    asg = " := " if o.gost_assign else " = "
    u = ast.unparse

    def comment_above(node) -> str:
        first = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
        buf = []
        k = first - 2
        while k >= 0 and lines[k].strip().startswith("#"):
            buf.append(lines[k].strip().lstrip("#").strip())
            k -= 1
        buf.reverse()
        doc = ast.get_docstring(node) or ""
        doc = " ".join(doc.split())
        if len(doc) > 220:
            doc = doc[:217] + "…"
        parts = [p for p in ["\n".join(buf), doc] if p]
        return "\n".join(parts)

    def register(node, prefix):
        name = ".".join(prefix + [node.name])
        body = conv_body(node.body, prefix + [node.name])
        sig = f"{name}({u(node.args)})"
        ch = Chart(name=name, body=body, signature=sig, comment=comment_above(node), kind="function")
        ch.line = node.lineno
        charts.append(ch)

    def conv_body(stmts, prefix, module=False) -> list:
        out = []
        for s in stmts:
            out.extend(conv_stmt(s, prefix, module))
        return out

    def conv_stmt(s, prefix, module) -> list:
        res = _conv_stmt(s, prefix, module)
        simple = not hasattr(s, "body")
        for n in res:
            if not hasattr(n, "line"):
                n.line = s.lineno
                n.end = getattr(s, "end_lineno", s.lineno) if (simple and isinstance(n, (Proc, Ret, Jump))) else s.lineno
        return res

    def _conv_stmt(s, prefix, module) -> list:
        if isinstance(s, (ast.Import, ast.ImportFrom, ast.Pass, ast.Global, ast.Nonlocal)):
            return []
        if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)):
            register(s, prefix)
            return []
        if isinstance(s, ast.ClassDef):
            for sub in s.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    register(sub, prefix + [s.name])
                elif isinstance(sub, ast.ClassDef):
                    conv_stmt(sub, prefix + [s.name], False)
            return []
        if isinstance(s, ast.Expr):
            if isinstance(s.value, ast.Constant) and isinstance(s.value.value, str):
                return []
            return [Proc(u(s.value))]
        if isinstance(s, ast.Assign):
            return [Proc(asg.join([u(t) for t in s.targets] + [u(s.value)]))]
        if isinstance(s, ast.AugAssign):
            b = ast.BinOp(left=s.target, op=s.op, right=s.value)
            return [Proc(f"{u(s.target)}{asg}{u(b)}")]
        if isinstance(s, ast.AnnAssign):
            return [] if s.value is None else [Proc(f"{u(s.target)}{asg}{u(s.value)}")]
        if isinstance(s, ast.Return):
            return [Ret("возврат " + u(s.value) if s.value is not None else "возврат")]
        if isinstance(s, ast.Raise):
            return [Ret("raise " + u(s.exc) if s.exc is not None else "raise")]
        if isinstance(s, ast.Assert):
            return [Proc("assert " + u(s.test))]
        if isinstance(s, ast.Delete):
            return [Proc("del " + ", ".join(u(t) for t in s.targets))]
        if isinstance(s, ast.Break):
            return [Jump("break")]
        if isinstance(s, ast.Continue):
            return [Jump("continue")]
        if isinstance(s, ast.If):
            t = s.test
            if (module and isinstance(t, ast.Compare) and isinstance(t.left, ast.Name) and t.left.id == "__name__"):
                return conv_body(s.body, prefix, module)
            return [If(strip_outer_parens(u(t)), conv_body(s.body, prefix), conv_body(s.orelse, prefix))]
        if isinstance(s, ast.While):
            if s.orelse:
                warns.append(f"строка {s.lineno}: ветка else у цикла while не отображена")
            return [Loop("пока " + strip_outer_parens(u(s.test)), None, conv_body(s.body, prefix))]
        if isinstance(s, (ast.For, ast.AsyncFor)):
            if s.orelse:
                warns.append(f"строка {s.lineno}: ветка else у цикла for не отображена")
            return [Loop(f"для {u(s.target)} in {u(s.iter)}", None, conv_body(s.body, prefix))]
        if isinstance(s, ast.Try) or s.__class__.__name__ == "TryStar":
            body = conv_body(s.body, prefix)
            els: list = []
            for h in reversed(s.handlers):
                cond = "Исключение" + (": " + u(h.type) if h.type is not None else "") + "?"
                node = If(cond, conv_body(h.body, prefix), els)
                node.line = node.end = h.lineno
                els = [node]
            return body + els + conv_body(s.orelse, prefix) + conv_body(s.finalbody, prefix)
        if isinstance(s, (ast.With, ast.AsyncWith)):
            head = "with " + ", ".join(u(i) for i in s.items)
            return [Proc(head)] + conv_body(s.body, prefix)
        if s.__class__.__name__ == "Match":
            cases = []
            for c in s.cases:
                pat = u(c.pattern)
                if pat == "_":
                    pat = "иначе"
                if c.guard is not None:
                    pat += " if " + u(c.guard)
                cases.append((pat, conv_body(c.body, prefix)))
            return [Switch(u(s.subject), cases)]
        try:
            return [Proc(u(s).split("\n")[0])]
        except Exception:
            return []

    body = conv_body(tree.body, [], module=True)
    funcs = charts[:]
    charts.clear()
    if body:
        charts.append(Chart(name="Основная программа", body=body, kind="program"))
    charts.extend(sorted(funcs, key=lambda c: getattr(c, 'line', 0)))
    return charts, warns
