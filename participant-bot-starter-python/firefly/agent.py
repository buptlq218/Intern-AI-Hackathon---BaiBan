"""Agent 大脑：与传输层无关的完整状态机。

**这是接官方 SDK 的地方。** 两种接法：

1.  SDK 只给「策略回调」（最常见）：把 :meth:`FireflyAgent.on_strategy_frame`
    接到回调上，它吃一帧 refreshData 的 dict，返回 0 或 1 条动作 dict。
2.  SDK 直接把原始消息丢过来：用 :meth:`FireflyAgent.handle`，它返回一个
    「需要发送的消息」列表，覆盖认证、入房、心跳、训练闭环全流程。

无论哪种，都不要在这个文件之外再自建 WebSocket 或定时器 —— 细则明令禁止绕过 SDK
的限频逻辑。

状态流转（细则 §2.1）::

    botConnect → botConnected → roundAssigned → roundStarted → aiEnterRoom
      → roomEntered → startGame → refreshData×N → closeGame
      → matchFinished → roundFinished
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .constants import BOT_VERSION, Cmd, ErrCode, TUNE, Tune
from .control import Controller
from .protocol import Frame
from .strategy import Strategy
from .telemetry import MatchRecorder, console
from .worldmodel import WorldModel

#: 会话状态
IDLE = "IDLE"
LOBBY = "LOBBY"
ASSIGNED = "ASSIGNED"          # 收到 roundAssigned，但还不能入房
ROUND_OPEN = "ROUND_OPEN"      # 收到 roundStarted，可以入房
IN_ROOM = "IN_ROOM"
PLAYING = "PLAYING"
FINISHED = "FINISHED"


@dataclass
class Assignment:
    """一次分桌。用 (tournamentCode, roundNo, pairingVersion, matchId) 做幂等键。"""

    tournament_code: str = ""
    round_no: int = 0
    pairing_version: int = 0
    match_id: Optional[int] = None
    match_code: str = ""
    room_id: str = ""
    assignment_type: str = "MATCH"
    match_type: str = ""

    @property
    def key(self) -> Tuple[str, int, int, Optional[int]]:
        return (self.tournament_code, self.round_no, self.pairing_version, self.match_id)

    @property
    def is_bye(self) -> bool:
        return self.assignment_type.upper() == "BYE"

    @property
    def is_practice(self) -> bool:
        return self.match_type.upper() == "PRACTICE"


class FireflyAgent:
    """完整会话状态机 + 策略。"""

    def __init__(
        self,
        access_key: str,
        tune: Optional[Tune] = None,
        *,
        bot_version: str = BOT_VERSION,
        auto_practice: bool = True,
        record: bool = True,
        run_dir: str = "runs",
        quiet: bool = False,
    ) -> None:
        # AK 只在首条 botConnect 里出现，绝不进日志（telemetry.redact 兜底）
        self._access_key = access_key
        self.bot_version = bot_version
        self.auto_practice = auto_practice
        self.quiet = quiet

        self.tune = tune or TUNE
        self.world = WorldModel(tune=self.tune)
        self.controller = Controller(self.tune)
        self.strategy = Strategy(self.tune, self.world, self.controller)

        self.state = IDLE
        self.bot_id: Optional[int] = None
        self.bot_name: Optional[str] = None
        self.assignment: Optional[Assignment] = None
        #: 已经初始化过的分桌键，防止重连补发导致重复初始化（细则 §2.4）
        self._seen_keys: set = set()

        self.recorder = MatchRecorder(
            run_dir=run_dir, bot_version=bot_version, enabled=record
        )
        self.results: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # 接法一：SDK 只给策略回调
    # ------------------------------------------------------------------

    def on_strategy_frame(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """吃一帧数据，返回 0 或 1 条动作消息。

        对 startGame / refreshData 都能处理，方便直接挂在 SDK 的帧回调上。
        """
        cmd = str(message.get("commandType", ""))
        if cmd == Cmd.START_GAME:
            self._begin_match(message)
            return None
        if cmd != Cmd.REFRESH_DATA:
            return None
        return self._play_frame(message)

    # ------------------------------------------------------------------
    # 接法二：SDK 把原始消息丢过来
    # ------------------------------------------------------------------

    def handle(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理任意服务端消息，返回需要发送的消息列表（通常 0 或 1 条）。"""
        cmd = str(message.get("commandType", ""))
        handler = getattr(self, "_on_" + _snake(cmd), None)
        if handler is None:
            return []
        result = handler(message)
        if result is None:
            return []
        return result if isinstance(result, list) else [result]

    def connect_message(self, strategy_hash: Optional[str] = None) -> Dict[str, Any]:
        """首条业务消息。**AK 只在这里出现一次。**"""
        msg: Dict[str, Any] = {
            "commandType": Cmd.BOT_CONNECT,
            "accessKey": self._access_key,
            "botVersion": self.bot_version,
        }
        if strategy_hash:
            msg["strategyHash"] = strategy_hash
        return msg

    def heartbeat_message(self) -> Dict[str, Any]:
        return {"commandType": Cmd.BOT_HEARTBEAT}

    # ------------------------------------------------------------------
    # 各消息处理
    # ------------------------------------------------------------------

    def _on_bot_connected(self, message: Dict[str, Any]) -> None:
        self.bot_id = message.get("botId")
        self.bot_name = message.get("botName")
        self.state = LOBBY
        self.world.identify_self(name=self.bot_name)
        self._say("已进入大厅 botId={} name={}".format(self.bot_id, self.bot_name))

    def _on_bot_ready(self, message: Dict[str, Any]) -> None:
        self.state = LOBBY
        self._say("已就绪，等待下一次分桌")

    def _on_round_assigned(self, message: Dict[str, Any]) -> None:
        """只保存房间信息，**不要立刻入房**（细则 §2.3）。"""
        assignment = Assignment(
            tournament_code=str(message.get("tournamentCode", "")),
            round_no=int(message.get("roundNo") or 0),
            pairing_version=int(message.get("pairingVersion") or 0),
            match_id=message.get("matchId"),
            match_code=str(message.get("matchCode", "")),
            room_id=str(message.get("roomId", "")),
            assignment_type=str(message.get("assignmentType", "MATCH")),
            match_type=str(message.get("matchType", "")),
        )

        prev = self.assignment
        if prev is not None and assignment.pairing_version < prev.pairing_version:
            self._say("忽略过期配桌版本 {} < {}".format(
                assignment.pairing_version, prev.pairing_version))
            return

        if prev is not None and assignment.pairing_version > prev.pairing_version:
            # 细则：收到更高 pairingVersion 时丢弃旧房间的待执行动作
            self.controller.reset()
            self._say("配桌版本升级到 {}，丢弃旧房间状态".format(assignment.pairing_version))

        self.assignment = assignment
        if assignment.is_bye:
            self.state = LOBBY
            self._say("本轮轮空（BYE），不需要入房")
            return

        self.state = ASSIGNED
        self._say("已分配 第{}轮 桌{} room={}（等 roundStarted 再入房）".format(
            assignment.round_no, message.get("tableNo"), assignment.room_id))

    def _on_round_started(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self.assignment is None or self.assignment.is_bye:
            return None
        self.state = ROUND_OPEN
        return self._enter_room_message()

    def _enter_room_message(self) -> Optional[Dict[str, Any]]:
        """入房。**正式赛入房不要再带 AK**（细则 §2.3）。"""
        if self.assignment is None or not self.assignment.room_id:
            return None
        return {
            "commandType": Cmd.AI_ENTER_ROOM,
            "roomId": self.assignment.room_id,
        }

    def _on_room_entered(self, message: Dict[str, Any]) -> None:
        self.state = IN_ROOM
        self._say("已入房，等待 startGame（不要用 roomEntered 当开车信号）")

    def _on_start_game(self, message: Dict[str, Any]) -> None:
        self._begin_match(message)

    def _begin_match(self, message: Dict[str, Any]) -> None:
        key = self.assignment.key if self.assignment else None
        if key is not None and key in self._seen_keys:
            self._say("同一配桌重复 startGame，跳过重复初始化")
        elif key is not None:
            self._seen_keys.add(key)

        self.world.reset()
        self.controller.reset()
        frame = Frame.parse(message)
        self.world.on_start_game(frame)
        if self.bot_name:
            self.world.identify_self(name=self.bot_name)

        self.state = PLAYING
        self.recorder.start(self.assignment.match_code if self.assignment else "local")

        blocks = len(self.world.game_map.block_hulls) if self.world.game_map else 0
        borders = len(self.world.game_map.border_hulls) if self.world.game_map else 0
        self._say("开赛！地图 {}x{}，障碍凸块 {} 个，边界凸块 {} 个".format(
            int(self.world.game_map.width) if self.world.game_map else 0,
            int(self.world.game_map.height) if self.world.game_map else 0,
            blocks, borders))

    def _on_refresh_data(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._play_frame(message)

    def _play_frame(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """核心一帧：更新世界模型 → 决策 → 最多一个动作。"""
        if self.state not in (PLAYING, IN_ROOM):
            return None
        self.state = PLAYING

        frame = Frame.parse(message)
        before = len(self.world.collisions)
        self.world.on_frame(frame)

        # 新增的碰撞事件写进 replay —— 这是复盘每次得失分的依据
        for event in self.world.collisions[before:]:
            self.recorder.log_collision({
                "at": round(event.at_seconds, 2),
                "sprite": event.sprite_id,
                "is_self": event.sprite_id == self.world.self_id,
                "energy_spent": round(event.energy_spent, 1),
                "score_delta": event.score_delta,
                "kind": event.kind,
            })
            if event.sprite_id == self.world.self_id:
                self.controller.invalidate()

        action = self.strategy.decide()
        payload = action.to_message() if action else None
        self.recorder.log_frame(
            self.world.summary(),
            self.strategy.explain(),
            {**payload, "why": action.reason} if (payload and action) else None,
        )
        return payload

    def _on_close_game(self, message: Dict[str, Any]) -> None:
        """停止发送控制指令，但成绩以 matchFinished / roundFinished 为准。"""
        self.state = FINISHED
        me = self.world.me
        self._say("closeGame：停止操作。本地观测 果实={} 碰撞={} 次".format(
            me.score if me else "?", len(self.world.collisions)))

    def _on_match_finished(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        payload = {
            "match_code": message.get("matchCode"),
            "round_no": message.get("roundNo"),
            "rank": message.get("resultRank"),
            "advancement": message.get("advancementStatus"),
        }
        self.results.append(payload)
        self.recorder.log_result(payload)
        path = self.recorder.finish({
            "frames": self.recorder.frames,
            "collisions": len(self.world.collisions),
            "heart_pickups": self.world.heart_pickups,
            "final_score": self.world.me.score if self.world.me else None,
        })
        self._say("matchFinished 名次={} 晋级={} replay={}".format(
            payload["rank"], payload["advancement"], path))

        out: List[Dict[str, Any]] = []
        if self.auto_practice:
            # 训练闭环：先取比赛数据存档，再申请下一场
            out.append({"commandType": Cmd.GET_MY_BATTLE_DATA, "limit": 100})
            out.append({"commandType": Cmd.READY_FOR_NEXT_MATCH})
        return out

    def _on_round_finished(self, message: Dict[str, Any]) -> None:
        self._say("roundFinished（整轮权威结果）：{}".format(
            {k: message.get(k) for k in ("roundNo", "advancementStatus", "roundPoints")}))

    def _on_my_battle_data(self, message: Dict[str, Any]) -> None:
        data = message.get("data") or message.get("myBattleData") or []
        count = len(data) if isinstance(data, list) else 0
        self.recorder.write({"type": "battle_data", "count": count, "payload": data})
        self._say("已保存历史比赛数据 {} 条".format(count))

    def _on_error(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        code = str(message.get("code", ""))
        self._say("服务端错误 code={} {}".format(code, message.get("message", "")))

        if code == ErrCode.ROOM_NOT_OPEN:
            # 保持当前连接，按 retryAfterMs 重试；不要重新认证或换房间
            return {
                "__retry_after_ms": message.get("retryAfterMs", 2000),
                **(self._enter_room_message() or {}),
            }
        if code == ErrCode.BOT_ALREADY_ONLINE:
            self._say("⚠️ 同一 AK 已有连接。请确认没有第二个进程在跑，不要无限重试。")
        if code == ErrCode.BOT_NOT_ASSIGNED:
            self._say("⚠️ 只能进入最新 roundAssigned 给的房间。")
        return None

    # ------------------------------------------------------------------

    def _say(self, message: str) -> None:
        console("[firefly] " + message, quiet=self.quiet)


def _snake(camel: str) -> str:
    out: List[str] = []
    for ch in camel:
        if ch.isupper():
            out.append("_")
            out.append(ch.lower())
        else:
            out.append(ch)
    return "".join(out)
