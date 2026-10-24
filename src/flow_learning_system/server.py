"""MCP 서버: AI가 교재를 쓰고 → 검사하고 → 코드를 확인하고 → 녹음하고 → 빌드합니다.

실행: flow-learning-system-mcp   (stdio)
"""
from __future__ import annotations

import json
from importlib import resources

try:  # MCP Python SDK 2.x
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # 1.x
    from mcp.server.fastmcp import FastMCP as _Server

from . import __version__, course as C, pipeline
from .build import build as _build
from .lesson import analyze

GUIDE = resources.files(__package__).joinpath("guide.md").read_text(encoding="utf-8")

mcp = _Server(
    "flow-learning-system",
    instructions=(
        "모션 그래픽과 TTS를 활용한 학습 시스템. 문장 하나가 장면 하나인 교재를 만든다. "
        "레슨을 쓰기 전에 authoring_guide를 반드시 읽고, 작업 순서는 "
        "course_init → (render_3d) → lesson_save → speech_preview → code_verify → audio_synthesize → course_build. 수학·과학·영어·생물·프로그래밍 등 어떤 과목이든 된다."
    ),
)


def _load(course_dir: str):
    return C.load(course_dir)


@mcp.tool()
def authoring_guide() -> str:
    """레슨 JSON 형식(op, 장면 옵션, 위젯), 모션 규칙, TTS 문장 쓰는 법을 담은 가이드. 레슨을 쓰기 전에 읽으세요."""
    return GUIDE


@mcp.resource("fls://guide")
def guide_resource() -> str:
    """레슨 작성 가이드"""
    return GUIDE


@mcp.tool()
def course_init(course_dir: str, title: str, subtitle: str = "", code_lang: str = "csharp", voice: str = "F1") -> dict:
    """새 코스 폴더를 만듭니다. code_lang: csharp | python, voice: F1~F5, M1~M5."""
    c = C.init(course_dir, title, subtitle=subtitle, code_lang=code_lang, voice=voice)
    return {"course": str(c.root), "meta": c.meta}


@mcp.tool()
def course_status(course_dir: str) -> dict:
    """코스의 레슨 목록, 장면 수, 형식 문제 수, 음성 상태를 보여 줍니다."""
    c = _load(course_dir)
    timing = c.load_timing().get("lessons", {})
    rows = []
    for L in c.lessons:
        scenes, codes, issues = analyze(L, c.pron)
        rows.append({"id": L["id"], "title": L.get("title"), "scenes": len(scenes), "code_blocks": len(codes),
                     "errors": sum(i.level == "error" for i in issues), "warnings": sum(i.level == "warn" for i in issues),
                     "audio": "있음" if str(L["id"]) in timing else "없음"})
    return {"title": c.meta.get("title"), "lessons": rows}


@mcp.tool()
def lesson_get(course_dir: str, lesson_id: int) -> dict:
    """레슨 JSON 하나를 그대로 돌려줍니다(고쳐 쓸 때)."""
    return _load(course_dir).lesson(lesson_id)


@mcp.tool()
def lesson_save(course_dir: str, lesson: dict) -> dict:
    """레슨 JSON을 검사하고, 오류가 없으면 lessons/NN.json으로 저장합니다(같은 id면 덮어씀).
    lesson = {"id": 1, "group": "...", "title": "...", "sub": "...", "ops": [...]}"""
    if isinstance(lesson, str):
        lesson = json.loads(lesson)
    c = _load(course_dir)
    scenes, codes, issues = analyze(lesson, c.pron)
    errors = [str(i) for i in issues if i.level == "error"]
    if errors:
        return {"saved": False, "errors": errors, "warnings": [str(i) for i in issues if i.level == "warn"]}
    p = C.save_lesson(c, lesson)
    return {"saved": True, "path": str(p), "scenes": len(scenes), "code_blocks": len(codes),
            "warnings": [str(i) for i in issues if i.level == "warn"]}


@mcp.tool()
def lesson_validate(course_dir: str, lesson_id: int | None = None) -> dict:
    """레슨 형식을 검사합니다(없는 코드 줄, 모르는 op·위젯, 읽기 어려운 단어 등). lesson_id를 비우면 전체."""
    return pipeline.validate(_load(course_dir), lesson_id)


@mcp.tool()
def speech_preview(course_dir: str, lesson_id: int) -> dict:
    """장면마다 TTS가 실제로 읽을 문장을 보여 주고, 영어 단어처럼 읽기 어려운 조각을 표시합니다."""
    return pipeline.speech(_load(course_dir), lesson_id)


@mcp.tool()
def pronunciation_add(course_dir: str, word: str, reading: str) -> dict:
    """영어 단어의 한글 읽기를 코스에 등록합니다. 예: word="Dictionary", reading="딕셔너리"."""
    c = _load(course_dir)
    c.meta.setdefault("pronunciations", {})[word] = reading
    C.save_meta(c)
    return {"pronunciations": c.meta["pronunciations"]}


@mcp.tool()
def code_verify(course_dir: str, lesson_id: int | None = None) -> dict:
    """코드 블록을 실제로 컴파일·실행해 화면 콘솔 출력(out/write)과 같은지 확인합니다. C#은 mono 또는 dotnet, Python은 python."""
    return pipeline.verify(_load(course_dir), lesson_id)


@mcp.tool()
def audio_synthesize(course_dir: str, lesson_id: int | None = None, voice: str | None = None, force: bool = False) -> dict:
    """Supertonic TTS로 레슨 음성(audio/lNN.mp3)과 문장별 시각표(timing.json)를 만듭니다.
    바뀌지 않은 레슨은 건너뜁니다. 레슨이 많으면 lesson_id를 하나씩 주어 나눠 실행하세요."""
    return pipeline.synthesize(_load(course_dir), lesson_id, voice, force, log=lambda *_: None)


@mcp.tool()
def render_3d(course_dir: str, name: str, script: str, width: int = 1280, height: int = 720, samples: int = 64) -> dict:
    """Blender로 3D 장면을 렌더해 assets/<name>.png 와 핫스폿 좌표를 만듭니다.
    script: bpy 파이썬 코드(장면만 만들면 됨). spot("이름", (x, y, z))로 찍은 3D 위치가 이미지의 어디인지 계산되어,
    레슨에서 {"img": ["assets/<name>.png", {"spots": ["이름"], "arrows": [{"from": "a", "to": "b"}]}]}로 가리킬 수 있습니다.
    도우미: mat(이름, (r,g,b), rough, metal, emit, sss), paint(obj, mat), spot, camera(위치, 대상, lens), sun, area, world, look_at, cylinder_between.
    Blender가 PATH에 없으면 FLS_BLENDER 환경 변수에 실행 파일 경로를 넣으세요."""
    from .render import render
    return render(_load(course_dir), name, script, width, height, samples)


@mcp.tool()
def assets_list(course_dir: str) -> dict:
    """코스의 이미지와 각 이미지의 핫스폿 이름·좌표(0~1)를 보여 줍니다."""
    return _load(course_dir).assets()


@mcp.tool()
def course_build(course_dir: str, out_dir: str | None = None) -> dict:
    """한 파일짜리 HTML 플레이어(dist/index.html)와 음성 파일을 만듭니다. 음성이 없는 레슨은 소리 없이 예상 시간으로 진행합니다."""
    return _build(_load(course_dir), out_dir)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
