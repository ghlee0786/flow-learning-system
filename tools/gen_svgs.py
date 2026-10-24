"""README용 움직이는 SVG 인포그래픽 생성기 (SMIL 애니메이션: GitHub README에서 재생됨)."""
from pathlib import Path
OUT = Path(__file__).resolve().parent.parent / "docs" / "media"
SANS = "'Pretendard','Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR',sans-serif"
MONO = "Consolas,'JetBrains Mono','D2Coding',monospace"
BG, PANEL, EDGE, INK, MUTED = "#0F161E", "#18222C", "#2D3A46", "#E5ECF0", "#8FA0AC"
AMBER, GREEN, VIOLET, BLUE, RED, TEAL = "#F2C14E", "#3FBF84", "#B385EE", "#5E9BF0", "#EF6F5E", "#3FC1B0"


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{title}">'
            f'<title>{title}</title><rect width="{w}" height="{h}" rx="18" fill="{BG}"/>{body}</svg>\n')


def t(x, y, s, size=14, fill=INK, weight=400, anchor="start", font=SANS, extra=""):
    return f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {extra}>{s}</text>'


def vis(key_times, values, dur, attr="opacity"):
    return f'<animate attributeName="{attr}" dur="{dur}s" repeatCount="indefinite" keyTimes="{key_times}" values="{values}" calcMode="discrete"/>'


# ---------- 1. 음성과 장면의 동기화 ----------
def sync():
    W, H, D = 960, 430, 9.0
    segs = [(0.0, 2.6), (3.0, 5.6), (6.0, 8.6)]
    cols = [BLUE, VIOLET, GREEN]
    heads = ["new int[5] → 0으로 채운 5칸", "arr[0] = 0 + 1", "arr[1] = 1 + 1"]
    lines = [1, 3, 3]
    script = [["new int[5]는 정수 칸 다섯 개", "짜리 배열을 새로 만듭니다."], ["i가 0일 때, i 더하기 1인 1을", "0번 칸에 넣습니다."], ["i가 1이면 1번 칸에", "2가 들어갑니다."]]
    cells = [[0, 0, 0, 0, 0], [1, 0, 0, 0, 0], [1, 2, 0, 0, 0]]
    b = t(28, 40, "음성이 문장을 읽기 시작하는 순간 = 장면이 바뀌는 순간", 19, INK, 700)
    # 무대
    b += f'<rect x="28" y="60" width="600" height="230" rx="14" fill="{PANEL}" stroke="{EDGE}"/>'
    b += t(46, 84, "무대", 12, AMBER, 700)
    code = ["int[] arr = new int[5];", "for (int i = 0; i &lt; 5; i++)", "    arr[i] = i + 1;"]
    for k, (s, e) in enumerate(segs):
        st, en = s / D, (segs[k + 1][0] / D if k < 2 else 1.0)
        kt = f"0;{st:.4f};{en:.4f};1" if st > 0 else f"0;{en:.4f};1"
        vv = "0;1;0;0" if st > 0 else "1;0;0"
        g = t(46, 116, heads[k], 21, INK, 700)
        for i, ln in enumerate(code):
            y = 150 + i * 26
            on = (i + 1) == lines[k]
            if on:
                g += f'<rect x="46" y="{y - 18}" width="270" height="25" fill="{AMBER}" fill-opacity=".16"/><rect x="46" y="{y - 18}" width="4" height="25" fill="{AMBER}"/>'
            g += t(58, y, ln, 13.5, INK if on else MUTED, 400, font=MONO)
        for c, v in enumerate(cells[k]):
            x = 352 + c * 50
            changed = k > 0 and c == k - 1
            fill = "#12382A" if changed else "#1D2833"
            stroke = GREEN if changed else EDGE
            g += f'<rect x="{x}" y="150" width="42" height="42" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>' + t(x + 21, 177, v, 17, INK, 700, "middle", MONO) + t(x + 21, 210, c, 11, MUTED, 400, "middle", MONO)
        g += t(352, 140, "arr", 12, MUTED)
        b += f'<g opacity="{1 if st == 0 else 0}">{vis(kt, vv, D)}{g}</g>'
    # 대본 패널
    b += f'<rect x="648" y="60" width="284" height="230" rx="14" fill="{PANEL}" stroke="{EDGE}"/>' + t(666, 84, "대본 (오른쪽 1/5)", 12, VIOLET, 700)
    for k, s in enumerate(script):
        y = 104 + k * 60
        st, en = segs[k][0] / D, (segs[k + 1][0] / D if k < 2 else 1.0)
        kt = f"0;{st:.4f};{en:.4f};1" if st > 0 else f"0;{en:.4f};1"
        vv = "0;1;0;0" if st > 0 else "1;0;0"
        b += f'<rect x="660" y="{y}" width="260" height="50" rx="8" fill="{VIOLET}" fill-opacity=".22" opacity="{1 if st == 0 else 0}">{vis(kt, vv, D)}</rect>'
        b += t(670, y + 21, s[0], 13, INK) + t(670, y + 40, s[1], 13, INK)
    # 타임라인
    y0, x0, x1 = 330, 28, 932
    sx = lambda s: x0 + (x1 - x0) * s / D
    b += t(28, 318, "녹음된 음성 (문장마다 시작·끝 시각을 기록)", 12, MUTED)
    import random
    random.seed(7)
    for k, (s, e) in enumerate(segs):
        b += f'<rect x="{sx(s):.1f}" y="{y0}" width="{sx(e) - sx(s):.1f}" height="46" rx="6" fill="{cols[k]}" fill-opacity=".12"/>'
        x = sx(s) + 4
        while x < sx(e) - 4:
            h = random.uniform(6, 38)
            b += f'<rect x="{x:.1f}" y="{y0 + 23 - h / 2:.1f}" width="3" height="{h:.1f}" rx="1.5" fill="{cols[k]}"/>'
            x += 6
        b += t(sx(s), y0 + 66, f"문장 {k + 1} · {s:.1f}초", 12, cols[k], 700)
        b += f'<line x1="{sx(s):.1f}" y1="{y0 - 8}" x2="{sx(s):.1f}" y2="{y0 + 52}" stroke="{cols[k]}" stroke-dasharray="3 3"/>'
    b += (f'<g><line x1="{x0}" y1="{y0 - 14}" x2="{x0}" y2="{y0 + 58}" stroke="{AMBER}" stroke-width="2.5"/>'
          f'<circle cx="{x0}" cy="{y0 - 14}" r="6" fill="{AMBER}"/>'
          f'<animateTransform attributeName="transform" type="translate" from="0 0" to="{x1 - x0} 0" dur="{D}s" repeatCount="indefinite"/></g>')
    return svg(W, H, b, "음성과 장면의 동기화")


