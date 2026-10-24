"""검사 → 코드 확인 → 음성 → 빌드. CLI와 MCP 서버가 함께 씁니다."""
from __future__ import annotations

from .course import Course
from .lesson import analyze
from .speech import speech_parts, speech_text, unreadable
from .verify import verify_blocks


def _pick(course: Course, lesson_id: int | None):
    return [course.lesson(lesson_id)] if lesson_id is not None else course.lessons


def validate(course: Course, lesson_id: int | None = None) -> dict:
    out = {"lessons": [], "errors": 0, "warnings": 0}
    assets = course.assets()
    for L in _pick(course, lesson_id):
        scenes, codes, issues = analyze(L, course.pron, assets)
        e = sum(i.level == "error" for i in issues)
        out["errors"] += e
        out["warnings"] += len(issues) - e
        out["lessons"].append({"lesson": L["id"], "title": L.get("title"), "scenes": len(scenes), "code_blocks": len(codes),
                               "issues": [str(i) for i in issues]})
    return out


def verify(course: Course, lesson_id: int | None = None) -> dict:
    res = []
    for L in _pick(course, lesson_id):
        _, codes, _ = analyze(L, course.pron)
        res += verify_blocks(L["id"], codes, course.meta.get("code_lang", "csharp"))
    counts = {}
    for r in res:
        counts[r.status] = counts.get(r.status, 0) + 1
    return {"summary": counts, "problems": [r.as_dict() for r in res if r.status in ("fail", "error")],
            "skipped": [r.as_dict() for r in res if r.status == "skip"]}


def speech(course: Course, lesson_id: int) -> dict:
    scenes, _, _ = analyze(course.lesson(lesson_id), course.pron)
    rows = []
    for s in scenes:
        sp = speech_text(s.text, course.pron)
        rows.append({"scene": s.index + 1, "script": s.text, "spoken": sp, "unreadable": unreadable(sp)})
    return {"lesson": lesson_id, "scenes": rows, "flagged": sum(bool(r["unreadable"]) for r in rows)}


def synthesize(course: Course, lesson_id: int | None = None, voice: str | None = None, force: bool = False, log=print) -> dict:
    from .tts import Synth, lesson_hash, synthesize_lesson
    voice = voice or course.meta.get("voice", "F1")
    speed = course.meta.get("speed", 1.05)
    if voice != course.meta.get("voice"):
        course.meta["voice"] = voice
        from .course import save_meta
        save_meta(course)
    timing = course.load_timing()
    timing.setdefault("lessons", {})
    synth, done = None, []
    course.audio_dir.mkdir(exist_ok=True)
    for L in _pick(course, lesson_id):
        scenes, _, issues = analyze(L, course.pron, course.assets())
        if any(i.level == "error" for i in issues):
            done.append({"lesson": L["id"], "status": "건너뜀: 형식 오류부터 고치세요"})
            continue
        spoken = [speech_text(s.text, course.pron) for s in scenes]
        parts = [speech_parts(s.text, course.pron) for s in scenes]
        h = lesson_hash(spoken, voice, speed)
        old = timing["lessons"].get(str(L["id"]))
        if old and old.get("hash") == h and (course.audio_dir / old["file"]).exists() and not force:
            done.append({"lesson": L["id"], "status": "최신 상태"})
            continue
        synth = synth or Synth(voice, speed)
        log(f"레슨 {L['id']}: {len(spoken)}문장 합성 중")
        f, segs = synthesize_lesson(synth, parts, course.audio_dir / f"l{L['id']:02d}")
        timing["lessons"][str(L["id"])] = {"file": f.name, "hash": h, "voice": voice, "segments": segs}
        course.save_timing(timing)
        done.append({"lesson": L["id"], "status": "완료", "seconds": round(segs[-1][1], 1), "file": f.name})
    return {"voice": voice, "lessons": done}
