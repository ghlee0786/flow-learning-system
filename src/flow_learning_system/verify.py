"""레슨의 코드 블록을 실제로 실행해, 화면 콘솔에 보여 줄 출력과 같은지 확인합니다.

C#: Mono(mcs + mono)가 있으면 그것을, 없으면 .NET SDK(dotnet)를 씁니다.
Python: python3(또는 python)으로 실행합니다.
wrap
  main     코드를 Main 메서드(파이썬은 그대로) 안에 넣어 실행
  members  코드에 static 메서드와 static void Main()이 들어 있음
  none     코드를 그대로 두고 test 코드를 뒤에 붙여 실행
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .lesson import CodeBlock

CS_USINGS = "using System;\nusing System.Collections.Generic;\nusing System.Linq;\nusing System.Text;\n"


@dataclass
class Result:
    lesson: int
    block: int
    status: str  # pass | fail | error | skip
    detail: str = ""
    got: list | None = None
    expected: list | None = None

    def as_dict(self):
        return self.__dict__


def _cs_source(b: CodeBlock) -> str:
    if b.wrap == "main":
        return CS_USINGS + "class Program {\n static void Main() {\n" + b.src + "\n }\n}\n"
    if b.wrap == "members":
        return CS_USINGS + "class Program {\n" + b.src + "\n}\n"
    return CS_USINGS + b.src + "\n" + (b.test or "") + "\n"


def _lines(stdout: str) -> list[str]:
    s = stdout.replace("\r\n", "\n").rstrip("\n")
    return [x.rstrip() for x in s.split("\n")] if s.strip() else []


def _run_cs(b: CodeBlock, work: Path) -> tuple[str, list[str] | str]:
    src = _cs_source(b)
    if shutil.which("mcs") and shutil.which("mono"):
        f = work / f"b{b.index}.cs"
        f.write_text(src, encoding="utf-8")
        exe = f.with_suffix(".exe")
        r = subprocess.run(["mcs", "-nowarn:219,168,414", f"-out:{exe}", str(f)], capture_output=True, text=True)
        if r.returncode:
            return "error", (r.stdout + r.stderr)[-1500:]
        o = subprocess.run(["mono", str(exe)], capture_output=True, text=True, timeout=60)
        return "ok", _lines(o.stdout)
    if shutil.which("dotnet"):
        d = work / f"b{b.index}"
        d.mkdir()
        (d / "snippet.csproj").write_text(
            '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType>'
            '<TargetFramework>net8.0</TargetFramework><ImplicitUsings>disable</ImplicitUsings>'
            '<Nullable>disable</Nullable><NoWarn>CS0219;CS0168;CS0414</NoWarn></PropertyGroup></Project>', encoding="utf-8")
        (d / "Program.cs").write_text(src, encoding="utf-8")
        o = subprocess.run(["dotnet", "run", "--project", str(d)], capture_output=True, text=True, timeout=300)
        if o.returncode:
            return "error", (o.stdout + o.stderr)[-1500:]
        return "ok", _lines(o.stdout)
    return "skip", "C# 실행 환경(mcs+mono 또는 dotnet)이 없습니다"


def _run_py(b: CodeBlock, work: Path) -> tuple[str, list[str] | str]:
    f = work / f"b{b.index}.py"
    f.write_text(b.src + ("\n" + b.test if b.test else "") + "\n", encoding="utf-8")
    o = subprocess.run([sys.executable, str(f)], capture_output=True, text=True, timeout=60)
    if o.returncode:
        return "error", o.stderr[-1500:]
    return "ok", _lines(o.stdout)


RUNNERS = {"csharp": _run_cs, "cs": _run_cs, "c#": _run_cs, "python": _run_py, "py": _run_py}


def verify_blocks(lesson_id: int, blocks: list[CodeBlock], default_lang: str = "csharp") -> list[Result]:
    out = []
    with tempfile.TemporaryDirectory(prefix="fls-") as tmp:
        work = Path(tmp)
        for b in blocks:
            if not b.run:
                out.append(Result(lesson_id, b.index, "skip", "run=false (설명용 코드)"))
                continue
            lang = (b.lang or default_lang).lower()
            runner = RUNNERS.get(lang)
            if not runner:
                out.append(Result(lesson_id, b.index, "skip", f"'{lang}' 실행기는 아직 없습니다"))
                continue
            exp = [str(x).rstrip() for x in (b.expect if b.expect is not None else b.out)]
            try:
                status, got = runner(b, work)
            except subprocess.TimeoutExpired:
                out.append(Result(lesson_id, b.index, "error", "시간 초과"))
                continue
            if status != "ok":
                out.append(Result(lesson_id, b.index, status, got if isinstance(got, str) else ""))
                continue
            ok = got == exp
            out.append(Result(lesson_id, b.index, "pass" if ok else "fail", "" if ok else "출력이 다릅니다", got, exp))
    return out
