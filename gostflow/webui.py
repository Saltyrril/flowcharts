"""Страница веб-интерфейса (HTML + CSS + JS)."""
from .webcore import JS_CORE

CSS = r"""
:root{--bg:#f5f6f8;--card:#fff;--ink:#1c2230;--mut:#667085;--line:#d9dde5;--acc:#2f5bea;--acc2:#e8edff;--hl:#fff3b0}
@media (prefers-color-scheme:dark){:root{--bg:#14171d;--card:#1d222b;--ink:#e8ebf2;--mut:#9aa3b5;--line:#313846;--acc:#6b8cff;--acc2:#252d45;--hl:#5b4b00}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,Segoe UI,Roboto,Arial,sans-serif}
header{padding:16px 28px;border-bottom:1px solid var(--line);background:var(--card)}
header h1{margin:0;font-size:20px}header p{margin:2px 0 0;color:var(--mut);font-size:13px}
main{display:grid;grid-template-columns:minmax(320px,400px) minmax(0,1fr);gap:20px;padding:20px 28px;align-items:start}
@media(max-width:1000px){main{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;min-width:0}
.drop{border:2px dashed var(--line);border-radius:10px;padding:16px;text-align:center;color:var(--mut);cursor:pointer;transition:.15s}
.drop.over,.drop:hover{border-color:var(--acc);background:var(--acc2);color:var(--ink)}
.drop b{color:var(--ink)}
textarea{width:100%;height:200px;margin-top:10px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);padding:10px;font:13px/1.45 ui-monospace,Consolas,monospace;resize:vertical}
label{display:block;font-size:13px;color:var(--mut);margin:12px 0 4px}
select,input[type=number]{width:100%;padding:8px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);font:inherit}
.chk{display:flex;gap:8px;align-items:flex-start;margin:8px 0;font-size:14px}.chk input{margin-top:4px}
.chk small{display:block;color:var(--mut)}
button{font:inherit;border:0;border-radius:8px;padding:9px 16px;cursor:pointer;background:var(--acc);color:#fff}
button.sec{background:var(--acc2);color:var(--ink);border:1px solid var(--line);padding:5px 11px;font-size:13px}
button.sec.on{background:var(--acc);color:#fff;border-color:var(--acc)}
button:disabled{opacity:.5;cursor:default}
.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
#status{color:var(--mut);font-size:13px}
.err{color:#c0392b;white-space:pre-wrap}
.warn{background:#fff7e0;color:#6b4b00;border:1px solid #f0d58a;border-radius:8px;padding:8px 12px;font-size:13px;margin-bottom:12px}
.tabs{display:flex;gap:4px;overflow-x:auto;border-bottom:1px solid var(--line);margin:-4px 0 12px;padding-bottom:0}
.tab{padding:7px 12px;border:1px solid var(--line);border-bottom:0;border-radius:8px 8px 0 0;background:var(--bg);cursor:pointer;white-space:nowrap;font-size:13px;display:flex;gap:8px;align-items:center}
.tab.act{background:var(--card);border-color:var(--acc);color:var(--acc);font-weight:600}
.tab .x{color:var(--mut);font-size:15px;line-height:1}.tab .x:hover{color:#c0392b}
.tab small{color:var(--mut);font-weight:400}
.work{display:grid;grid-template-columns:minmax(220px,32%) minmax(0,1fr);gap:14px;align-items:start}
@media(max-width:1250px){.work{grid-template-columns:1fr}.src{position:static!important;max-height:260px!important}}
.src{border:1px solid var(--line);border-radius:8px;background:var(--bg);font:12px/1.5 ui-monospace,Consolas,monospace;max-height:80vh;overflow:auto;position:sticky;top:10px}
.src .ln{display:flex;cursor:pointer;white-space:pre}.src .ln:hover{background:var(--acc2)}
.src .ln i{flex:none;width:42px;text-align:right;padding-right:8px;color:var(--mut);font-style:normal;user-select:none}
.src .ln span{padding-right:10px}
.src .ln.hl{background:var(--hl)}
.chart{margin-bottom:18px}
.chart h3{margin:0 0 8px;font-size:15px;display:flex;justify-content:space-between;gap:10px;align-items:center;flex-wrap:wrap}
.canvas{overflow:auto;border:1px solid var(--line);border-radius:8px;background:#fff;max-height:78vh;text-align:center}
.canvas svg{max-width:100%;height:auto;display:block;margin:0 auto}.canvas.full svg{max-width:none}
.canvas.edit{outline:2px solid var(--acc);touch-action:none;user-select:none}
.hint{font-size:12px;color:var(--mut);margin:4px 0 8px}
.nd{cursor:pointer}
.nd:hover polygon,.nd:hover rect,.nd:hover ellipse{stroke:#2f5bea;stroke-width:2.2}
.nd.hl polygon,.nd.hl rect,.nd.hl ellipse,.nd.sel polygon,.nd.sel rect,.nd.sel ellipse{fill:#fff3b0;stroke:#d97706;stroke-width:2.5}
.canvas.edit .nd{cursor:move}
.empty{color:var(--mut);text-align:center;padding:60px 10px}
details{margin-top:12px}summary{cursor:pointer;color:var(--mut);font-size:13px}
dialog{border:1px solid var(--line);border-radius:12px;background:var(--card);color:var(--ink);padding:16px;width:min(520px,92vw)}
dialog textarea{height:140px;margin:0 0 12px}
dialog::backdrop{background:rgba(0,0,0,.4)}
@media print{header,main>.card:first-child,.chart h3 button,.tabs,#status,.warn,.src,.hint,.bar{display:none!important}main{display:block;padding:0}.card{border:0;padding:0}.work{display:block}
.chart{page-break-after:always}.canvas{border:0;max-height:none;overflow:visible;outline:0!important}}
"""

