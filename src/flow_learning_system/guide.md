# 레슨 작성 가이드

교재는 **문장 하나 = 장면 하나**입니다. 레슨은 `ops` 배열로 된 JSON이고,
`say` op 하나가 장면 하나가 됩니다. `say` 앞에 나온 op들이 그 장면의 화면 상태(코드, 변수, 배열, 콘솔 …)를 만들고,
`say`가 그 순간을 문장과 함께 찍어 둡니다. 플레이어는 음성에서 그 문장이 시작되는 순간 장면을 바꿉니다.

## 1. 코스 폴더

```
my-course/
  course.json        제목, 코드 언어, 음성, 레슨 목록, 읽기 규칙
  lessons/01.json    레슨
  audio/, timing.json  (audio_synthesize가 만듦)
```

`course.json`

```json
{
  "title": "C# 문법 모션 교재",
  "subtitle": "코딩 테스트용 C# 17강",
  "code_lang": "csharp",
  "voice": "F1",
  "speed": 1.05,
  "lessons": ["lessons/01.json"],
  "pronunciations": { "Dictionary": "딕셔너리" }
}
```

- `code_lang`: `csharp`, `python`(코드 확인과 색칠에 씀), 코드가 없는 과목은 `text`
- `voice`: Supertonic 음성 `F1`~`F5`, `M1`~`M5`
- `pronunciations`: 영어 단어 → 한글 읽기. 기본 규칙에 없는 단어를 여기에 더합니다.

## 2. 레슨 JSON

```json
{
  "id": 1,
  "group": "기초",
  "title": "변수",
  "sub": "int와 string",
  "ops": [
    {"op": "part", "title": "변수 만들기"},
    {"op": "code", "src": "int age = 25;\nConsole.WriteLine(age);"},
    {"op": "var", "name": "age", "value": 25, "type": "int"},
    {"op": "say", "line": 1, "text": "int age = 25는 정수 상자 age를 만들고 25를 넣습니다.", "head": "변수 = 이름표 붙은 상자"},
    {"op": "out", "text": "25"},
    {"op": "say", "line": 2, "text": "age를 출력하면 25가 나옵니다.", "head": "Console.WriteLine"}
  ]
}
```

## 3. op 목록

| op | 필드 | 하는 일 |
|---|---|---|
| `part` | `title` | 소단원 시작. 목차와 대본에 제목이 생깁니다 |
| `code` | `src`, `wrap?`, `run?`, `test?`, `expect?`, `lang?` | 왼쪽 칸에 보여 줄 코드를 바꿉니다. `lang: "en"`/`"text"`이면 예문·지문처럼 보여 줍니다(`run: false`). 아래 "코드 확인" 참고 |
| `nocode` | | 코드 칸을 숨기고 그림을 가운데에 크게 |
| `use` | `code` | 앞에서 만든 코드 블록(0부터 번호)으로 돌아가기 |
| `var` | `name`, `value`, `type?` | 변수 상자를 만들거나 값 바꾸기. 값이 바뀌면 깜빡입니다 |
| `ref` | `name`, `target`, `type?` | 참조 변수(→ `target` 화살표) |
| `drop` | `names` | 변수 상자 지우기 |
| `array` | `name`, `values`, `tag?`, `title?`, `byVal?`, `idx?` | 배열 칸. `byVal: true`면 값 기준으로 이어져 정렬할 때 칸이 미끄러집니다 |
| `stack` | `name`, `items` | 스택(아래 → 위) |
| `queue` | `name`, `items` | 큐(앞 → 뒤) |
| `dict` | `name`, `pairs` | 사전 `[[키, 값], …]` |
| `set` | `name`, `items` | 집합 |
| `grid` | `name`, `rows`, `g?` | 2차원 격자. `g`에 칸 모양 행렬(`cls`, `txt`)을 줄 수 있습니다 |
| `free` | `names` | 그림 지우기 |
| `out` | `text` | 콘솔에 한 줄 출력(코드 확인 때 기대 출력이 됨) |
| `write` | `text` | 줄을 바꾸지 않는 출력(`Console.Write`) |
| `show_out` | `text` | 화면에만 보이고 코드 확인에서는 빠지는 출력 |
| `table` | `head`, `title?` | 실행 기록 표 시작 |
| `row` | `cells` | 실행 기록 한 줄 추가(최근 6줄만 보임) |
| `board` | `widget` | 장면들에 계속 남는 보조 그림 |
| `clear` | | 변수·그림·콘솔·기록 모두 지우기(새 소단원 시작 때) |
| `say` | `text`, `line?`, `head?`, 그 밖의 장면 옵션 | **장면 하나**를 만듭니다 |

### say 장면 옵션

