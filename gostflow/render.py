"""Вывод примитивов в SVG, PNG и PDF."""
from __future__ import annotations
import io
import math
import os
from typing import List
from xml.sax.saxutils import escape
from .layout import Rendered, FS

STROKE = 1.5
FONT_FAMILY = "'DejaVu Sans', 'Segoe UI', Arial, 'Liberation Sans', sans-serif"


def arrow_poly(p0, p1, size=9.0, half=4.2):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    d = math.hypot(dx, dy) or 1.0
    ux, uy = dx / d, dy / d
    bx, by = p1[0] - ux * size, p1[1] - uy * size
    return [(p1[0], p1[1]), (bx - uy * half, by + ux * half), (bx + uy * half, by - ux * half)]


def _pts(pts):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def render_svg(r: Rendered, with_header: bool = True, interactive: bool = False) -> str:
    """interactive=True добавляет группы <g class="nd" data-n data-l data-e> для подсветки код <-> схема."""
    out: List[str] = []
    lines_map = getattr(r, "lines", {})
    if with_header:
        out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{r.width}" height="{r.height}" '
               f'viewBox="0 0 {r.width} {r.height}" font-family="{FONT_FAMILY}" font-size="{FS}">')
    out.append('<rect width="100%" height="100%" fill="#ffffff"/>')
    out.append(f'<g fill="#ffffff" stroke="#000000" stroke-width="{STROKE}" stroke-linejoin="miter">')
    for p in r.prims:
        k = p[0]
        if k == "mark":
            if interactive:
                if p[1] == "b":
                    ln = lines_map.get(p[2])
                    attrs = f' data-l="{ln[0]}" data-e="{ln[1]}"' if ln else ""
                    if ln and len(ln) > 2 and ln[2] is not None:
                        attrs += f' data-f="{ln[2]}"'
                    out.append(f'<g class="nd" data-n="{p[2]}"{attrs}>')
                else:
                    out.append("</g>")
        elif k == "poly":
            out.append(f'<polygon points="{_pts(p[1])}"/>')
        elif k == "ellipse":
            out.append(f'<ellipse cx="{p[1]:.1f}" cy="{p[2]:.1f}" rx="{p[3]:.1f}" ry="{p[4]:.1f}"/>')
        elif k == "stadium":
            h = p[4] - p[2]
            out.append(f'<rect x="{p[1]:.1f}" y="{p[2]:.1f}" width="{p[3] - p[1]:.1f}" height="{h:.1f}" rx="{h / 2:.1f}"/>')
        elif k == "line":
            pts, arrow, dashed = p[1], p[2], p[3]
            dash = ' stroke-dasharray="6 4"' if dashed else ""
            out.append(f'<polyline points="{_pts(pts)}" fill="none"{dash}/>')
            if arrow and len(pts) >= 2:
                out.append(f'<polygon points="{_pts(arrow_poly(pts[-2], pts[-1]))}" fill="#000000" stroke="none"/>')
        elif k == "text":
            _, x, y, s, size, anchor, style = p
            extra, fill = "", "#000000"
            if style == "note":
                extra = ' font-style="italic"'; fill = "#555555"
            elif style == "caption":
                extra = ' font-weight="bold"'
            out.append(f'<text x="{x:.1f}" y="{y:.1f}" dy=".35em" text-anchor="{anchor}" font-size="{size}"{extra} '
                       f'fill="{fill}" stroke="none">{escape(s)}</text>')
    out.append("</g></svg>")
    return "\n".join(out)


# ------------------------------------------------------------------ PNG / PDF (Pillow)
_FONT_CANDIDATES = [
    "DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf",
    "/Library/Fonts/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "/usr/share/fonts/TTF/DejaVuSans.ttf",
]
_BOLD_CANDIDATES = [
    "DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf", "/Library/Fonts/Arial Bold.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def pil_available() -> bool:
    try:
        import PIL  # noqa
        return True
    except Exception:
        return False


def _font(cands, size):
    from PIL import ImageFont
    for c in cands:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()


def render_png(r: Rendered, scale: float = 2.0) -> bytes:
    from PIL import Image, ImageDraw
    ss = 3                                   # суперсэмплинг для сглаживания
    S = scale * ss
    img = Image.new("RGB", (int(r.width * S), int(r.height * S)), "white")
    d = ImageDraw.Draw(img)
    lw = max(1, int(round(STROKE * S)))
    fonts = {}

    def font(size, bold=False):
        key = (round(size * S), bold)
        if key not in fonts:
            fonts[key] = _font(_BOLD_CANDIDATES if bold else _FONT_CANDIDATES, key[0])
        return fonts[key]

    def sc(pts):
        return [(x * S, y * S) for x, y in pts]

    texts = []
    for p in r.prims:
        k = p[0]
        if k == "poly":
            pts = sc(p[1])
            d.polygon(pts, fill="white")
            d.line(pts + [pts[0]], fill="black", width=lw, joint="curve")
        elif k == "ellipse":
            d.ellipse([(p[1] - p[3]) * S, (p[2] - p[4]) * S, (p[1] + p[3]) * S, (p[2] + p[4]) * S], fill="white", outline="black", width=lw)
        elif k == "stadium":
            d.rounded_rectangle([p[1] * S, p[2] * S, p[3] * S, p[4] * S], radius=(p[4] - p[2]) * S / 2, fill="white", outline="black", width=lw)
        elif k == "line":
            pts, arrow, dashed = sc(p[1]), p[2], p[3]
            if dashed:
                for a, b in zip(pts, pts[1:]):
                    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
                    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
                    t = 0.0
                    while t < L:
                        e = min(L, t + 6 * S)
                        d.line([(a[0] + ux * t, a[1] + uy * t), (a[0] + ux * e, a[1] + uy * e)], fill="black", width=lw)
                        t += 10 * S
            else:
                d.line(pts, fill="black", width=lw, joint="curve")
            if arrow and len(p[1]) >= 2:
                d.polygon(sc(arrow_poly(p[1][-2], p[1][-1])), fill="black")
        elif k == "text":
            texts.append(p)
    for _, x, y, s, size, anchor, style in texts:
        a = {"middle": "mm", "start": "lm", "end": "rm"}[anchor]
        color = (85, 85, 85) if style == "note" else "black"
        d.text((x * S, y * S), s, fill=color, font=font(size, style == "caption"), anchor=a)
    img = img.resize((int(r.width * scale), int(r.height * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "PNG", dpi=(96 * scale, 96 * scale))
    return buf.getvalue()


def render_pdf(rs: List[Rendered]) -> bytes:
    """PDF: по одной странице на схему (растровый, 150 dpi)."""
    from PIL import Image
    pages = []
    for r in rs:
        pages.append(Image.open(io.BytesIO(render_png(r, scale=150 / 96 * 1.0))).convert("RGB"))
    buf = io.BytesIO()
    pages[0].save(buf, "PDF", save_all=True, append_images=pages[1:], resolution=150.0)
    return buf.getvalue()