HTML = r"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Блок-схемы по ГОСТ 19.701-90</title><style>/*CSS*/</style></head><body>
<header><h1>Блок-схемы по ГОСТ 19.701-90</h1><p>Загрузите файл, несколько файлов или целую папку с проектом — программа построит схемы всех функций.</p></header>
<main>
<section class="card" id="side">
  <div class="drop" id="drop"><b>Перетащите файлы или папку сюда</b><br>или нажмите, чтобы выбрать файлы
    <input id="file" type="file" multiple hidden></div>
  <div class="row" style="margin-top:8px"><button class="sec" id="pickDir">Выбрать папку проекта…</button><input id="dir" type="file" webkitdirectory multiple hidden>
    <span id="fileInfo" style="font-size:12px;color:var(--mut)"></span></div>
  <textarea id="code" spellcheck="false" placeholder="…или вставьте код сюда"></textarea>
  <label for="lang">Язык</label>
  <select id="lang"><option value="auto">Определить автоматически</option></select>
  <label for="detail">Уровень детализации</label>
  <select id="detail">
    <option value="full">Полная схема</option>
    <option value="calls">Структура + вызовы функций</option>
    <option value="structure">Только структура (циклы и условия)</option>
  </select>
  <div class="chk"><input type="checkbox" id="expand"><div>Развернуть вызовы функций внутрь схемы
    <small>тело вызываемой функции подставляется на место вызова (в том числе из других файлов проекта)</small></div></div>
  <div class="chk"><input type="checkbox" id="assign" checked><div>«:=» вместо «=» <small>x = 5 → x := 5, i++ → i := i + 1</small></div></div>
  <div class="chk"><input type="checkbox" id="comment" checked><div>Символ «Комментарий» <small>сигнатура и описание функции у блока «начало»</small></div></div>
  <details><summary>Дополнительно</summary>
    <label for="depth">Глубина разворачивания вызовов</label><input type="number" id="depth" min="1" max="5" value="2">
    <label for="merge">Объединять простые операторы (макс. в одном блоке)</label><input type="number" id="merge" min="1" max="20" value="1">
    <div class="chk"><input type="checkbox" id="decl"><div>Показывать объявления без инициализации</div></div>
    <label for="asmgroup">Ассемблер: макс. команд в одном блоке</label><input type="number" id="asmgroup" min="1" max="30" value="6">
    <div class="chk"><input type="checkbox" id="asmcom"><div>Ассемблер: добавлять комментарии из исходника</div></div>
  </details>
  <div class="row" style="margin-top:16px"><button id="go">Построить схемы</button><span id="status"></span></div>