| 필드 | 예 | 뜻 |
|---|---|---|
| `line` | `3`, `"sum += i"`, `["i++", 2]`, `[2, 4]` | 강조할 코드 줄. 번호, 찾을 글자, `[글자, n번째]`, 또는 그 목록 |
| `head` | `"정수 ÷ 정수 = 몫만"` | 무대 위 큰 핵심 문구. 생략하면 앞 장면 것을 이어 씀 |
| `board` | 위젯 | 이 장면에만 보이는 보조 그림 |
| `eq` | `"17 / 5 = 3"` | 계산식 한 줄 |
| `err` | `"IndexOutOfRangeException: …"` | 빨간 오류 띠 |
| `ret` | `"7"` | `return 7` 표시 |
| `hl` `ok` `bad` `dim` `g1` `g2` `g3` | `{"arr": [0, 2]}` | 그림 이름 → 칸 번호(사전은 키) 색칠. hl 노랑, ok 초록, bad 빨강, dim 흐리게, g1~g3 묶음색 |
| `ptr` | `{"arr": {"0": "left", "4": "right"}}` | 배열 칸 위 화살표 이름표. 이름이 같으면 칸 사이를 미끄러져 이동 |
| `from` | `{"answer": {"3": "waarr:1"}}` | 이 칸의 값이 다른 칸에서 날아오게. 출발 키는 `wa{배열이름}:{칸}`, 격자 값은 `wg{이름}t:{행},{열}` |
| `grid` | `{"g": {"cls": [["hl", ""], ["", "ok"]]}}` | 격자 칸 색(`cls`), 글자(`txt`) 행렬 |
| `hot` / `okv` | `["sum"]` | 변수 상자 강조(노랑 / 초록) |

## 4. 위젯 (과목 공통)

| 위젯 | 인자 | 쓰임 |
|---|---|---|
| `math` | `줄 목록`, `{"hl": [줄], "ok": [줄], "big": true}` | 수식 풀이. `\frac{a}{b}`, `x^2`, `x_1`, `\sqrt{x}`, `\pm`, `\theta`, `\sin`, `\text{글}`, 부분 강조 `\hl{…}` `\ok{…}` `\g1{…}` |
| `plot` | `{xmin, xmax, ymin, ymax, w, h, step, tick, ystep?, ytick?, key, curves, points, segs, labels}` | 좌표평면. `curves: [{"fn": "(x-2)**2+1", "c": "g1", "key": "p"}]` — **같은 key의 곡선은 장면이 바뀔 때 모양이 이어져 변형**(평행이동이 미끄러지듯 보임). 식은 자바스크립트 문법(`x**2`, `sin(x)`, `PI`)이고, 음수 부호 뒤 거듭제곱은 `-((x-1)**2)`처럼 괄호로 감쌉니다. `points`, `segs`(`arrow`, `dash`), `labels` |
| `tokens` | `[[낱말, 역할, 상태], …]`, `{"big": true}` | 문장 성분. 같은 낱말은 자리를 옮겨 미끄러짐(어순 변화, 수동태, 의문문) |
| `img` | `"assets/파일.png"`, `{spots, focus, zoom, arrows, w, cap}` | 그림·3D 렌더. `spots: {"이름": {"label": "핵", "c": "hl"}}`, `focus`+`zoom`으로 확대(장면 사이에 부드럽게), `arrows: [{"from": "a", "to": "b", "label": "mg", "c": "bad"}]`(새 화살표는 늘어나며 등장). 핫스폿 좌표는 `render_3d`가 만들거나 `at: {"이름": [x, y]}`(0~1)로 직접 |
| `svg` | `"<svg …>…</svg>"` | 직접 그린 그림 |

### 프로그래밍·공통 위젯

위젯은 `{"이름": [인자, …]}` 모양이고, 여러 개를 이어 붙일 때는 `{"seq": [위젯, 위젯]}`입니다.
문자열 안에서 `` `코드` ``와 `**굵게**`를 쓸 수 있고, 표 칸 등에 HTML이 필요하면 `{"h": "<code>…</code>"}`를 씁니다.

| 위젯 | 인자 | 예 |
|---|---|---|
| `cards` | `[[제목, 설명, 상태?], …]` | `{"cards": [[["int", "정수", "g1"], ["string", "문자열", "g2"]]]}` |
| `flow` | `[[글자, 상태?], …]`, `{"labels": [화살표 위 글자]}` | `{"flow": [[["\"123\"", "g3"], ["123", "ok"]], {"labels": ["int.Parse"]}]}` |
| `tbl` | `머리줄`, `줄들`, `{"hl"/"ok"/"bad"/"dim": [줄 번호]}` | `{"tbl": [["식", "결과"], [["17 / 5", "3"]], {"ok": [0]}]}` |
| `chips` | `[[글자, 상태?], …]` | 칩 나열 |
| `bars` | `[[이름, 값, 표시글?, 상태?], …]`, `{"max": n}` | 가로 막대 비교 |
| `arr` | `값들`, `{"hl": [...], "idx": false, "key": "x"}` | 보조 배열 그림 |
| `stack` | `아래→위 항목` | 보조 스택 그림 |
| `kv` | `[[키, 값], …]`, `{"title": "…"}` | 보조 사전 그림 |
| `eq` / `note` / `cap` / `err` | `글자` | 식 / 메모 / 설명글 / 오류 띠 |
| `row` | `위젯, 위젯, …` | 가로로 나란히 |
| `lab` | `제목`, `위젯` | 제목 붙은 묶음 |

