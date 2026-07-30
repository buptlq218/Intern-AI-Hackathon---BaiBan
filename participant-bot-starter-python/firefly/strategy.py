"""决策函数：一帧状态进，最多一个动作出。

## 优先级阶梯（顺序即优先级，命中即返回）

0.  已淘汰 / 不在场 → 不发指令
1.  **持有森林之心** → 全力追击。碰撞不耗能、对未持心者必胜、撞障碍不扣果实。
    10s 窗口 × 1.5s 冷却 ≈ 最多 6 次免费 +1，这是全局最高价值的事，压过一切。
2.  **对手持有森林之心且逼近** → 逃。我方必输 -1 而对方零成本，没有任何博弈空间。
3.  **森林之心已刷新** → 比 ETA 决定抢或撤。抢不到还待在附近，等于给持心者送分。
4.  **即将撞障碍** → 脱离。每次 -1 是纯损失，且不带来任何收益。
5.  **无碰撞惩罚即将触发** → 保活。找不到精灵目标就主动撞障碍：**-1 优于 -3**。
6.  **能量不足以赢下一次碰撞** → 避战，等 30s 重置。
7.  **有优势目标** → 主动撞。
8.  兜底 → 巡航保持机动。

## 为什么第 5 条要「主动撞障碍」

细则 §5.3：连续 30s 未与其他精灵或障碍物碰撞扣 3 果实；撞障碍物扣 1 果实。
两者都会重置无碰撞计时。所以在实在找不到安全精灵目标时，主动付 1 分买掉 3 分的
罚单，净赚 2 分。这是一个有保底的下界策略，而不是消极行为。
（⚠️ 前提是「边缘/障碍接触确实会重置计时」，见 docs/EXPERIMENTS.md E1/E2。）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from . import control as ctl
from . import geometry as g
from .attack import AttackDecision, decide_attack
from .constants import RULE_FRAME_INTERVAL, Tune
from .control import Controller, DesiredState
from .protocol import Action, Sprite
from .worldmodel import WorldModel


@dataclass
class Intent:
    """本帧的战术意图。分离「想干什么」与「怎么发指令」，两边都好测。"""

    kind: str
    target: Optional[g.Point] = None
    hazard: Optional[g.Point] = None
    commit_contact: bool = False     # 是否已决定主动接触（喂给梭哈判断）
    avoid_obstacles: bool = True
    reason: str = ""


class Strategy:
    """状态机 + 优先级阶梯。无状态副作用集中在 WorldModel 与 Controller。"""

    def __init__(self, tune: Tune, world: WorldModel, controller: Controller) -> None:
        self.tune = tune
        self.world = world
        self.controller = controller
        self.last_intent: Optional[Intent] = None
        self.last_attack: Optional[AttackDecision] = None

    # ------------------------------------------------------------------

    def decide(self) -> Optional[Action]:
        """主入口：返回本帧要发送的唯一动作，或 None。"""
        world = self.world
        me = world.me
        if me is None or not me.alive:
            return None

        self.controller.observe(me)

        intent = self.choose_intent(me)
        self.last_intent = intent

        attack = decide_attack(
            self.tune,
            energy=me.energy,
            threat=world.threat_level(),
            seconds_to_reset=world.seconds_to_energy_reset,
            invincible=me.invincible,
            committing_to_contact=intent.commit_contact,
        )
        self.last_attack = attack

        desired = self.plan_motion(me, intent)
        desired.attack = attack.value
        desired.attack_urgent = self._contact_imminent(me)

        return self.controller.emit(desired)

    # ------------------------------------------------------------------
    # 意图选择
    # ------------------------------------------------------------------

    def choose_intent(self, me: Sprite) -> Intent:
        world = self.world
        t = self.tune

        # --- 1. 我持森林之心：免费输出窗口，优先级最高 -----------------
        if me.invincible:
            victim = self._best_heart_victim(me)
            if victim is not None:
                return Intent(
                    "heart_rampage",
                    target=victim.position,
                    commit_contact=True,
                    avoid_obstacles=False,   # 持心撞障碍不扣果实，不必绕
                    reason="持森林之心，追击 {}（免费必胜）".format(victim.name or victim.id),
                )
            return Intent(
                "heart_hunt_none",
                target=world.map_center(),
                avoid_obstacles=False,
                reason="持森林之心但无可撞目标，往中场找人",
            )

        # --- 2. 对手持心且逼近：必输，只能躲 ---------------------------
        threat_holder = self._nearest_invincible_rival(me)
        if threat_holder is not None:
            dist = g.distance(me.position, threat_holder.position)
            if dist < t.flee_invincible_radius:
                return Intent(
                    "flee_invincible",
                    hazard=threat_holder.position,
                    commit_contact=False,
                    reason="{} 持森林之心且距离 {:.0f}，必输 → 逃".format(
                        threat_holder.name or threat_holder.id, dist
                    ),
                )

        # --- 3. 森林之心刷新：抢 or 撤 ---------------------------------
        carrot = world.gold_carrot
        if carrot is not None:
            decision = self._contest_heart(me, carrot)
            if decision is not None:
                return decision

        # --- 4. 已经贴住障碍动不了：这是唯一需要「接管」意图的障碍情况 ----
        #
        # 普通避障**不在这个阶梯里**，而是在 plan_motion 里作为运动层滤波统一施加。
        # 原因：避障几乎对每个意图都适用，把它做成一根横杆会让排在它前面的意图
        # （抢道具、逃离持心对手）完全绕过避障。沙盒实测过这个坑：seek_heart
        # 一路把 clearance 从 128 磨到 0，从没触发过避障，最后撞墙撞到淘汰。
        idle_pressure = world.seconds_since_self_collision >= t.idle_obstacle_fallback_at
        if not idle_pressure and self._stuck_against_obstacle(me):
            hazard = self._imminent_obstacle(me)
            if hazard is not None:
                return Intent(
                    "unstick_obstacle",
                    hazard=hazard,
                    commit_contact=False,
                    reason="已贴住障碍且几乎停住 → 倒车脱离（光转向会一路磨墙）",
                )

        # --- 5. 无碰撞惩罚兜底 -----------------------------------------
        idle_for = world.seconds_since_self_collision
        if idle_for >= t.idle_seek_at:
            target = self._cheapest_interaction(me)
            if target is not None:
                kind, point = target
                return Intent(
                    kind,
                    target=point,
                    commit_contact=True,
                    avoid_obstacles=(kind != "idle_hit_obstacle"),
                    reason="已空转 {:.0f}s（{:.0f}s 后 -3）→ {}".format(
                        idle_for, world.seconds_to_idle_penalty, kind
                    ),
                )

        posture = self.endgame_posture(me)

        # --- 5.5 终局领先：保成果 --------------------------------------
        # 一次失败碰撞既丢名次分又丢 tiebreak 的果实。领先时不必再冒险。
        if posture == "protect":
            danger = self._nearest_rival(me)
            if danger is not None and g.distance(me.position, danger.position) < 260.0:
                return Intent(
                    "protect_lead",
                    hazard=danger.position,
                    commit_contact=False,
                    reason="终局领先 {:.0f} 果实，剩 {:.0f}s → 避免不必要碰撞".format(
                        world.score_margin_to_cutoff(), world.remaining
                    ),
                )

        # --- 6. 能量不足，赢不了 ---------------------------------------
        probe = decide_attack(
            t, me.energy, world.threat_level(), world.seconds_to_energy_reset
        )
        # 只有「连平都做不到」才避战 —— 平局不丢果实，还免费重置无碰撞计时。
        # 眼看要垫底（0 分）时没有下行空间，不利赔率也得打。
        if t.low_energy_flee and not probe.worth_engaging and posture != "desperate":
            nearest = self._nearest_rival(me)
            return Intent(
                "conserve",
                hazard=nearest.position if nearest else None,
                target=world.map_center() if nearest is None else None,
                commit_contact=False,
                reason="能量 {:.0f} 打不赢（需 {:.0f}），{:.0f}s 后重置 → 避战".format(
                    me.energy, probe.value, world.seconds_to_energy_reset
                ),
            )

        # --- 7. 主动进攻 -----------------------------------------------
        prey = self._best_target(me, allow_unfavourable=(posture == "desperate"))
        if prey is not None:
            return Intent(
                "ram",
                target=prey.position,
                commit_contact=True,
                reason="进攻 {}（其果实 {:.0f}，威胁 {:.0f}）".format(
                    prey.name or prey.id, prey.score, world.threat_of(prey.id)
                ),
            )

        # --- 8. 兜底巡航 -----------------------------------------------
        return Intent(
            "patrol",
            target=world.map_center(),
            commit_contact=False,
            reason="无明确目标，保持机动",
        )

    # ------------------------------------------------------------------
    # 目标选择辅助
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # 终局姿态
    # ------------------------------------------------------------------

    def endgame_posture(self, me: Sprite) -> str:
        """终局时该保成果还是该拼一把。

        依据积分规则：每轮按名次积 3/2/1/0 分，同分取果实多者，4 进 2。
        推论是**不对称的**：

        *   3 名→2 名、2 名→1 名都只值 1 分；但 3 名→4 名要丢掉最后 1 分，
            而且果实还是总榜的第一顺位 tiebreak。
        *   所以领先时「少输」比「多赢」更值钱 —— 一次失败碰撞既丢分又丢 tiebreak。
        *   反过来，眼看要垫底（0 分）时，不利赔率的碰撞也值得打，
            因为再差也就是 0 分，没有下行空间了。

        返回 ``"protect"`` / ``"normal"`` / ``"desperate"``。
        """
        t = self.tune
        if self.world.remaining > t.endgame_seconds:
            return "normal"
        margin = self.world.score_margin_to_cutoff()
        if margin >= t.protect_margin:
            return "protect"
        if margin <= t.desperate_margin:
            return "desperate"
        return "normal"

    def _underlying_goal(self, me: Sprite) -> g.Point:
        """避障时「本来想去哪」，用来在两条切向中选保留进度的那条。"""
        carrot = self.world.gold_carrot
        if carrot is not None:
            return carrot
        prey = self._best_target(me)
        if prey is not None:
            return prey.position
        return self.world.map_center()

    def _nearest_rival(self, me: Sprite) -> Optional[Sprite]:
        rivals = self.world.rivals
        if not rivals:
            return None
        return min(rivals, key=lambda r: g.distance(me.position, r.position))

    def _nearest_invincible_rival(self, me: Sprite) -> Optional[Sprite]:
        holders = [r for r in self.world.rivals if r.invincible]
        if not holders:
            return None
        return min(holders, key=lambda r: g.distance(me.position, r.position))

    def _best_heart_victim(self, me: Sprite) -> Optional[Sprite]:
        """持心期间的最佳目标：近、且不在碰撞冷却里、且自己没持心。"""
        candidates = [
            r for r in self.world.rivals
            if not r.invincible
            and self.world.can_collide_with(r.id)
            and g.distance(me.position, r.position) <= self.tune.heart_chase_radius
        ]
        if not candidates:
            # 冷却中的也行，10s 很短，跑过去时冷却大概也过了
            candidates = [r for r in self.world.rivals if not r.invincible]
        if not candidates:
            return None
        return min(candidates, key=lambda r: g.distance(me.position, r.position))

    def _contest_heart(self, me: Sprite, carrot: g.Point) -> Optional[Intent]:
        """抢森林之心，还是躲开它？

        森林之心的期望收益很高（10s 免费输出，理论上 +3~+6 果实），所以只要 ETA
        不明显劣于最快对手就应该去抢。但抢不到又赖在附近是最差的选择 —— 持心者
        会拿我们当免费果实。所以「抢不到」时明确远离。
        """
        # 用巡航速度而非瞬时速度：瞬时速度会因反弹/转向剧烈波动，
        # 导致「抢」与「不抢」每几帧翻转一次。
        my_eta = self.world.eta_for(me, carrot)

        best_rival_eta = float("inf")
        for r in self.world.rivals:
            best_rival_eta = min(best_rival_eta, self.world.eta_for(r, carrot))

        if my_eta <= best_rival_eta * self.tune.heart_contest_eta_ratio:
            return Intent(
                "seek_heart",
                target=carrot,
                commit_contact=False,   # 去吃道具，不是去撞人，别梭哈能量
                reason="抢森林之心（我 {:.1f}s / 最快对手 {:.1f}s）".format(
                    my_eta, best_rival_eta
                ),
            )
        return Intent(
            "yield_heart",
            hazard=carrot,
            commit_contact=False,
            reason="抢不到森林之心（我 {:.1f}s / 对手 {:.1f}s）→ 远离，别当免费果实".format(
                my_eta, best_rival_eta
            ),
        )

    def _best_target(
        self, me: Sprite, allow_unfavourable: bool = False
    ) -> Optional[Sprite]:
        """给每个对手打分，选最优进攻目标。

        打分偏好：近、赢面大、对手果实少（有机会打到淘汰，且淘汰后场上少一个威胁）。
        在冷却中的目标直接排除 —— 贴上去也不结算。

        :param allow_unfavourable: 终局眼看要垫底时置 True，此时接受赔率不利的
            碰撞 —— 第 4 名已经是 0 分，没有下行空间了。
        """
        world = self.world
        t = self.tune
        candidates = [
            r for r in world.rivals
            if not r.invincible and world.can_collide_with(r.id)
        ]
        if not candidates:
            return None

        my_bid = decide_attack(
            t, me.energy, world.threat_level(), world.seconds_to_energy_reset
        ).value

        best: Optional[Sprite] = None
        best_score = float("-inf")
        for r in candidates:
            dist = g.distance(me.position, r.position)
            # 归一化距离：整张地图对角线约 1650px
            near = 1.0 - min(1.0, dist / 1650.0)
            their_threat = world.threat_of(r.id)   # 已按对手当前能量截断
            winning = 1.0 if my_bid > their_threat else 0.0
            # 对手果实越少，打掉他的边际价值越高
            weakness = 1.0 - min(1.0, r.score / 20.0)
            # ⭐ 能量枯竭的对手是白送的果实：actualAttack = min(设定, 能量)，
            # 能量低意味着他这次最多只能打出这么点，赢他几乎没有代价。
            drained = 1.0 - min(1.0, r.energy / 1000.0)

            score = (
                t.w_distance * near
                + t.w_winrate * winning
                + t.w_target_fruit * weakness
                + t.w_target_drained * drained
            )
            if score > best_score:
                best, best_score = r, score

        # 一定会输的目标不要硬送：交给上层的避战分支。
        # 注意用 ``<`` 而不是 ``<=`` —— 出价与对手相等是**平局**，不丢果实，
        # 且免费重置无碰撞计时，值得打。
        # 终局垫底时更进一步：连不利赔率也接受，因为 0 分已经没有下行空间。
        if (best is not None and not allow_unfavourable
                and my_bid < world.threat_of(best.id)):
            return None
        return best

    def _cheapest_interaction(self, me: Sprite) -> Optional[Tuple[str, g.Point]]:
        """保活模式下最便宜的一次互动。

        优先级：能赢的精灵（+1）> 任意精灵（可能 -1）> 障碍物（确定 -1，但省下 -3）。
        """
        world = self.world
        idle_for = world.seconds_since_self_collision

        winnable = self._best_target(me)
        if winnable is not None:
            return "idle_ram", winnable.position

        # 时间还够就先找人；快到点了就认命撞障碍
        if idle_for < self.tune.idle_obstacle_fallback_at:
            nearest = self._nearest_rival(me)
            if nearest is not None and not nearest.invincible:
                return "idle_ram_risky", nearest.position

        obstacle = world.nearest_obstacle_point(me.position)
        if obstacle is not None:
            return "idle_hit_obstacle", obstacle
        nearest = self._nearest_rival(me)
        if nearest is not None:
            return "idle_ram_risky", nearest.position
        return None

    # ------------------------------------------------------------------
    # 危险检测
    # ------------------------------------------------------------------

    def _imminent_obstacle(self, me: Sprite) -> Optional[g.Point]:
        """沿当前速度短期外推，判断是否即将撞上障碍物或贴边。

        注意 velocity 是 px/frame，所以前瞻秒数必须换算成帧数
        （见 geometry.extrapolate 的单位说明）。
        """
        t = self.tune
        world = self.world
        radius = g.bounding_radius(me.width, me.height) + t.obstacle_safety_margin

        frames = g.seconds_to_frames(t.obstacle_lookahead_seconds, RULE_FRAME_INTERVAL)
        future = g.extrapolate(me.position, me.velocity, frames)

        # 当前位置和外推位置都检查：已经贴住障碍时外推点可能已在物体另一侧
        for probe in (me.position, future):
            clearance, hull = world.obstacle_clearance(probe)
            if hull is not None and clearance < radius:
                return min(hull, key=lambda p: g.distance(probe, p))
            if world.border_clearance(probe) < t.border_keepout:
                return self._border_hazard_point(probe)
        return None

    def _stuck_against_obstacle(self, me: Sprite) -> bool:
        """已经贴住障碍且几乎动不了 —— 这种状态下光转向没用，得先倒车脱开。"""
        radius = g.bounding_radius(me.width, me.height)
        clearance, hull = self.world.obstacle_clearance(me.position)
        if hull is None:
            return False
        return clearance < radius * 0.8 and me.speed < 1.5

    def _border_hazard_point(self, point: g.Point) -> g.Point:
        """把最近的那条边映射成一个「危险点」，方便统一用 evade 处理。"""
        world = self.world
        w = world.game_map.width if world.game_map else 1440.0
        h = world.game_map.height if world.game_map else 820.0
        options = [
            ((0.0, point[1]), point[0]),
            ((w, point[1]), w - point[0]),
            ((point[0], 0.0), point[1]),
            ((point[0], h), h - point[1]),
        ]
        return min(options, key=lambda o: o[1])[0]

    def _contact_imminent(self, me: Sprite) -> bool:
        """是否很快会与某个对手接触 —— 用来抢占出价的发送优先级。"""
        radius = g.bounding_radius(me.width, me.height)
        horizon = g.seconds_to_frames(0.8, RULE_FRAME_INTERVAL)
        for r in self.world.rivals:
            _, dist = g.closest_approach(
                me.position, me.velocity, r.position, r.velocity, horizon=horizon
            )
            if dist <= radius + g.bounding_radius(r.width, r.height) + 20.0:
                return True
        return False

    # ------------------------------------------------------------------
    # 运动规划
    # ------------------------------------------------------------------

    def plan_motion(self, me: Sprite, intent: Intent) -> DesiredState:
        """意图 → 期望运动状态。

        避障在这里作为**运动层滤波**统一施加：不管上层想干什么，只要它没有显式
        opt-out（``avoid_obstacles=False``，目前只有持森林之心时会这样，因为那时
        撞障碍不扣果实），都会先被绕行逻辑改写航向。这样新增意图不会忘记避障。
        """
        # 1) 卡住是硬接管，先倒车
        if intent.kind == "unstick_obstacle" and intent.hazard is not None:
            move, turn, rate = self.controller.unstick(me, intent.hazard)
            return DesiredState(move=move, turn=turn, turn_rate=rate)

        # 2) 先算出「无视障碍时」想怎么走
        if intent.hazard is not None and intent.target is None:
            base = self.controller.evade_point(me, intent.hazard)
            goal = g.add(me.position, g.sub(me.position, intent.hazard))
        elif intent.target is not None:
            base = self.controller.steer_towards(me, intent.target)
            goal = intent.target
        else:
            base = (ctl.FORWARD, ctl.STRAIGHT, 0.02)
            goal = self.world.map_center()

        # 3) 避障滤波
        if intent.avoid_obstacles:
            obstacle = self._imminent_obstacle(me)
            if obstacle is not None:
                move, turn, rate = self.controller.avoid_obstacle(me, obstacle, goal)
                return DesiredState(move=move, turn=turn, turn_rate=rate)

        move, turn, rate = base
        return DesiredState(move=move, turn=turn, turn_rate=rate)

    # ------------------------------------------------------------------

    def explain(self) -> str:
        """一行可读的当前决策解释，进 replay 用。"""
        parts: List[str] = []
        if self.last_intent:
            parts.append("[{}] {}".format(self.last_intent.kind, self.last_intent.reason))
        if self.last_attack:
            parts.append("攻击={}".format(self.last_attack))
        return " | ".join(parts)
