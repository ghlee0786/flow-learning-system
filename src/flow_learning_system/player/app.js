/* ---------- 교재 플레이어 ---------- */
(function () {
  const $ = id => document.getElementById(id);
  const store = {
    get(k, d) { try { const v = localStorage.getItem('csg:' + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem('csg:' + k, JSON.stringify(v)); } catch (e) { } }
  };
  const pad = n => String(n).padStart(2, '0');
  const reduced = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  const narrow = () => innerWidth <= 900;
  const EASE = 'cubic-bezier(.2,.8,.2,1)';
  const L = LESSONS.slice().sort((a, b) => a.id - b.id);
  L.forEach(x => x.scenes.forEach(s => { s.html = showText(s.say); }));

  let li = Math.max(0, Math.min(L.length - 1, store.get('li', 0) | 0));
  let k = 0, shownK = -1, shownCode = -2, playing = false, timer = null, raf = 0, gen = 0;
  let rate = store.get('rate', 1), autoNext = store.get('auto', true);
  const done = new Set(store.get('done', []));
  const T = () => (TIMING[L[li].id] || [[]])[0];

  /* ---------- 오디오 ---------- */
  const aud = $('aud');
  let audOK = true, triedBlob = false, pendingSeek = null, blobUrl = null;
  function loadAudio() {
    audOK = true; triedBlob = false; pendingSeek = null;
    if (blobUrl) { URL.revokeObjectURL(blobUrl); blobUrl = null; }
    aud.src = `audio/l${pad(L[li].id)}.${AUDIO_EXT}`; aud.load();
  }
  aud.addEventListener('error', () => {
    if (!triedBlob) {
      triedBlob = true; const want = li;
      fetch(`audio/l${pad(L[li].id)}.${AUDIO_EXT}`).then(r => { if (!r.ok) throw 0; return r.blob(); }).then(b => {
        if (want !== li) return;
        blobUrl = URL.createObjectURL(new Blob([b], { type: 'audio/mpeg' })); aud.src = blobUrl; aud.load();
        if (playing) startAudio();
      }).catch(() => { audOK = false; if (playing) { toast('음성 파일을 불러오지 못해 소리 없이 진행합니다'); silent(); } });
    } else { audOK = false; if (playing) silent(); }
  });
  aud.addEventListener('loadedmetadata', () => { if (pendingSeek != null) { try { aud.currentTime = pendingSeek; } catch (e) { } pendingSeek = null; } });
  aud.addEventListener('ended', () => { if (playing) finish(); });
  function seekAudio(t) { if (aud.readyState >= 1) { try { aud.currentTime = t; } catch (e) { pendingSeek = t; } } else pendingSeek = t; }
  function startAudio() {
    aud.playbackRate = rate; try { aud.preservesPitch = true; } catch (e) { }
    const tm = T()[k]; seekAudio(tm ? tm[0] + 0.001 : 0);
    const pr = aud.play();
    if (pr && pr.catch) pr.catch(err => { if (playing && err && err.name === 'NotAllowedError') { stop(); toast('재생 버튼을 한 번 더 눌러 주세요'); } });
    loop();
  }
  function loop() {
    cancelAnimationFrame(raf);
    const tick = () => {
      if (!playing || !audOK) return;
      const t = aud.currentTime, tm = T(); let nk = 0;
      for (let i = 0; i < tm.length; i++) if (tm[i][0] <= t + 0.04) nk = i;
      if (nk !== k) { k = nk; show(true); }
      progress(t);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
  }
  const est = s => Math.max(1600, s.length * 150) / rate;
  function silent() {
    clearTimeout(timer); const my = ++gen; show(true);
    timer = setTimeout(() => {
      if (my !== gen || !playing) return;
      if (k < L[li].scenes.length - 1) { k++; silent(); } else finish();
    }, est(L[li].scenes[k].say));
  }
  function play() {
    playing = true; $('bigplay').hidden = true; bar();
    if (k >= L[li].scenes.length - 1 && shownK === k && aud.ended) k = 0;
    show(false);
    if (audOK) startAudio(); else silent();
  }
  function stop() { playing = false; gen++; clearTimeout(timer); cancelAnimationFrame(raf); aud.pause(); bar(); }
  function finish() {
    done.add(L[li].id); store.set('done', [...done]); buildToc();
    if (autoNext && li < L.length - 1) { go(li + 1, true); return; }
    stop(); toast('강의를 끝까지 들었습니다');
  }
  function seek(nk, anim) {
    $('bigplay').hidden = true;
    nk = Math.max(0, Math.min(L[li].scenes.length - 1, nk));
    const adj = Math.abs(nk - k) === 1; k = nk;
    if (playing) { if (audOK) { show(adj); startAudio(); } else silent(); }
    else { show(anim && adj); const tm = T()[k]; if (tm) { seekAudio(tm[0] + 0.001); progress(tm[0]); } }
  }

  /* ---------- 모션: 같은 키끼리 이어서 움직이기 ---------- */
  function snap(e) { const cs = getComputedStyle(e); return { background: cs.backgroundColor, border: cs.border, borderRadius: cs.borderRadius, color: cs.color, font: cs.font, display: 'flex', alignItems: 'center', justifyContent: 'center' }; }
  /* SVG 도형은 좌표 숫자를 그대로 보간(곡선 이동, 점 이동, 화살표 늘어남) */
  const SVG_ATTRS = ['d', 'cx', 'cy', 'r', 'x', 'y', 'x1', 'y1', 'x2', 'y2', 'width', 'height', 'points'];
  const NUM = /-?\d*\.?\d+(?:e-?\d+)?/gi;
  function tweenAttrs(el, from, to, ms) {
    const plan = [];
    for (const a in to) {
      if (from[a] == null || from[a] === to[a]) continue;
      const fa = from[a].match(NUM) || [], ta = to[a].match(NUM) || [];
      if (fa.length !== ta.length || !ta.length) continue;
      const parts = to[a].split(NUM);
      plan.push([a, parts, fa.map(Number), ta.map(Number)]);
    }
    if (!plan.length) return;
    const t0 = performance.now();
    const step = now => {
      let u = Math.min(1, (now - t0) / ms); const e = 1 - Math.pow(1 - u, 3);
      plan.forEach(([a, parts, f, t]) => { let o = parts[0]; for (let k = 0; k < t.length; k++) o += (+(f[k] + (t[k] - f[k]) * e).toFixed(2)) + parts[k + 1]; el.setAttribute(a, o); });
      if (u < 1) requestAnimationFrame(step);
    };
    plan.forEach(([a, parts, f]) => { let o = parts[0]; for (let k = 0; k < f.length; k++) o += f[k] + parts[k + 1]; el.setAttribute(a, o); });
    requestAnimationFrame(step);
  }
  const attrsOf = e => { const o = {}; SVG_ATTRS.forEach(a => { if (e.hasAttribute(a)) o[a] = e.getAttribute(a); }); return o; };
  function morph(box, html, anim) {
    if (!anim || reduced) { box.innerHTML = html; enter(box); return; }
    const bb = box.getBoundingClientRect(), old = new Map();
    box.querySelectorAll('[data-k]').forEach(e => old.set(e.dataset.k, { r: e.getBoundingClientRect(), t: e.textContent, c: e.className && e.className.baseVal != null ? e.className.baseVal : e.className, el: e, st: e instanceof SVGElement ? null : snap(e), svg: e instanceof SVGElement && e.tagName !== 'svg' ? attrsOf(e) : null, tf: e.dataset.tf }));
    box.innerHTML = html;
    const kept = new Set();
    box.querySelectorAll('[data-k]').forEach(e => {
      const key = e.dataset.k, o = old.get(key), r = e.getBoundingClientRect();
      const isSvg = e instanceof SVGElement && e.tagName !== 'svg';
      if (isSvg) {
        if (o && o.svg) { kept.add(key); tweenAttrs(e, o.svg, attrsOf(e), 750); }
        else if (e.dataset.grow && e.hasAttribute('x2')) { const to = attrsOf(e); tweenAttrs(e, Object.assign({}, to, { x2: to.x1, y2: to.y1 }), to, 800); }
        else e.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 500, easing: EASE });
        return;
      }
      if (e.dataset.tf) {
        if (o) { kept.add(key); if (o.tf && o.tf !== e.dataset.tf) { const [ft, fo] = o.tf.split('|'), [tt, to] = e.dataset.tf.split('|'); e.animate([{ transform: ft, transformOrigin: fo }, { transform: tt, transformOrigin: to }], { duration: 900, easing: EASE }); } }
        return;
      }
      if (!o) {
        const fr = e.dataset.from && old.get(e.dataset.from);
        if (fr) e.animate([{ transform: `translate(${fr.r.left - r.left}px,${fr.r.top - r.top}px) scale(1.2)`, opacity: .5 }, { transform: 'none', opacity: 1 }], { duration: 750, easing: EASE });
        else e.animate([{ opacity: 0, transform: 'scale(.5) translateY(10px)' }, { opacity: 1, transform: 'none' }], { duration: 480, easing: EASE });
        return;
      }
      kept.add(key);
      if (e.closest('.vimg-in') && e.classList.contains('spot')) { if (o.c !== e.className) e.animate([{ transform: 'translate(-50%,-50%) scale(1.5)' }, { transform: 'translate(-50%,-50%)' }], { duration: 450, easing: EASE }); return; }
      const dx = o.r.left - r.left, dy = o.r.top - r.top, sx = e.dataset.kz && r.width > 0 ? o.r.width / r.width : 1;
      if (Math.abs(dx) > .5 || Math.abs(dy) > .5 || Math.abs(sx - 1) > .01) e.animate([{ transformOrigin: 'left center', transform: `translate(${dx}px,${dy}px) scaleX(${sx})` }, { transformOrigin: 'left center', transform: 'none' }], { duration: 650, easing: EASE });
      else if (o.t !== e.textContent && e.dataset.from && old.get(e.dataset.from)) { const fr = old.get(e.dataset.from); e.animate([{ transform: `translate(${fr.r.left - r.left}px,${fr.r.top - r.top}px) scale(1.25)`, opacity: .4 }, { transform: 'none', opacity: 1 }], { duration: 750, easing: EASE }); }
      else if (o.t !== e.textContent) { if (r.width > 180) e.animate([{ opacity: .2 }, { opacity: 1 }], { duration: 450 }); else e.animate([{ transform: 'scale(1.4)', filter: 'brightness(1.4)' }, { transform: 'none', filter: 'none' }], { duration: 520, easing: EASE }); }
      else if (o.c !== e.className) e.animate([{ transform: 'scale(1.1)' }, { transform: 'none' }], { duration: 380, easing: EASE });
    });
    old.forEach((o, key) => {
      if (kept.has(key) || !o.r.width || !o.st) return;
      if (o.el.closest('.vimg-in')) return;
      const par = o.el.parentElement && o.el.parentElement.closest('[data-k]');
      if (par && old.has(par.dataset.k) && !kept.has(par.dataset.k)) return;
      const g = document.createElement('div'); g.className = 'ghost'; g.innerHTML = o.el.innerHTML;
      Object.assign(g.style, o.st, { position: 'absolute', left: (o.r.left - bb.left + box.scrollLeft) + 'px', top: (o.r.top - bb.top + box.scrollTop) + 'px', width: o.r.width + 'px', height: o.r.height + 'px' });
      box.appendChild(g);
      g.animate([{ opacity: 1, transform: 'none' }, { opacity: 0, transform: 'translateY(-16px) scale(.7)' }], { duration: 500, easing: EASE }).onfinish = () => g.remove();
    });
    box.querySelectorAll('.wboard, .verr, .veq, .wret').forEach(el => { if (!old.has(el.dataset.k || '')) stagger(el); });
  }
  function stagger(root) {
    if (reduced) return;
    const els = root.querySelectorAll(':scope .vcard, :scope .vf-b, :scope .vf-a, :scope tbody tr, :scope .vbar-r, :scope .vch .vf-b, :scope td[data-k]');
    const gap = Math.min(110, 900 / Math.max(1, els.length));
    els.forEach((e, n) => e.animate([{ opacity: 0, transform: 'translateY(10px)' }, { opacity: 1, transform: 'none' }], { duration: 420, delay: 80 + n * gap, easing: EASE, fill: 'backwards' }));
  }
  function enter(box) { if (!reduced) box.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 300 }); }

  /* ---------- 장면 그리기 ---------- */
  function codeHtml(src, lang) { return src.split('\n').map((ln, n) => `<span class="ln" data-ln="${n + 1}"><i>${n + 1}</i>${hlLine(ln, lang) || ' '}</span>`).join(''); }
  function show(anim) {
    const les = L[li], sc = les.scenes[k];
    if (!sc) return;
    const first = shownK < 0;
    // 핵심 문구
    const headHtml = showText(sc.head || '');
    if ($('stHead').dataset.raw !== sc.head) {
      $('stHead').innerHTML = headHtml; $('stHead').dataset.raw = sc.head;
      if (anim && !reduced) $('stHead').animate([{ opacity: 0, transform: 'translateY(8px)' }, { opacity: 1, transform: 'none' }], { duration: 380, easing: EASE });
    }
    $('stSec').textContent = sc.secName || '';
    $('stCnt').textContent = `${k + 1} / ${les.scenes.length}`;
    // 코드
    const body = $('stBody');
    body.classList.toggle('nocode', sc.code < 0);
    if (sc.code >= 0 && shownCode !== sc.code) {
      $('code').innerHTML = codeHtml(les.codes[sc.code].src, les.codes[sc.code].lang || COURSE.code_lang); $('code').classList.toggle('prose', /^(text|plain|en|ko)$/.test(les.codes[sc.code].lang || '')); shownCode = sc.code;
      if (!first && !reduced) $('code').animate([{ opacity: 0, transform: 'translateX(-12px)' }, { opacity: 1, transform: 'none' }], { duration: 420, easing: EASE });
    } else if (sc.code < 0) shownCode = -1;
    $('code').classList.toggle('focus', sc.lines.length > 0);
    $('code').querySelectorAll('.ln').forEach(el => el.classList.toggle('on', sc.lines.includes(+el.dataset.ln)));
    const on = $('code').querySelector('.ln.on');
    if (on) { const pane = $('code'); const top = on.offsetTop - pane.clientHeight * 0.3; if (on.offsetTop < pane.scrollTop || on.offsetTop + on.offsetHeight > pane.scrollTop + pane.clientHeight) pane.scrollTo({ top: Math.max(0, top), behavior: anim && !reduced ? 'smooth' : 'auto' }); }
    // 메모리 그림
    morph($('viz'), sc.viz, anim && shownK >= 0);
    shownK = k;
    // 대본 · 목차 · 타임라인
    const sl = $('script').querySelectorAll('.sl');
    sl.forEach((el, n) => { el.classList.toggle('cur', n === k); el.classList.toggle('past', n < k); });
    const cur = sl[k];
    if (cur && !$('app').classList.contains('no-scr')) { const box = $('script'); const r = cur.getBoundingClientRect(), b = box.getBoundingClientRect(); if (r.top < b.top + 30 || r.bottom > b.bottom - 30) cur.scrollIntoView({ block: 'center', behavior: reduced ? 'auto' : 'smooth' }); }
    $('toc').querySelectorAll('.sec').forEach(el => el.classList.toggle('cur', el.dataset.name === sc.secName));
    if (!playing) progress(T()[k] ? T()[k][0] : 0);
    bar();
  }
  function progress(t) {
    const tm = T(); const total = tm.length ? tm[tm.length - 1][1] : 0;
    $('tl').querySelectorAll('.tl-seg').forEach((el, n) => {
      const [a, b] = tm[n] || [0, 0];
      el.classList.toggle('past', t >= b);
      el.firstChild.style.width = t >= b ? '100%' : t > a ? ((t - a) / (b - a) * 100) + '%' : '0%';
    });
    const f = s => `${Math.floor(s / 60)}:${pad(Math.floor(s % 60))}`;
    $('tlTime').textContent = `${f(Math.min(t, total))} / ${f(total)}`;
  }
  function buildLesson() {
    const les = L[li];
    let h = '', sec = null;
    les.scenes.forEach((s, n) => {
      if (s.sec) h += `<div class="s-sec">${esc(s.sec)}</div>`;
      h += `<button class="sl" data-k="${n}">${s.html}</button>`;
    });
    $('script').innerHTML = h;
    $('script').querySelectorAll('.sl').forEach(el => el.addEventListener('click', () => { seek(+el.dataset.k, false); if (!playing) play(); closeOverlays(); }));
    const tm = T();
    $('tl').innerHTML = les.scenes.map((s, n) => `<div class="tl-seg${s.sec && n ? ' sec0' : ''}" data-k="${n}" style="flex-grow:${tm[n] ? Math.max(.3, tm[n][1] - tm[n][0]) : 1}" title="${esc(s.secName || '')}"><i></i></div>`).join('');
    $('tl').querySelectorAll('.tl-seg').forEach(el => el.addEventListener('click', () => seek(+el.dataset.k, false)));
    $('lno').textContent = pad(les.id); $('ltitle').textContent = les.title; $('lsub').textContent = les.sub;
    document.title = `${pad(les.id)} ${les.title} · ${COURSE.title}`;
    $('bigLabel').textContent = `${pad(les.id)}강 ${les.title} 재생`;
    shownK = -1; shownCode = -2; $('stHead').dataset.raw = '';
  }
  function buildToc() {
    let h = '', grp = '';
    L.forEach((les, n) => {
      if (les.group !== grp) { grp = les.group; h += `<div class="grp">${esc(grp)}</div>`; }
      const tm = (TIMING[les.id] || [[]])[0], dur = tm.length ? tm[tm.length - 1][1] : 0;
      h += `<button class="les${n === li ? ' cur' : ''}${done.has(les.id) ? ' done' : ''}" data-i="${n}"><span class="n">${pad(les.id)}</span><span class="t">${esc(les.title)}</span><span class="m">${Math.round(dur / 60)}분</span></button>`;
      if (n === li) {
        const secs = []; les.scenes.forEach((s, q) => { if (s.sec) secs.push([s.sec, q]); });
        h += `<div class="secs">${secs.map(([s, q]) => `<button class="sec" data-k="${q}" data-name="${esc(s)}">${esc(s)}</button>`).join('')}</div>`;
      }
    });
    $('toc').innerHTML = h;
    $('toc').querySelectorAll('.les').forEach(b => b.addEventListener('click', () => { if (+b.dataset.i !== li) go(+b.dataset.i, playing); closeOverlays(); }));
    $('toc').querySelectorAll('.sec').forEach(b => b.addEventListener('click', () => { seek(+b.dataset.k, false); closeOverlays(); }));
  }
  function go(i, autoplay) {
    stop(); li = Math.max(0, Math.min(L.length - 1, i)); k = 0; store.set('li', li);
    buildLesson(); buildToc(); loadAudio(); show(false); progress(0);
    $('bigplay').hidden = !!autoplay;
    if (autoplay) play();
  }
  function bar() {
    $('playIco').innerHTML = playing ? '<path d="M7 5h4v14H7zm6 0h4v14h-4z"/>' : '<path d="M8 5v14l11-7z"/>';
    $('play').setAttribute('aria-label', playing ? '일시정지' : '재생');
    $('prevL').disabled = li === 0; $('nextL').disabled = li === L.length - 1;
    $('idxBtn').classList.toggle('on', !$('app').classList.contains('no-idx'));
    $('scrBtn').classList.toggle('on', !$('app').classList.contains('no-scr'));
  }

  /* ---------- 패널 접기 ---------- */
  function setPanel(cls, open) {
    $('app').classList.toggle(cls, !open);
    if (!narrow()) store.set(cls, !open);
    $('scrim').hidden = !(narrow() && (!$('app').classList.contains('no-idx') || !$('app').classList.contains('no-scr')));
    bar();
    if (cls === 'no-scr' && open) setTimeout(() => { const c = $('script').querySelector('.sl.cur'); if (c) c.scrollIntoView({ block: 'center' }); }, 300);
  }
  function closeOverlays() { if (narrow()) { $('app').classList.add('no-idx', 'no-scr'); $('scrim').hidden = true; bar(); } }
  function initPanels() {
    if (narrow()) { $('app').classList.add('no-idx', 'no-scr'); }
    else { $('app').classList.toggle('no-idx', store.get('no-idx', false)); $('app').classList.toggle('no-scr', store.get('no-scr', false)); }
  }
  $('idxBtn').addEventListener('click', () => { const open = $('app').classList.contains('no-idx'); if (narrow() && open) $('app').classList.add('no-scr'); setPanel('no-idx', open); });
  $('scrBtn').addEventListener('click', () => { const open = $('app').classList.contains('no-scr'); if (narrow() && open) $('app').classList.add('no-idx'); setPanel('no-scr', open); });
  $('idxClose').addEventListener('click', () => setPanel('no-idx', false));
  $('scrClose').addEventListener('click', () => setPanel('no-scr', false));
  $('scrim').addEventListener('click', closeOverlays);

  let toastT = null;
  function toast(t) { const el = $('toast'); el.textContent = t; el.hidden = false; clearTimeout(toastT); toastT = setTimeout(() => { el.hidden = true; }, 2400); }

  /* ---------- 이벤트 ---------- */
  $('play').addEventListener('click', () => playing ? stop() : play());
  $('bigplay').addEventListener('click', play);
  $('prevS').addEventListener('click', () => seek(k - 1, true));
  $('nextS').addEventListener('click', () => seek(k + 1, true));
  $('prevL').addEventListener('click', () => go(li - 1, playing));
  $('nextL').addEventListener('click', () => go(li + 1, playing));
  const rs = $('rate'); rs.value = String(rate); if (!rs.value) { rate = 1; rs.value = '1'; }
  rs.addEventListener('change', () => { rate = parseFloat(rs.value); store.set('rate', rate); aud.playbackRate = rate; });
  $('autoChk').checked = autoNext;
  $('autoChk').addEventListener('change', e => { autoNext = e.target.checked; store.set('auto', autoNext); });
  addEventListener('keydown', e => {
    if (e.target.closest && e.target.closest('input, select, textarea')) return;
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.key === ' ') { e.preventDefault(); playing ? stop() : play(); }
    else if (e.key === 'ArrowRight') { e.preventDefault(); seek(k + 1, true); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); seek(k - 1, true); }
    else if (e.key === ']') go(li + 1, playing);
    else if (e.key === '[') go(li - 1, playing);
    else if (e.key === 'Escape') closeOverlays();
  });
  addEventListener('hashchange', () => { const m = (location.hash || '').match(/^#l(\d+)$/); if (m && +m[1] - 1 !== li) go(+m[1] - 1, false); });
  let wasNarrow = narrow();
  addEventListener('resize', () => { if (narrow() !== wasNarrow) { wasNarrow = narrow(); initPanels(); $('scrim').hidden = true; bar(); } });

  const h = (location.hash || '').match(/^#l(\d+)$/);
  if (h) li = Math.max(0, Math.min(L.length - 1, +h[1] - 1));
  initPanels();
  go(li, false);
})();