상태 값: `hl` `ok` `bad` `dim` `g1` `g2` `g3`

## 5. 모션이 생기는 규칙

- 장면이 바뀔 때 **이름(키)이 같은 요소는 새 위치로 미끄러지고**, 새 요소는 커지며 나타나고, 사라진 요소는 위로 흩어집니다.
- 변수 상자는 이름, 배열 칸은 `배열이름:칸번호`(또는 `byVal`이면 값)로 이어집니다. 같은 이름을 계속 쓰세요.
- 값만 바뀐 칸은 크게 깜빡입니다. `from`을 주면 다른 칸에서 날아와 바뀝니다.
- 표의 줄, 카드, 흐름 상자는 차례로 하나씩 나타납니다.

## 6. 문장 쓰는 법 (TTS)

- **한 장면에 한두 문장.** 장면이 바뀌는 순간 = 그 문장을 읽기 시작하는 순간입니다. 화면 변화 하나마다 장면을 나누세요.
- 화면에 지금 보이는 것을 설명하세요. "왼쪽 코드의 3번째 줄", "0이었던 칸이 1로 바뀝니다"처럼.
- 코드 표기는 `` `x += 3` ``처럼 백틱으로, 읽기가 어려우면 `[[x += 3|엑스 플러스 이퀄 삼]]`처럼 화면 표기와 읽는 말을 함께 씁니다.
- 수식은 `{m|y = (x - 2)^2}`로 화면에 수식으로 보이고, 읽기는 `[[{m|y = x^2}|와이 이퀄 엑스 제곱]]`처럼 함께 적습니다.
- 영어 문장은 `{en|The letter was written by Tom.}`처럼 감싸면 **영어 음성**으로 읽고 화면에서는 영어 글꼴로 보입니다. 한국어 문장 속에 섞어 써도 됩니다.
- 숫자는 그대로 써도 됩니다. `17개` → 열일곱 개, `3번 칸` → 삼 번 칸, `2,147,483,647` → 이십일억… 으로 자동으로 읽습니다.
- 모르는 영어 단어는 `speech_preview`가 알려 줍니다. `pronunciation_add`로 읽기를 등록하세요.

## 7. 코드 확인

`code` op의 코드는 `code_verify`로 실제로 실행되고, 그 코드가 보이는 동안 쓴 `out`/`write` 줄과 출력이 같아야 통과합니다.

| `wrap` | C# | Python |
|---|---|---|
| `main`(기본) | `static void Main()` 안에 넣어 실행 | 그대로 실행 |
| `members` | 코드 안에 `static` 메서드와 `static void Main()`이 있음 | — |
| `none` | 코드 + `test` 코드를 그대로 컴파일 | 코드 + `test` |

- 설명만 하는 코드(컴파일 오류 예시 등)는 `"run": false`
- 화면 출력과 실제 기대 출력이 다르면 `"expect": ["7"]`

## 8. 3D 그림: render_3d (Blender)

`render_3d(course_dir, name, script)`는 bpy 스크립트로 장면을 만들어 Cycles로 렌더하고, `spot("이름", (x, y, z))`로 찍은
3D 위치가 이미지의 어디인지 계산해 `assets/<name>.png.json`에 남깁니다. 그 이름을 `img`의 `spots`, `focus`, `arrows`에 그대로 씁니다.

```python
# 빗면 위 상자: 힘 화살표 끝점을 3D에서 계산해 핫스폿으로
th = math.radians(30); d = V3((math.cos(th), 0, -math.sin(th))); n = V3((math.sin(th), 0, math.cos(th)))
bpy.ops.mesh.primitive_cube_add(size=1.1, location=C, rotation=(0, th, 0)); paint(bpy.context.object, mat("box", (0.1, 0.55, 0.6)))
spot("block", C); spot("g_tip", C + V3((0, 0, -2.6))); spot("par_tip", C + d * 1.3); spot("perp_tip", C - n * 2.25)
camera((2.9, -12.5, 2.4), (2.9, 0, 1.55), lens=42)
```

도우미: `mat(이름, (r,g,b), rough, metal, emit, sss)`, `paint(obj, mat)`, `spot`, `camera(위치, 대상, lens)`, `sun`, `area(위치, 대상, energy, size)`, `world(색)`, `look_at`, `cylinder_between(p1, p2, r, mat)`.
3D 위치에서 계산한 점(힘의 끝점, 소기관 위치)은 원근이 반영된 정확한 2D 위치가 되므로, 그 위에 그린 화살표·이름표가 그림과 어긋나지 않습니다.

## 9. 작업 순서

1. `course_init` → 2. (필요하면) `render_3d` → 3. `lesson_save`(검사 포함) → 4. `speech_preview`로 읽기 확인 →
5. `code_verify`(코드가 있을 때) → 6. `audio_synthesize` → 7. `course_build` → `dist/index.html`
