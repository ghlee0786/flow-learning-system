"""MCPB 번들 진입점: 설치 없이도 src/ 의 패키지를 찾아 MCP 서버(stdio)를 띄웁니다."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from flow_learning_system.server import main  # noqa: E402

if __name__ == "__main__":
    main()