</section>
<section id="out" class="card"><div class="empty">Здесь появятся блок-схемы</div></section>
</main>
<dialog id="dlg"><form method="dialog"><div style="margin-bottom:8px;font-weight:600">Текст блока</div>
<textarea id="dlgText"></textarea><div class="row"><button value="ok">Применить</button><button class="sec" value="cancel" formnovalidate>Отмена</button></div></form></dialog>
<script>/*CORE*/</script>
<script>/*UI*/</script>
</body></html>"""

JS_UI = r"""
(function () {
'use strict';
var $ = function (id) { return document.getElementById(id); };
var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); };
var S = {files: [], active: 0, results: null, caps: {langs: {}, pil: false, exts: []}, edits: {}, editing: null, busy: false};
var IGNORE = ['node_modules', '.git', '__pycache__', 'venv', '.venv', 'dist', 'build', 'target', '.idea', '.vs', 'obj', '.gradle'];

fetch('/api/info').then(function (r) { return r.json(); }).then(function (d) {
  S.caps = d;
  Object.keys(d.langs).forEach(function (k) { var o = document.createElement('option'); o.value = k; o.textContent = d.langs[k]; $('lang').appendChild(o); });
});
function ping() { fetch('/api/ping').catch(function () {}); }
setInterval(ping, 2000); ping();

function decode(buf) { try { return new TextDecoder('utf-8', {fatal: true}).decode(buf); } catch (e) { return new TextDecoder('windows-1251').decode(buf); } }
function status(t) { $('status').textContent = t || ''; }

