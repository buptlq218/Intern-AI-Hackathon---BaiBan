#!/usr/bin/env python3
"""本地检查：语法检查 + 全部测试。等价于 Node 版的 npm run check。"""

import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SOURCES = [
    "bot.py",
    "strategy.py",
    "replay_recorder.py",
    "replay_server.py",
    "check.py",
    "test_strategy.py",
    "test_replay_recorder.py",
    "test_replay_server.py",
    "test_lifecycle.py",
]
TESTS = [
    "test_strategy.py",
    "test_replay_recorder.py",
    "test_replay_server.py",
    "test_lifecycle.py",
]


def main():
    try:
        import websockets  # noqa: F401
    except ImportError:
        print("缺少 websockets 依赖，请先运行：python3 -m pip install -r requirements.txt",
              file=sys.stderr)
        return 1

    for name in SOURCES:
        path = BASE_DIR / name
        try:
            compile(path.read_text(encoding="utf-8"), name, "exec")
        except SyntaxError as error:
            print(f"{name} 语法错误：{error}", file=sys.stderr)
            return 1
    print(f"syntax check passed ({len(SOURCES)} files)", flush=True)

    for name in TESTS:
        result = subprocess.run([sys.executable, str(BASE_DIR / name)], cwd=str(BASE_DIR))
        if result.returncode != 0:
            print(f"\n{name} 失败", file=sys.stderr)
            return result.returncode

    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
