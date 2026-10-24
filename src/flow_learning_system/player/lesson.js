/* ===== 교재 장면 빌더: 문장 하나 = 장면 하나 =====
   장면마다 핵심 문구(head), 코드와 강조 줄, 메모리 그림(변수·배열·자료구조), 콘솔 출력, 보조 그림(board)을 함께 기록합니다. */
var LESSONS = [];
const TYPE_KIND = { int: 'val', long: 'val', double: 'val', float: 'val', bool: 'val', char: 'val', decimal: 'val', byte: 'val', 'int[]': 'ref', 'string': 'ref', 'int[,]': 'ref', 'char[]': 'ref', 'string[]': 'ref' };
const kindOf = t => !t ? '' : TYPE_KIND[t] || (/[\[<]/.test(t) || /^[A-Z]/.test(t) ? 'ref' : 'val');

/* 숫자 뒤 조사: j(4,'이') → "4가" */
function j(n, p) {
  const s = String(n).replace(/,/g, '');
  const m = s.match(/(\d+)$/);
  let fin;
  if (!m) { const ch = s.charCodeAt(s.length - 1); fin = ch >= 0xAC00 && ch <= 0xD7A3 ? (ch - 0xAC00) % 28 : 0; }
  else {
    const d = m[1]; const nz = d.replace(/0+$/, ''), zeros = d.length - nz.length;
    if (d === '0') fin = 21;
    else if (zeros === 0) fin = [0, 8, 0, 16, 0, 0, 1, 8, 8, 0][+d[d.length - 1]];
    else if (zeros === 1) fin = 17; else if (zeros === 2) fin = 1; else fin = 4;
  }
  const has = fin !== 0, rieul = fin === 8;
  const P2 = { '이': ['이', '가'], '은': ['은', '는'], '을': ['을', '를'], '과': ['과', '와'], '으로': [rieul ? '로' : '으로', '로'] };
  return s + (has ? P2[p][0] : P2[p][1]);
}

/* 변수 상자: [이름, 값, 형, 상태] — 값이 {ref:'A'}면 화살표 */
V.vars = function (list, o) {
  const K = (o && o.key) || 'vv';
  return '<div class="vvars">' + list.map(([n, v, t, c]) => {
    const kd = kindOf(t);
    const val = v && typeof v === 'object' && v.ref ? `<span class="vref">→ ${esc(v.ref)}</span>` : fmt(v);
    return `<div class="vbox ${kd} ${c || ''}"${dk(K + ':' + n)}>${t ? `<span class="vt">${esc(t)}</span>` : ''}<span class="vn">${esc(n)}</span><b${dk(K + 'v:' + n)}>${val}</b></div>`;
  }).join('') + '</div>';
};
/* 콘솔 출력 */
V.con = function (lines, fresh) {
  return `<div class="vcon"><div class="vcon-t">콘솔 출력</div><div class="vcon-b">${lines.length ? lines.map((l, i) => `<div class="vcl${i >= lines.length - fresh ? ' new' : ''}"${dk('con:' + i)}>${esc(l)}</div>`).join('') : '<div class="vcl dim">(아직 출력 없음)</div>'}</div></div>`;
};
/* 비교 카드: [[제목, 내용html, 상태], …] */
V.cards = function (items, o) {
  const K = (o && o.key) || 'cd';
  return '<div class="vcards">' + items.map(([t, b, c], i) => `<div class="vcard ${c || ''}"${dk(K + ':' + i)}><div class="vcard-t">${fmt(t)}</div><div class="vcard-b">${typeof b === 'string' ? fmt(b) : b.h}</div></div>`).join('') + '</div>';
};
/* 가로 막대: [[이름, 값, 표시글, 상태], …], 최대값 기준 */
V.bars = function (items, o) {
  const K = (o && o.key) || 'br';
  const max = (o && o.max) || Math.max(...items.map(x => x[1]));
  return '<div class="vbars">' + items.map(([n, v, lab, c]) => `<div class="vbar-r"><span class="vbar-n">${fmt(n)}</span><div class="vbar-t"><div class="vbar-b ${c || ''}"${dk(K + ':' + n)} data-kz="1" style="width:${Math.max(1.5, v / max * 100)}%"></div></div><span class="vbar-v">${fmt(lab != null ? lab : v)}</span></div>`).join('') + '</div>';
};
/* 오류 띠 */
V.err = (t) => `<div class="verr"${dk('err')}>${fmt(t)}</div>`;

/* ---------- 과목 공통 위젯 ---------- */
var ASSETS = typeof ASSETS !== 'undefined' ? ASSETS : {};
const CLR = { hl: 'var(--hl-bd)', ok: 'var(--ok-bd)', bad: 'var(--bad-bd)', g1: 'var(--g1-bd)', g2: 'var(--g2-bd)', g3: 'var(--g3-bd)', dim: 'var(--muted)', ink: 'var(--ink)' };
const clr = c => CLR[c] || c || 'var(--g1-bd)';
/* 수식: 한 줄 또는 여러 줄(위에서 아래로 풀이). o.hl: 강조할 줄 번호 */
V.math = function (lines, o) {
  o = o || {}; const K = o.key || 'mt';
  const L = Array.isArray(lines) ? lines : [lines];
  return `<div class="vmath${o.big ? ' big' : ''}">` + L.map((x, i) => `<div class="vml${(o.hl || []).includes(i) ? ' hl' : ''}${(o.ok || []).includes(i) ? ' ok' : ''}${(o.dim || []).includes(i) ? ' dim' : ''}"${dk(K + ':' + i)}>${mathHtml(x)}</div>`).join('') + '</div>';
};
/* 좌표평면 그래프 */
V.plot = function (p) {
  p = Object.assign({ xmin: -5, xmax: 5, ymin: -5, ymax: 5, w: 440, h: 340, step: 1, tick: 1, curves: [], points: [], segs: [], labels: [], key: 'pl' }, p || {});
  const K = p.key, pad = 30, W = p.w, H = p.h;
  const sx = x => pad + (x - p.xmin) / (p.xmax - p.xmin) * (W - 2 * pad);
  const sy = y => H - pad - (y - p.ymin) / (p.ymax - p.ymin) * (H - 2 * pad);
  const f2 = v => (Math.round(v * 10) / 10).toFixed(1);
  let g = `<svg class="vplot" viewBox="0 0 ${W} ${H}" width="${W}" style="max-width:100%;height:auto"><defs><clipPath id="clip-${K}"><rect x="${pad}" y="${pad}" width="${W - 2 * pad}" height="${H - 2 * pad}"/></clipPath>` +
    `<marker id="ah-${K}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="context-stroke"/></marker></defs>`;
  for (let x = Math.ceil(p.xmin / p.step) * p.step; x <= p.xmax + 1e-9; x += p.step) g += `<line x1="${f2(sx(x))}" y1="${pad}" x2="${f2(sx(x))}" y2="${H - pad}" class="pg${Math.abs(x) < 1e-9 ? ' ax' : ''}"/>`;
  for (let y = Math.ceil(p.ymin / (p.ystep || p.step)) * (p.ystep || p.step); y <= p.ymax + 1e-9; y += (p.ystep || p.step)) g += `<line x1="${pad}" y1="${f2(sy(y))}" x2="${W - pad}" y2="${f2(sy(y))}" class="pg${Math.abs(y) < 1e-9 ? ' ax' : ''}"/>`;
  for (let x = Math.ceil(p.xmin / p.tick) * p.tick; x <= p.xmax + 1e-9; x += p.tick) if (Math.abs(x) > 1e-9) g += `<text x="${f2(sx(x))}" y="${f2(Math.min(H - pad + 14, Math.max(pad + 12, sy(0) + 14)))}" class="pt" text-anchor="middle">${+x.toFixed(2)}</text>`;
  for (let y = Math.ceil(p.ymin / (p.ytick || p.tick)) * (p.ytick || p.tick); y <= p.ymax + 1e-9; y += (p.ytick || p.tick)) if (Math.abs(y) > 1e-9) g += `<text x="${f2(Math.max(pad - 4, Math.min(W - pad - 4, sx(0) - 5)))}" y="${f2(sy(y) + 4)}" class="pt" text-anchor="end">${+y.toFixed(2)}</text>`;
  g += `<g clip-path="url(#clip-${K})">`;
  p.curves.forEach(c => {
    let fn; try { fn = new Function('x', `with (Math) { return (${c.fn}); }`); fn(0); } catch (e) { console.warn('plot: 그릴 수 없는 식', c.fn, e.message); return; }
    const N = 160;
    let d = '', last = 0;
    for (let i = 0; i <= N; i++) { const x = p.xmin + (p.xmax - p.xmin) * i / N; let y = fn(x); if (!isFinite(y)) y = last; last = y; y = Math.max(p.ymin - (p.ymax - p.ymin), Math.min(p.ymax + (p.ymax - p.ymin), y)); d += (i ? 'L' : 'M') + f2(sx(x)) + ' ' + f2(sy(y)); }
    g += `<path d="${d}" fill="none" stroke="${clr(c.c)}" stroke-width="${c.w || 3}"${c.dash ? ' stroke-dasharray="7 6"' : ''} stroke-linecap="round"${dk(K + 'c:' + (c.key || c.fn))}/>`;
  });
  g += '</g>';
  p.segs.forEach((s, i) => { g += `<line x1="${f2(sx(s.x1))}" y1="${f2(sy(s.y1))}" x2="${f2(sx(s.x2))}" y2="${f2(sy(s.y2))}" stroke="${clr(s.c)}" stroke-width="${s.w || 2.5}"${s.dash ? ' stroke-dasharray="6 5"' : ''}${s.arrow ? ` marker-end="url(#ah-${K})"` : ''}${dk(K + 's:' + (s.key || i))}/>`; });
  p.points.forEach((q, i) => {
    g += `<circle cx="${f2(sx(q.x))}" cy="${f2(sy(q.y))}" r="${q.r || 6}" fill="${clr(q.c || 'hl')}" stroke="#0B1218" stroke-width="2"${dk(K + 'p:' + (q.key || i))}/>`;
    if (q.label) g += `<text x="${f2(sx(q.x) + (q.dx != null ? q.dx : 10))}" y="${f2(sy(q.y) + (q.dy != null ? q.dy : -10))}" class="plab" fill="${clr(q.c || 'hl')}"${dk(K + 'pl:' + (q.key || i))}>${esc(q.label)}</text>`;
  });
  p.labels.forEach((q, i) => { g += `<text x="${f2(sx(q.x))}" y="${f2(sy(q.y))}" class="plab" fill="${clr(q.c || 'ink')}" text-anchor="${q.anchor || 'start'}"${dk(K + 'l:' + (q.key || i))}>${esc(q.text)}</text>`; });
  return `<div class="vplotw"${dk(K + ':box')}>${g}</svg></div>`;
};
/* 문장 성분 토큰: [[낱말, 역할, 색], …] — 같은 낱말은 자리를 옮겨 미끄러짐 */
V.tokens = function (items, o) {
  o = o || {}; const K = o.key || 'tk', seen = {};
  return `<div class="vtok${o.big ? ' big' : ''}">` + items.map(([w, role, c]) => {
    const n = (seen[w] = (seen[w] || 0) + 1);
    return `<div class="tok ${c || ''}"${dk(K + ':' + w + (n > 1 ? '#' + n : ''))}><span class="tw">${showText(w)}</span>${role ? `<span class="tr">${esc(role)}</span>` : ''}</div>`;
  }).join('') + '</div>';
};
/* 이미지(3D 렌더 등) + 핫스폿 이름표 + 화살표 + 확대 */
V.img = function (src, o) {
  o = o || {}; const K = o.key || src, meta = ASSETS[src] || {}, hs = meta.hotspots || {};
  const at = n => (o.at && o.at[n]) || hs[n];
  const asp = meta.w && meta.h ? meta.h / meta.w : 0.5625, VW = 1000, VH = Math.round(1000 * asp);
  const z = o.zoom || 1, f = (o.focus && at(o.focus)) || [0.5, 0.5];
  const tf = `scale(${z})`, org = `${(f[0] * 100).toFixed(1)}% ${(f[1] * 100).toFixed(1)}%`;
  let ov = `<svg class="vimg-ov" viewBox="0 0 ${VW} ${VH}"><defs><marker id="ia-${esc(K)}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="context-stroke"/></marker></defs>`;
  (o.arrows || []).forEach((a, i) => {
    const p1 = at(a.from), p2 = at(a.to); if (!p1 || !p2) return;
    ov += `<line x1="${(p1[0] * VW).toFixed(1)}" y1="${(p1[1] * VH).toFixed(1)}" x2="${(p2[0] * VW).toFixed(1)}" y2="${(p2[1] * VH).toFixed(1)}" stroke="${clr(a.c)}" stroke-width="${(a.w || 6) / z}" stroke-linecap="round" marker-end="url(#ia-${esc(K)})" data-grow="1"${dk('ia:' + K + ':' + (a.key || a.from + '>' + a.to))}/>`;
    if (a.label) ov += `<text x="${((p1[0] * .3 + p2[0] * .7) * VW + (a.dx || 14)).toFixed(1)}" y="${((p1[1] * .3 + p2[1] * .7) * VH + (a.dy || 0)).toFixed(1)}" class="ilab" fill="${clr(a.c)}" font-size="${34 / z}"${dk('ial:' + K + ':' + (a.key || a.from + '>' + a.to))}>${esc(a.label)}</text>`;
  });
  ov += '</svg>';
  const spots = Array.isArray(o.spots) ? Object.fromEntries(o.spots.map(n => [n, {}])) : (o.spots || {});
  let sp = '';
  Object.entries(spots).forEach(([n, s]) => {
    const p = at(n); if (!p) return;
    const side = s.side || (p[0] > .62 ? 'l' : 'r');
    sp += `<div class="spot ${s.c || (o.focus === n ? 'hl' : 'ok')} ${side}" style="left:${(p[0] * 100).toFixed(2)}%;top:${(p[1] * 100).toFixed(2)}%;--z:${z}"${dk('sp:' + K + ':' + n)}><i></i>${s.label !== '' ? `<span>${esc(s.label || n)}</span>` : ''}</div>`;
  });
  return `<div class="vimg${o.dimOthers ? ' dimo' : ''}" style="max-width:${o.w || 640}px"${dk('img:' + K)}><div class="vimg-in" style="transform:${tf};transform-origin:${org}" data-tf="${tf}|${org}"${dk('imgin:' + K)}><img src="${esc(src)}" alt="${esc(o.alt || '')}" draggable="false">${ov}${sp}</div>${o.cap ? `<div class="vcap">${fmt(o.cap)}</div>` : ''}</div>`;
};
/* 직접 그린 SVG */
V.svg = (raw, o) => `<div class="vsvg"${dk((o && o.key) || 'svg')}>${raw}</div>`;

function Lesson(meta) {
  Object.assign(this, { m: meta, codes: [], cur: -1, sc: [], vars: new Map(), objs: new Map(), outs: [], fresh: 0, trace: null, chg: new Set(), newRow: false, secName: null, secNew: false, brd: '' });
}
Lesson.prototype = {
  part(t) { this.secName = t; this.secNew = true; return this; },
  code(src, o) { o = o || {}; this.open = false; this.codes.push({ src: src.replace(/^\n/, '').replace(/\s+$/, ''), wrap: o.wrap || 'main', run: o.run !== false, out: [], test: o.test || '', expect: o.expect || null, lang: o.lang || null }); this.cur = this.codes.length - 1; return this; },
  nocode() { this.cur = -1; return this; },
  use(i) { this.cur = i; this.open = false; return this; },
  L(needle, nth) {
    const lines = this.codes[this.cur].src.split('\n'); nth = nth || 1; let c = 0;
    for (let i = 0; i < lines.length; i++) if (lines[i].includes(needle) && ++c === nth) return i + 1;
    throw new Error(`[${this.m.id}] 코드에서 찾지 못함: ${needle}`);
  },
  v(name, val, type) { const old = this.vars.get(name); this.vars.set(name, { val, type: type || (old && old.type) }); this.chg.add('v:' + name); return this; },
  ref(name, target, type) { return this.v(name, { ref: target }, type); },
  drop(...names) { names.forEach(n => this.vars.delete(n)); return this; },
  obj(name, kind, data, o) { this.objs.set(name, { kind, data, o: o || {} }); this.chg.add('o:' + name); return this; },
  arr(name, vals, o) { return this.obj(name, 'arr', vals.slice(), o); },
  stack(name, items, o) { return this.obj(name, 'stack', items.slice(), o); },
  queue(name, items, o) { return this.obj(name, 'queue', items.slice(), o); },
  dict(name, pairs, o) { return this.obj(name, 'dict', pairs.map(x => x.slice()), o); },
  hset(name, items, o) { return this.obj(name, 'set', items.slice(), o); },
  grid(name, mat, o) { return this.obj(name, 'grid', mat.map(r => r.slice()), o); },
  free(...names) { names.forEach(n => this.objs.delete(n)); return this; },
  out(t) { return this._o(String(t), false); },
  outw(t) { return this._o(String(t), true); },
  _o(t, stay) {
    const c = this.cur >= 0 ? this.codes[this.cur] : null;
    if (this.open && this.outs.length) { this.outs[this.outs.length - 1] += t; if (c && c.out.length) c.out[c.out.length - 1] += t; }
    else { this.outs.push(t); if (c) c.out.push(t); }
    this.open = stay; this.fresh = Math.max(this.fresh, 1); return this;
  },
  /* 실제로는 실행되지 않는 설명용 출력(검증에서 제외) */
  showOut(t) { this.outs.push(String(t)); this.fresh++; return this; },
  tbl(head, title) { this.trace = { head, rows: [], title: title || '실행 기록' }; return this; },
  row(cells) { this.trace.rows.push(cells.map(String)); this.newRow = true; return this; },
  board(html) { this.brd = html; return this; },
  clear() { this.vars.clear(); this.objs.clear(); this.outs = []; this.fresh = 0; this.open = false; this.trace = null; this.brd = ''; return this; },
  say(line, text, o) {
    o = o || {};
    let ls = [];
    if (line != null && this.cur >= 0) {
      if (Array.isArray(line) && line.length === 2 && typeof line[0] === 'string' && typeof line[1] === 'number') line = [line];
      ls = (Array.isArray(line) ? line : [line]).map(x => typeof x === 'number' ? x : Array.isArray(x) ? this.L(x[0], x[1]) : this.L(x));
    }
    this.sc.push({ sec: this.secNew ? this.secName : null, secName: this.secName, say: text, head: o.head != null ? o.head : (this.sc.length ? this.sc[this.sc.length - 1].headRaw : ''), headRaw: o.head != null ? o.head : (this.sc.length ? this.sc[this.sc.length - 1].headRaw : ''), code: this.cur, lines: ls, viz: this.render(o) });
    this.secNew = false; this.chg.clear(); this.newRow = false; this.fresh = 0;
    return this;
  },
  render(o) {
    const pick = (k, n) => o[k] && o[k][n] ? o[k][n] : undefined;
    let h = '<div class="wv">';
    if (o.board || this.brd) h += `<div class="wboard">${o.board || this.brd}</div>`;
    if (this.vars.size) h += V.vars([...this.vars].map(([n, x]) => [n, x.val, x.type, (o.hot && o.hot.includes(n)) || this.chg.has('v:' + n) ? 'hl' : (o.okv && o.okv.includes(n) ? 'ok' : '')]), { key: 'wr' });
    this.objs.forEach((ob, n) => {
      const opt = { hl: pick('hl', n), ok: pick('ok', n), dim: pick('dim', n), bad: pick('bad', n), g1: pick('g1', n), g2: pick('g2', n), g3: pick('g3', n), ptr: pick('ptr', n), from: pick('from', n) };
      Object.keys(opt).forEach(k => opt[k] === undefined && delete opt[k]);
      const title = ob.o.title || n;
      let body;
      if (ob.kind === 'arr') body = V.arr(ob.data, Object.assign({ key: 'wa' + n, byVal: ob.o.byVal, idx: ob.o.idx }, opt));
      else if (ob.kind === 'queue') body = V.arr(ob.data.length ? ob.data : [''], Object.assign({ key: 'wq' + n, byVal: true, idx: false }, opt));
      else if (ob.kind === 'stack') body = V.stack(ob.data, Object.assign({ key: 'ws' + n, byVal: ob.o.byVal }, opt));
      else if (ob.kind === 'dict') body = V.kv(ob.data.map(p => [p[0], p[1], (opt.hl || []).includes(p[0]) ? 'g1' : (opt.ok || []).includes(p[0]) ? 'g2' : (opt.bad || []).includes(p[0]) ? 'g3' : '']), { key: 'wd' + n });
      else if (ob.kind === 'set') body = V.chips(ob.data.length ? ob.data.map(x => [x, (opt.hl || []).includes(x) ? 'hl' : (opt.bad || []).includes(x) ? 'bad' : '']) : [['{ }', 'dim']], { key: 'wh' + n, byVal: true });
      else if (ob.kind === 'grid') body = V.grid(ob.data, Object.assign({ key: 'wg' + n, ix: true }, ob.o.g || {}, o.grid && o.grid[n] ? o.grid[n] : {}));
      const tag = ob.o.tag ? `<span class="otag">${esc(ob.o.tag)}</span>` : '';
      h += `<div class="wobj${this.chg.has('o:' + n) ? ' new' : ''}"${dk('obj:' + n)}><div class="vblk-t">${tag}${fmt(title)}</div>${body}</div>`;
    });
    if (o.eq) h += V.eq(o.eq, 'weq');
    if (o.err) h += V.err(o.err);
    if (o.ret != null) h += `<div class="wret"${dk('wret')}>return ${esc(o.ret)}</div>`;
    if (this.trace && this.trace.rows.length) {
      const R = this.trace.rows, from = Math.max(0, R.length - 6);
      h += `<div class="wtrace">${V.lab(this.trace.title, V.tbl(this.trace.head, R.slice(from), { key: 'wtr', rk: from, hl: this.newRow ? [R.length - 1 - from] : [] }))}</div>`;
    }
    if (this.outs.length || o.con) h += V.con(this.outs, this.fresh);
    return h + '</div>';
  },
  done() { this.m.scenes = this.sc; this.m.codes = this.codes; LESSONS.push(this.m); return this; }
};
function LS(meta, fn) { const l = new Lesson(meta); fn(l); l.done(); }
