"""Локальный веб-интерфейс: файлы/папка проекта -> блок-схемы; редактор; экспорт SVG/PNG/PDF/ZIP."""
from __future__ import annotations
import io
import json
import re
import threading
import time
import webbrowser
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .core import build_project, LANGS, EXT
from .ir import Options
from .render import render_svg, render_png, render_pdf, pil_available
from .webui import PAGE

STATE = {"last_ping": 0.0}


def _options(d: dict) -> Options:
    o = Options()
    for k in ("gost_assign", "keep_decl", "asm_comments", "show_comment"):
        if k in d:
            setattr(o, k, bool(d[k]))
    o.merge = max(1, int(d.get("merge", 1) or 1))
    o.asm_group = max(1, int(d.get("asm_group", 6) or 6))
    o.detail = d.get("detail", "full") if d.get("detail") in ("full", "calls", "structure") else "full"
    o.expand = max(0, min(5, int(d.get("expand", 0) or 0)))
    return o


def _project(req: dict):
    return build_project(req.get("files") or [], _options(req.get("options", {})), req.get("lang", "auto") or "auto")


def _safe(s: str) -> str:
    return re.sub(r"[^\w.\-]+", "_", s, flags=re.U).strip("_") or "program"


def _render_payload(res) -> dict:
    files = []
    for fr in res:
        files.append({
            "name": fr.name, "lang": fr.lang, "langName": LANGS.get(fr.lang, fr.lang), "warnings": fr.warns, "error": fr.error,
            "charts": [{"name": r.name, "svg": render_svg(r, with_header=False, interactive=True), "model": r.model,
                        "width": r.width, "height": r.height} for r in fr.charts]})
    return {"files": files}


def _export(req: dict):
    res = _project(req)
    fmt = req.get("format", "svg")
    fi, ci = int(req.get("file", -1)), int(req.get("chart", -1))
    sel = [(fr, k, r) for i, fr in enumerate(res) if fi < 0 or i == fi for k, r in enumerate(fr.charts) if ci < 0 or k == ci]
    if not sel:
        raise ValueError("нет схем для экспорта")
    if fmt == "svg":
        return render_svg(sel[0][2]).encode("utf-8"), "image/svg+xml"
    if fmt == "png":
        return render_png(sel[0][2]), "image/png"
    if fmt == "pdf":
        return render_pdf([r for _, _, r in sel]), "application/pdf"
    if fmt in ("zip-svg", "zip-png"):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for fr, k, r in sel:
                parts = (fr.name or "program").split("/")
                parts[-1] = parts[-1].replace(".", "_")
                path = "/".join(_safe(p) for p in parts) + f"/{k + 1:02d}_{_safe(r.name)}"
                if fmt == "zip-svg":
                    z.writestr(path + ".svg", render_svg(r))
                else:
                    z.writestr(path + ".png", render_png(r))
        return buf.getvalue(), "application/zip"
    raise ValueError("неизвестный формат")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
        elif self.path == "/api/ping":
            STATE["last_ping"] = time.time()
            self._send(200, b"{}")
        elif self.path == "/api/info":
            self._send(200, json.dumps({"langs": LANGS, "pil": pil_available(), "exts": sorted(set(EXT) | {"S"})}).encode())
        else:
            self._send(404, b"{}")

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n).decode("utf-8"))
            if self.path == "/api/render":
                self._send(200, json.dumps(_render_payload(_project(req)), ensure_ascii=False).encode("utf-8"))
            elif self.path == "/api/export":
                body, ctype = _export(req)
                self._send(200, body, ctype)
            else:
                self._send(404, b"{}")
        except Exception as e:  # noqa
            import traceback
            traceback.print_exc()
            self._send(200 if self.path == "/api/render" else 400,
                       json.dumps({"error": f"Не удалось построить схему: {type(e).__name__}: {e}"}, ensure_ascii=False).encode("utf-8"))


def make_server(port=0):
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(port=8765, open_browser=True):
    srv = make_server(port)
    url = f"http://127.0.0.1:{port}/"
    print(f"Веб-интерфейс: {url}   (остановить: Ctrl+C)")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановлено.")
