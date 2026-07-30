"""独立 WebSocket 客户端（**兜底方案**）。

优先用官方 SDK。这个 runner 存在的意义是：

*   SDK 还没到手 / 装不上时，也能先跑通链路验证策略；
*   出问题时能对照排查，判断是 SDK 问题还是我们的策略问题。

如果最终用官方 SDK，请把 :class:`~firefly.agent.FireflyAgent` 接到 SDK 回调上，
**不要**再用这个文件 —— 细则禁止自建 WebSocket / 定时器绕过 SDK 的限频逻辑。

自己实现时必须自己守住的规则：
*   动作指令不得快于每 100ms 一次；
*   心跳 4~30s 一次，不要用高频心跳代替状态机；
*   断线用带抖动的指数退避重连（1/2/4/8s，上限 ~30s），重连后重发 botConnect；
*   同一 AK 同时只允许一条有效连接。

依赖：``pip install websockets``（只有这个文件需要，核心策略零依赖）。
"""

from __future__ import annotations

import asyncio
import json
import random
import time
from typing import Any, Dict, Optional

from .agent import FireflyAgent
from .constants import (
    AGENT_WS_URL,
    RULE_MIN_ACTION_INTERVAL_MS,
    Cmd,
)
from .telemetry import console

HEARTBEAT_INTERVAL = 5.0        # 细则建议 4~30s
MAX_BACKOFF = 30.0
ACTION_MIN_INTERVAL = RULE_MIN_ACTION_INTERVAL_MS / 1000.0


class WsRunner:
    """最小可用客户端。"""

    def __init__(
        self,
        agent: FireflyAgent,
        url: str = AGENT_WS_URL,
        *,
        max_reconnects: int = 8,
        quiet: bool = False,
    ) -> None:
        self.agent = agent
        self.url = url
        self.max_reconnects = max_reconnects
        self.quiet = quiet
        self._last_action_at = 0.0
        self._stop = False

    # ------------------------------------------------------------------

    async def run(self) -> None:
        attempt = 0
        while not self._stop:
            try:
                await self._session()
                attempt = 0            # 正常结束，重置退避
            except _FatalError as exc:
                self._say("致命错误，停止重连：{}".format(exc))
                return
            except Exception as exc:   # noqa: BLE001 - 网络层什么都可能抛
                attempt += 1
                if attempt > self.max_reconnects:
                    self._say("重连次数超上限（{}），放弃".format(self.max_reconnects))
                    return
                delay = min(MAX_BACKOFF, (2 ** (attempt - 1)))
                delay += random.uniform(0, delay * 0.3)   # 抖动，避免同时重连
                self._say("连接异常（{}），{:.1f}s 后第 {} 次重连".format(
                    type(exc).__name__, delay, attempt))
                await asyncio.sleep(delay)

    async def _session(self) -> None:
        try:
            import websockets
        except ImportError as exc:  # pragma: no cover
            raise _FatalError("缺少依赖：pip install websockets") from exc

        self._say("连接 {}".format(self.url))
        async with websockets.connect(self.url, max_size=8 * 1024 * 1024) as ws:
            # 首条业务消息：botConnect（AK 只出现在这里）
            await self._send(ws, self.agent.connect_message())

            heartbeat = asyncio.ensure_future(self._heartbeat_loop(ws))
            try:
                async for raw in ws:
                    await self._on_raw(ws, raw)
                    if self._stop:
                        break
            finally:
                heartbeat.cancel()

    async def _heartbeat_loop(self, ws: Any) -> None:
        try:
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                await self._send(ws, self.agent.heartbeat_message(), rate_limit=False)
        except asyncio.CancelledError:  # pragma: no cover
            pass

    # ------------------------------------------------------------------

    async def _on_raw(self, ws: Any, raw: Any) -> None:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        try:
            message = json.loads(raw)
        except (TypeError, ValueError):
            self._say("收到无法解析的消息，已忽略")
            return
        if not isinstance(message, dict):
            return

        code = str(message.get("code", ""))
        if code == "BOT_ALREADY_ONLINE":
            raise _FatalError("同一 AK 已有有效连接，请先确认旧进程退出")

        for outbound in self.agent.handle(message):
            retry_ms = outbound.pop("__retry_after_ms", None)
            if retry_ms:
                await asyncio.sleep(float(retry_ms) / 1000.0)
            if outbound.get("commandType"):
                await self._send(ws, outbound)

    async def _send(self, ws: Any, message: Dict[str, Any],
                    *, rate_limit: bool = True) -> None:
        """发送。对控制指令强制 100ms 最小间隔。"""
        if rate_limit and _is_control(message):
            now = time.monotonic()
            wait = ACTION_MIN_INTERVAL - (now - self._last_action_at)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_action_at = time.monotonic()
        await ws.send(json.dumps(message, ensure_ascii=False))

    def stop(self) -> None:
        self._stop = True

    def _say(self, message: str) -> None:
        console("[runner] " + message, quiet=self.quiet)


_CONTROL_COMMANDS = {
    Cmd.GO_FORWARD, Cmd.GO_BACK, Cmd.TURN_LEFT, Cmd.TURN_RIGHT,
    Cmd.STOP, Cmd.STEER_BACK, Cmd.SET_ATTACK_VALUE,
}


def _is_control(message: Dict[str, Any]) -> bool:
    return str(message.get("commandType", "")) in _CONTROL_COMMANDS


class _FatalError(RuntimeError):
    """不应重连的错误。"""


def main() -> None:
    """命令行入口：``python -m firefly.runner``

    AK 从环境变量 ``FIREFLY_ACCESS_KEY`` 读取 —— **不要写进代码或命令行参数**
    （命令行参数会进 shell history）。
    """
    import argparse
    import os

    parser = argparse.ArgumentParser(description="萤火森林 Agent 兜底客户端")
    parser.add_argument("--url", default=AGENT_WS_URL)
    parser.add_argument("--no-record", action="store_true", help="不落盘 replay")
    parser.add_argument("--no-practice", action="store_true",
                        help="matchFinished 后不自动申请下一场训练")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    access_key = os.environ.get("FIREFLY_ACCESS_KEY", "").strip()
    if not access_key:
        raise SystemExit(
            "未设置 AK。请先执行：export FIREFLY_ACCESS_KEY='报名平台发放的AK'\n"
            "（细则要求 AK 不得出现在代码、日志、截图与仓库中）"
        )

    agent = FireflyAgent(
        access_key,
        auto_practice=not args.no_practice,
        record=not args.no_record,
        quiet=args.quiet,
    )
    runner = WsRunner(agent, url=args.url, quiet=args.quiet)
    try:
        asyncio.get_event_loop().run_until_complete(runner.run())
    except KeyboardInterrupt:
        console("[runner] 手动停止")


if __name__ == "__main__":  # pragma: no cover
    main()