# ---------- 2. 값이 날아가 바뀌는 모션 ----------
def morph():
    W, H, D = 960, 300, 9.0
    arr, n = [1, 2, 3, 4, 5], 5
    b = t(28, 40, "모션 규칙: 같은 이름의 요소는 이어서 움직이고, 값은 출발 칸에서 날아온다", 19, INK, 700)
    ax, ay, bx, by = 120, 90, 120, 200
    b += t(28, ay + 28, "arr", 15, MUTED, 600, font=MONO) + t(28, by + 28, "answer", 15, MUTED, 600, font=MONO)
    for c in range(n):
        b += f'<rect x="{ax + c * 64}" y="{ay}" width="52" height="44" rx="9" fill="#1D2833" stroke="{EDGE}" stroke-width="1.5"/>' + t(ax + c * 64 + 26, ay + 29, arr[c], 18, INK, 700, "middle", MONO)
        b += t(bx + c * 64 + 26, by + 64, c, 11, MUTED, 400, "middle", MONO)
    step = D / (n + 1)
    for i in range(n):
        to = (i + 2) % n
        t0, t1 = (i + 0.4) * step / D, (i + 0.9) * step / D
        # 받는 칸: 0 → 값, 초록
        cx = bx + to * 64
        b += f'<rect x="{cx}" y="{by}" width="52" height="44" rx="9" fill="#1D2833" stroke="{EDGE}" stroke-width="1.5"><animate attributeName="fill" dur="{D}s" repeatCount="indefinite" keyTimes="0;{t1:.4f};{min(t1 + .06, .99):.4f};1" values="#1D2833;#1D2833;#12382A;#12382A" calcMode="discrete"/><animate attributeName="stroke" dur="{D}s" repeatCount="indefinite" keyTimes="0;{t1:.4f};1" values="{EDGE};{GREEN};{GREEN}" calcMode="discrete"/></rect>'
        b += f'<text x="{cx + 26}" y="{by + 29}" font-family="{MONO}" font-size="18" font-weight="700" fill="{MUTED}" text-anchor="middle">0{vis(f"0;{t1:.4f};1", "1;0;0", D)}</text>'
        # 날아가는 값
        dx, dy = (bx + to * 64) - (ax + i * 64), by - ay
        b += (f'<g opacity="0">{vis(f"0;{t0:.4f};1", "0;1;1", D)}'
              f'<text x="{ax + i * 64 + 26}" y="{ay + 29}" font-family="{MONO}" font-size="18" font-weight="700" fill="{GREEN}" text-anchor="middle">{arr[i]}</text>'
              f'<animateTransform attributeName="transform" type="translate" dur="{D}s" repeatCount="indefinite" keyTimes="0;{t0:.4f};{t1:.4f};1" values="0 0;0 0;{dx} {dy};{dx} {dy}" calcMode="spline" keySplines="0 0 1 1;.2 .8 .2 1;0 0 1 1"/></g>')
    # 포인터 i
    kts = ";".join(f"{(i + 0.15) * step / D:.4f}" for i in range(n))
    vals = ";".join(f"{i * 64} 0" for i in range(n))
    b += (f'<g>{t(ax + 26, ay - 12, "i ▾", 13, AMBER, 700, "middle", MONO)}'
          f'<animateTransform attributeName="transform" type="translate" dur="{D}s" repeatCount="indefinite" keyTimes="0;{kts};1" values="0 0;{vals};{(n - 1) * 64} 0" calcMode="spline" keySplines="{";".join([".2 .8 .2 1"] * (n + 1))}"/></g>')
    b += t(500, 112, "for (int i = 0; i &lt; n; i++)", 14, MUTED, 400, font=MONO)
    b += t(500, 136, "    answer[(i + k) % n] = arr[i];", 14, INK, 400, font=MONO)
    b += f'<rect x="496" y="120" width="320" height="24" fill="{AMBER}" fill-opacity=".14"/><rect x="496" y="120" width="4" height="24" fill="{AMBER}"/>'
    legend = [("미끄러짐", "같은 이름 → 새 위치", AMBER), ("날아옴", "출발 칸 → 도착 칸", GREEN), ("깜빡임", "값만 바뀐 상자", BLUE), ("흩어짐", "사라진 요소", RED)]
    for k, (a, d, c) in enumerate(legend):
        x = 500 + (k % 2) * 228
        y = 196 + (k // 2) * 40
        b += f'<circle cx="{x + 6}" cy="{y - 5}" r="6" fill="{c}"/>' + t(x + 20, y, a, 14, INK, 700) + t(x + 84, y, d, 12, MUTED)
    return svg(W, H, b, "값이 날아가 바뀌는 모션")


# ---------- 3. 3단 화면: 목차·대본 접기 ----------
def layout():
    W, H, D = 960, 330, 8.0
    b = t(28, 40, "목차와 대본은 접고, 무대(모션 그래픽)가 가운데를 넓게", 19, INK, 700)
    y, h = 64, 236
    kt = "0;0.2;0.32;0.48;0.6;0.8;0.92;1"
    spl = ";".join([".4 0 .2 1"] * 7)
    # 목차
    iw = "200;200;0;0;0;0;200;200"
    b += f'<rect x="28" y="{y}" width="200" height="{h}" rx="12" fill="{PANEL}" stroke="{EDGE}"><animate attributeName="width" dur="{D}s" repeatCount="indefinite" keyTimes="{kt}" values="{iw}" calcMode="spline" keySplines="{spl}"/></rect>'
    idx = f'<g>{vis("0;0.22;0.9;1", "1;0;1;1", D)}' + t(44, y + 28, "목차", 13, MUTED, 700)
    for k, s in enumerate(["01 답안의 뼈대", "02 변수와 자료형", "06 반복문", "07 배열", "13 Dictionary"]):
        on = k == 3
        if on:
            idx += f'<rect x="38" y="{y + 44 + k * 34}" width="180" height="28" rx="7" fill="{VIOLET}" fill-opacity=".25"/>'
        idx += t(48, y + 63 + k * 34, s, 13, INK if on else MUTED, 600 if on else 400)
    b += idx + "</g>"
    # 대본
    sx = "742;742;742;742;932;932;742;742"
    sw = "190;190;190;190;0;0;190;190"
    b += f'<rect x="742" y="{y}" width="190" height="{h}" rx="12" fill="{PANEL}" stroke="{EDGE}"><animate attributeName="x" dur="{D}s" repeatCount="indefinite" keyTimes="{kt}" values="{sx}" calcMode="spline" keySplines="{spl}"/><animate attributeName="width" dur="{D}s" repeatCount="indefinite" keyTimes="{kt}" values="{sw}" calcMode="spline" keySplines="{spl}"/></rect>'
    scr = f'<g>{vis("0;0.5;0.9;1", "1;0;1;1", D)}' + t(758, y + 28, "대본", 13, MUTED, 700)
    for k in range(5):
        on = k == 2
        scr += f'<rect x="754" y="{y + 44 + k * 36}" width="166" height="28" rx="7" fill="{VIOLET if on else EDGE}" fill-opacity="{.3 if on else .5}"/>'
    b += scr + "</g>"
    # 무대
    stx = "240;240;40;40;40;40;240;240"
    stw = "490;490;690;690;880;880;490;490"
    b += f'<rect x="240" y="{y}" width="490" height="{h}" rx="14" fill="#0B1218" stroke="{AMBER}" stroke-width="1.5"><animate attributeName="x" dur="{D}s" repeatCount="indefinite" keyTimes="{kt}" values="{stx}" calcMode="spline" keySplines="{spl}"/><animate attributeName="width" dur="{D}s" repeatCount="indefinite" keyTimes="{kt}" values="{stw}" calcMode="spline" keySplines="{spl}"/></rect>'
    cx = "485;485;385;385;480;480;485;485"
    g = t(0, y + 48, "무대 · 모션 그래픽", 15, AMBER, 700, "middle") + t(0, y + 84, "arr[2] = 2 + 1", 22, INK, 700, "middle")
    for c, v in enumerate([1, 2, 3, 0, 0]):
        g += f'<rect x="{-130 + c * 54}" y="{y + 110}" width="44" height="44" rx="8" fill="{"#12382A" if c == 2 else "#1D2833"}" stroke="{GREEN if c == 2 else EDGE}" stroke-width="1.5"/>' + t(-108 + c * 54, y + 139, v, 18, INK, 700, "middle", MONO)
    g += t(0, y + 200, "← 접기 ·  ·  · 펴기 →", 12, MUTED, 400, "middle")
    b += f'<g>{g}<animateTransform attributeName="transform" type="translate" dur="{D}s" repeatCount="indefinite" keyTimes="{kt}" values="{cx.replace(";", " 0;")} 0" calcMode="spline" keySplines="{spl}"/></g>'
    return svg(W, H, b, "3단 화면 구성")


# ---------- 4. 작업 흐름 ----------
def pipeline():
    W, H, D = 960, 250, 7.0
    nodes = [("3D 렌더", "render_3d", RED), ("레슨 JSON", "lesson_save", BLUE), ("형식 검사", "lesson_validate", VIOLET), ("코드 실행", "code_verify", TEAL),
             ("TTS 녹음", "audio_synthesize", AMBER), ("빌드", "course_build", GREEN), ("교재", "index.html", INK)]
    b = t(28, 40, "AI가 MCP 도구로 교재를 만드는 흐름 (어떤 과목이든)", 19, INK, 700)
    xs = [78 + i * 134 for i in range(7)]
    y = 130
    b += f'<path d="M{xs[0]} {y} H{xs[-1]}" stroke="{EDGE}" stroke-width="3" fill="none"/>'
    for i, (a, tool, c) in enumerate(nodes):
        t0 = i / 7
        b += (f'<circle cx="{xs[i]}" cy="{y}" r="34" fill="{PANEL}" stroke="{c}" stroke-width="2.5">'
              f'<animate attributeName="r" dur="{D}s" repeatCount="indefinite" keyTimes="0;{t0:.3f};{t0 + .05:.3f};{t0 + .12:.3f};1" values="34;34;40;34;34"/></circle>')
        b += f'<circle cx="{xs[i]}" cy="{y}" r="34" fill="{c}" opacity="0">{vis(f"0;{t0:.3f};{t0 + .14:.3f};1", "0;.28;0;0", D)}</circle>'
        b += t(xs[i], y + 6, i + 1, 20, c, 700, "middle", MONO)
        b += t(xs[i], y + 62, a, 15, INK, 700, "middle") + t(xs[i], y + 84, tool, 11.5, MUTED, 400, "middle", MONO)
    b += (f'<circle r="8" fill="{AMBER}"><animateMotion dur="{D}s" repeatCount="indefinite" path="M{xs[0]} {y} H{xs[-1]}" '
          f'keyTimes="0;1" keyPoints="0;1" calcMode="linear"/></circle>')
    b += t(480, 236, "3D 렌더는 필요할 때만 · speech_preview로 읽기 확인 · 코드가 없는 과목은 코드 실행을 건너뜀", 12.5, MUTED, 400, "middle")
    return svg(W, H, b, "작업 흐름")


# ---------- 5. 레슨 하나의 해부도 ----------
def anatomy():
    W, H = 960, 470
    b = t(28, 40, "JSON op → 무대의 어디에 나타나나", 19, INK, 700)
    ops = [('{"op":"part", "title":"배열 만들고 채우기"}', VIOLET, "소단원 · 목차"),
           ('{"op":"code", "src":"int[] arr = new int[5]; …"}', TEAL, "코드 칸"),
           ('{"op":"array", "name":"arr", "values":[0,0,0,0,0]}', BLUE, "메모리 그림"),
           ('{"op":"var", "name":"i", "value":0, "type":"int"}', BLUE, "변수 상자"),
           ('{"op":"out", "text":"6"}', GREEN, "콘솔 출력"),
           ('{"op":"say", "line":3, "head":"arr[0] = 0 + 1",', AMBER, "장면 1개"),
           ('        "text":"i가 0일 때 1을 0번 칸에…"}', AMBER, "대본 + 음성")]
    b += f'<rect x="28" y="62" width="452" height="380" rx="14" fill="{PANEL}" stroke="{EDGE}"/>' + t(46, 88, "lessons/07.json", 12, MUTED, 700, font=MONO)
    for k, (s, c, _) in enumerate(ops):
        yy = 122 + k * 44
        b += f'<rect x="40" y="{yy - 20}" width="4" height="28" fill="{c}"/>' + t(54, yy, s.replace("<", "&lt;"), 12, INK, 400, font=MONO)
    # 무대
    sx, sy = 540, 62
    b += f'<rect x="{sx}" y="{sy}" width="392" height="380" rx="14" fill="#0B1218" stroke="{EDGE}"/>'
    regions = [(sx + 14, sy + 12, 200, 22, VIOLET, "배열 만들고 채우기", 12), (sx + 14, sy + 40, 364, 36, AMBER, "arr[0] = 0 + 1", 19),
               (sx + 14, sy + 88, 170, 110, TEAL, "코드 (3번 줄 강조)", 12), (sx + 196, sy + 88, 182, 50, BLUE, "i = 0", 13),
               (sx + 196, sy + 146, 182, 52, BLUE, "arr [1][0][0][0][0]", 13), (sx + 14, sy + 210, 364, 54, GREEN, "콘솔: 6", 13),
               (sx + 14, sy + 276, 364, 90, AMBER, "대본 패널 강조 + 이 문장의 음성 재생", 12)]
    for k, (x, y, w, h, c, s, fs) in enumerate(regions):
        b += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{c}" fill-opacity=".12" stroke="{c}" stroke-width="1.5"/>' + t(x + 10, y + h / 2 + 5, s, fs, INK, 700 if k == 1 else 400)
    links = [(0, 0), (1, 2), (2, 4), (3, 3), (4, 5), (5, 1), (6, 6)]
    for k, (o, r) in enumerate(links):
        y1 = 122 + o * 44 - 5
        x2, y2 = regions[r][0], regions[r][1] + regions[r][3] / 2
        c = ops[o][1]
        b += (f'<path d="M480 {y1} C510 {y1} 510 {y2} {x2} {y2}" stroke="{c}" stroke-width="2" fill="none" stroke-dasharray="5 5" opacity=".75">'
              f'<animate attributeName="stroke-dashoffset" from="20" to="0" dur="1.2s" repeatCount="indefinite"/></path>')
    return svg(W, H, b, "레슨 해부도")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, f in [("sync", sync), ("morph", morph), ("layout", layout), ("pipeline", pipeline), ("anatomy", anatomy)]:
        (OUT / f"{name}.svg").write_text(f(), encoding="utf-8")
        print(name, (OUT / f"{name}.svg").stat().st_size)
