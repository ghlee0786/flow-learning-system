"""코스 → 한 파일짜리 HTML 플레이어 (+ 음성 파일 복사)."""
from __future__ import annotations

import json
import shutil
from importlib import resources
from pathlib import Path

from .course import Course
from .lesson import analyze
from .speech import speech_text
from .tts import lesson_hash

PLAYER_JS = ["core.js", "lesson.js", "interp.js"]


def _player(name: str) -> str:
    return resources.files(__package__).joinpath("player", name).read_text(encoding="utf-8")


def _safe_json(x) -> str:
    return json.dumps(x, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def estimate(sentences: list[str]) -> list[list[float]]:
    segs, pos = [], 0.0
    for s in sentences:
        d = max(1.6, len(s) * 0.13)
        segs.append([round(pos, 2), round(pos + d, 2)])
        pos += d + 0.4
    return segs


def build(course: Course, out_dir: str | Path | None = None) -> dict:
    out = Path(out_dir) if out_dir else course.root / "dist"
    out.mkdir(parents=True, exist_ok=True)
    timing = course.load_timing().get("lessons", {})
    T, report, ext = {}, [], "mp3"
    voice, speed = course.meta.get("voice", "F1"), course.meta.get("speed", 1.05)
    for L in course.lessons:
        scenes, _, _ = analyze(L, course.pron)
        spoken = [speech_text(s.text, course.pron) for s in scenes]
        t = timing.get(str(L["id"]))
        fresh = bool(t) and t.get("hash") == lesson_hash(spoken, voice, speed) and len(t.get("segments", [])) == len(scenes)
        audio = None
        if fresh:
            src = course.audio_dir / t["file"]
            if src.exists():
                (out / "audio").mkdir(exist_ok=True)
                shutil.copy2(src, out / "audio" / src.name)
                audio = src.name
                ext = src.suffix.lstrip(".")
        T[L["id"]] = [t["segments"] if fresh else estimate(spoken)]
        report.append({"lesson": L["id"], "scenes": len(scenes), "audio": audio or ("오래됨: 다시 합성 필요" if t else "없음")})
    meta = course.meta
    assets = course.assets()
    if assets:
        dst = out / "assets"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(course.assets_dir, dst, ignore=shutil.ignore_patterns("*.json", "src", "*.py", "*.blend"))
    lessons_js = _safe_json(course.lessons)
    js = (f"var COURSE = {_safe_json({k: meta[k] for k in ('title', 'subtitle', 'code_lang') if k in meta})};\n"
          f"var TIMING = {_safe_json(T)};\nvar AUDIO_EXT = {json.dumps(ext)};\nvar ASSETS = {_safe_json(assets)};\n"
          + "\n".join(_player(f) for f in PLAYER_JS)
          + f"\n{lessons_js}.forEach(compileLesson);\n" + _player("app.js"))
    html = (_player("shell.html").replace("{{TITLE}}", meta.get("title", "교재"))
            .replace("{{COUNT}}", f"{len(course.lessons)}강").replace("/*__JS__*/", js))
    page = out / "index.html"
    page.write_text(html, encoding="utf-8")
    return {"page": str(page), "lessons": report, "assets": sorted(assets), "bytes": len(html.encode("utf-8"))}
