"""战斗策略入口 —— 官方 SDK 只调用这个文件。

真正的决策逻辑在 ``firefly/`` 包里（分层、可单测、零三方依赖）。这个文件只做三件事：

1.  把官方契约（``choose_command(game_state, bot_id)`` → 一个动作 dict）翻译成
    引擎的输入输出；
2.  维护官方帧里**缺失的信息**（见下）；
3.  保证任何异常都不会拖垮连接 —— 出错就返回 ``stop``，并且不抛给 bot.py。

## 官方契约里三个必须自己补的坑

**① 帧里没有时间。** ``refreshData.data`` 只有 ``rabbits`` 和 ``goldCarrot``，
没有 ``elapsedSeconds`` / ``remainingTime``。但**两个 30 秒周期**（能量重置、
无碰撞惩罚 -3）都依赖时间。所以这里用本地单调时钟，在 ``on_start_game`` 时对零；
能量重置的相位还会被引擎观测到的实际重置二次校正。

**② 帧里没有地图。** ``map`` 只在 ``startGame`` 下发一次，而官方
``choose_command`` 拿不到它 —— 所以避障本来是做不了的。解决办法是在 bot.py 的
``startGame`` 分支里加一行，调用本文件的 :func:`on_start_game`。
没有这个 hook 时策略仍然能跑，只是退化成「只躲边缘、不躲石头」。

**③ 必须返回一个合法 dict，不能返回 None。** bot.py 的 ``normalize_command``
对 None 会抛 ValueError 并降级成 ``stop``。但引擎在「状态没变化」时本应什么都不发
（细则要求仅在状态变化时发送）。折中办法：这种帧重发上一条**移动**指令 ——
移动是持续状态，重发是幂等的，不会打断转向。

## 参数调整

策略参数集中在 ``firefly/constants.py`` 的 ``TUNE``。**Loop 每轮只改一个。**
改完跑 ``python mytests/run_all.py`` 回归。
"""

import math
import os
import time

from firefly.constants import BOT_VERSION, TUNE
from firefly.control import Controller
from firefly.protocol import Frame
from firefly.strategy import Strategy
from firefly.worldmodel import WorldModel

STRATEGY_IMPLEMENTED = True

#: 设为 1 时每帧往 stderr 打一行决策解释，用于现场定位行为偏差。
DEBUG = os.environ.get("FIREFLY_DEBUG") == "1"

_STOP = {"commandType": "stop"}
#: 移动类指令重发是幂等的，可以安全地用来填「本帧无变化」。
_IDEMPOTENT_MOVES = ("goForward", "goBack", "stop")


class _Session:
    """一局比赛的状态。检测到新的一局会自动重置。"""

    def __init__(self):
        self.world = WorldModel(tune=TUNE)
        self.controller = Controller(TUNE)
        self.strategy = Strategy(TUNE, self.world, self.controller)
        self.started_at = None          # 本局开始的单调时钟
        self.last_move = None           # 最近一次发出的移动指令
        self.frames = 0
        self.map_ready = False

    # -- 时钟 ---------------------------------------------------------

    def elapsed(self):
        """本局已进行的秒数（本地单调时钟）。"""
        if self.started_at is None:
            self.started_at = time.monotonic()
            return 0.0
        return time.monotonic() - self.started_at

    def begin(self, start_data):
        """startGame：重置本局状态并缓存地图。"""
        self.world.reset()
        self.controller.reset()
        self.started_at = time.monotonic()
        self.last_move = None
        self.frames = 0

        payload = start_data if isinstance(start_data, dict) else {}
        frame = Frame.parse({"commandType": "startGame", "timeStamp": 0,
                             "data": payload})
        self.world.on_start_game(frame)
        blocks = len(self.world.game_map.block_hulls) if self.world.game_map else 0
        self.map_ready = blocks > 0
        if DEBUG:
            _debug("startGame：障碍凸块 {} 个，边界凸块 {} 个".format(
                blocks,
                len(self.world.game_map.border_hulls) if self.world.game_map else 0))