/* ---------------------------------------------------------------- файлы */
function okPath(path, size) {
  var parts = path.split('/'), ext = (parts[parts.length - 1].split('.').pop() || '');
  if (parts.slice(0, -1).some(function (p) { return IGNORE.indexOf(p) >= 0; })) return false;
  if (S.caps.exts.indexOf(ext) < 0 && S.caps.exts.indexOf(ext.toLowerCase()) < 0) return false;
  return size < 2 * 1024 * 1024;
}
function addFiles(list) {
  var items = list.filter(function (x) { return okPath(x.path, x.file.size); }).slice(0, 400);
  var skipped = list.length - items.length;
  return Promise.all(items.map(function (x) { return x.file.arrayBuffer().then(function (b) { return {name: x.path, code: decode(b)}; }); }))
    .then(function (fs) {
      if (!fs.length) { status('Нет подходящих файлов с кодом'); return; }
      fs.sort(function (a, b) { return a.name.localeCompare(b.name); });
      if (fs.length > 1 || list.length > 1) S.files = [];
      fs.forEach(function (f) { var i = S.files.findIndex(function (g) { return g.name === f.name; }); if (i >= 0) S.files[i] = f; else S.files.push(f); });
      S.active = Math.max(0, S.files.findIndex(function (g) { return g.name === fs[0].name; }));
      $('fileInfo').textContent = S.files.length + ' файл(ов)' + (skipped > 0 ? ', пропущено ' + skipped : '');
      syncCode(); build(true);
    });
}
$('drop').onclick = function () { $('file').click(); };
$('pickDir').onclick = function () { $('dir').click(); };
function fromInput(inp) { return Array.prototype.map.call(inp.files, function (f) { return {file: f, path: f.webkitRelativePath || f.name}; }); }
$('file').onchange = function (e) { addFiles(fromInput(e.target)); e.target.value = ''; };
$('dir').onchange = function (e) { addFiles(fromInput(e.target)); e.target.value = ''; };
['dragover', 'dragenter'].forEach(function (t) { $('drop').addEventListener(t, function (e) { e.preventDefault(); $('drop').classList.add('over'); }); });
['dragleave', 'drop'].forEach(function (t) { $('drop').addEventListener(t, function (e) { e.preventDefault(); $('drop').classList.remove('over'); }); });
function readEntry(entry, path, out) {
  return new Promise(function (resolve) {
    if (entry.isFile) { entry.file(function (f) { out.push({file: f, path: path + f.name}); resolve(); }, resolve); }
    else if (entry.isDirectory) {
      var all = [], rd = entry.createReader();
      (function more() { rd.readEntries(function (es) {
        if (es.length) { all = all.concat(Array.prototype.slice.call(es)); more(); }
        else Promise.all(all.map(function (e2) { return readEntry(e2, path + entry.name + '/', out); })).then(resolve);
      }, resolve); })();
    } else resolve();
  });
}
$('drop').addEventListener('drop', function (e) {
  var items = e.dataTransfer.items, entries = [];
  if (items && items.length && items[0].webkitGetAsEntry) {
    for (var i = 0; i < items.length; i++) { var en = items[i].webkitGetAsEntry(); if (en) entries.push(en); }
    var out = [];
    Promise.all(entries.map(function (en) { return readEntry(en, '', out); })).then(function () { addFiles(out); });
  } else addFiles(Array.prototype.map.call(e.dataTransfer.files, function (f) { return {file: f, path: f.name}; }));
});
function syncCode() { var f = S.files[S.active]; $('code').value = f ? f.code : ''; }
$('code').addEventListener('input', function () {
  if (!S.files.length) S.files.push({name: '', code: ''});
  S.files[S.active].code = $('code').value; status('Код изменён — нажмите «Построить схемы»');
});

/* ---------------------------------------------------------------- построение */
function opts() {
  return {gost_assign: $('assign').checked, show_comment: $('comment').checked, keep_decl: $('decl').checked,
    merge: +$('merge').value || 1, asm_group: +$('asmgroup').value || 6, asm_comments: $('asmcom').checked,
    detail: $('detail').value, expand: $('expand').checked ? (+$('depth').value || 2) : 0};
}
function payload(extra) {
  if (!S.files.length && $('code').value.trim()) S.files = [{name: '', code: $('code').value}];
  return Object.assign({files: S.files, lang: $('lang').value, options: opts()}, extra || {});
}
function anyEdits() { return Object.keys(S.edits).some(function (k) { return S.edits[k].dirty; }); }
function build(auto) {
  if (!$('code').value.trim() && !S.files.length) { status('Нет кода'); return Promise.resolve(); }
  if (!auto && anyEdits() && !confirm('Ручные правки схем будут потеряны. Продолжить?')) return Promise.resolve();
  $('go').disabled = true; status('Строю…');
  return fetch('/api/render', {method: 'POST', body: JSON.stringify(payload())}).then(function (r) { return r.json(); }).then(function (d) {
    if (d.error) { $('out').innerHTML = '<div class="err">' + esc(d.error) + '</div>'; status(''); return; }
    S.results = d.files; S.edits = {}; S.editing = null;
    if (S.active >= S.results.length) S.active = 0;
    render(); status('Готово');
  }).catch(function (e) { $('out').innerHTML = '<div class="err">' + esc(String(e)) + '</div>'; status(''); })
    .then(function () { $('go').disabled = false; });
}
$('go').onclick = function () { build(false); };
$('expand').onchange = function () { if (S.results) build(true); };
$('detail').onchange = function () { if (S.results) build(true); };

