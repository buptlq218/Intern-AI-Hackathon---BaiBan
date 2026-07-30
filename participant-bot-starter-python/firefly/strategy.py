"""决策函数：一帧状态进，最多一个动作出。

## 优先级阶梯（顺序即优先级，命中即返回）

0.  已淘汰 / 不在场 → 不发指令
1.  **持有森林之心** → 全力追击。碰撞不耗能、对未持心者必胜。10s 窗口 × 1.5s 冷却
    ≈ 最多 6 次免费 +1，这是全局最高价值的事，压过一切。
    （持心撞石头虽然不扣果实，但会把车卡住，所以**照样绕障** —— 见 R4。）
2.  **对手持有森林之心且逼近** → 逃。我方必输 -1 而对方零成本，没有任何博弈空间。
3.  **森林之心已刷新** → 比 ETA 决定抢或撤。抢不到还待在附近，等于给持心者送分。
4.  **即将撞障碍** → 脱离。每次 -1 是纯损失，且不带来任何收益。
5.  **无碰撞惩罚即将触发** → 保活。找不到精灵目标就主动撞障碍：**-1 优于 -3**。
6.  **能量不足以赢下一次碰撞** → 避战，等 30s 重置。
7.  **有优势目标** → 主动撞。
7.5 **森林之心即将刷新** → 卡位到「我方最先到达的区域最大」的点（R5）。
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
from .constants import RULE_FRAME_INTERVAL, RULE_HEART_DURATION, Tune
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
    #: 打算撞哪个对手。出价要按**这一个**对手算，而不是全场最大威胁 ——
    #: 否则冲着见底的弱敌去，却按满能量的强敌出价，白烧能量（R3）。
    target_id: Optional[str] = None


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

        # 出价按「下一次真正会撞上的那个对手」算。没有明确目标时才退回全场最大值
        # （此时接触是被动的，谁都可能撞上来，保守一点是对的）。
        threat = (world.threat_for_contact(intent.target_id, me)
                  if intent.target_id else world.threat_level())

        attack = decide_attack(
            self.tune,
            energy=me.energy,
            threat=threat,
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
        #
        # R4 ⭐ 这里原本设了 ``avoid_obstacles=False``，理由是「持心撞障碍不扣果实，
        # 不必绕」。**不扣果实是对的，但结论错了** —— 石头虽然不扣分，却会把车
        # 实实在在地卡住，而这 10s 是全局最贵的资源。
        #
        # 现场实测（15 局、5 次持心、共 37.0s）：其中 **24% 的帧贴在石头上**，
        # 也就是白扔了约 9s 的无敌时间；而地图正中那个木墩正好在生成区中央，
        # 追击路线几乎必经。按 1.5s 冷却算，9s ≈ 6 次免费 +1 被磨掉了。
        # 所以持心期间照样绕障 —— 绕开石头的代价是几帧航向，卡住的代价是整个窗口。
        if me.invincible:
            victim = self._best_heart_victim(me)
            if victim is not None:
                return Intent(
                    "heart_rampage",
                    target=victim.position,
                    target_id=victim.id,
                    commit_contact=True,
                    reason="持森林之心，追击 {}（免费必胜）".format(victim.name or victim.id),
                )
            return Intent(
                "heart_hunt_none",
                target=world.rally_point(),
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
                kind, point, victim_id = target
                return Intent(
                    kind,
                    target=point,
                    target_id=victim_id,
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

        # --- 6. 一个都打不赢，才避战 -----------------------------------
        #
        # R7 ⭐ 判据从「压不过全场最高威胁」改成「**一个**打得赢的都没有」。
        # 只有场上每个能撞的对手都赢不了也平不了，避战才是对的；只要还有一个软柿子，
        # 避战就是白扔一个 +1。真机实测旧判据让 conserve 吃掉整局 76% 的帧。
        # 眼看要垫底（0 分）时没有下行空间，不利赔率也得打。
        if (t.low_energy_flee and posture != "desperate"
                and not self._can_beat_anyone(me)):
            nearest = self._nearest_rival(me)
            return Intent(
                "conserve",
                hazard=nearest.position if nearest else None,
                target=world.rally_point() if nearest is None else None,
                commit_contact=False,
                reason="能量 {:.0f}，场上没有一个打得赢/打得平的，{:.0f}s 后重置 → 避战".format(
                    me.energy, world.seconds_to_energy_reset
                ),
            )

        # --- 7. 主动进攻 -----------------------------------------------
        prey = self._best_target(me, allow_unfavourable=(posture == "desperate"))
        if prey is not None:
            return Intent(
                "ram",
                target=prey.position,
                target_id=prey.id,
                commit_contact=True,
                reason="进攻 {}（其果实 {:.0f}，威胁 {:.0f}）".format(
                    prey.name or prey.id, prey.score, world.threat_of(prey.id)
                ),
            )

        # --- 7.5 森林之心刷新前卡位 ------------------------------------
        #
        # R5 ⭐ 森林之心的**位置**事先不可知，但**时刻**已验证（E6：15/15 局在
        # 30.0s）、**分布**已实测（只落在中央区，见 RULE_HEART_SPAWN_BOX）。
        # 于是可以在刷新前占住「我方 Voronoi 单元最大」的位置。
        #
        # 现场 15 次生成的反算：
        #     现状              平均排名 2.47   抢到第一 20%   平均距离 519px
        #     站生成区质心      平均排名 1.67   抢到第一 47%   平均距离 223px
        # 四人局随机就是 2.50 —— 我们目前**完全没有站位优势**，这是纯白捡的收益。
        #
        # 为什么排在 ram 之后而不是之前：卡位只是把抢到概率从 20% 提到约 47%，
        # 是概率收益；而放弃一个已经算赢的目标是确定损失。所以有优势目标时照打，
        # 只用本来在「无目标巡航」的时间来卡位 —— 这段时间原本产出为零。
        to_spawn = world.seconds_to_heart_spawn
        if world.gold_carrot is None and to_spawn <= t.heart_preposition_lead:
            spot = world.heart_preposition_point(me, t.heart_preposition_grid)
            return Intent(
                "preposition_heart",
                target=spot,
                commit_contact=False,
                reason="{:.1f}s 后刷新森林之心 → 卡位 ({:.0f},{:.0f})".format(
                    to_spawn, spot[0], spot[1]
                ),
            )

        # --- 8. 兜底巡航 -----------------------------------------------
        # R4：目标点用 rally_point() 而不是 map_center()。实测 map_center()=(720,410)
        # 到石头只有 51.8px，而避障触发半径是 75.5px —— 巡航目标点本身就在危险区，
        # 于是「开过去→报警→绕开→被目标点拉回」无限循环。83 次撞障碍里 71% 出在
        # patrol，就是这么来的。
        return Intent(
            "patrol",
            target=world.rally_point(),
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
        # R4：不能用 map_center() —— 它落在木墩的警戒圈内，会让切向选择朝着石头走。
        return self.world.rally_point()

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

        # R8 ⭐ 竞速输了，但对手**根本没来**：那它就是免费道具，去拿。
        #
        # 实测森林之心通常在生成后 1.3~2.7s 内被抢走。所以只要它已经放了明显超过
        # 对手 ETA 的时间还在原地，「我跑不过他」这个理由就已经作废了 —— 对手可能
        # 在缠斗、在避战、或者压根不看道具。这时躲开是纯亏。
        #
        # 阈值取「对手 ETA + 一个宽限」：给他真的在路上的可能性留足时间，
        # 同时不至于等到心消失。宽限用森林之心持续时间的一半兜底，避免
        # best_rival_eta 极小时（对手就站在心旁边）阈值退化成 0 而抖动。
        unclaimed = self.world.seconds_carrot_unclaimed
        grace = max(best_rival_eta * 2.0, RULE_HEART_DURATION * 0.5)
        if unclaimed >= grace:
            return Intent(
                "seek_heart",
                target=carrot,
                commit_contact=False,
                reason="心已无人认领 {:.1f}s（>{:.1f}s）→ 对手没在抢，当免费道具拿".format(
                    unclaimed, grace
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

    def _engageable(self, me: Sprite) -> List[Sprite]:
        """现在真的能去撞的对手：活着、没持心、不在碰撞冷却里。"""
        world = self.world
        return [r for r in world.rivals
                if not r.invincible and world.can_collide_with(r.id)]

    def _can_beat_anyone(self, me: Sprite) -> bool:
        """场上**是否存在**一个我方打得赢（或打得平）的对手。

        R7 ⭐ 这是「该不该避战」的正确问法。原来问的是「我能不能压过**全场最高**
        威胁」（``world.threat_level()``），只要有一个对手出价高，答案就是否，于是
        整个窗口都在避战 —— 真机实测 conserve 占到一局的 76%，同期赢的次数从
        7.0/局 掉到 4.0/局。

        平局也算：平局不丢果实，还免费重置无碰撞计时。

        ⚠️ 这里**故意不排除碰撞冷却中的对手**（与 :meth:`_engageable` 不同）。
        冷却是暂时的，而这个函数回答的是「我现在有没有战斗力」。若把冷却也算进去，
        所有对手刚好都在冷却的那几帧会被判成「谁都打不赢」→ 去避战；而正确行为是
        继续巡航/卡位，等冷却过去。
        """
        world = self.world
        for r in world.rivals:
            if r.invincible:
                continue
            probe = decide_attack(
                self.tune, me.energy, world.threat_for_contact(r.id, me),
                world.seconds_to_energy_reset,
            )
            if probe.worth_engaging:
                return True
        return False

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
        candidates = self._engageable(me)
        if not candidates:
            return None

        best: Optional[Sprite] = None
        best_score = float("-inf")
        best_bid = 0.0
        for r in candidates:
            dist = g.distance(me.position, r.position)
            # 归一化距离：整张地图对角线约 1650px
            near = 1.0 - min(1.0, dist / 1650.0)
            their_threat = world.threat_of(r.id)   # 已按对手当前能量截断
            # R7 ⭐ 出价要按**这一个**对手算。原本这里用 world.threat_level()
            # （全场最大值）算一次 my_bid 给所有候选人共用，于是只要场上有一个高
            # 出价的对手，my_bid 就退化成 starved 模式的「能量-底线」，把本来打得赢
            # 的弱敌也判成「赢不了」→ 返回 None → 上层去避战。
            # 真机实测这条链导致 conserve 占了整局 76% 的帧。
            my_bid = decide_attack(
                t, me.energy, world.threat_for_contact(r.id, me),
                world.seconds_to_energy_reset,
            ).value
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
                best, best_score, best_bid = r, score, my_bid

        # 一定会输的目标不要硬送：交给上层的避战分支。
        # 注意用 ``<`` 而不是 ``<=`` —— 出价与对手相等是**平局**，不丢果实，
        # 且免费重置无碰撞计时，值得打。
        # 终局垫底时更进一步：连不利赔率也接受，因为 0 分已经没有下行空间。
        #
        # ⚠️ 这里必须用 ``best_bid``（选中那个目标对应的出价），不能用循环变量
        # ``my_bid`` —— 后者是**最后一个候选**的出价，和 best 未必是同一个人。
        if (best is not None and not allow_unfavourable
                and best_bid < world.threat_of(best.id)):
            return None
        return best

    def _cheapest_interaction(
        self, me: Sprite
    ) -> Optional[Tuple[str, g.Point, Optional[str]]]:
        """保活模式下最便宜的一次互动。

        优先级：能赢的精灵（+1）> 任意精灵（可能 -1）> 障碍物（确定 -1，但省下 -3）。

        :return: ``(意图名, 目标点, 对手 id 或 None)``。带上 id 是为了让出价按
            这一个对手算，而不是全场最大威胁（R3）。
        """
        world = self.world
        idle_for = world.seconds_since_self_collision

        winnable = self._best_target(me)
        if winnable is not None:
            return "idle_ram", winnable.position, winnable.id

        # 时间还够就先找人；快到点了就认命撞障碍
        if idle_for < self.tune.idle_obstacle_fallback_at:
            nearest = self._nearest_rival(me)
            if nearest is not None and not nearest.invincible:
                return "idle_ram_risky", nearest.position, nearest.id

        obstacle = world.nearest_obstacle_point(me.position)
        if obstacle is not None:
            return "idle_hit_obstacle", obstacle, None
        nearest = self._nearest_rival(me)
        if nearest is not None:
            return "idle_ram_risky", nearest.position, nearest.id
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
        opt-out（``avoid_obstacles=False``），都会先被绕行逻辑改写航向。这样新增
        意图不会忘记避障。

        R4 起**唯一**的 opt-out 是「主动撞障碍保活」（``idle_hit_obstacle``）——
        那是故意用 -1 买掉 -3。持森林之心时曾经也 opt-out，理由是撞障碍不扣果实；
        实测那让 24% 的无敌时间卡在木墩上，已改回绕障。
        """
        # 1) 卡住是硬接管，先倒车
        if intent.kind == "unstick_obstacle" and intent.hazard is not None:
            move, turn, rate = self.controller.unstick(me, intent.hazard)
            return DesiredState(move=move, turn=turn, turn_rate=rate)

        # 2) 先算出「无视障碍时」想怎么走
        if intent.hazard is not None and intent.target is None:
            # R6：逃跑方向掺一个「往空旷处」的分量，避免被逼进墙角后再也拉不开
            # 距离（持心方零成本必胜，贴墙就是站着挨打）。
            open_space = self.world.rally_point()
            base = self.controller.evade_point(me, intent.hazard, open_space)
            goal = g.add(me.position, g.sub(me.position, intent.hazard))
        elif intent.target is not None:
            base = self.controller.steer_towards(me, intent.target)
            goal = intent.target
        else:
            base = (ctl.FORWARD, ctl.STRAIGHT, 0.02)
            goal = self.world.rally_point()

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
