/* ---------- 공통: 그림 도우미, 대본 처리, 코드 강조 ---------- */
var P = [];
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const inl = s => esc(s).replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
const fmt = x => (x && typeof x === 'object' && 'h' in x) ? x.h : inl(x == null ? '' : x);
const KEYS = ['hl', 'ok', 'dim', 'bad', 'g1', 'g2', 'g3'];
const cellCls = (o, i) => KEYS.filter(k => o[k] && o[k].includes(i)).join(' ');

const dk = k => ` data-k="${esc(k)}"`;
const V = {
  /* 1차원 배열: 값 칸 + 인덱스 + 포인터. o.key: 키 접두사, o.byVal: 값으로 키(재배치 애니메이션), o.from: {i: 날아올 출발 키} */
  arr(vals, o = {}) {
    const lab = o.label !== undefined;
    const K = o.key || o.label || 'a';
    const ck = (v, i) => o.byVal ? `${K}#${v}` : `${K}:${i}`;
    let h = '<table class="va">';
    if (o.ptr) h += '<tr class="ptr">' + (lab ? '<th></th>' : '') + vals.map((_, i) => {
      if (o.ptr[i] == null) return '<td></td>';
      const names = String(o.ptr[i]).split(' · ');
      return `<td>${names.map(n => `<span class="pt"${dk(K + '^' + n)}><span>${esc(n)}</span><i>▾</i></span>`).join('')}</td>`;
    }).join('') + '</tr>';
    h += '<tr class="val">' + (lab ? `<th>${esc(o.label)}</th>` : '') + vals.map((v, i) =>
      `<td class="${cellCls(o, i)}"${v === '' ? '' : dk(ck(v, i))}${o.from && o.from[i] ? ` data-from="${esc(o.from[i])}"` : ''}>${esc(v)}</td>`).join('') + '</tr>';
    if (o.idx !== false) {
      const ix = Array.isArray(o.idx) ? o.idx : vals.map((_, i) => i);
      h += '<tr class="ix">' + (lab ? '<th></th>' : '') + ix.map(x => `<td>${esc(x)}</td>`).join('') + '</tr>';
    }
    return h + '</table>';
  },
  /* 2차원 격자. o.html(v,r,c): 칸 안에 넣을 HTML(이동 표시 등) */
  grid(mat, o = {}) {
    const K = o.key || 'g';
    let h = '<table class="vg">';
    if (o.ix) h += '<tr><th></th>' + mat[0].map((_, j) => `<th>${j}</th>`).join('') + '</tr>';
    mat.forEach((row, r) => {
      h += '<tr>' + (o.ix ? `<th>${r}</th>` : '') + row.map((v, c) => {
        const cls = o.cls ? (o.cls(v, r, c) || '') : '';
        const t = o.txt ? o.txt(v, r, c) : v;
        const extra = o.html ? (o.html(v, r, c) || '') : '';
        const from = o.from ? o.from(v, r, c) : null;
        return `<td class="${cls}"${dk(`${K}:${r},${c}`)}>${t === '' || t == null ? '' : `<span${dk(`${K}t:${r},${c}`)}${from ? ` data-from="${esc(from)}"` : ''}>${esc(t)}</span>`}${extra}</td>`;
      }).join('') + '</tr>';
    });
    return h + '</table>';
  },
  /* 표 */
  tbl(head, rows, o = {}) {
    let h = '<table class="vt">';
    if (o.cap) h += `<caption>${fmt(o.cap)}</caption>`;
    h += '<thead><tr>' + head.map(x => `<th>${fmt(x)}</th>`).join('') + '</tr></thead><tbody>';
    rows.forEach((row, r) => {
      const rc = ['hl', 'ok', 'bad', 'dim'].find(k => o[k] && o[k].includes(r)) || '';
      h += `<tr class="${rc}"${o.key ? dk(`${o.key}:${(o.rk || 0) + r}`) : ''}>` + row.map(x => `<td>${fmt(x)}</td>`).join('') + '</tr>';
    });
    return h + '</tbody></table>';
  },
  /* 스택: items는 아래 → 위. o.byVal: 값으로 키 */
  stack(items, o = {}) {
    const K = o.key || 's';
    let h = '<div class="vs"><div class="vs-col">';
    if (!items.length) h += '<div class="vs-it vs-empty">비어 있음</div>';
    for (let i = items.length - 1; i >= 0; i--) {
      const raw = typeof items[i] === 'object' ? JSON.stringify(items[i]) : items[i];
      h += `<div class="vs-it ${cellCls(o, i)}"${dk(o.byVal ? `${K}#${raw}` : `${K}:${i}`)}>${fmt(items[i])}${i === items.length - 1 ? `<span class="vs-top"${dk(K + '^top')}>top</span>` : ''}</div>`;
    }
    h += '</div>' + (o.cap ? `<div class="vcap">${fmt(o.cap)}</div>` : '') + '</div>';
    return h;
  },
  /* 사전(키 → 값) */
  kv(pairs, o = {}) {
    const K = o.key || 'kv';
    return `<div class="vk">${o.title ? `<div class="vk-t">${fmt(o.title)}</div>` : ''}<div class="vk-b">` +
      (pairs.length ? pairs.map(p => `<div class="vk-i ${p[2] || ''}"${dk(`${K}:${p[0]}`)}><span>${fmt(p[0])}</span><b${dk(`${K}v:${p[0]}`)}>${fmt(p[1])}</b></div>`).join('') : '<div class="vk-i vk-e">{ }</div>') +
      '</div></div>';
  },
  /* 흐름: 상자 → 상자 */
  flow(items, o = {}) {
    const K = o.key || 'f';
    return '<div class="vf">' + items.map((it, i) => {
      const [t, c] = Array.isArray(it) ? it : [it, ''];
      const ar = i ? `<span class="vf-a"${dk(`${K}a:${i}`)}>${o.labels && o.labels[i - 1] ? `<em>${fmt(o.labels[i - 1])}</em>` : ''}<span>→</span></span>` : '';
      return ar + `<span class="vf-b ${c || ''}"${dk(`${K}:${i}`)}>${fmt(t)}</span>`;
    }).join('') + '</div>';
  },
  chips(items, o = {}) {
    const K = o.key || 'c';
    return '<div class="vch">' + items.map((it, i) => { const [t, c] = Array.isArray(it) ? it : [it, '']; return `<span class="vf-b ${c || ''}"${dk(`${K}:${o.byVal ? t : i}`)}>${fmt(t)}</span>`; }).join('') + '</div>';
  },
  /* 시간 구간 막대. 다섯째 값: 막대 키 */
  tl(items, o = {}) {
    const K = o.key || 't';
    const lo = o.min != null ? o.min : 0;
    const hi = o.max != null ? o.max : Math.max(...items.map(x => x[1]));
    const pct = v => (v - lo) / (hi - lo) * 100;
    let h = '<div class="vtl">';
    items.forEach(([s, e, c, lab, key], i) => {
      const kk = key != null ? key : i;
      h += `<div class="vtl-r"${dk(`${K}r:${kk}`)}><span class="vtl-l">${fmt(lab != null ? lab : `[${s}, ${e}]`)}</span><div class="vtl-t"><div class="vtl-b ${c || ''}"${dk(`${K}:${kk}`)} data-kz="1" style="left:${pct(s)}%;width:${Math.max(pct(e) - pct(s), 1.4)}%"></div></div></div>`;
    });
    const step = o.step || 1;
    h += '<div class="vtl-r vtl-ax"><span class="vtl-l"></span><div class="vtl-t">';
    for (let v = lo; v <= hi; v += step) h += `<span style="left:${pct(v)}%">${v}</span>`;
    return h + '</div></div></div>';
  },
  /* 변수 상자: [[이름, 값, 상태], …] — 값이 바뀌면 깜빡임 */
  regs(pairs, o = {}) {
    const K = o.key || 'rg';
    return '<div class="vreg">' + pairs.map(([n, v, c]) => `<div class="rg ${c || ''}"><span class="rg-n">${fmt(n)}</span><b${dk(`${K}:${n}`)}>${fmt(v)}</b></div>`).join('') + '</div>';
  },
  row: (...p) => `<div class="vrow">${p.join('')}</div>`,
  cap: (t, k) => `<div class="vcap"${k ? dk(k) : ''}>${fmt(t)}</div>`,
  note: t => `<div class="vnote">${fmt(t)}</div>`,
  eq: (t, k) => `<div class="veq"${k ? dk(k) : ''}>${fmt(t)}</div>`,
  lab: (t, html) => `<div class="vblk"><div class="vblk-t">${fmt(t)}</div>${html}</div>`
};