/* ---------------------------------------------------------------- вывод */
function key(fi, ci) { return fi + ':' + ci; }
function edited(k) { return S.edits[k] && S.edits[k].dirty; }
function cardHtml(fi, ci) {
  var c = S.results[fi].charts[ci], k = key(fi, ci), ed = S.editing === k, has = edited(k);
  var svg = has || ed ? GF.buildSvg(S.edits[k].model, {sel: S.edits[k].model.sel}).svg : c.svg;
  var btns = '<button class="sec" data-act="svg" data-k="' + k + '">SVG</button>' +
    (S.caps.pil ? '<button class="sec" data-act="png" data-k="' + k + '">PNG</button>' : '') +
    '<button class="sec' + (ed ? ' on' : '') + '" data-act="edit" data-k="' + k + '">' + (ed ? 'Готово' : 'Править') + '</button>' +
    (ed || has ? '<button class="sec" data-act="undo" data-k="' + k + '">↶ Отменить</button><button class="sec" data-act="reset" data-k="' + k + '">Сбросить</button>' : '') +
    '<button class="sec" data-act="zoom" data-k="' + k + '">Масштаб</button>';
  return '<div class="chart" data-k="' + k + '"><h3><span>' + esc(c.name) + (has ? ' <small style="color:var(--mut)">(изменена вручную)</small>' : '') + '</span><span class="row">' + btns + '</span></h3>' +
    (ed ? '<div class="hint">Перетаскивайте блоки мышью — связи перестроятся. Двойной щелчок по блоку — изменить текст. Ctrl+Z — отменить.</div>' : '') +
    '<div class="canvas' + (ed ? ' edit' : '') + '" data-k="' + k + '">' + svg + '</div></div>';
}
function srcHtml(code) {
  var lines = code.split('\n');
  if (lines.length > 6000) lines = lines.slice(0, 6000);
  return lines.map(function (l, i) { return '<div class="ln" data-n="' + (i + 1) + '"><i>' + (i + 1) + '</i><span>' + (esc(l) || ' ') + '</span></div>'; }).join('');
}
function render() {
  var R = S.results; if (!R) return;
  var h = '';
  if (R.length > 1 || (R[0] && R[0].name)) {
    h += '<div class="tabs">' + R.map(function (f, i) {
      var n = f.charts.length, nm = f.name || 'Вставленный код';
      return '<div class="tab' + (i === S.active ? ' act' : '') + '" data-tab="' + i + '" title="' + esc(nm) + '">' + esc(nm.split('/').pop()) +
        ' <small>' + (f.error ? '⚠' : n) + '</small>' + (R.length > 1 ? '<span class="x" data-close="' + i + '">×</span>' : '') + '</div>';
    }).join('') + '</div>';
  }
  var f = R[S.active], total = R.reduce(function (s, x) { return s + x.charts.length; }, 0);
  h += '<div class="row bar" style="margin-bottom:12px"><span style="font-size:13px;color:var(--mut)">' +
    (R.length > 1 ? 'Проект: ' + R.length + ' файл(ов), схем: ' + total + '. ' : '') + 'Язык: <b>' + esc(f.langName || f.lang) + '</b>, схем в файле: ' + f.charts.length + '</span>' +
    (R.length > 1 ? '<button class="sec" data-act="zip-svg">Весь проект: ZIP (SVG)</button>' + (S.caps.pil ? '<button class="sec" data-act="zip-png">ZIP (PNG)</button><button class="sec" data-act="pdf-all">PDF (все схемы)</button>' : '')
                  : (S.caps.pil && f.charts.length ? '<button class="sec" data-act="pdf-all">Все схемы в PDF</button>' : '')) +
    '<button class="sec" data-act="print">Печать</button></div>';
  if (f.error) h += '<div class="err">' + esc(f.error) + '</div>';
  if (f.warnings && f.warnings.length) h += '<div class="warn">' + f.warnings.map(esc).join('<br>') + '</div>';
  if (!f.error && !f.charts.length) h += '<div class="empty">В этом файле нет функций или исполняемых операторов</div>';
  else if (!f.error) {
    var code = (S.files[S.active] && S.files[S.active].code) || '';
    h += '<div class="work"><div class="src" id="src">' + srcHtml(code) + '</div><div id="charts">' +
      f.charts.map(function (c, ci) { return cardHtml(S.active, ci); }).join('') + '</div></div>';
  }
  $('out').innerHTML = h;
}
function switchTab(i, then) { S.active = i; S.editing = null; syncCode(); render(); if (then) then(); }
function redrawCard(k) {
  var p = k.split(':'), el = document.querySelector('.chart[data-k="' + k + '"]');
  if (!el) return; var t = document.createElement('div'); t.innerHTML = cardHtml(+p[0], +p[1]); el.replaceWith(t.firstChild);
}
function redrawCanvas(k) {
  var cv = document.querySelector('.canvas[data-k="' + k + '"]'), m = S.edits[k].model;
  if (cv) cv.innerHTML = GF.buildSvg(m, {sel: m.sel}).svg;
}

