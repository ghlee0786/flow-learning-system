"""레슨 ops를 따라가며 장면·코드 블록·출력을 계산하고, 형식 오류를 찾습니다.

플레이어(player/lesson.js, interp.js)와 같은 규칙으로 움직입니다.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .speech import speech_text, unreadable

WIDGETS = {"arr", "grid", "tbl", "stack", "kv", "flow", "chips", "tl", "regs", "row", "cap", "note",
           "eq", "lab", "vars", "con", "cards", "bars", "err", "math", "plot", "tokens", "img", "svg"}
SAY_OPTS = {"line", "text", "head", "board", "eq", "err", "ret", "note", "hl", "ok", "dim", "bad", "g1", "g2", "g3",
            "ptr", "from", "grid", "hot", "okv", "con", "op"}
# op 이름 → (필수 필드, 선택 필드)
OPS = {
    "part": ({"title"}, set()),
    "code": ({"src"}, {"wrap", "run", "test", "expect", "lang"}),
    "nocode": (set(), set()),
    "use": ({"code"}, set()),
    "var": ({"name", "value"}, {"type"}),
    "ref": ({"name", "target"}, {"type"}),
    "drop": ({"names"}, set()),
    "free": ({"names"}, set()),
    "array": ({"name", "values"}, {"tag", "title", "byVal", "idx"}),
    "stack": ({"name", "items"}, {"tag", "title", "byVal"}),
    "queue": ({"name", "items"}, {"tag", "title"}),
    "dict": ({"name", "pairs"}, {"tag", "title"}),
    "set": ({"name", "items"}, {"tag", "title"}),
    "grid": ({"name", "rows"}, {"tag", "title", "g"}),
    "out": ({"text"}, set()),
    "write": ({"text"}, set()),
    "show_out": ({"text"}, set()),
    "table": ({"head"}, {"title"}),
    "row": ({"cells"}, set()),
    "board": ({"widget"}, set()),
    "clear": (set(), set()),
    "say": ({"text"}, SAY_OPTS),
}


@dataclass
class CodeBlock:
    index: int
    src: str
    wrap: str = "main"
    run: bool = True
    test: str = ""
    expect: list | None = None
    lang: str | None = None
    out: list = field(default_factory=list)


@dataclass
class Scene:
    index: int
    text: str
    head: str
    code: int
    lines: list
    section: str | None


@dataclass
class Issue:
    lesson: int
    op: int | None
    level: str  # error | warn
    msg: str

    def __str__(self):
        where = f"레슨 {self.lesson}" + (f" · op {self.op}" if self.op is not None else "")
        return f"[{self.level}] {where}: {self.msg}"


def _clean_src(src: str) -> str:
    if src.startswith("\n"):
        src = src[1:]
    return src.rstrip()


def resolve_line(src: str, ref) -> int:
    lines = src.split("\n")
    if isinstance(ref, int):
        if not 1 <= ref <= len(lines):
            raise ValueError(f"줄 번호 {ref}가 범위(1~{len(lines)}) 밖입니다")
        return ref
    needle, nth = (ref[0], ref[1]) if isinstance(ref, list) else (ref, 1)
    c = 0
    for i, ln in enumerate(lines):
        if needle in ln:
            c += 1
            if c == nth:
                return i + 1
    raise ValueError(f"코드에서 '{needle}'({nth}번째)를 찾지 못했습니다")


def _line_refs(line):
    if line is None:
        return []
    if isinstance(line, list) and len(line) == 2 and isinstance(line[0], str) and isinstance(line[1], int):
        return [line]
    return line if isinstance(line, list) else [line]


def _check_img(args, issues, L, n, assets):
    src = args[0] if args else None
    o = args[1] if len(args) > 1 and isinstance(args[1], dict) else {}
    if not isinstance(src, str):
        issues.append(Issue(L, n, "error", "img: 첫 인자는 이미지 경로여야 합니다"))
        return
    if assets is None:
        return
    if src not in assets:
        issues.append(Issue(L, n, "error", f"img: 코스에 '{src}' 이미지가 없습니다(assets/ 폴더). 있는 이미지: {sorted(assets)[:8]}"))
        return
    hs = set((assets[src] or {}).get("hotspots", {})) | set((o.get("at") or {}))
    names = list(o.get("spots") or []) + ([o["focus"]] if o.get("focus") else [])
    for a in o.get("arrows") or []:
        names += [a.get("from"), a.get("to")]
    miss = sorted({x for x in names if x and x not in hs})
    if miss:
        issues.append(Issue(L, n, "error", f"img '{src}': 핫스폿 {miss}이(가) 없습니다. 있는 핫스폿: {sorted(hs)}"))


def _check_widget(w, path, issues, L, n, assets=None):
    if w is None or isinstance(w, (str, int, float)):
        return
    if isinstance(w, list):
        for x in w:
            _check_widget(x, path, issues, L, n, assets)
        return
    if isinstance(w, dict):
        if "seq" in w:
            _check_widget(w["seq"], path, issues, L, n, assets)
            return
        if "h" in w:
            return
        keys = list(w)
        if len(keys) == 1 and keys[0] in WIDGETS:
            args = w[keys[0]]
            args = args if isinstance(args, list) else [args]
            if keys[0] == "img":
                _check_img(args, issues, L, n, assets)
            for a in args:
                if isinstance(a, dict) and len(a) == 1 and list(a)[0] in WIDGETS | {"seq"}:
                    _check_widget(a, path, issues, L, n, assets)
            return
        issues.append(Issue(L, n, "error", f"{path}: 알 수 없는 위젯 {keys[:3]}. 쓸 수 있는 위젯: {sorted(WIDGETS)}"))


def analyze(lesson: dict, pron: dict | None = None, assets: dict | None = None):
    """레슨을 따라가며 (장면 목록, 코드 블록 목록, 문제 목록)을 돌려줍니다."""
    L = lesson.get("id", "?")
    issues: list[Issue] = []
    for k in ("id", "title", "ops"):
        if k not in lesson:
            issues.append(Issue(L, None, "error", f"'{k}' 필드가 없습니다"))
    if not isinstance(lesson.get("id"), int):
        issues.append(Issue(L, None, "error", "'id'는 정수여야 합니다"))
    codes: list[CodeBlock] = []
    scenes: list[Scene] = []
    cur, open_line, section, sec_new = -1, False, None, False
    objs: dict[str, str] = {}
    table = False
    head = ""
    for n, op in enumerate(lesson.get("ops", [])):
        kind = op.get("op")
        if kind not in OPS:
            issues.append(Issue(L, n, "error", f"알 수 없는 op '{kind}'. 쓸 수 있는 op: {sorted(OPS)}"))
            continue
        req, opt = OPS[kind]
        missing = req - set(op)
        if missing:
            issues.append(Issue(L, n, "error", f"{kind}: 필수 필드 {sorted(missing)}가 없습니다"))
            continue
        extra = set(op) - req - opt - {"op"}
        if extra and kind != "say":
            issues.append(Issue(L, n, "warn", f"{kind}: 쓰이지 않는 필드 {sorted(extra)}"))
        if kind == "part":
            section, sec_new = op["title"], True
        elif kind == "code":
            codes.append(CodeBlock(len(codes), _clean_src(op["src"]), op.get("wrap", "main"), op.get("run", True),
                                   op.get("test", ""), op.get("expect"), op.get("lang")))
            cur, open_line = len(codes) - 1, False
        elif kind == "nocode":
            cur = -1
        elif kind == "use":
            if not (isinstance(op["code"], int) and 0 <= op["code"] < len(codes)):
                issues.append(Issue(L, n, "error", f"use: 코드 블록 {op['code']}이(가) 없습니다(0~{len(codes) - 1})"))
            else:
                cur, open_line = op["code"], False
        elif kind in ("array", "stack", "queue", "dict", "set", "grid"):
            objs[op["name"]] = kind
            if kind == "grid":
                rows = op["rows"]
                if not (isinstance(rows, list) and rows and all(isinstance(r, list) for r in rows)):
                    issues.append(Issue(L, n, "error", "grid: rows는 2차원 배열이어야 합니다"))
        elif kind == "free":
            for x in op["names"]:
                objs.pop(x, None)
        elif kind in ("out", "write"):
            t = str(op["text"])
            c = codes[cur] if cur >= 0 else None
            if open_line:
                if c and c.out:
                    c.out[-1] += t
            elif c:
                c.out.append(t)
            open_line = kind == "write"
        elif kind == "table":
            table = True
        elif kind == "row":
            if not table:
                issues.append(Issue(L, n, "error", "row: 먼저 table로 표를 시작해야 합니다"))
        elif kind == "board":
            _check_widget(op["widget"], "board", issues, L, n, assets)
        elif kind == "clear":
            objs.clear(); table = False; open_line = False
        elif kind == "say":
            text = op["text"]
            if not str(text).strip():
                issues.append(Issue(L, n, "error", "say: 빈 문장입니다"))
            lines = []
            refs = _line_refs(op.get("line"))
            if refs and cur < 0:
                issues.append(Issue(L, n, "error", "say: 지금 보이는 코드가 없는데 line을 지정했습니다"))
            elif refs:
                for r in refs:
                    try:
                        lines.append(resolve_line(codes[cur].src, r))
                    except ValueError as e:
                        issues.append(Issue(L, n, "error", f"say: {e}"))
            for key in ("board", "err", "eq", "note"):
                if key in op and not isinstance(op[key], str):
                    _check_widget(op[key], key, issues, L, n, assets)
            for key in ("hl", "ok", "dim", "bad", "g1", "g2", "g3", "ptr", "from", "grid"):
                for name in (op.get(key) or {}):
                    if name not in objs:
                        issues.append(Issue(L, n, "warn", f"say.{key}: '{name}' 그림이 지금 화면에 없습니다"))
            unknown = set(op) - SAY_OPTS
            if unknown:
                issues.append(Issue(L, n, "warn", f"say: 쓰이지 않는 필드 {sorted(unknown)}"))
            if "head" in op:
                head = op["head"]
            spoken = speech_text(text, pron)
            bad = unreadable(spoken)
            if bad:
                issues.append(Issue(L, n, "warn", f"say: TTS가 읽기 어려운 조각 {bad} → [[표기|읽는 말]] 또는 pronunciations에 추가하세요"))
            scenes.append(Scene(len(scenes), text, head, cur, lines, section if sec_new else None))
            sec_new = False
    if not scenes:
        issues.append(Issue(L, None, "error", "say가 하나도 없습니다(장면 0개)"))
    return scenes, codes, issues
