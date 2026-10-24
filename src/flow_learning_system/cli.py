"""명령줄: fls <명령> <코스 폴더>"""
from __future__ import annotations

import argparse
import json
import sys

from . import __version__, course as C, pipeline
from .build import build


def _print(x):
    print(json.dumps(x, ensure_ascii=False, indent=2))


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="fls", description="모션 그래픽과 TTS를 활용한 학습 시스템")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init", help="새 코스 만들기"); i.add_argument("course"); i.add_argument("--title", required=True)
    i.add_argument("--code-lang", default="csharp"); i.add_argument("--voice", default="F1")
    for name, h in [("validate", "형식 검사"), ("verify", "코드 실행 확인"), ("speech", "TTS 읽기 미리 보기"), ("audio", "음성 합성"), ("build", "HTML 빌드"), ("all", "검사 → 확인 → 음성 → 빌드")]:
        s = sub.add_parser(name, help=h); s.add_argument("course"); s.add_argument("--lesson", type=int)
        if name in ("audio", "all"):
            s.add_argument("--voice"); s.add_argument("--force", action="store_true")
        if name in ("build", "all"):
            s.add_argument("--out")
    rd = sub.add_parser("render", help="Blender로 3D 장면을 렌더해 assets/에 넣기")
    rd.add_argument("course"); rd.add_argument("--name", required=True); rd.add_argument("--script", required=True)
    rd.add_argument("--width", type=int, default=1280); rd.add_argument("--height", type=int, default=720); rd.add_argument("--samples", type=int, default=64)
    sv = sub.add_parser("serve", help="빌드한 교재를 로컬 웹 서버로 열기(같은 와이파이의 휴대폰에서도)")
    sv.add_argument("course"); sv.add_argument("--port", type=int, default=8765); sv.add_argument("--out")
    a = p.parse_args(argv)
    if a.cmd == "init":
        _print(C.init(a.course, a.title, code_lang=a.code_lang, voice=a.voice).meta); return 0
    if a.cmd == "serve":
        return serve(a.course, a.port, a.out)
    c = C.load(a.course)
    if a.cmd == "render":
        from .render import render
        _print(render(c, a.name, a.script, a.width, a.height, a.samples)); return 0
    if a.cmd == "speech":
        if a.lesson is None:
            p.error("speech에는 --lesson이 필요합니다")
        r = pipeline.speech(c, a.lesson)
        for row in r["scenes"]:
            print(f"{row['scene']:>3}  {row['spoken']}" + (f"   ⚠ {row['unreadable']}" if row["unreadable"] else ""))
        return 0
    rc = 0
    if a.cmd in ("validate", "all"):
        r = pipeline.validate(c, a.lesson)
        for L in r["lessons"]:
            print(f"레슨 {L['lesson']:>2} {L['title']}: 장면 {L['scenes']}, 코드 {L['code_blocks']}")
            for x in L["issues"]:
                print("   ", x)
        print(f"오류 {r['errors']}, 경고 {r['warnings']}")
        if r["errors"]:
            return 1
    if a.cmd in ("verify", "all"):
        r = pipeline.verify(c, a.lesson); _print(r["summary"])
        for x in r["problems"]:
            _print(x)
        rc = 1 if r["problems"] else 0
        if a.cmd == "verify":
            return rc
    if a.cmd in ("audio", "all"):
        _print(pipeline.synthesize(c, a.lesson, a.voice, a.force))
    if a.cmd in ("build", "all"):
        _print(build(C.load(a.course), a.out))
    return rc


def serve(course_dir: str, port: int, out: str | None = None) -> int:
    """dist 폴더를 정적 웹 서버로 엽니다. 교재 자체는 서버 없이도 동작하고, 이 명령은 미리 보기용입니다."""
    import functools
    import http.server
    import socket
    from pathlib import Path
    root = Path(out) if out else Path(course_dir).expanduser().resolve() / "dist"
    if not (root / "index.html").exists():
        print(f"{root / 'index.html'} 가 없습니다. 먼저 'fls build {course_dir}'를 실행하세요.")
        return 1
    ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close()
    except OSError:
        pass
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    print(f"이 컴퓨터: http://localhost:{port}/\n같은 와이파이의 휴대폰: http://{ip}:{port}/\n끄려면 Ctrl+C")
    with http.server.ThreadingHTTPServer(("0.0.0.0", port), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