/* ---------------------------------------------------------------- подсветка код <-> схема */
function clearHl() {
  Array.prototype.forEach.call(document.querySelectorAll('.hl'), function (e) { e.classList.remove('hl'); });
}
function hlLines(a, b) {
  var first = null;
  for (var n = a; n <= b; n++) { var el = document.querySelector('.ln[data-n="' + n + '"]'); if (el) { el.classList.add('hl'); first = first || el; } }
  var src = $('src');
  if (first && src) src.scrollTop = Math.max(0, first.offsetTop - src.clientHeight / 2);
}
function selectNode(g, noSwitch) {
  var l = +g.dataset.l, e = +(g.dataset.e || g.dataset.l);
  var fi = g.dataset.f !== undefined ? +g.dataset.f : S.active;
  var other = fi !== S.active && S.results[fi];
  var apply = function () {
    clearHl();
    if (!other && g.isConnected && !g.closest('.canvas.edit')) g.classList.add('hl');
    if (l) hlLines(l, e || l);
  };
  if (other && noSwitch) { clearHl(); status('Блок из другого файла: ' + (S.results[fi].name || fi)); return; }
  if (other) switchTab(fi, apply); else apply();
  if (!l) status('Этому блоку не соответствует строка кода'); else if (!other) status('');
}
function selectLine(n) {
  clearHl();
  var hits = Array.prototype.filter.call(document.querySelectorAll('#charts .nd[data-l]'), function (g) {
    if (g.dataset.f !== undefined && +g.dataset.f !== S.active) return false;
    return +g.dataset.l <= n && n <= +(g.dataset.e || g.dataset.l);
  });
  var ln = document.querySelector('.ln[data-n="' + n + '"]'); if (ln) ln.classList.add('hl');
  if (!hits.length) { status('Для этой строки нет блока'); return; }
  status('');
  hits.forEach(function (g) { g.classList.add('hl'); });
  hits[0].scrollIntoView({block: 'center', behavior: 'smooth'});
}

/* ---------------------------------------------------------------- экспорт */
function download(blob, name) { var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); }, 5000); }
function safe(n) { return String(n).replace(/[^\w.\-\u0400-\u04FF]+/g, '_'); }
function baseName() { var f = S.results && S.results[S.active]; return safe(((f && f.name) || 'program').split('/').pop().replace(/\.[^.]+$/, '')); }
function svgToPng(svg, w, h, cb) {
  var img = new Image();
  img.onload = function () { var c = document.createElement('canvas'), s = 2; c.width = w * s; c.height = h * s; var x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0, 0, c.width, c.height); x.scale(s, s); x.drawImage(img, 0, 0, w, h); c.toBlob(cb, 'image/png'); };
  img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
}
function serverExport(extra, name) {
  status('Готовлю файл…');
  return fetch('/api/export', {method: 'POST', body: JSON.stringify(payload(extra))}).then(function (r) { if (!r.ok) throw new Error('export'); return r.blob(); })
    .then(function (b) { download(b, name); status(''); }).catch(function () { status('Ошибка экспорта'); });
}
function exportChart(k, fmt) {
  var p = k.split(':').map(Number), c = S.results[p[0]].charts[p[1]], nm = baseName() + '_' + safe(c.name);
  if (edited(k)) {
    var o = GF.buildSvg(S.edits[k].model, {});
    if (fmt === 'svg') download(new Blob(['<?xml version="1.0" encoding="UTF-8"?>\n' + o.svg], {type: 'image/svg+xml'}), nm + '.svg');
    else svgToPng(o.svg, o.w, o.h, function (b) { download(b, nm + '.png'); });
    return;
  }
  serverExport({format: fmt, file: p[0], chart: p[1]}, nm + '.' + fmt);
}

