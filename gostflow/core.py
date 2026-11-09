"""Определение языка, разбор исходников (один файл или проект) и построение схем."""
from __future__ import annotations
import os
import re
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from .ir import Options, Chart, finalize, short_name, expand_charts, apply_detail
from .layout import build_chart, Rendered

EXT = {
    "py": "python", "pyw": "python",
    "c": "c", "h": "c",
    "cpp": "cpp", "cc": "cpp", "cxx": "cpp", "hpp": "cpp", "hh": "cpp", "hxx": "cpp", "ino": "cpp",
    "java": "java", "cs": "csharp",
    "js": "javascript", "mjs": "javascript", "cjs": "javascript", "jsx": "javascript",
    "ts": "typescript", "tsx": "typescript",
    "go": "go", "rs": "rust", "php": "php", "kt": "kotlin", "kts": "kotlin", "swift": "swift", "dart": "dart",
    "scala": "scala", "pas": "pascal", "pp": "pascal", "dpr": "pascal", "lpr": "pascal", "inc": "pascal",
    "asm": "asm", "s": "asm", "nasm": "asm", "masm": "asm", "a51": "asm", "z80": "asm", "mac": "asm",
}
LANGS = {
    "python": "Python", "c": "C", "cpp": "C++", "java": "Java", "csharp": "C#", "javascript": "JavaScript",
    "typescript": "TypeScript", "go": "Go", "rust": "Rust", "php": "PHP", "kotlin": "Kotlin", "swift": "Swift",
    "dart": "Dart", "scala": "Scala", "pascal": "Pascal / Delphi", "asm": "Ассемблер (x86, ARM, MIPS, AVR, ...)",
}


def detect_language(filename: str, text: str) -> str:
    ext = os.path.splitext(filename or "")[1].lstrip(".")
    if ext in EXT:
        return EXT[ext]
    if ext == "S":
        return "asm"
    t = text
    if re.search(r"^\s*(def |import |from \w+ import|class \w+.*:)", t, re.M) and "{" not in t[:400]:
        return "python"
    if re.search(r"\bbegin\b", t, re.I) and re.search(r"\b(end\.|writeln|procedure|program)\b", t, re.I):
        return "pascal"
    if re.search(r"^\s*(mov|push|pop|jmp|call|ret|add|sub|cmp|ldr|str|bl|lw|sw|addi)\b", t, re.M | re.I) and ";" not in t.split("\n", 1)[0] + "":
        return "asm"
    if re.search(r"^\s*(section|segment|global|\.text|\.data)\b|^\w+:\s*$", t, re.M):
        return "asm"
    if "<?php" in t:
        return "php"
    if re.search(r"\bfunc\s+\w+\(|package\s+main", t):
        return "go"
    if re.search(r"\bfn\s+\w+\(", t):
        return "rust"
    if re.search(r"#include\s*<", t):
        return "cpp" if re.search(r"\bstd::|cout|class\s", t) else "c"
    if re.search(r"public\s+static\s+void\s+main|System\.out", t):
        return "java"
    if re.search(r"\bfunction\b|console\.log|=>", t):
        return "javascript"
    return "c"


def _norm(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")


def parse_raw(text: str, lang: str, o: Options) -> Tuple[List[Chart], List[str]]:
    text = _norm(text)
    if lang == "python":
        from .lang_python import parse_python
        return parse_python(text, o)
    if lang == "asm":
        from .lang_asm import parse_asm
        return parse_asm(text, o)
    if lang == "pascal":
        from .lang_pascal import parse_pascal
        return parse_pascal(text, o)
    from .lang_clike import parse_clike
    return parse_clike(text, lang, o)


def parse_source(text: str, lang: str, o: Options) -> Tuple[List[Chart], List[str]]:
    charts, warns = parse_raw(text, lang, o)
    return finalize(charts, o), warns


@dataclass
class FileResult:
    name: str
    lang: str = ""
    text: str = ""
    charts: List[Rendered] = field(default_factory=list)
    warns: List[str] = field(default_factory=list)
    error: Optional[str] = None


def build_project(files: List[dict], o: Options, lang: str = "auto") -> List[FileResult]:
    """files: [{name, code, lang?}]. Функции разных файлов видят друг друга (предопределённый процесс, развёртывание вызовов)."""
    results: List[FileResult] = []
    parsed: List[Optional[List[Chart]]] = []
    for f in files:
        name, code = f.get("name") or "программа", _norm(f.get("code", ""))
        fl = f.get("lang") or lang or "auto"
        if fl in ("", "auto") and lang not in ("", "auto"):
            fl = lang
        if fl in ("", "auto"):
            fl = detect_language(name, code)
        fr = FileResult(name=name, lang=fl, text=code)
        results.append(fr)
        try:
            charts, warns = parse_raw(code, fl, o)
            fr.warns = list(warns)
            parsed.append(charts)
        except SyntaxError as e:
            fr.error = f"Синтаксическая ошибка: {e}"
            parsed.append(None)
        except Exception as e:  # noqa
            fr.error = f"Не удалось разобрать файл: {type(e).__name__}: {e}"
            parsed.append(None)
    ok = [c for c in parsed if c is not None]
    names = {short_name(c.name) for cs in ok for c in cs if c.kind == "function"}
    for cs in ok:
        finalize(cs, o, extra_names=names)
    expand_charts(ok, o, [i for i, c in enumerate(parsed) if c is not None])
    for cs in ok:
        apply_detail(cs, o)
    for fr, cs in zip(results, parsed):
        if cs is None:
            continue
        for c in cs:
            try:
                r = build_chart(c, o)
            except Exception as e:  # noqa
                fr.warns.append(f"{c.name}: не удалось построить схему ({type(e).__name__}: {e})")
                continue
            fr.warns.extend(f"{c.name}: {w}" for w in getattr(r, "warns", []))
            fr.charts.append(r)
    return results


def make_charts(text: str, lang: str, o: Options) -> Tuple[List[Rendered], List[str]]:
    res = build_project([{"name": "", "code": text, "lang": lang}], o)[0]
    if res.error:
        if res.error.startswith("Синтаксическая"):
            raise SyntaxError(res.error)
        raise RuntimeError(res.error)
    return res.charts, res.warns
