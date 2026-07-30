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
from typing import Callable, Optional, Tuple

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

    #: R6 倒车迟滞的进入/退出阈值（rad）。100° 进、80° 出。
    #: 目标落在后半平面（>90°）时倒车才有靠近分量，所以阈值必须跨在 90° 两侧；
    #: 留 ±10° 的死区是为了不在边界上每帧翻转指令。
    _REVERSE_ENTER = math.radians(100.0)
    _REVERSE_EXIT = math.radians(80.0)

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
        #: 倒车迟滞状态。跨帧保留，所以必须在每局开始时清掉。
        self._reversing: bool = False
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

        # R6 ⭐ 目标在身后就倒车 —— 判据必须是**几何**，不是「已经快停下了」。
        #
        # 旧条件是 ``abs_err > 2.5rad(143°) and me.speed < 1.0``：两个都难满足，
        # 结果 4817 条移动指令里只有 **25 条（0.5%）** 是 goBack，等于倒车是死代码。
        # 于是误差在 90°~180° 之间时我们一直「朝前开 + 慢慢打方向」，而朝前开
        # 恰好在**远离**目标，要等 1~1.6s 转过来才开始靠近。现场实测的后果：
        #   * 追击（ram）帧里 **17%** 车头与目标夹角 >90°（在往反方向开）；
        #   * 逃离持心对手的帧里 **39%** 车头还朝着追我的人 —— 正是「不果断」。
        #
        # 为什么可以放心倒车：实测 goBack 的速度中位数 **5.00 px/帧**，与 goForward
        # **完全相同**，倒车不损失速度。所以只要目标落在车身后半平面（|err|>90°），
        # 倒车就严格优于前进：前进的靠近分量是 cos(err)<0（在跑远），倒车是
        # -cos(err)>0（在靠近）。碰撞只看车身接触，不看朝向，所以倒着撞一样算。
        #
        # 用 100°/80° 双阈值做迟滞，避免在 90° 附近来回切换指令（细则要求仅状态
        # 变化时发送，抖动会白白吃掉动作位）。转向照常继续，误差降下来就切回前进。
        move = FORWARD
        if allow_reverse:
            enter, exit_ = self._REVERSE_ENTER, self._REVERSE_EXIT
            if self._reversing:
                self._reversing = abs_err > exit_
            else:
                self._reversing = abs_err > enter
            if self._reversing:
                move = BACKWARD
        else:
            self._reversing = False
        return move, turn, rate

    def evade_point(self, me: Sprite, hazard: g.Point,
                    open_space: Optional[g.Point] = None,
                    is_clear: Optional[Callable[[g.Point], bool]] = None
                    ) -> Tuple[str, str, float]:
        """远离某个点（持心对手、抢不到的道具）。

        R6 ⭐ 「直接朝反方向跑」有两个坑，实测都踩到了：

        1.  **朝向问题** —— 反方向意味着当追我的人在正前方时要掉头 180°，转身
            那 1.6s 里车头还朝着他、还在前进，等于往对方怀里送。这一半由
            :meth:`steer_towards` 的倒车判据解决（目标在后半平面就倒车）。
        2.  **方向问题** —— 纯反方向会把自己逼进墙角：一旦贴住边界就再也拉不开
            距离，而持心方是零成本必胜，等于站着挨打。

        R9 ⭐ 逃跑方向改成**切向为主**（垂直于「我—追兵」连线），而不是径向后退。
        这正是「狮子与人」问题（Lion and Man，Rado 1920s；Besicovitch 1952 给出
        逃脱构造）的核心：在等速追逃里，**沿垂直于连线的方向移动，追兵无法缩短
        直线距离**；而径向后退在有界场地里必然把自己推到边界。

        ⚠️ 但那个定理**不能照搬**到这个游戏，两个前提都不成立：

        *   Besicovitch 的构造要求逃跑者能**瞬间**折向（每段都垂直于当前连线）。
            这里是车式运动，角速度上限 0.1 rad/帧，转 90° 要约 1.6s。
        *   经典结论说的是**圆盘**。这里是 1440×820 的矩形，还有石头 —— 角落是
            陷阱，圆盘没有角落。

        所以我们**只取那条可执行的结论**（切向优于径向），不假装能永远逃脱。
        已实测的有利条件是：持心方速度中位 5.00 px/帧，我方正常 4.63、上限同为
        5.00 —— **持心不加速**，所以等速前提是成立的，切向逃跑确实能维持距离。

        逃跑的目标不是「离他最远」，而是「能一直保持距离」—— 有退路比瞬时距离大
        更重要。
        """
        to_hazard = g.sub(hazard, me.position)
        #: **纯径向**的远离方向。瞄点可以掺切向，但「前进还是后退」必须拿它来判 ——
        #: 用掺过的方向去判会得出「朝追兵开」的结论（见下面的用例反例）。
        radial_away = g.normalize(g.scale(to_hazard, -1.0))
        if radial_away == (0.0, 0.0):
            radial_away = (math.cos(me.angle), math.sin(me.angle))
        away = radial_away

        unit = g.normalize(to_hazard)
        if unit != (0.0, 0.0):
            # 两条切向：选与「当前车头」以及「空旷方向」都更一致的那条，
            # 这样既不用急打方向，也不会切向切进墙里。
            left_t = (-unit[1], unit[0])
            right_t = (unit[1], -unit[0])
            ref = (math.cos(me.angle), math.sin(me.angle))
            if open_space is not None:
                to_open = g.normalize(g.sub(open_space, me.position))
                ref = g.normalize(g.add(ref, g.scale(to_open, 1.2)))
            tangent = left_t if g.dot(left_t, ref) >= g.dot(right_t, ref) else right_t
            # 切向为主、径向为辅。径向留 0.55 是因为我们**转不动那么快**：
            # 纯切向在车式运动下会被追兵切内线，掺一点后退能保住净距离。
            escape = g.normalize(g.add(g.scale(tangent, 1.0), g.scale(away, 0.55)))
            if escape != (0.0, 0.0) and g.dot(escape, away) > 0.0:
                away = escape

        target = g.add(me.position, g.scale(away, 320.0))
        _move, turn, rate = self.steer_towards(me, target, allow_reverse=True)

        # ⭐ 前进/后退**单独判**，不能交给 steer_towards。
        #
        # 切向瞄点的径向分量本来就小，而车头往往还没转过来；这时按「朝瞄点开」
        # 去前进，可能正好是在朝追兵靠近。自己的用例抓到过这个反例：追兵在车头
        # 右前方 30°，切向瞄点在 -60°，误差只有 60° 所以判前进 —— 结果每帧朝追兵
        # 靠近 cos30° = 0.87 个身位。
        #
        # 正确判据只有一条：**这一帧的位移在「远离追兵」方向上的投影必须为正**。
        # 位移只有 ±车头两种方向，所以直接取更远离的那个。转向照常朝切向掰，于是
        # 「先倒着拉开、同时把车头转到切向、转好了再切前进」自然涌现。
        nose = (math.cos(me.angle), math.sin(me.angle))
        radial = g.dot(nose, radial_away)   # >0 = 车头朝着「远离追兵」的方向
        if radial > 0.05:
            move = FORWARD
        elif radial < -0.05:
            move = BACKWARD
        else:
            # 正好垂直：两个方向都不改变距离，保持上一次的选择以免抖动。
            move = BACKWARD if self._reversing else FORWARD
        self._reversing = (move == BACKWARD)
        return move, turn, rate

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

        # R4 ⭐ 转不过来就先刹车 —— 不能一边朝着石头全速前进一边慢慢打方向。
        #
        # 现场 15 局实测（8 局 R2+R3，83 次撞障碍）把机制钉死了：
        #   * 危险检测**没有失灵**：83/83 次撞击前都报了警（100%）；
        #   * 但连续预警只有 **0.30s**（87% 不足 0.5s），此刻石头在正前方 31°、
        #     距离 53px、速度 5px/帧 ≈ 1.0s 到达；
        #   * 而切向脱离要转约 90°，按 0.1 rad/帧要 **1.6s** —— 物理上来不及；
        #   * 于是 94% 的情况下我们仍在前进/转向，70/83 帧发的是 goForward。
        # 提前预警（加大 lookahead/margin）是另一条路，但已有 30% 的帧在报警，
        # 再放大会让整局都在避障。所以这里改**降低闭合速度**：倒车立刻把 t_hit
        # 拉长，还顺带把车尾方向的空间让出来，转向照常继续。
        #
        # 判据：石头是不是**already 在转弯半径以内、且几乎正前方**。
        #
        # 车式运动的转弯半径 R = 速度(px/帧) / 角速度(rad/帧)。石头离得比 R 远时，
        # 打方向就能绕开，不需要减速；近于 R 且在正前方时，无论怎么打方向车身都会
        # 扫过它 —— 这时唯一的办法是先把闭合速度降下来。
        #
        # 第一版我写成「转到脱离航向的时间 > 撞上的时间」就刹车，结果太保守：
        # 实测追击中的 305 个报警帧里有 **149 帧（49%）** 本来正朝着目标前进，
        # 却被改成倒车，累计白丢约 15s 的接近时间。原因是那个判据要求转完整个 90°
        # 切向，而实际上只要侧向挪开一点点就能擦过去。改成下面这个几何判据后，
        # 只在真正躲不开时才刹车。
        rate = max(self.tune.bucket_turn_rate(RULE_TURN_RATE_MAX), 1e-6)
        speed = max(abs(me.speed), 1e-6)
        turn_radius = speed / rate
        nose = (math.cos(me.angle), math.sin(me.angle))
        closing = g.dot(to_hazard, nose)            # 1 = 正前方，<0 = 已在身后
        gap = max(0.0, g.distance(me.position, hazard)
                  - g.bounding_radius(me.width, me.height))

        if closing > 0.7 and gap < turn_radius:
            # 正前方且已在转弯半径内 → 转不出去，先倒车把闭合速度降下来。
            err = g.heading_error(me.angle, me.position, aim)
            turn = STRAIGHT if abs(err) < self.tune.heading_tolerance \
                else self.calib.command_for(err)
            return BACKWARD, turn, self.tune.bucket_turn_rate(RULE_TURN_RATE_MAX)

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
