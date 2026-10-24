/* ===== 레슨 JSON → 장면 =====
   JSON의 op를 차례로 Lesson 빌더에 넘기고, 위젯 설명(board, err 등)은 V 그림 함수로 그립니다. */
function renderW(w) {
  if (w == null) return '';
  if (typeof w === 'string') return w;
  if (Array.isArray(w)) return w.map(renderW).join('');
  if (w.seq) return w.seq.map(renderW).join('');
  const keys = Object.keys(w);
  if (keys.length === 1 && typeof V[keys[0]] === 'function') {
    const args = (Array.isArray(w[keys[0]]) ? w[keys[0]] : [w[keys[0]]]).map(resolveArg);
    return V[keys[0]](...args);
  }
  throw new Error('알 수 없는 위젯: ' + JSON.stringify(w).slice(0, 80));
}
const isWidget = x => x && typeof x === 'object' && !Array.isArray(x) && (x.seq || (Object.keys(x).length === 1 && typeof V[Object.keys(x)[0]] === 'function' && !('h' in x)));
function resolveArg(x) {
  if (isWidget(x)) return renderW(x);
  if (Array.isArray(x)) return x.map(resolveArg);
  if (x && typeof x === 'object' && !('h' in x)) { const o = {}; for (const k in x) o[k] = resolveArg(x[k]); return o; }
  return x;
}
const matFn = m => (Array.isArray(m) ? (v, r, c) => (m[r] && m[r][c] != null && m[r][c] !== '' ? m[r][c] : (m.__def != null ? m.__def : '')) : m);
function gridOpts(g) { if (!g) return g; const o = {}; for (const k in g) o[k] = Array.isArray(g[k]) ? matFn(g[k]) : g[k]; return o; }
function sayOpts(op) {
  const o = {};
  for (const k in op) if (!['op', 'line', 'text'].includes(k)) o[k] = op[k];
  ['board', 'err', 'eq', 'note'].forEach(k => { if (o[k] != null && typeof o[k] !== 'string') o[k] = renderW(o[k]); });
  if (o.grid) { const g = {}; for (const n in o.grid) g[n] = gridOpts(o.grid[n]); o.grid = g; }
  return o;
}
function compileLesson(json) {
  const l = new Lesson({ id: json.id, group: json.group || '', title: json.title, sub: json.sub || '' });
  const pick = (op, skip) => { const o = {}; for (const k in op) if (!skip.includes(k)) o[k] = op[k]; return o; };
  json.ops.forEach((op, n) => {
    try {
      switch (op.op) {
        case 'part': l.part(op.title); break;
        case 'code': l.code(op.src, pick(op, ['op', 'src'])); break;
        case 'nocode': l.nocode(); break;
        case 'use': l.use(op.code); break;
        case 'var': l.v(op.name, op.value, op.type); break;
        case 'ref': l.ref(op.name, op.target, op.type); break;
        case 'drop': l.drop(...op.names); break;
        case 'free': l.free(...op.names); break;
        case 'array': l.arr(op.name, op.values, pick(op, ['op', 'name', 'values'])); break;
        case 'stack': l.stack(op.name, op.items, pick(op, ['op', 'name', 'items'])); break;
        case 'queue': l.queue(op.name, op.items, pick(op, ['op', 'name', 'items'])); break;
        case 'dict': l.dict(op.name, op.pairs, pick(op, ['op', 'name', 'pairs'])); break;
        case 'set': l.hset(op.name, op.items, pick(op, ['op', 'name', 'items'])); break;
        case 'grid': { const o = pick(op, ['op', 'name', 'rows']); if (o.g) o.g = gridOpts(o.g); l.grid(op.name, op.rows, o); break; }
        case 'out': l.out(op.text); break;
        case 'write': l.outw(op.text); break;
        case 'show_out': l.showOut(op.text); break;
        case 'table': l.tbl(op.head, op.title); break;
        case 'row': l.row(op.cells); break;
        case 'board': l.board(renderW(op.widget)); break;
        case 'clear': l.clear(); break;
        case 'say': l.say(op.line == null ? null : op.line, op.text, sayOpts(op)); break;
        default: throw new Error('알 수 없는 op: ' + op.op);
      }
    } catch (e) { throw new Error(`[레슨 ${json.id} · op ${n} (${op.op})] ${e.message}`); }
  });
  l.done();
}