/* ---------------------------------------------------------------- редактор */
function snapshot(ed) { return JSON.stringify(ed.model.nodes.map(function (n) { return [n.id, n.x, n.y, n.text]; })); }
function restore(ed, snap) {
  JSON.parse(snap).forEach(function (a) {
    var n = ed.model.nodes.find(function (x) { return x.id === a[0]; });
    if (n) { n.x = a[1]; n.y = a[2]; if (n.text !== a[3]) { n.text = a[3]; GF.layoutText(n, true); n.x = a[1]; } }
  });
}
function startEdit(k) {
  var p = k.split(':').map(Number);
  if (S.editing && S.editing !== k) { var old = S.editing; S.editing = null; redrawCard(old); }
  if (!S.edits[k]) {
    var m = JSON.parse(JSON.stringify(S.results[p[0]].charts[p[1]].model));
    m.nodes.forEach(function (n) { GF.layoutText(n, false); });
    S.edits[k] = {model: m, hist: [], dirty: false};
  }
  S.editing = k; redrawCard(k);
}
function stopEdit(k) { S.editing = null; if (S.edits[k]) S.edits[k].model.sel = null; redrawCard(k); }
var drag = null;
function toSvg(svg, e) { var pt = svg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY; return pt.matrixTransform(svg.getScreenCTM().inverse()); }
document.addEventListener('pointerdown', function (e) {
  if (!S.editing) return;
  var g = e.target.closest && e.target.closest('.nd'); if (!g) return;
  var cv = g.closest('.canvas'); if (!cv || cv.dataset.k !== S.editing) return;
  e.preventDefault();
  var ed = S.edits[S.editing], n = ed.model.nodes.find(function (x) { return x.id === g.dataset.n; }); if (!n) return;
  var pt = toSvg(g.ownerSVGElement, e);
  drag = {n: n, ox: pt.x - n.x, oy: pt.y - n.y, moved: false, snap: snapshot(ed), sx: e.clientX, sy: e.clientY, k: S.editing};
  ed.model.sel = n.id;
  Array.prototype.forEach.call(cv.querySelectorAll('.nd.sel'), function (x) { x.classList.remove('sel'); });
  g.classList.add('sel'); selectNode(g, true);
});
window.addEventListener('pointermove', function (e) {
  if (!drag) return;
  if (!drag.moved && Math.hypot(e.clientX - drag.sx, e.clientY - drag.sy) < 4) return;
  var ed = S.edits[drag.k];
  if (!drag.moved) { drag.moved = true; ed.hist.push(drag.snap); }
  var svg = document.querySelector('.canvas[data-k="' + drag.k + '"] svg'); if (!svg) return;
  var pt = toSvg(svg, e);
  drag.n.x = Math.max(8, Math.round((pt.x - drag.ox) / 5) * 5); drag.n.y = Math.max(8, Math.round((pt.y - drag.oy) / 5) * 5);
  var d0 = drag;
  if (!d0.raf) d0.raf = requestAnimationFrame(function () { d0.raf = 0; redrawCanvas(d0.k); });
});
window.addEventListener('pointerup', function () {
  if (!drag) return; var d = drag; drag = null;
  if (d.moved) { S.edits[d.k].dirty = true; S.justDragged = true; setTimeout(function () { S.justDragged = false; }, 0); redrawCanvas(d.k); }
});
document.addEventListener('dblclick', function (e) {
  if (!S.editing) return;
  var g = e.target.closest && e.target.closest('.nd'); if (!g) return;
  var cv = g.closest('.canvas'); if (!cv || cv.dataset.k !== S.editing) return;
  var ed = S.edits[S.editing], n = ed.model.nodes.find(function (x) { return x.id === g.dataset.n; }); if (!n) return;
  $('dlgText').value = n.text;
  var k = S.editing;
  $('dlg').onclose = function () {
    if ($('dlg').returnValue !== 'ok') return;
    var t = $('dlgText').value; if (t === n.text) return;
    ed.hist.push(snapshot(ed)); n.text = t; GF.layoutText(n, true); ed.dirty = true;
    redrawCard(k);
  };
  $('dlg').returnValue = ''; $('dlg').showModal();
});
document.addEventListener('keydown', function (e) {
  if (S.editing && (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z' && document.activeElement.tagName !== 'TEXTAREA') { e.preventDefault(); undo(S.editing); }
});
function undo(k) {
  var ed = S.edits[k]; if (!ed || !ed.hist.length) return;
  restore(ed, ed.hist.pop()); ed.dirty = ed.hist.length > 0; redrawCard(k);
}

/* ---------------------------------------------------------------- события страницы */
document.addEventListener('click', function (e) {
  var t = e.target;
  var close = t.closest && t.closest('[data-close]');
  if (close) {
    e.stopPropagation(); var i = +close.dataset.close;
    S.files.splice(i, 1); S.edits = {}; S.editing = null; S.active = Math.min(S.active, Math.max(0, S.files.length - 1));
    syncCode(); $('fileInfo').textContent = S.files.length + ' файл(ов)';
    if (S.files.length) build(true); else { S.results = null; $('out').innerHTML = '<div class="empty">Здесь появятся блок-схемы</div>'; }
    return;
  }
  var tab = t.closest && t.closest('[data-tab]');
  if (tab) { switchTab(+tab.dataset.tab); return; }
  var b = t.closest && t.closest('[data-act]');
  if (b) {
    var k = b.dataset.k, a = b.dataset.act;
    if (a === 'svg' || a === 'png') exportChart(k, a);
    else if (a === 'edit') { if (S.editing === k) stopEdit(k); else startEdit(k); }
    else if (a === 'undo') undo(k);
    else if (a === 'reset') { delete S.edits[k]; if (S.editing === k) S.editing = null; redrawCard(k); }
    else if (a === 'zoom') document.querySelector('.canvas[data-k="' + k + '"]').classList.toggle('full');
    else if (a === 'print') window.print();
    else if (a === 'zip-svg') serverExport({format: 'zip-svg', file: -1, chart: -1}, 'gostflow_project_svg.zip');
    else if (a === 'zip-png') serverExport({format: 'zip-png', file: -1, chart: -1}, 'gostflow_project_png.zip');
    else if (a === 'pdf-all') serverExport({format: 'pdf', file: S.results.length > 1 ? -1 : 0, chart: -1}, baseName() + '.pdf');
    return;
  }
  if (S.justDragged) return;
  var g = t.closest && t.closest('.nd'); if (g && g.closest('#charts')) { selectNode(g); return; }
  var ln = t.closest && t.closest('.ln'); if (ln) { selectLine(+ln.dataset.n); return; }
});
if (typeof window !== 'undefined' && window.__GF_TEST) window.__GF_TEST({S: S, render: render, build: build, cardHtml: cardHtml, startEdit: startEdit, undo: undo, redrawCard: redrawCard, selectLine: selectLine, selectNode: selectNode, exportChart: exportChart, opts: opts});
})();
"""

PAGE = HTML.replace("/*CSS*/", CSS).replace("/*CORE*/", JS_CORE).replace("/*UI*/", JS_UI)
