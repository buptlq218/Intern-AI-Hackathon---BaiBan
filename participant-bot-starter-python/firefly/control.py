"""运动控制：把「我想去哪」翻译成合法指令流。

处理三个协议层面的硬约束：

1.  **每次回调最多一个动作**。所以这里维护「期望状态 vs 已发送状态」，每帧只发出
    优先级最高的那一个差异，其余留到后续帧。移动和转向是持续状态，晚一帧生效
    通常无所谓；出价错了却会直接丢一个果实，所以出价优先级更高。
2.  **相同指令仅在状态变化时发送**。所有指令都过 ``_changed`` 检查。
3.  **转向 data 是角速度标量（0.01~0.1），方向由 commandType 决定**。左右不是靠正负号。

另外解决一个文档没说清的问题：``turnLeft`` 到底让 ``angle`` 变大还是变小？屏幕坐标
y 向下，符号约定不确定，猜错会导致「越转越偏」这种极难 debug 的行为。所以这里
**在线标定**：记录自己发出的转向指令与随后 ``angle`` 的实际变化，几帧内就能定出符号。
标定完成前用保守的小角速度试探，不会造成大偏航。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple

from . import geometry as g
from . import protocol as P
from .constants import RULE_TURN_RATE_MAX, Tune
from .protocol import Action, Sprite

STRAIGHT = "straight"
LEFT = "left"
RIGHT = "right"

FORWARD = "forward"
BACKWARD = "backward"
HALT = "halt"


@dataclass
class TurnCalibration:
    """在线标定 turnLeft 对应 angle 的增减方向。

    ``sign`` 的含义：发送 turnLeft 时 ``angle`` 的变化符号。
    +1 表示 turnLeft 使 angle 增大；-1 表示减小。

    默认取 **-1**：官方 starter 的基准策略用的是
    ``turnRight if delta > 0 else turnLeft``（delta = 目标角 - 当前角），
    即「要把 angle 调大就右转」→ turnLeft 使 angle 减小。
    在线标定仍然保留，以防不同版本约定不一致。
    """

    sign: int = -1
    _votes: int = 0
    #: 需要几票一致才认为标定完成。太小会被单帧噪声骗到。
    _needed: int = 3

    @property
    def calibrated(self) -> bool:
        return self.sign != 0 and abs(self._votes) >= self._needed

    def observe(self, last_turn: str, delta_angle: float) -> None:
        """喂入一次观测：上一帧发的转向指令，以及本帧 angle 的变化量。"""
        if last_turn not in (LEFT, RIGHT):
            return
        if abs(delta_angle) < 1e-4:
            return  # 没转动，无信息
        # 归一化成「turnLeft 会让 angle 怎么变」
        observed = 1 if delta_angle > 0 else -1
        if last_turn == RIGHT:
            observed = -observed
        self._votes += observed
        if abs(self._votes) >= self._needed:
            self.sign = 1 if self._votes > 0 else -1

    def command_for(self, desired_delta: float) -> str:
        """想让 angle 变化 desired_delta，应该发左转还是右转。"""
        sign = self.sign if self.sign != 0 else -1
        if desired_delta * sign > 0:
            return LEFT
        return RIGHT


@dataclass
class DesiredState:
    """这一帧「希望精灵处于」的状态。"""

    move: str = FORWARD
    turn: str = STRAIGHT
    turn_rate: float = 0.05
    attack: Optional[float] = None
    #: 出价是否紧急（预计很快就要接触）。紧急时抢占移动指令的发送位。
    attack_urgent: bool = False


class Controller:
    """期望状态 → 单个动作。每局开始前必须 ``reset()``。"""

    def __init__(self, tune: Tune) -> None:
        self.tune = tune
        self.calib = TurnCalibration()
        self.reset()

    def reset(self) -> None:
        self._sent_move: Optional[str] = None
        self._sent_turn: Optional[str] = None
        self._sent_rate: Optional[float] = None
        self._sent_attack: Optional[float] = None
        self._last_turn_cmd: str = STRAIGHT
        self._prev_angle: Optional[float] = None
        # 标定信息跨局保留（同一引擎，符号不会变），但票数重置以防上一局污染。
        self.calib = TurnCalibration(sign=self.calib.sign)

    # ------------------------------------------------------------------

    def observe(self, me: Sprite) -> None:
        """每帧喂入自身状态，推进转向符号标定。"""
        if self._prev_angle is not None:
            delta = g.normalize_angle(me.angle - self._prev_angle)
            self.calib.observe(self._last_turn_cmd, delta)
        self._prev_angle = me.angle

    # ------------------------------------------------------------------

    def steer_towards(
        self, me: Sprite, target: g.Point, allow_reverse: bool = True
    ) -> Tuple[str, str, float]:
        """算出朝目标前进所需的 (move, turn, rate)。"""
        err = g.heading_error(me.angle, me.position, target)
        abs_err = abs(err)

        if abs_err <= self.tune.heading_tolerance:
            return FORWARD, STRAIGHT, self.tune.turn_rate_buckets[0]

        # 误差越大转得越猛，量化到档位避免每帧抖动重发。
        desired_rate = min(RULE_TURN_RATE_MAX, abs_err / math.pi * RULE_TURN_RATE_MAX)
        rate = self.tune.bucket_turn_rate(desired_rate)
        turn = self.calib.command_for(err)

        # 目标在正后方：原地打方向盘转过去最慢。速度已经很低时倒车更容易脱身。
        move = FORWARD
        if allow_reverse and abs_err > self.tune.reverse_threshold and me.speed < 1.0:
            move = BACKWARD
        return move, turn, rate

    def evade_point(self, me: Sprite, hazard: g.Point) -> Tuple[str, str, float]:
        """远离某个点（持心对手、抢不到的道具）。直接朝反方向跑。"""
        away = g.add(me.position, g.sub(me.position, hazard))
        return self.steer_towards(me, away, allow_reverse=True)

    def avoid_obstacle(
        self, me: Sprite, hazard: g.Point, goal: Optional[g.Point] = None
    ) -> Tuple[str, str, float]:
        """绕开障碍物。

        关键点：**切向绕行，不要原地掉头**。精灵是车式运动，「远离障碍」等于要求
        它掉头 180°，转向期间车头仍朝着墙，结果是一路磨着墙走、反复吃 -1。
        沿垂直方向绕过去要快得多，也不用放弃原本的目标。
        """
        to_hazard = g.normalize(g.sub(hazard, me.position))
        if to_hazard == (0.0, 0.0):
            return FORWARD, STRAIGHT, self.tune.turn_rate_buckets[0]

        # 障碍方向的两条切线
        left_t = (-to_hazard[1], to_hazard[0])
        right_t = (to_hazard[1], -to_hazard[0])

        if goal is not None:
            ref = g.normalize(g.sub(goal, me.position))
        else:
            # 没有目标时选与当前车头更一致的那条，避免急打方向
            ref = (math.cos(me.angle), math.sin(me.angle))

        tangent = left_t if g.dot(left_t, ref) >= g.dot(right_t, ref) else right_t
        # 切向里掺一点「离开障碍」的分量，保证净距离在增大
        escape = g.normalize(g.add(g.scale(tangent, 1.0),
                                   g.scale(to_hazard, -0.45)))
        aim = g.add(me.position, g.scale(escape, 260.0))
        return self.steer_towards(me, aim, allow_reverse=False)

    def unstick(self, me: Sprite, hazard: g.Point) -> Tuple[str, str, float]:
        """已经贴住障碍、几乎停住：先倒车拉开距离，同时把车头往切向掰。"""
        to_hazard = g.normalize(g.sub(hazard, me.position))
        ref = (math.cos(me.angle), math.sin(me.angle))
        left_t = (-to_hazard[1], to_hazard[0])
        right_t = (to_hazard[1], -to_hazard[0])
        tangent = left_t if g.dot(left_t, ref) >= g.dot(right_t, ref) else right_t
        aim = g.add(me.position, g.scale(tangent, 200.0))
        err = g.heading_error(me.angle, me.position, aim)
        turn = STRAIGHT if abs(err) < self.tune.heading_tolerance else \
            self.calib.command_for(err)
        rate = self.tune.bucket_turn_rate(RULE_TURN_RATE_MAX)
        return BACKWARD, turn, rate

    # ------------------------------------------------------------------

    def emit(self, desired: DesiredState) -> Optional[Action]:
        """把期望状态压成**一个**动作；无差异时返回 None（这一帧不发送）。

        优先级：
          1. 从未设置过攻击强度（默认值只有 50，开局就可能吃亏）
          2. 紧急出价（马上要接触了）
          3. 移动状态变化（含避障脱离）
          4. 转向状态变化
          5. 常规出价变化
        """
        attack_changed = (
            desired.attack is not None
            and (self._sent_attack is None
                 or abs(desired.attack - self._sent_attack) >= 1.0)
        )

        if attack_changed and self._sent_attack is None:
            return self._send_attack(desired.attack, "开局先设攻击强度，避免用默认 50")

        if attack_changed and desired.attack_urgent:
            return self._send_attack(desired.attack, "接触在即，优先校正出价")

        if desired.move != self._sent_move:
            return self._send_move(desired.move)

        if desired.turn != self._sent_turn or (
            desired.turn in (LEFT, RIGHT)
            and (self._sent_rate is None
                 or abs(desired.turn_rate - self._sent_rate) > 1e-6)
        ):
            return self._send_turn(desired.turn, desired.turn_rate)

        if attack_changed:
            return self._send_attack(desired.attack, "常规出价更新")

        return None

    # ------------------------------------------------------------------

    def _send_move(self, move: str) -> Action:
        self._sent_move = move
        if move == FORWARD:
            return P.go_forward("前进")
        if move == BACKWARD:
            return P.go_back("倒车脱离")
        return P.stop("停止")

    def _send_turn(self, turn: str, rate: float) -> Action:
        self._sent_turn = turn
        self._sent_rate = rate
        self._last_turn_cmd = turn
        if turn == LEFT:
            return P.turn_left(rate, "左转")
        if turn == RIGHT:
            return P.turn_right(rate, "右转")
        self._sent_rate = None
        return P.steer_back("回正方向盘")

    def _send_attack(self, value: float, reason: str) -> Action:
        self._sent_attack = value
        return P.set_attack_value(value, reason)

    # ------------------------------------------------------------------

    def invalidate(self) -> None:
        """碰撞/反弹后精灵状态可能被引擎打断，强制下一帧重发移动意图。

        细则 §6：反弹结束后精灵会恢复碰撞前的移动/转向指令状态。所以严格来说
        不必重发，但反弹期间我们的目标通常已经变了，主动失效更安全。
        """
        self._sent_move = None
        self._sent_turn = None
        self._sent_rate = None
