"""Ядро редактора схем (чистый JS без DOM): размеры блоков, маршрутизация связей, генерация SVG."""

JS_CORE = r"""
(function (root) {
'use strict';
var CW = 7.7, LH = 17, W = 232, DHW0 = 124, FS = 13, GAPA = 18;
var FONT = "'DejaVu Sans','Segoe UI',Arial,'Liberation Sans',sans-serif";

function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); }

function wrapText(s, maxc, maxl) {
  maxc = Math.max(4, maxc); var out = [];
  String(s).split('\n').forEach(function (par) {
    par = par.replace(/\s+$/, '');
    if (par === '') { out.push(''); return; }
    var words = par.split(/\s+/).filter(Boolean), cur = '';
    words.forEach(function (w) {
      while (w.length > maxc) { if (cur) { out.push(cur); cur = ''; } out.push(w.slice(0, maxc)); w = w.slice(maxc); }
      if (!cur) cur = w; else if ((cur + ' ' + w).length <= maxc) cur += ' ' + w; else { out.push(cur); cur = w; }
    });
    if (cur) out.push(cur);
  });
  if (!out.length) out.push('');
  if (maxl && out.length > maxl) { out.length = maxl; out[maxl - 1] = out[maxl - 1].slice(0, Math.max(1, maxc - 1)) + '\u2026'; }
  return out;
}

function decisionInfo(text) {
  var words = String(text).split(/\s+/).filter(Boolean);
  var longest = words.reduce(function (m, w) { return Math.max(m, w.length); }, 1);
  var dhw = DHW0;
  if (longest * CW + 8 > 0.62 * 2 * dhw) dhw = Math.min(260, Math.ceil((longest * CW + 8) / 0.62 / 2));
  var best = null;
  for (var maxc = Math.max(10, Math.min(longest, 40)); maxc < 50; maxc++) {
    var lines = wrapText(text, maxc, 8);
    var tw = Math.max.apply(null, lines.map(function (l) { return l.length; })) * CW + 8;
    var th = lines.length * LH + 6;
    if (tw / (2 * dhw) >= 0.80) continue;
    var H = th / (1 - tw / (2 * dhw));
    if (best === null || H < best[0] - 1) best = [H, lines];
  }
  if (!best) { var l2 = wrapText(text, Math.max(10, longest), 8); best = [l2.length * LH * 3.2, l2]; }
  return {dhw: dhw, H: Math.max(72, Math.ceil(best[0])), lines: best[1]};
}

function maxLen(lines) { return Math.max.apply(null, lines.map(function (l) { return l.length; })); }

/* Переразбить текст блока на строки; resize=true – ещё и пересчитать размеры (центр по x сохраняется). */
function layoutText(n, resize) {
  var cx = n.x + n.w / 2, lines, w = n.w, h = n.h, t = String(n.text);
  switch (n.k) {
    case 'process': case 'predef':
      lines = wrapText(t, Math.floor((W - 22) / CW), 14); w = W; h = Math.max(44, lines.length * LH + 18); break;
    case 'io':
      lines = wrapText(t, Math.floor((W - 46) / CW), 12); w = W; h = Math.max(44, lines.length * LH + 18); break;
    case 'looptop': case 'loopbot':
      lines = wrapText(t, Math.floor((W - 34) / CW), 8); w = W; h = Math.max(40, lines.length * LH + 16); break;
    case 'term':
      lines = wrapText(t, Math.floor((W - 30) / CW), 6); w = Math.min(W, Math.max(150, maxLen(lines) * CW + 44)); h = Math.max(38, lines.length * LH + 14); break;
    case 'decision': var d = decisionInfo(t); lines = d.lines; w = 2 * d.dhw; h = d.H; break;
    case 'conn': lines = [t]; w = 34; h = 34; break;
    case 'comment': lines = wrapText(t, 40, 14); w = maxLen(lines) * CW + 18; h = lines.length * LH + 10; break;
    default: lines = wrapText(t, 27, 14);
  }
  n.lines = lines;
  if (resize) { n.w = w; n.h = h; if (n.k !== 'comment') n.x = cx - w / 2; }
}

function port(n, p) {
  switch (p) {
    case 'l': return [n.x, n.y + n.h / 2];
    case 'r': return [n.x + n.w, n.y + n.h / 2];
    case 't': return [n.x + n.w / 2, n.y];
    default: return [n.x + n.w / 2, n.y + n.h];
  }
}

function avoid(nodes, xo, y0, y1, skip, dir) {
  for (var it = 0; it < 8; it++) {
    var hit = null;
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      if (skip.indexOf(n) >= 0 || n.k === 'comment') continue;
      if (n.y + n.h < y0 - 2 || n.y > y1 + 2) continue;
      if (xo > n.x - 8 && xo < n.x + n.w + 8) { hit = n; break; }
    }
    if (!hit) return xo;
    xo = dir > 0 ? hit.x + hit.w + 22 : hit.x - 22;
  }
  return xo;
}

function route(m, e, byId) {
  var f = byId[e.f], t = byId[e.t];
  if (!f || !t) return null;
  var P = port(f, e.p), T = [t.x + t.w / 2, t.y];
  if (e.d) {
    var Q = [t.x, t.y + t.h / 2];
    if (Math.abs(P[1] - Q[1]) < 1) return [P, Q];
    return [P, [P[0] + 20, P[1]], [P[0] + 20, Q[1]], Q];
  }
  var pts;
  if (e.p === 'b') {
    if (Math.abs(P[0] - T[0]) < 1 && T[1] > P[1]) pts = [P, T];
    else if (T[1] > P[1] + GAPA + 12) { var ym = T[1] - GAPA; pts = [P, [P[0], ym], [T[0], ym], T]; }
    else {
      var xs = Math.max(f.x + f.w, t.x + t.w, P[0]) + 36, yb = P[1] + 16;
      pts = [P, [P[0], yb], [xs, yb], [xs, T[1] - GAPA], [T[0], T[1] - GAPA], T];
    }
  } else {
    var dir = e.p === 'r' ? 1 : -1;
    if ((T[0] - P[0]) * dir > 8 && T[1] > P[1] + 4) {
      var xo2 = avoid(m.nodes, T[0], P[1], T[1] - 1, [f, t], 0);
      pts = [P, [T[0], P[1]], T];
    } else {
      var xo = avoid(m.nodes, P[0] + dir * 28, P[1], T[1], [f, t], dir);
      if (T[1] > P[1] + GAPA + 12) { var ym2 = T[1] - GAPA; pts = [P, [xo, P[1]], [xo, ym2], [T[0], ym2], T]; }
      else {
        var xs2 = dir > 0 ? Math.max(f.x + f.w, t.x + t.w, xo) + 36 : Math.min(f.x, t.x, xo) - 36;
        pts = [P, [xs2, P[1]], [xs2, T[1] - GAPA], [T[0], T[1] - GAPA], T];
      }
    }
  }
  return pts;
}

function arrow(a, b) {
  var dx = b[0] - a[0], dy = b[1] - a[1], d = Math.hypot(dx, dy) || 1, ux = dx / d, uy = dy / d, s = 9, h = 4.2;
  var bx = b[0] - ux * s, by = b[1] - uy * s;
  return [[b[0], b[1]], [bx - uy * h, by + ux * h], [bx + uy * h, by - ux * h]];
}

function fmt(v) { return Math.round(v * 10) / 10; }
function pstr(pts) { return pts.map(function (p) { return fmt(p[0]) + ',' + fmt(p[1]); }).join(' '); }

function textSvg(lines, cx, cy, anchor, size, extra) {
  var out = '', n = lines.length, y0 = cy - (n - 1) * LH / 2;
  for (var i = 0; i < n; i++)
    out += '<text x="' + fmt(cx) + '" y="' + fmt(y0 + i * LH) + '" dy=".35em" text-anchor="' + anchor + '" font-size="' + (size || FS) +
           '" fill="#000" stroke="none"' + (extra || '') + '>' + esc(lines[i]) + '</text>';
  return out;
}

function nodeSvg(n, cls, plain) {
  var x = n.x, y = n.y, w = n.w, h = n.h, cx = x + w / 2, cy = y + h / 2, s = '';
  switch (n.k) {
    case 'process': s = '<rect x="' + fmt(x) + '" y="' + fmt(y) + '" width="' + fmt(w) + '" height="' + fmt(h) + '"/>'; break;
    case 'predef':
      s = '<rect x="' + fmt(x) + '" y="' + fmt(y) + '" width="' + fmt(w) + '" height="' + fmt(h) + '"/>' +
          '<polyline points="' + pstr([[x + 13, y], [x + 13, y + h]]) + '" fill="none"/><polyline points="' + pstr([[x + w - 13, y], [x + w - 13, y + h]]) + '" fill="none"/>'; break;
    case 'io': s = '<polygon points="' + pstr([[x + 20, y], [x + w, y], [x + w - 20, y + h], [x, y + h]]) + '"/>'; break;
    case 'decision': s = '<polygon points="' + pstr([[cx, y], [x + w, cy], [cx, y + h], [x, cy]]) + '"/>'; break;
    case 'term': s = '<rect x="' + fmt(x) + '" y="' + fmt(y) + '" width="' + fmt(w) + '" height="' + fmt(h) + '" rx="' + fmt(h / 2) + '"/>'; break;
    case 'looptop': s = '<polygon points="' + pstr([[x + 15, y], [x + w - 15, y], [x + w, y + 15], [x + w, y + h], [x, y + h], [x, y + 15]]) + '"/>'; break;
    case 'loopbot': s = '<polygon points="' + pstr([[x, y], [x + w, y], [x + w, y + h - 15], [x + w - 15, y + h], [x + 15, y + h], [x, y + h - 15]]) + '"/>'; break;
    case 'conn': s = '<ellipse cx="' + fmt(cx) + '" cy="' + fmt(cy) + '" rx="' + fmt(w / 2) + '" ry="' + fmt(h / 2) + '"/>'; break;
    case 'comment': s = '<polyline points="' + pstr([[x + 10, y], [x, y], [x, y + h], [x + 10, y + h]]) + '" fill="none"/>'; break;
    default: s = '<rect x="' + fmt(x) + '" y="' + fmt(y) + '" width="' + fmt(w) + '" height="' + fmt(h) + '"/>';
  }
  var lines = n.lines || [String(n.text)];
  if (n.k === 'comment') s += textSvg(lines, x + 18, cy, 'start');
  else if (n.k === 'conn') {
    s += textSvg(lines, cx, cy, 'middle', 12);
    if (n.note) s += '<text x="' + fmt(x + w + 8) + '" y="' + fmt(cy) + '" dy=".35em" font-size="11" font-style="italic" fill="#555" stroke="none">' + esc(n.note) + '</text>';
  } else if (n.align === 'left') s += textSvg(lines, x + 10, cy, 'start');
  else s += textSvg(lines, cx, cy, 'middle');
  var at = ' class="nd' + (cls ? ' ' + cls : '') + '" data-n="' + n.id + '"';
  if (n.l) at += ' data-l="' + n.l + '" data-e="' + (n.e || n.l) + '"';
  if (n.f !== undefined) at += ' data-f="' + n.f + '"';
  return '<g' + at + '>' + s + '</g>';
}

/* Полный SVG схемы по модели. opts.sel – id выделенного блока. Возвращает {svg, w, h}. */
function buildSvg(m, opts) {
  opts = opts || {};
  var byId = {}, i;
  m.nodes.forEach(function (n) { byId[n.id] = n; });
  var maxX = 0, maxY = 0;
  m.nodes.forEach(function (n) { maxX = Math.max(maxX, n.x + n.w + (n.k === 'conn' && n.note ? 8 + n.note.length * 6.5 : 0)); maxY = Math.max(maxY, n.y + n.h); });
  var routes = [], cnt = {};
  m.edges.forEach(function (e) { var k = e.f + ':' + e.p; cnt[k] = (cnt[k] || 0) + 1; });
  m.edges.forEach(function (e) {
    var pts = route(m, e, byId);
    routes.push(pts);
    if (pts) pts.forEach(function (p) { maxX = Math.max(maxX, p[0]); maxY = Math.max(maxY, p[1]); });
  });
  var capW = (m.caption.length * CW * 1.05) + 56;
  var W_ = Math.ceil(Math.max(maxX + 28, capW)), H_ = Math.ceil(maxY + 66);
  var out = ['<svg xmlns="http://www.w3.org/2000/svg" width="' + W_ + '" height="' + H_ + '" viewBox="0 0 ' + W_ + ' ' + H_ +
    '" font-family="' + FONT + '" font-size="' + FS + '"><rect width="100%" height="100%" fill="#fff"/>',
    '<g fill="#fff" stroke="#000" stroke-width="1.5" stroke-linejoin="miter">'];
  m.edges.forEach(function (e, idx) {
    var pts = routes[idx]; if (!pts) return;
    out.push('<polyline points="' + pstr(pts) + '" fill="none"' + (e.d ? ' stroke-dasharray="6 4"' : '') + '/>');
    if (!e.d) out.push('<polygon points="' + pstr(arrow(pts[pts.length - 2], pts[pts.length - 1])) + '" fill="#000" stroke="none"/>');
    if (e.lb) {
      var P = pts[0], T = pts[pts.length - 1], multi = cnt[e.f + ':' + e.p] > 1, lx, ly, an;
      if (multi && e.p === 'b') { lx = T[0] + 8; ly = T[1] - 9; an = 'start'; }
      else if (e.p === 'l') { lx = P[0] - 4; ly = P[1] - 8; an = 'end'; }
      else if (e.p === 'r') { lx = P[0] + 4; ly = P[1] - 8; an = 'start'; }
      else { lx = P[0] + 6; ly = P[1] + 14; an = 'start'; }
      out.push('<text x="' + fmt(lx) + '" y="' + fmt(ly) + '" dy=".35em" text-anchor="' + an + '" font-size="12" fill="#000" stroke="none">' + esc(e.lb) + '</text>');
    }
  });
  m.nodes.forEach(function (n) { out.push(nodeSvg(n, n.id === opts.sel ? 'sel' : '', opts.plain)); });
  out.push('<text x="' + fmt(W_ / 2) + '" y="' + fmt(maxY + 44) + '" dy=".35em" text-anchor="middle" font-size="14" font-weight="bold" fill="#000" stroke="none">' + esc(m.caption) + '</text>');
  out.push('</g></svg>');
  return {svg: out.join(''), w: W_, h: H_};
}

var API = {wrapText: wrapText, decisionInfo: decisionInfo, layoutText: layoutText, port: port, route: route, buildSvg: buildSvg, nodeSvg: nodeSvg};
if (typeof module !== 'undefined' && module.exports) module.exports = API; else root.GF = API;
})(typeof window !== 'undefined' ? window : this);
"""