/* ---------- 대본: 화면 표기와 읽기용 문장 ---------- */
function splitSent(t) {
  const parts = t.split(/([.?!])\s+/), out = [];
  for (let i = 0; i < parts.length; i += 2) out.push(parts[i] + (parts[i + 1] || ''));
  return out.map(s => s.trim()).filter(Boolean);
}
/* ---------- 수식: \frac{a}{b}, x^2, x_1, \sqrt{x}, \pm, \theta, \hl{강조} … ---------- */
const MSYM = { '\\pm': '±', '\\times': '×', '\\cdot': '·', '\\div': '÷', '\\le': '≤', '\\ge': '≥', '\\ne': '≠', '\\approx': '≈', '\\to': '→', '\\Rightarrow': '⇒',
  '\\theta': 'θ', '\\pi': 'π', '\\alpha': 'α', '\\beta': 'β', '\\gamma': 'γ', '\\Delta': 'Δ', '\\mu': 'μ', '\\lambda': 'λ', '\\omega': 'ω', '\\infty': '∞', '\\deg': '°', '\\circ': '°', '\\parallel': '∥', '\\perp': '⊥', '\\angle': '∠', '\\triangle': '△', '\\sigma': 'σ', '\\rho': 'ρ', '\\phi': 'φ', '\\leftrightarrow': '↔', '\\leftarrow': '←',
  '\\sin': '<span class="mfn">sin</span>', '\\cos': '<span class="mfn">cos</span>', '\\tan': '<span class="mfn">tan</span>', '\\log': '<span class="mfn">log</span>', '\\quad': '<span class="mq"></span>', '\\,': ' ' };
