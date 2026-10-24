import json
import shutil
from pathlib import Path

import pytest

from flow_learning_system import course as C
from flow_learning_system import pipeline
from flow_learning_system.build import build
from flow_learning_system.lesson import analyze

EX = Path(__file__).resolve().parent.parent / "examples" / "csharp-grammar"


def test_example_is_clean():
    c = C.load(EX)
    r = pipeline.validate(c)
    assert r["errors"] == 0 and r["warnings"] == 0
    assert sum(L["scenes"] for L in r["lessons"]) == 321


def test_bad_lesson_is_rejected():
    bad = {"id": 1, "title": "x", "ops": [
        {"op": "code", "src": "int a = 1;"},
        {"op": "say", "line": "없는 줄", "text": "설명"},
        {"op": "row", "cells": [1]},
        {"op": "say", "text": "보드", "board": {"없는위젯": []}},
        {"op": "fly"}]}
    _, _, issues = analyze(bad)
    msgs = " ".join(str(i) for i in issues if i.level == "error")
    assert "찾지 못했습니다" in msgs and "table" in msgs and "알 수 없는 위젯" in msgs and "알 수 없는 op" in msgs


def test_python_course_end_to_end(tmp_path):
    c = C.init(tmp_path / "py", "파이썬", code_lang="python")
    lesson = {"id": 1, "title": "합", "ops": [
        {"op": "code", "src": "print(1 + 2)"},
        {"op": "out", "text": "3"},
        {"op": "say", "line": 1, "text": "1 더하기 2는 3입니다.", "head": "1 + 2 = 3"}]}
    C.save_lesson(c, lesson)
    c = C.load(tmp_path / "py")
    assert pipeline.verify(c)["summary"] == {"pass": 1}
    out = build(c, tmp_path / "out")
    html = Path(out["page"]).read_text(encoding="utf-8")
    assert "<title>파이썬</title>" in html and "compileLesson" in html


def test_build_example_without_audio(tmp_path):
    shutil.copytree(EX, tmp_path / "ex", ignore=shutil.ignore_patterns("audio", "timing.json", "dist"))
    r = build(C.load(tmp_path / "ex"))
    assert len(r["lessons"]) == 17 and all(L["audio"] == "없음" for L in r["lessons"])


@pytest.mark.skipif(not (shutil.which("mcs") or shutil.which("dotnet")), reason="C# 실행 환경 없음")
def test_example_code_runs():
    r = pipeline.verify(C.load(EX), 7)
    assert r["problems"] == [] and r["summary"].get("pass", 0) >= 4