_session = _Session()


def _debug(message):
    import sys
    sys.stderr.write("[firefly] " + message + "\n")
    sys.stderr.flush()


def _resolve_self_id(rabbits, bot_id):
    """在帧里找到「我」。

    官方基准策略同时兼容 ``str(botId)`` 和 ``"ai:" + str(botId)``
    （本地 sample 服务会加 ``ai:`` 前缀），这里保持一致。
    """
    expected = str(bot_id)
    prefixed = "ai:" + expected
    for rabbit in rabbits:
        if not isinstance(rabbit, dict):
            continue
        rid = str(rabbit.get("id"))
        if rid == expected or rid == prefixed:
            return rid
    return None


def _is_active(rabbit):
    active = rabbit.get("active")
    return active is not False and active != "false"


# 关于「怎么知道换了一局」：只依赖 bot.py 的 on_start_game hook。
#
# 曾经想过用数据形态兜底猜测（所有精灵满能量 + 果实 = 10 → 新的一局），
# 但这是**错的**：能量每 30 秒对所有精灵重置为 1000，若此时还没人得失分，
# 果实也仍是 10 —— 于是每个 30 秒窗口开头都会被误判成新的一局，
# 把缓存的地图和对手模型一起清掉。所以宁可不猜。


# ---------------------------------------------------------------------------
# bot.py 调用的可选 hook
# ---------------------------------------------------------------------------

def on_start_game(start_data):
    """由 bot.py 在收到 ``startGame`` 时调用，用来缓存地图并重置本局状态。

    这是**避障能力的前提** —— ``map`` 只在 startGame 下发一次，
    而 ``choose_command`` 拿不到它。
    """
    try:
        _session.begin(start_data)
    except Exception as error:          # hook 不能影响比赛
        if DEBUG:
            _debug("on_start_game 失败：{}".format(error))


# ---------------------------------------------------------------------------
# 官方契约
# ---------------------------------------------------------------------------

def choose_command(game_state, bot_id):
    """每约 100ms 调用一次，每次最多返回一个动作。

    :param game_state: 服务端最新 ``refreshData.data``（dict）
    :param bot_id: ``botConnected`` 返回的本人 BOT ID
    :return: ``{"commandType": str, "data": str（可选）}``，**绝不返回 None**
    """
    session = _session

    rabbits = game_state.get("rabbits") if isinstance(game_state, dict) else None
    if not isinstance(rabbits, list):
        rabbits = []

    self_id = _resolve_self_id(rabbits, bot_id)
    if self_id is None:
        return dict(_STOP)              # 找不到本人：必须停止

    me_raw = next((r for r in rabbits
                   if isinstance(r, dict) and str(r.get("id")) == self_id), None)
    if me_raw is None or not _is_active(me_raw):
        return dict(_STOP)              # 已淘汰：不要再往房间发无效动作
    position = me_raw.get("position")
    if not isinstance(position, dict):
        return dict(_STOP)

    session.frames += 1
    session.world.identify_self(sprite_id=self_id)

    frame = Frame.parse({
        "commandType": "refreshData",
        "timestamp": 0,
        "data": game_state,
    })
    session.world.on_frame(frame, elapsed=session.elapsed())

    action = session.strategy.decide()

    if DEBUG:
        _debug("{:6.1f}s {} -> {}".format(
            session.world.elapsed,
            session.strategy.explain()[:110],
            (action.command_type if action else "(无变化)")))

    if action is None:
        # 状态没变化。契约不允许返回 None，所以重发上一条移动指令（幂等，
        # 不会打断持续转向）；还没发过任何移动就先前进。
        return {"commandType": session.last_move or "goForward"}

    command = {"commandType": action.command_type}
    if action.data is not None:
        command["data"] = action.data
    if action.command_type in _IDEMPOTENT_MOVES:
        session.last_move = action.command_type
    return command
