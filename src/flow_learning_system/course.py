"""코스 폴더 읽기·쓰기.

코스 폴더 구조::

    my-course/
      course.json          제목, 언어, 코드 언어, 음성, 레슨 목록, 읽기 규칙
      lessons/01.json      레슨 하나 = 메타 정보 + ops 목록
      audio/l01.mp3        (audio 명령이 만듦)
      timing.json          (audio 명령이 만듦) 문장별 시작·끝 시각
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_COURSE = {
    "title": "새 코스",
    "subtitle": "",
    "language": "ko",
    "code_lang": "csharp",
    "voice": "F1",
    "speed": 1.05,
    "lessons": [],
    "pronunciations": {},
}


@dataclass
class Course:
    root: Path
    meta: dict
    lessons: list[dict] = field(default_factory=list)

    @property
    def pron(self) -> dict:
        return self.meta.get("pronunciations") or {}

    def lesson(self, lesson_id: int) -> dict:
        for L in self.lessons:
            if L["id"] == lesson_id:
                return L
        raise KeyError(f"레슨 {lesson_id}이(가) 없습니다. 있는 레슨: {[L['id'] for L in self.lessons]}")

    def lesson_path(self, lesson_id: int) -> Path:
        return self.root / "lessons" / f"{lesson_id:02d}.json"

    @property
    def audio_dir(self) -> Path:
        return self.root / "audio"

    @property
    def timing_path(self) -> Path:
        return self.root / "timing.json"

    @property
    def assets_dir(self) -> Path:
        return self.root / "assets"

    def assets(self) -> dict:
        """assets/ 안의 이미지 → {경로: {w, h, hotspots}} (같은 이름의 .json 사이드카에서 읽음)"""
        out = {}
        if not self.assets_dir.exists():
            return out
        for p in sorted(self.assets_dir.rglob("*")):
            if p.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"):
                continue
            rel = p.relative_to(self.root).as_posix()
            side = p.with_suffix(p.suffix + ".json")
            meta = json.loads(side.read_text(encoding="utf-8")) if side.exists() else {}
            if "w" not in meta:
                meta.update(_image_size(p))
            out[rel] = meta
        return out

    def load_timing(self) -> dict:
        if self.timing_path.exists():
            return json.loads(self.timing_path.read_text(encoding="utf-8"))
        return {"lessons": {}}

    def save_timing(self, t: dict) -> None:
        self.timing_path.write_text(json.dumps(t, ensure_ascii=False, indent=1), encoding="utf-8")


def _image_size(p: Path) -> dict:
    """PNG/JPEG 크기(라이브러리 없이)."""
    import struct
    b = p.read_bytes()[:65536]
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", b[16:24])
        return {"w": w, "h": h}
    if b[:2] == b"\xff\xd8":
        i = 2
        while i < len(b) - 9:
            if b[i] != 0xFF:
                i += 1; continue
            m, ln = b[i + 1], struct.unpack(">H", b[i + 2:i + 4])[0]
            if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", b[i + 5:i + 9])
                return {"w": w, "h": h}
            i += 2 + ln
    return {}


def load(root: str | Path) -> Course:
    root = Path(root).expanduser().resolve()
    cj = root / "course.json"
    if not cj.exists():
        raise FileNotFoundError(f"{cj} 가 없습니다. course_init으로 코스를 먼저 만드세요.")
    meta = {**DEFAULT_COURSE, **json.loads(cj.read_text(encoding="utf-8"))}
    lessons = []
    for rel in meta["lessons"]:
        p = root / rel
        lessons.append(json.loads(p.read_text(encoding="utf-8")))
    lessons.sort(key=lambda L: L["id"])
    return Course(root, meta, lessons)


def init(root: str | Path, title: str, **opts) -> Course:
    root = Path(root).expanduser().resolve()
    (root / "lessons").mkdir(parents=True, exist_ok=True)
    cj = root / "course.json"
    if cj.exists():
        raise FileExistsError(f"{cj} 가 이미 있습니다.")
    meta = {**DEFAULT_COURSE, "title": title, **{k: v for k, v in opts.items() if v is not None}}
    cj.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return load(root)


def dump_lesson(L: dict) -> str:
    """레슨 JSON을 op 한 줄씩 쓰는 읽기 쉬운 형태로."""
    meta = {k: v for k, v in L.items() if k != "ops"}
    head = "".join(f"  {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)},\n" for k, v in meta.items())
    ops = ",\n".join("    " + json.dumps(o, ensure_ascii=False) for o in L.get("ops", []))
    return "{\n" + head + '  "ops": [\n' + ops + "\n  ]\n}\n"


def save_lesson(course: Course, L: dict) -> Path:
    p = course.lesson_path(L["id"])
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(dump_lesson(L), encoding="utf-8")
    rel = p.relative_to(course.root).as_posix()
    if rel not in course.meta["lessons"]:
        course.meta["lessons"].append(rel)
        course.meta["lessons"].sort()
        save_meta(course)
    course.lessons = [x for x in course.lessons if x["id"] != L["id"]] + [L]
    course.lessons.sort(key=lambda x: x["id"])
    return p


def save_meta(course: Course) -> None:
    (course.root / "course.json").write_text(json.dumps(course.meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
