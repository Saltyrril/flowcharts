"""Командная строка и запуск веб-интерфейса."""
from __future__ import annotations
import argparse
import os
import re
import sys
from .core import build_project, LANGS
from .ir import Options
from .render import render_svg, render_png, render_pdf, pil_available


def read_text(path: str) -> str:
    data = open(path, "rb").read()
    for enc in ("utf-8-sig", "cp1251", "cp866", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", "replace")


def safe(name: str) -> str:
    return re.sub(r"[^\w.\-]+", "_", name, flags=re.U).strip("_") or "chart"


IGNORE_DIRS = {"node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build", "target", ".idea", ".vs", "obj", ".gradle"}


def collect_files(paths):
    """Файлы и папки (рекурсивно) -> [(путь на диске, имя в проекте)]."""
    from .core import EXT
    out = []
    for p in paths:
        if os.path.isdir(p):
            root = os.path.abspath(p)
            base = os.path.basename(root)
            for dp, dn, fn in os.walk(root):
                dn[:] = sorted(d for d in dn if d not in IGNORE_DIRS)
                for f in sorted(fn):
                    ext = f.rsplit(".", 1)[-1] if "." in f else ""
                    if ext in EXT or ext == "S":
                        full = os.path.join(dp, f)
                        out.append((full, base + "/" + os.path.relpath(full, root).replace(os.sep, "/")))
        else:
            out.append((p, os.path.basename(p)))
    return out


def build_parser():
    p = argparse.ArgumentParser(
        prog="gostflow",
        description="Построение блок-схем по исходному коду в соответствии с ГОСТ 19.701-90.\n"
                    "Без аргументов запускает веб-интерфейс (загрузка файлов и папок в окне программы).",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="*", help="исходные файлы и/или папки проекта (язык определяется по расширению)")
    p.add_argument("-l", "--lang", choices=sorted(LANGS), help="язык (по умолчанию определяется автоматически)")
    p.add_argument("-o", "--out", default="flowcharts", help="каталог для результата (по умолчанию ./flowcharts)")
    p.add_argument("-f", "--format", default="svg", help="форматы через запятую: svg,png,pdf (по умолчанию svg)")
    p.add_argument("--detail", choices=["full", "calls", "structure"], default="full",
                   help="уровень детализации: full – полная, calls – структура + вызовы, structure – только циклы и условия")
    p.add_argument("--expand", type=int, default=0, metavar="N", help="развернуть вызовы функций проекта внутрь схемы (глубина N)")
    p.add_argument("--merge", type=int, default=1, metavar="N", help="объединять до N подряд идущих простых операторов в один блок")
    p.add_argument("--keep-assign", action="store_true", help="не заменять «=» на «:=» и не упрощать i++ / x += 1")
    p.add_argument("--keep-decl", action="store_true", help="показывать объявления переменных без инициализации")
    p.add_argument("--no-comment", action="store_true", help="не рисовать символ «Комментарий» у блока «начало»")
    p.add_argument("--asm-group", type=int, default=6, metavar="N", help="ассемблер: макс. команд в одном блоке (по умолчанию 6)")
    p.add_argument("--asm-comments", action="store_true", help="ассемблер: добавлять комментарии из исходника в блоки")
    p.add_argument("--serve", action="store_true", help="запустить веб-интерфейс в браузере")
    p.add_argument("--port", type=int, default=8765, help="порт веб-интерфейса (по умолчанию 8765)")
    p.add_argument("--no-browser", action="store_true", help="не открывать браузер автоматически")
    p.add_argument("--list-langs", action="store_true", help="показать поддерживаемые языки")
    return p


def options_from(a) -> Options:
    return Options(gost_assign=not a.keep_assign, keep_decl=a.keep_decl, merge=max(1, a.merge), asm_group=max(1, a.asm_group),
                   asm_comments=a.asm_comments, show_comment=not a.no_comment, detail=a.detail, expand=max(0, a.expand))


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    if a.list_langs:
        for k, v in LANGS.items():
            print(f"{k:12s} {v}")
        return 0
    if a.serve or not a.files:
        from .server import serve
        serve(a.port, open_browser=not a.no_browser)
        return 0
    fmts = [x.strip().lower() for x in a.format.split(",") if x.strip()]
    if any(f in ("png", "pdf") for f in fmts) and not pil_available():
        print("Для PNG/PDF нужен пакет Pillow:  pip install pillow", file=sys.stderr)
        fmts = [f for f in fmts if f == "svg"] or ["svg"]
    items = collect_files(a.files)
    if not items:
        print("Не найдено файлов с исходным кодом.", file=sys.stderr)
        return 1
    os.makedirs(a.out, exist_ok=True)
    files = [{"name": name, "code": read_text(path), "lang": a.lang or ""} for path, name in items]
    results = build_project(files, options_from(a), a.lang or "auto")
    rc, all_rendered = 0, []
    for fr in results:
        if fr.error:
            print(f"{fr.name}: {fr.error}", file=sys.stderr)
            rc = 1
            continue
        print(f"{fr.name}: язык {LANGS.get(fr.lang, fr.lang)}, схем: {len(fr.charts)}")
        for w in fr.warns:
            print("  ! " + w)
        stem_dir = os.path.join(a.out, *[safe(p) for p in fr.name.replace(".", "_").split("/")]) if len(results) > 1 else a.out
        os.makedirs(stem_dir, exist_ok=True)
        base = safe(os.path.basename(fr.name))
        for i, r in enumerate(fr.charts, 1):
            stem = os.path.join(stem_dir, f"{base}_{i:02d}_{safe(r.name)}" if len(results) == 1 else f"{i:02d}_{safe(r.name)}")
            if "svg" in fmts:
                open(stem + ".svg", "w", encoding="utf-8").write(render_svg(r))
            if "png" in fmts:
                open(stem + ".png", "wb").write(render_png(r))
            print(f"  {r.name:30s} -> {stem}.*")
            all_rendered.append(r)
    if "pdf" in fmts and all_rendered:
        pdf = os.path.join(a.out, "flowcharts.pdf")
        open(pdf, "wb").write(render_pdf(all_rendered))
        print(f"PDF: {pdf}")
    return rc
