"""结构化日志与 replay 落盘。

Loop 的「Checker」环节全靠这里。核心要求：**每次得失分都能被解释**。所以每帧记录
决策理由，每次碰撞记录双方攻击强度与胜负，局末记录一份汇总。

安全约束（细则 §1.2 明确要求）：
**日志、报错、截图、代码仓库和比赛数据文件中都不得输出 AK。**
所以这里有一层 :func:`redact` 兜底，任何写盘内容都会先过一遍脱敏。
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

#: 可能携带敏感值的键名（大小写不敏感）。
_SENSITIVE_KEYS = ("accesskey", "access_key", "ak", "token", "secret", "password")

#: AK 形态未知，用一个宽松的「长随机串」规则兜底。
_LONG_TOKEN = re.compile(r"\b[A-Za-z0-9_\-]{24,}\b")


def redact(value: Any) -> Any:
    """递归脱敏。宁可多打码，也不要把 AK 写进仓库。"""
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for k, v in value.items():
            if any(s in str(k).lower() for s in _SENSITIVE_KEYS):
                out[k] = "***REDACTED***"
            else:
                out[k] = redact(v)
        return out
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        return _LONG_TOKEN.sub("***REDACTED***", value)
    return value


@dataclass
class MatchRecorder:
    """一场比赛的记录器。写 JSONL，方便 tools/analyze.py 直接流式读。"""

    run_dir: str = "runs"
    bot_version: str = "dev"
    match_code: str = "local"
    enabled: bool = True

    _fh: Optional[Any] = None
    _path: Optional[str] = None
    frames: int = 0
    events: List[Dict[str, Any]] = field(default_factory=list)

    def start(self, match_code: Optional[str] = None) -> None:
        if match_code:
            self.match_code = match_code
        if not self.enabled:
            return
        os.makedirs(self.run_dir, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        safe_code = re.sub(r"[^A-Za-z0-9_.-]", "_", self.match_code)
        self._path = os.path.join(
            self.run_dir, "{}_{}_{}.jsonl".format(stamp, self.bot_version, safe_code)
        )
        self._fh = open(self._path, "a", encoding="utf-8")
        self.write({
            "type": "match_start",
            "bot_version": self.bot_version,
            "match_code": self.match_code,
            "wall_clock": stamp,
        })

    def write(self, record: Dict[str, Any]) -> None:
        if not self.enabled or self._fh is None:
            return
        self._fh.write(json.dumps(redact(record), ensure_ascii=False) + "\n")
        self._fh.flush()   # 现场可能强杀进程，逐行 flush 保证不丢

    def log_frame(self, snapshot: Dict[str, Any], explain: str,
                  action: Optional[Dict[str, Any]]) -> None:
        self.frames += 1
        self.write({
            "type": "frame",
            "snapshot": snapshot,
            "decision": explain,
            "action": action,
        })

    def log_collision(self, event: Dict[str, Any]) -> None:
        self.events.append(event)
        self.write({"type": "collision", **event})

    def log_result(self, payload: Dict[str, Any]) -> None:
        self.write({"type": "result", **payload})

    def finish(self, summary: Optional[Dict[str, Any]] = None) -> Optional[str]:
        if summary:
            self.write({"type": "match_end", **summary})
        if self._fh is not None:
            self._fh.close()
            self._fh = None
        return self._path


def console(message: str, *, quiet: bool = False) -> None:
    """现场唯一的 stdout 出口，方便一键静音。内容同样脱敏。"""
    if quiet:
        return
    print(redact(message), flush=True)