function mathHtml(s) {
  s = String(s); let i = 0;
  const arg = () => { if (s[i] === '{') { i++; const g = group(); i++; return g; } return atom(); };
  const group = () => { let o = ''; while (i < s.length && s[i] !== '}') o += atom(); return o; };
  const atom = () => {
    const c = s[i];
    if (c === '\\') {
      const m = /^\\([a-zA-Z]+|.)/.exec(s.slice(i)); const cmd = m[0]; i += cmd.length;
      if (cmd === '\\frac') { const a = arg(), b = arg(); return `<span class="mfrac"><span>${a}</span><span>${b}</span></span>`; }
      if (cmd === '\\sqrt') { const a = arg(); return `<span class="msqrt"><span class="mrad">√</span><span class="mrt">${a}</span></span>`; }
      if (cmd === '\\text') return `<span class="mtext">${arg()}</span>`;
      if (/^\\(hl|ok|bad|g1|g2|g3|dim)$/.test(cmd)) return `<span class="mhl ${cmd.slice(1)}">${arg()}</span>`;
      return MSYM[cmd] || esc(cmd.slice(1));
    }
    if (c === '^') { i++; return `<sup>${arg()}</sup>`; }
    if (c === '_') { i++; return `<sub>${arg()}</sub>`; }
    if (c === '{') { i++; const g = group(); i++; return g; }
    i++;
    if (/[a-zA-Z]/.test(c)) return `<i>${c}</i>`;
    if (c === '-') return '−';
    if (c === '*') return '×';
    if (c === ' ') return ' ';
    return esc(c);
  };
  let o = ''; while (i < s.length) { if (s[i] === '}') { i++; continue; } o += atom(); }
  return `<span class="math">${o}</span>`;
}
/* 화면 표기: [[표기|읽는 말]], `코드`, **굵게**, {en|English}, {m|수식} */
function showText(s) {
  const inline = x => x.replace(/\{m\|((?:[^{}]|\{[^{}]*\})+)\}/g, (_, m) => mathHtml(m.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&')))
    .replace(/\{en\|([^}]+)\}/g, '<span class="en">$1</span>');
  return inline(esc(s).replace(/\[\[((?:\{[^}]*\}|\](?!\])|[^|\]])+)\|(.+?)\]\]/g, (_, d) => /^\{(m|en)\|/.test(d) ? d : `<code>${d}</code>`)
    .replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>'));
}
const LET = { a: '에이', b: '비', c: '씨', d: '디', e: '이', f: '에프', g: '지', h: '에이치', i: '아이', j: '제이', k: '케이', l: '엘', m: '엠', n: '엔', o: '오', p: '피', q: '큐', r: '알', s: '에스', t: '티', u: '유', v: '브이', w: '더블유', x: '엑스', y: '와이', z: '제트' };
const PRON = [
  [/\bConsole\.WriteLine\b/g, '콘솔 라이트라인'], [/\bConsole\.Write\b/g, '콘솔 라이트'], [/\bToCharArray\b/g, '투차어레이'], [/\bToArray\b/g, '투어레이'], [/\bToList\b/g, '투리스트'], [/\bToString\b/g, '투스트링'], [/\bToUpper\b/g, '투어퍼'], [/\bTryParse\b/g, '트라이파스'], [/\bCompareTo\b/g, '컴페어투'], [/\bParse\b/g, '파스'], [/\bWriteLine\b/g, '라이트라인'], [/\bWrite\b/g, '라이트'], [/\bFact\b/g, '팩트'], [/\bdouble\b/g, '더블'], [/\bage\b/g, '에이지'], [/\bswitch\b/g, '스위치'], [/\busing\b/g, '유징'], [/\bscore\b/g, '스코어'], [/\bcase\b/g, '케이스'], [/\btotal\b/g, '토탈'], [/\bSystem\b/g, '시스템'], [/\bpublic\b/g, '퍼블릭'], [/\bSolution\b/g, '솔루션'], [/\brest\b/g, '레스트'], [/\bdigits\b/g, '디짓츠'], [/\bMax\b/g, '맥스'], [/\bMin\b/g, '민'], [/\bSum\b/g, '썸'], [/\bAverage\b/g, '애버리지'], [/\bapple\b/g, '애플'], [/\bMain\b/g, '메인'], [/\bKey\b/g, '키'], [/\bValue\b/g, '밸류'], [/\bvalue\b/g, '밸류'], [/\bWhere\b/g, '웨어'], [/\bSelect\b/g, '셀렉트'], [/\bAny\b/g, '애니'], [/\bAll\b/g, '올'], [/\bclass\b/g, '클래스'], [/\bok\b/g, '오케이'], [/\badult\b/g, '어덜트'], [/\bteen\b/g, '틴'], [/\bdefault\b/g, '디폴트'], [/\bClone\b/g, '클론'], [/\bReplace\b/g, '리플레이스'], [/\babc\b/g, '에이 비 씨'], [/\bABC\b/g, '에이 비 씨'], [/\bbanana\b/g, '바나나'], [/\bSwap\b/g, '스왑'], [/\bref\b/g, '레프'], [/\bPoint\b/g, '포인트'], [/\bDist\b/g, '디스트'],
  [/\bBitCount\b/g, '비트카운트'], [/Enumerable\.Range/g, '이뉴머러블 레인지'], [/\bGetLength\b/g, '겟렝스'], [/\bDfs\b/g, '디에프에스'], [/\bCompare\b/g, '컴페어'], [/\bbool\b/g, '불'], [/\beat\b/g, '잇'], [/\btea\b/g, '티'], [/\btan\b/g, '탠'], [/\bate\b/g, '에이트'], [/\bnat\b/g, '냇'], [/\bbat\b/g, '뱃'], [/\baet\b/g, '에이 이 티'], [/\bant\b/g, '에이 엔 티'], [/\babt\b/g, '에이 비 티'], [/\bdev\b/g, '데브'], [/\bhr\b/g, '에이치알'], [/\bops\b/g, '옵스'], [/\bpark\b/g, '박'], [/\blee\b/g, '리'], [/\bchoi\b/g, '최'], [/\bjung\b/g, '정'], [/\bthe\b/g, '더'], [/\bday\b/g, '데이'], [/\bis\b/g, '이즈'], [/\bsunny\b/g, '써니'],
  [/O\(n log n\)/g, '오 엔 로그 엔'], [/O\(n²\)/g, '오 엔 제곱'], [/O\(log n\)/g, '오 로그 엔'], [/O\(n\)/g, '오 엔'], [/O\(1\)/g, '오 일'], [/O\(n \+ q\)/g, '오 엔 더하기 큐'],
  [/\.NET/g, '닷넷'], [/C#/g, '씨샵'], [/LINQ/g, '링크'], [/Mono/g, '모노'], [/BFS/g, '비에프에스'], [/DFS/g, '디에프에스'], [/Union-Find/g, '유니온 파인드'],
  [/StringBuilder/g, '스트링빌더'], [/StringComparer/g, '스트링컴페어러'], [/Dictionary/g, '딕셔너리'], [/HashSet/g, '해시셋'], [/StackOverflow/g, '스택 오버플로'],
  [/Stack/g, '스택'], [/Queue/g, '큐'], [/List/g, '리스트'], [/OrderByDescending/g, '오더바이 디센딩'], [/OrderBy/g, '오더바이'], [/ThenBy/g, '덴바이'],
  [/GroupBy/g, '그룹바이'], [/Distinct/g, '디스팅트'], [/Array\.Sort/g, '어레이 소트'], [/Sort/g, '소트'], [/Append/g, '어펜드'], [/Contains/g, '컨테인즈'], [/Remove/g, '리무브'],
  [/Find/g, '파인드'], [/Peek/g, '피크'], [/Add/g, '애드'], [/Count/g, '카운트'], [/Split/g, '스플릿'], [/Array/g, '어레이'], [/Math/g, '매스'],
  [/lower bound/g, '로어 바운드'], [/true/g, '트루'], [/false/g, '폴스'], [/\bchar\b/g, '차'], [/\bint\b/g, '인트'], [/\blong\b/g, '롱'], [/\bout\b/g, '아웃'],
  [/\bstring\b/g, '스트링'], [/\bwhile\b/g, '와일'], [/\bparent\b/g, '페어런트'], [/\bprefix\b/g, '프리픽스'], [/\btarget\b/g, '타겟'], [/\bbest\b/g, '베스트'],
  [/\bcur\b/g, '커'], [/\brun\b/g, '런'], [/\bdp\b/g, '디피'], [/\blo\b/g, '로'], [/\bhi\b/g, '하이'], [/\bmid\b/g, '미드'], [/\bleft\b/g, '레프트'], [/\bright\b/g, '라이트'],
  [/\barr\b/g, '어레이'], [/\bnums\b/g, '넘스'], [/\bqueries\b/g, '쿼리즈'], [/\btemps\b/g, '템프스'], [/\bwords\b/g, '워즈'], [/\btext\b/g, '텍스트'],
  [/\bintervals\b/g, '인터벌즈'], [/\bnames\b/g, '네임즈'], [/\bdepts\b/g, '뎁츠'], [/\bsalaries\b/g, '샐러리즈'], [/\bcoins\b/g, '코인즈'], [/\bamount\b/g, '어마운트'],
  [/\bmeetings\b/g, '미팅즈'], [/\bmaze\b/g, '메이즈'], [/\bgrid\b/g, '그리드'], [/\bnumbers\b/g, '넘버즈'], [/\bcmds\b/g, '커맨즈'], [/\btimes\b/g, '타임즈'],
  [/\bversions\b/g, '버전즈'], [/\bedges\b/g, '엣지즈'], [/\blimit\b/g, '리밋'], [/\breturn\b/g, '리턴'], [/\bsolution\b/g, '솔루션'], [/HH:MM/g, '시와 분'],
  [/ = /g, ', '], [/ - /g, ' 빼기 '], [/ \+ /g, ' 더하기 '],
  [/\bTryGetValue\b/g, '트라이겟밸류'], [/\bcomposite\b/g, '컴포짓'], [/\bcontinue\b/g, '컨티뉴'], [/\bforeach\b/g, '포이치'], [/\bislands\b/g, '아일랜즈'], [/\blastEnd\b/g, '라스트엔드'], [/\bEnqueue\b/g, '인큐'], [/\bDequeue\b/g, '디큐'], [/\banswer\b/g, '앤서'], [/\bresult\b/g, '리절트'], [/\bgroups\b/g, '그룹스'], [/\bmerged\b/g, '머지드'], [/\bprefix\b/g, '프리픽스'], [/\bLength\b/g, '렝스'], [/\bAppend\b/g, '어펜드'], [/\bcount\b/g, '카운트'], [/\bbreak\b/g, '브레이크'], [/\bstack\b/g, '스택'], [/\bqueue\b/g, '큐'], [/\belse\b/g, '엘스'], [/\bseen\b/g, '신'], [/\bfreq\b/g, '프리퀀시'], [/\bneed\b/g, '니드'], [/\bprev\b/g, '프리브'], [/\bdist\b/g, '디스트'], [/\bmins\b/g, '민즈'], [/\blast\b/g, '라스트'], [/\blist\b/g, '리스트'], [/\bstrs\b/g, '스트링즈'], [/\brows\b/g, '로우즈'], [/\bcols\b/g, '콜즈'], [/\bopen\b/g, '오픈'], [/\bnull\b/g, '널'], [/\bPush\b/g, '푸시'], [/\bsum\b/g, '썸'], [/\bfor\b/g, '포'], [/\bnew\b/g, '뉴'], [/\bold\b/g, '올드'], [/\bcnt\b/g, '카운트'], [/\bidx\b/g, '인덱스'], [/\blen\b/g, '렌'], [/\bgcd\b/g, '지시디'], [/\blcm\b/g, '엘시엠'], [/\bvar\b/g, '바'], [/\bPop\b/g, '팝'], [/\bif\b/g, '이프'], [/\bsb\b/g, '에스비'], [/\bnr\b/g, '엔알'], [/\bnc\b/g, '엔씨'], [/\bdr\b/g, '디알'], [/\bdc\b/g, '디씨'], [/\bcs\b/g, '씨에스'], [/\bch\b/g, '씨에이치'],
  [/≤/g, ' 이하 '], [/≥/g, ' 이상 '], [/→/g, ', '], [/×/g, ' 곱하기 '], [/−/g, ' 빼기 ']
];
function sayText(s) {
  let t = s.replace(/\[\[(.+?)\|(.+?)\]\]/g, '$2').replace(/`([^`]+)`/g, '$1').replace(/\*\*/g, '');
  for (const [re, to] of PRON) t = t.replace(re, to);
  t = t.replace(/(^|[^A-Za-z])([A-Za-z])(?![A-Za-z])/g, (m, p, ch) => p + LET[ch.toLowerCase()]);
  return t.replace(/\s+/g, ' ').trim();
}

/* ---------- C# 코드 강조 ---------- */
const CS_KW = 'using|public|private|class|static|return|new|var|for|foreach|in|while|if|else|continue|break|switch|case|const|out|true|false|null|this|int|long|bool|string|char|void';
const CS_RE = new RegExp(`(\\/\\/.*$)|("(?:[^"\\\\]|\\\\.)*"|'(?:[^'\\\\]|\\\\.)*')|\\b(${CS_KW})\\b|\\b(\\d[\\d_]*)\\b|\\b([A-Z][A-Za-z0-9]*)\\b`, 'g');
const PY_KW = 'def|return|for|in|while|if|elif|else|import|from|as|class|True|False|None|and|or|not|print|range|len|lambda|break|continue|pass|with';
const PY_RE = new RegExp(`(#.*$)|("(?:[^"\\\\]|\\\\.)*"|'(?:[^'\\\\]|\\\\.)*')|\\b(${PY_KW})\\b|\\b(\\d[\\d_.]*)\\b|\\b([A-Z][A-Za-z0-9]*)\\b`, 'g');
function hlLine(src, lang) {
  if (lang && /^(text|plain|en|ko|none)$/.test(lang)) return esc(src);
  const RE = lang && /^(python|py)$/.test(lang) ? PY_RE : CS_RE;
  let out = '', last = 0, m;
  RE.lastIndex = 0;
  while ((m = RE.exec(src))) {
    out += esc(src.slice(last, m.index));
    const cls = m[1] ? 'c' : m[2] ? 's' : m[3] ? 'k' : m[4] ? 'n' : 't';
    out += `<span class="${cls}">${esc(m[0])}</span>`;
    last = m.index + m[0].length;
  }
  return out + esc(src.slice(last));
}
function codeLines(code, from, to, hl) {
  const lines = code.split('\n');
  const a = Math.max(1, from), b = Math.min(lines.length, to);
  let h = '';
  for (let n = a; n <= b; n++) h += `<span class="ln${hl && hl.includes(n) ? ' on' : ''}"><i>${n}</i>${hlLine(lines[n - 1]) || ' '}</span>`;
  return h;
}
function codeSlice(code, c) {
  let r, h;
  if (Array.isArray(c)) { r = c; h = []; for (let n = c[0]; n <= c[1]; n++) h.push(n); }
  else { r = c.r; h = c.h || []; if (!c.h) for (let n = r[0]; n <= r[1]; n++) h.push(n); }
  return codeLines(code, r[0] - 1, r[1] + 1, h);
}
/* ---------- 문제 읽기: 설명·제한사항·예 설명 → 문장 ---------- */
const QSAY = {
  '0 ≤ s ≤ e < `arr`의 길이': 's는 0 이상이고 e 이하이며, e는 arr의 길이보다 작습니다.',
  '1 ≤ `k` ≤ `arr`의 길이 ≤ 200,000': 'k는 1 이상 arr의 길이 이하이고, arr의 길이는 200,000 이하입니다.',
  '"HH:MM" 형식의 24시간제 시각들이 담긴 배열 `times`가 주어집니다.': '시와 분으로 적힌 24시간제 시각들이 담긴 배열 times가 주어집니다.',
  '"1.10.2"처럼 점으로 구분된 버전 문자열 배열 `versions`가 주어집니다.': '[[x|일 점 십 점 이]]처럼 점으로 구분된 버전 문자열 배열 versions가 주어집니다.',
  '0 ≤ 시작 ≤ 끝 ≤ 10⁹': '시작과 끝은 0 이상 10⁹ 이하이고, 시작은 끝보다 크지 않습니다.',
  '0 ≤ 시작 ≤ 끝 ≤ 100,000': '시작과 끝은 0 이상 100,000 이하이고, 시작은 끝보다 크지 않습니다.',
  '"aaabbc"는 a 세 개, b 두 개, c 한 개로 이루어져 있으므로 "a3b2c1"입니다.': '[[x|에이 에이 에이 비 비 씨]]는 a 세 개, b 두 개, c 한 개로 이루어져 있으므로 [[x|에이 삼 비 이 씨 일]]입니다.',
  '괄호 `( ) { } [ ]`로만 이루어진 문자열 `s`가 주어집니다.': '소괄호, 중괄호, 대괄호로만 이루어진 문자열 s가 주어집니다.'
};
function limSay(s) {
  if (QSAY[s]) return QSAY[s];
  const m = s.match(/^(.+?)\s*≤\s*(.+?)\s*≤\s*(.+)$/);
  if (m && !/[<≤]/.test(m[3])) return `${m[2]}: ${m[1]} 이상, ${m[3]} 이하.`;
  const m2 = s.match(/^(.+?)\s*≤\s*(.+)$/);
  if (m2 && !/[<≤]/.test(m2[2])) return `${m2[2]}: ${m2[1]} 이상.`;
  return s;
}
function htmlMd(h) {
  return h.replace(/<code>([\s\S]*?)<\/code>/g, '`$1`').replace(/<b>([\s\S]*?)<\/b>/g, '**$1**').replace(/<[^>]+>/g, '')
    .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&').replace(/\s+/g, ' ').trim();
}
function htmlBlocks(h) {
  const out = [], re = /<(ol|ul)>|<\/(ol|ul)>|<(p|li)>([\s\S]*?)<\/(?:p|li)>/g; let m, list = null;
  while ((m = re.exec(h))) {
    if (m[1]) list = m[1]; else if (m[2]) list = null; else out.push({ tag: m[3], list, md: htmlMd(m[4]) });
  }
  return out;
}
function mkSent(md, sayMd) { const sm = (sayMd != null ? sayMd : md).replace(/`\+`/g, '더하기 기호').replace(/`-`/g, '빼기 기호'); return { html: showText(md), say: sayText(sm) }; }
function buildQ(p) {
  const sec = { title: [mkSent(p.title, `문제 ${p.id}. ${p.title}.`)], desc: [], lim: [], exn: [] };
  htmlBlocks(p.desc).forEach(b => sec.desc.push({ tag: b.tag, list: b.list, sents: splitSent(b.md).map(x => mkSent(x, QSAY[x])) }));
  sec.limH = mkSent('제한사항', '제한사항.');
  p.limits.forEach(l => sec.lim.push({ tag: 'li', list: 'ul', sents: [mkSent(l, limSay(l))] }));
  if (p.exNote) {
    sec.exnH = mkSent('입출력 예 설명', '입출력 예 설명.');
    htmlBlocks(p.exNote).forEach(b => sec.exn.push({ tag: b.tag, list: b.list, sents: splitSent(b.md).map(x => mkSent(x, QSAY[x])) }));
  }
  const flat = [...sec.title];
  sec.desc.forEach(b => flat.push(...b.sents));
  flat.push(sec.limH); sec.lim.forEach(b => flat.push(...b.sents));
  if (sec.exnH) { flat.push(sec.exnH); sec.exn.forEach(b => flat.push(...b.sents)); }
  flat.forEach((s, i) => { s.u = i; });
  sec.flat = flat;
  return sec;
}
if (typeof module !== 'undefined') module.exports = { V, P, splitSent, sayText, showText, codeSlice };
