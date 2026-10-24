/* 예전 자바스크립트 빌더(les*.js)로 쓴 레슨 → 레슨 JSON 변환기. 사용: node tools/convert_js_lessons.js <les 폴더> <코스 폴더> */
const fs = require('fs'), vm = require('vm'), path = require('path');
const SRC = process.argv[2], OUT = process.argv[3];
const ctx = { console }; vm.createContext(ctx);
// core.js(V, esc 등)와 lesson.js의 j() 헬퍼를 불러온 뒤, V와 Lesson을 기록용으로 교체
vm.runInContext(fs.readFileSync(path.join(SRC, 'core.js'), 'utf8') + '\n' + fs.readFileSync(path.join(SRC, 'lesson.js'), 'utf8') + ';globalThis.__V=V;globalThis.__j=j;', ctx);
const reg = [];
const MK = /\u0001(\d+)\u0002/g;
function resolve(x) {
  if (typeof x === 'string') {
    if (!x.includes('\u0001')) return x;
    const parts = []; let last = 0, m; MK.lastIndex = 0;
    while ((m = MK.exec(x))) { if (m.index > last) parts.push(x.slice(last, m.index)); parts.push(reg[+m[1]]); last = m.index + m[0].length; }
    if (last < x.length) parts.push(x.slice(last));
    return parts.length === 1 ? parts[0] : { seq: parts };
  }
  if (Array.isArray(x)) return x.map(resolve);
  if (x && typeof x === 'object') { const o = {}; for (const k in x) o[k] = resolve(x[k]); return o; }
  return x;
}
const RV = {};
Object.keys(ctx.__V).forEach(name => {
  RV[name] = (...args) => { while (args.length && args[args.length - 1] === undefined) args.pop(); const id = reg.length; reg.push({ [name]: resolve(args) }); return `\u0001${id}\u0002`; };
});
Object.assign(ctx.__V, RV);
const LESSONS = [];
const ARGN = {
  part: ['title'], code: ['src', '*'], nocode: [], use: ['code'], v: ['name', 'value', 'type'], ref: ['name', 'target', 'type'], drop: ['...names'],
  arr: ['name', 'values', '*'], stack: ['name', 'items', '*'], queue: ['name', 'items', '*'], dict: ['name', 'pairs', '*'], hset: ['name', 'items', '*'], grid: ['name', 'rows', '*'],
  free: ['...names'], out: ['text'], outw: ['text'], showOut: ['text'], tbl: ['head', 'title'], row: ['cells'], board: ['widget'], clear: [], say: ['line', 'text', '*']
};
const OPNAME = { v: 'var', arr: 'array', hset: 'set', tbl: 'table', outw: 'write', showOut: 'show_out', drop: 'drop', free: 'free' };
function evalGrid(spec, mat) { // 함수형 칸 옵션 → 행렬
  const o = {};
  for (const k in spec) {
    const f = spec[k];
    if (typeof f === 'function') o[k] = mat.map((row, r) => row.map((v, c) => { const x = f(v, r, c); return x == null ? '' : x; }));
    else o[k] = f;
  }
  return o;
}
function LS(meta, fn) {
  const ops = [], grids = {};
  const l = {};
  Object.keys(ARGN).forEach(m => {
    l[m] = (...args) => {
      const op = { op: OPNAME[m] || m }, names = ARGN[m];
      names.forEach((n, i) => {
        if (n === '*') { const o = args[i]; if (o) Object.assign(op, o); }
        else if (n.startsWith('...')) op[n.slice(3)] = args.slice(i);
        else if (args[i] !== undefined) op[n] = args[i];
      });
      if (m === 'grid') { grids[args[0]] = args[1]; if (op.g) op.g = evalGrid(op.g, args[1]); }
      if (m === 'say' && op.grid) { const g = {}; for (const n in op.grid) g[n] = evalGrid(op.grid[n], grids[n]); op.grid = g; }
      if (m === 'say' && op.line === null) delete op.line;
      if (m === 'code' && op.test === '') delete op.test;
      ops.push(resolve(JSON.parse(JSON.stringify(op, (k, v) => typeof v === 'function' ? undefined : v))));
      return l;
    };
  });
  l.codes = { get length() { return ops.filter(o => o.op === 'code').length; } };
  fn(l);
  LESSONS.push(Object.assign({}, meta, { ops }));
}
ctx.LS = LS; ctx.j = ctx.__j;
fs.readdirSync(SRC).filter(f => /^les\d+\.js$/.test(f)).sort((a, b) => parseInt(a.slice(3)) - parseInt(b.slice(3)))
  .forEach(f => vm.runInContext(fs.readFileSync(path.join(SRC, f), 'utf8'), ctx));
fs.mkdirSync(path.join(OUT, 'lessons'), { recursive: true });
const dump = L => { const { ops, ...meta } = L; return '{\n' + Object.entries(meta).map(([k, v]) => `  ${JSON.stringify(k)}: ${JSON.stringify(v)},`).join('\n') + '\n  "ops": [\n' + ops.map(o => '    ' + JSON.stringify(o)).join(',\n') + '\n  ]\n}\n'; };
LESSONS.sort((a, b) => a.id - b.id).forEach(L => fs.writeFileSync(path.join(OUT, 'lessons', String(L.id).padStart(2, '0') + '.json'), dump(L)));
console.log('lessons', LESSONS.length, 'ops', LESSONS.reduce((s, L) => s + L.ops.length, 0), 'widgets', reg.length);
