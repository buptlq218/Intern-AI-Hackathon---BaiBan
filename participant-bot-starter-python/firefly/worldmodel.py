"""世界模型：把离散帧变成「可决策的状态」。

这个文件承担四件策略层不该重复做的事：

1.  **缓存开局地图**（``map`` 只在 startGame 下发一次，refreshData 里没有）。
2.  **推断对手攻击强度**。实时协议不广播对手的 ``setAttackValue``，但每次碰撞
    会精确扣掉 ``actualAttack`` 的能量，而能量是逐帧广播的 —— 所以
    **能量跌幅就是对手这次的实际攻击强度**。这是本方案最重要的信息优势。
3.  **维护两个 30s 周期**：能量重置周期，和无碰撞惩罚周期。两者独立且都会
    直接影响分数，必须分开跟踪。
4.  **识别碰撞事件**，供保活计时与对手建模使用。

刻意不做的事：长期纯积分推演。细则 §6 要求每帧用真实数据纠偏，所以这里
只保留上一帧，短期预测交给 strategy 层按需调用 geometry。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from . import geometry as g
from .constants import (
    RULE_ENERGY_RESET_PERIOD,
    RULE_ENERGY_RESET_VALUE,
    RULE_FRAME_INTERVAL,
    RULE_HEART_SPAWN_BOX,
    RULE_HEART_SPAWN_HINTS,
    RULE_IDLE_PENALTY_PERIOD,
    RULE_ADVANCE_PER_TABLE,
    RULE_MAP_HEIGHT,
    RULE_MAP_WIDTH,
    RULE_MATCH_SECONDS,
    RULE_TABLE_SIZE,
    Tune,
)
from .protocol import Frame, GameMap, Sprite

#: 能量涨幅超过这个值就认定是周期重置，而不是别的什么。
_RESET_JUMP_EPSILON = 1.0
#: 能量跌幅小于这个值忽略，避免浮点噪声被当成碰撞。
_COLLISION_DROP_EPSILON = 1.0
#: 巡航速度下限（px/frame），防止开局速度为 0 时 ETA 变成无穷大。
_MIN_NOMINAL_SPEED = 3.0
#: 计算「下一次接触的威胁」时，这个半径内的其它对手也要算进去 —— 防止瞄着弱的
#: 打却被旁边的强敌先撞上。不是调参旋钮，所以不放进 Tune。
_CONTACT_THREAT_RADIUS = 260.0


@dataclass
class CollisionEvent:
    """一次观测到的碰撞。"""

    at_seconds: float
    sprite_id: str
    energy_spent: float          # = actualAttack，对手建模的核心信号
    score_delta: float           # +1 赢 / -1 输 / 0 平或撞障碍
    #: 猜测的碰撞类型。障碍物碰撞只扣分不耗能，据此区分。
    kind: str = "unknown"        # "sprite" | "obstacle" | "unknown"


@dataclass
class OpponentModel:
    """单个对手的行为画像。"""

    sprite_id: str
    name: str = ""
    #: 历次观测到的实际攻击强度（能量跌幅）。
    observed_attacks: List[float] = field(default_factory=list)
    total_wins: int = 0
    total_losses: int = 0
    last_collision_at: float = -999.0

    def note_attack(self, value: float) -> None:
        if value > 0:
            self.observed_attacks.append(value)

    def threat(self, quantile: float, fallback: float) -> float:
        """估计对手下一次会出多少攻击强度。

        用分位数而不是均值：我们关心的是「会不会被压过」，所以要偏向上界。
        quantile=1.0 等价于取历史最大值。
        """
        if not self.observed_attacks:
            return fallback
        ordered = sorted(self.observed_attacks)
        idx = int(round((len(ordered) - 1) * max(0.0, min(1.0, quantile))))
        sampled = ordered[idx]
        # 对手可能正在逐轮加价，所以不低于「最近一次」观测值。
        return max(sampled, self.observed_attacks[-1])


@dataclass
class WorldModel:
    """整局比赛的可变状态。每局开始前必须 ``reset()``。"""

    tune: Tune

    game_map: Optional[GameMap] = None
    self_id: Optional[str] = None
    self_name: Optional[str] = None

    frame: Optional[Frame] = None
    prev_sprites: Dict[str, Sprite] = field(default_factory=dict)
    opponents: Dict[str, OpponentModel] = field(default_factory=dict)

    elapsed: float = 0.0
    remaining: float = 0.0
    frame_index: int = 0

    #: 最近一次观测到能量重置的比赛时刻，用于校正 30s 窗口相位。
    last_energy_reset_at: float = 0.0
    #: 最近一次「我方发生有效碰撞」的时刻，用于无碰撞惩罚倒计时。
    last_self_collision_at: float = 0.0
    collisions: List[CollisionEvent] = field(default_factory=list)

    #: 我方持有森林之心的观测起点（仅用于日志；判定一律以 invincible 字段为准）。
    heart_since: Optional[float] = None
    heart_pickups: int = 0
    #: 场上那个森林之心是什么时候出现的（没有则 None）。见 seconds_carrot_unclaimed。
    carrot_since: Optional[float] = None

    #: 每个精灵本局观测到的最大速度（px/frame），用于稳定的 ETA 估计。
    _max_speed: Dict[str, float] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """新的一局。地图与自身标识保留到 ``on_start_game`` 重新填。"""
        self.game_map = None
        self.frame = None
        self.prev_sprites = {}
        self.opponents = {}
        self.elapsed = 0.0
        self.remaining = 0.0
        self.frame_index = 0
        self.last_energy_reset_at = 0.0
        self.last_self_collision_at = 0.0
        self.collisions = []
        self.heart_since = None
        self.heart_pickups = 0
        self.carrot_since = None
        self._max_speed = {}

    def on_start_game(self, frame: Frame) -> None:
        """缓存地图。

        ⚠️ startGame 里 rabbits 的 position 可能还是入场前的占位值（官方示例里
        出现了负坐标，而地图是 1440x820），所以这里**只取地图**，精灵状态等第一帧
        refreshData 再建立。
        """
        if frame.game_map is not None:
            self.game_map = frame.game_map
        if self.game_map is None:
            self.game_map = GameMap(width=RULE_MAP_WIDTH, height=RULE_MAP_HEIGHT)

    def identify_self(self, sprite_id: Optional[str] = None,
                      name: Optional[str] = None) -> None:
        """告诉世界模型「哪个精灵是我」。

        SDK 一般会给出自身 id；拿不到时退化成按 botConnected 返回的 botName 匹配。
        """
        if sprite_id:
            self.self_id = str(sprite_id)
        if name:
            self.self_name = name

    # ------------------------------------------------------------------
    # 每帧更新
    # ------------------------------------------------------------------

    def on_frame(self, frame: Frame, elapsed: Optional[float] = None) -> None:
        """推进一帧。

        :param elapsed: 外部时钟（秒）。**官方 SDK 的 ``refreshData.data`` 里
            没有 ``elapsedSeconds`` / ``remainingTime``**（只有 ``rabbits`` 和
            ``goldCarrot``），所以真实比赛必须由调用方用本地时钟传进来。
            两个 30s 周期（能量重置、无碰撞惩罚）都依赖它。
            能量重置的相位还会用观测到的实际重置时刻二次校正，见
            :attr:`seconds_to_energy_reset`，所以本地时钟的小幅漂移不致命。
        """
        self.frame_index += 1
        if elapsed is not None:
            self.elapsed = elapsed
        elif frame.elapsed_seconds:
            self.elapsed = frame.elapsed_seconds
        else:
            # 兜底：按帧间隔累加，好过一直停在 0 导致周期判断全错
            self.elapsed += RULE_FRAME_INTERVAL
        self.remaining = frame.remaining_time or max(
            0.0, RULE_MATCH_SECONDS - self.elapsed
        )

        if frame.game_map is not None:
            self.game_map = frame.game_map

        self._resolve_self_id(frame)
        self._diff_sprites(frame)

        for sprite in frame.sprites:
            observed = max(sprite.speed, g.length(sprite.velocity))
            if observed > self._max_speed.get(sprite.id, 0.0):
                self._max_speed[sprite.id] = observed

        self.frame = frame
        self.prev_sprites = {s.id: s for s in frame.sprites}

        me = self.me
        if me is not None:
            if me.invincible and self.heart_since is None:
                self.heart_since = self.elapsed
                self.heart_pickups += 1
            elif not me.invincible:
                self.heart_since = None

        # R8：森林之心在场上待了多久。用来判断「对手到底是不是真的要来抢」——
        # ETA 竞速只在**刚刷新的那一瞬间**有意义，之后它就只是个静态道具了。
        if frame.gold_carrot is not None:
            if self.carrot_since is None:
                self.carrot_since = self.elapsed
        else:
            self.carrot_since = None

    def _resolve_self_id(self, frame: Frame) -> None:
        if self.self_id and any(s.id == self.self_id for s in frame.sprites):
            return
        if self.self_name:
            for s in frame.sprites:
                if s.name == self.self_name:
                    self.self_id = s.id
                    return

    def _diff_sprites(self, frame: Frame) -> None:
        """对比上一帧，抽取能量重置与碰撞事件。"""
        for sprite in frame.sprites:
            prev = self.prev_sprites.get(sprite.id)
            if prev is None:
                continue

            d_energy = sprite.energy - prev.energy
            d_score = sprite.score - prev.score
            is_self = sprite.id == self.self_id

            # 能量上涨 → 周期重置（不是「在剩余值上增加 1000」，是重置为 1000）
            if d_energy > _RESET_JUMP_EPSILON:
                self.last_energy_reset_at = self.elapsed
                # 重置帧上无法可靠地同时解读碰撞，跳过本帧的碰撞推断。
                if abs(sprite.energy - RULE_ENERGY_RESET_VALUE) < _RESET_JUMP_EPSILON:
                    continue

            spent = -d_energy if d_energy < -_COLLISION_DROP_EPSILON else 0.0
            if spent <= 0.0 and d_score == 0.0:
                continue  # 什么都没发生

            # 分类：耗能了 → 精灵间碰撞（森林之心持有者例外，它不耗能）；
            # 只掉 1 分没耗能 → 大概率撞障碍物。
            if spent > 0.0:
                kind = "sprite"
            elif d_score < 0 and not prev.invincible:
                kind = "obstacle"
            else:
                kind = "unknown"

            event = CollisionEvent(
                at_seconds=self.elapsed,
                sprite_id=sprite.id,
                energy_spent=spent,
                score_delta=d_score,
                kind=kind,
            )
            self.collisions.append(event)

            if is_self:
                self.last_self_collision_at = self.elapsed
            else:
                model = self._opponent(sprite)
                model.last_collision_at = self.elapsed
                # 这就是信息优势：能量跌幅 == 对手本次 actualAttack
                if kind == "sprite":
                    model.note_attack(spent)
                if d_score > 0:
                    model.total_wins += 1
                elif d_score < 0:
                    model.total_losses += 1

    def _opponent(self, sprite: Sprite) -> OpponentModel:
        model = self.opponents.get(sprite.id)
        if model is None:
            model = OpponentModel(sprite_id=sprite.id, name=sprite.name)
            self.opponents[sprite.id] = model
        return model

    # ------------------------------------------------------------------
    # 查询接口
    # ------------------------------------------------------------------

    @property
    def me(self) -> Optional[Sprite]:
        if self.frame is None or not self.self_id:
            return None
        for s in self.frame.sprites:
            if s.id == self.self_id:
                return s
        return None

    @property
    def rivals(self) -> List[Sprite]:
        """除自己以外、仍然存活的精灵。"""
        if self.frame is None:
            return []
        return [s for s in self.frame.sprites if s.id != self.self_id and s.alive]

    @property
    def gold_carrot(self) -> Optional[g.Point]:
        return self.frame.gold_carrot if self.frame else None

    @property
    def seconds_to_energy_reset(self) -> float:
        """距下一次能量重置还有多少秒。

        以观测到的重置时刻校正相位；观测不到时退回按 elapsed 取模。
        """
        if self.last_energy_reset_at > 0.0:
            since = self.elapsed - self.last_energy_reset_at
            return max(0.0, RULE_ENERGY_RESET_PERIOD - (since % RULE_ENERGY_RESET_PERIOD))
        phase = self.elapsed % RULE_ENERGY_RESET_PERIOD
        return max(0.0, RULE_ENERGY_RESET_PERIOD - phase)

    @property
    def seconds_carrot_unclaimed(self) -> float:
        """场上那个森林之心已经**没人捡**多久了（秒）。没有心时返回 0。

        R8 ⭐ 这个量存在的理由：ETA 竞速只在刚刷新的那一瞬间有意义。实测森林之心
        通常在生成后 **1.3~2.7s** 内就被抢走（是一场瞬间的抢地皮）。所以如果它已经
        在那儿放了远超对手 ETA 的时间还没人动，说明**对手根本没在抢** —— 这时它
        就是个免费道具，再拿「我跑不过他」当理由躲开是纯亏。

        真机 b068 就是这么亏掉一整局的：90s 刷出的心一直放到 174s 结束都没人捡，
        而我们每一帧都重新算一遍「我 6.8s / 对手 2.9s，抢不到」→ 连续 84s 执行
        yield_heart，自己的果实从 7 掉到 2，1v1 局面里白送一个必胜道具。
        """
        if self.carrot_since is None:
            return 0.0
        return max(0.0, self.elapsed - self.carrot_since)

    @property
    def seconds_to_heart_spawn(self) -> float:
        """距下一次森林之心刷新还有多少秒；没有下一次则返回 ``inf``。

        ✅ E6 已验证：现场 15 局 replay 中 ``goldCarrot`` 首次出现全部在
        **30.0s**（误差 ≤0.1s），第二次在 90.0s，与
        ``RULE_HEART_SPAWN_HINTS`` 完全一致。所以这个本地推算是可用的。

        ⚠️ 但细则要求「以实时字段为准」，因此它**只用于刷新前的预定位**；
        森林之心一旦真的出现，策略走的是实时 ``gold_carrot`` 坐标，不看这里。
        """
        for hint in RULE_HEART_SPAWN_HINTS:
            if self.elapsed < hint:
                return hint - self.elapsed
        return float("inf")

    @property
    def seconds_since_self_collision(self) -> float:
        """距上次我方有效碰撞过了多久；这是 -3 果实惩罚的倒计时输入。"""
        return max(0.0, self.elapsed - self.last_self_collision_at)

    @property
    def seconds_to_idle_penalty(self) -> float:
        return max(0.0, RULE_IDLE_PENALTY_PERIOD - self.seconds_since_self_collision)

    # ------------------------------------------------------------------
    # 名次感知（积分规则：每轮按名次积 3/2/1/0 分，同分取果实多者）
    # ------------------------------------------------------------------

    def my_rank(self) -> int:
        """我在场上的名次（1 起）。按果实数降序，只统计还活着的。

        已淘汰的精灵排在所有存活者之后 —— 它们的果实是 0，本来就垫底。
        """
        me = self.me
        if me is None or self.frame is None:
            return RULE_TABLE_SIZE
        everyone = [s for s in self.frame.sprites]
        if not everyone:
            return 1
        ordered = sorted(everyone, key=lambda s: (s.alive, s.score), reverse=True)
        for index, sprite in enumerate(ordered):
            if sprite.id == me.id:
                return index + 1
        return len(ordered)

    def score_margin_to_cutoff(self, advance: int = RULE_ADVANCE_PER_TABLE) -> float:
        """距「晋级线」的果实差。

        正数 = 我在线上，还领先多少；负数 = 我在线下，还差多少追上。
        4 进 2，所以 cutoff 是第 2 名和第 3 名之间那条线。
        """
        me = self.me
        if me is None or self.frame is None:
            return 0.0
        scores = sorted(
            (s.score for s in self.frame.sprites if s.id != me.id), reverse=True
        )
        if not scores:
            return me.score
        # 我要压过的是第 advance 名（0-indexed 为 advance-1）那个对手
        idx = min(len(scores) - 1, advance - 1)
        return me.score - scores[idx]

    def threat_level(self) -> float:
        """当前场上「我需要压过的攻击强度」。

        取所有存活、未持森林之心对手的威胁估计的最大值。持心对手不参与竞价 ——
        对他们攻击强度无意义（必输），处理方式是躲，不是加价。
        """
        best = 0.0
        seen = False
        for rival in self.rivals:
            if rival.invincible:
                continue
            seen = True
            # threat_of 会用对手当前能量做硬上限
            best = max(best, self.threat_of(rival.id))
        if not seen:
            return self.tune.assumed_opponent_attack
        return best

    def sprite_by_id(self, sprite_id: str) -> Optional[Sprite]:
        if self.frame is None:
            return None
        for s in self.frame.sprites:
            if s.id == sprite_id:
                return s
        return None

    def threat_of(self, sprite_id: str) -> float:
        """某个对手**这一刻**能打出的攻击强度。

        ⭐ 关键：``actualAttack = min(设定值, 当前能量)``，所以对手的当前能量是
        他攻击强度的**硬上限**，而能量是逐帧广播的。历史出价只是「他想出多少」，
        当前能量才决定「他能出多少」。

        这条修正的实战价值极大：每次梭哈 1000 的对手，在花完之后整个窗口剩余时间
        里能量都是 0 —— 此时他完全无害，我方随便出个最小值就能白拿 +1。
        只看历史出价会把他一直当成 1000 的威胁，于是全场躲着一个空壳打。
        """
        model = self.opponents.get(sprite_id)
        if model is None:
            est = self.tune.assumed_opponent_attack
        else:
            est = model.threat(self.tune.threat_quantile,
                               self.tune.assumed_opponent_attack)
        sprite = self.sprite_by_id(sprite_id)
        if sprite is not None:
            est = min(est, max(0.0, sprite.energy))
        return est

    def threat_for_contact(self, target_id: str, me: Sprite) -> float:
        """我方**下一次接触**真正需要压过的攻击强度。

        ⭐ 与 :meth:`threat_level` 的区别很重要：后者取全场最大值，但一次碰撞只会
        和**一个**对手结算。如果 A 还有 800 能量而 B 已经见底，我们冲着 B 去却按
        A 的 800 出价，就白扔了几百点能量 —— 现场 8 局实测的能量归零（22% 的帧）
        主要就是这样烧掉的。

        仍然要防一种情况：瞄着弱的打，结果被旁边的强敌先撞上。所以把「贴得比目标
        还近的对手」也算进来取最大值。
        """
        threat = self.threat_of(target_id)
        target = self.sprite_by_id(target_id)
        target_dist = (g.distance(me.position, target.position)
                       if target is not None else float("inf"))
        for rival in self.rivals:
            if rival.id == target_id or rival.invincible:
                continue
            dist = g.distance(me.position, rival.position)
            if dist <= min(target_dist, _CONTACT_THREAT_RADIUS):
                threat = max(threat, self.threat_of(rival.id))
        return threat

    def can_collide_with(self, sprite_id: str) -> bool:
        """碰撞冷却检查。

        细则 §5.2：同一精灵对（或精灵与障碍物）的连续接触存在约 1.5s 冷却，
        贴合时不会每帧重复结算。所以刚撞完同一个人再贴上去是白费的。
        """
        from .constants import RULE_COLLISION_COOLDOWN

        model = self.opponents.get(sprite_id)
        if model is None:
            return True
        return (self.elapsed - model.last_collision_at) >= RULE_COLLISION_COOLDOWN

    # ------------------------------------------------------------------
    # 空间查询
    # ------------------------------------------------------------------

    def obstacle_clearance(self, point: g.Point) -> Tuple[float, Optional[g.Polygon]]:
        """点到最近障碍物凸块的距离，以及那个凸块。

        注意遍历的是摊平后的凸块列表 —— 细则警告过凹形物体被拆成多块，
        不能只看每个物体的第 0 块。
        """
        if self.game_map is None:
            return float("inf"), None
        best = float("inf")
        best_hull: Optional[g.Polygon] = None
        for hull in self.game_map.block_hulls:
            d = g.point_polygon_distance(point, hull)
            if d < best:
                best, best_hull = d, hull
        return best, best_hull

    def border_clearance(self, point: g.Point) -> float:
        """到场地四边的最小距离。

        当前版本越界会被强制拉回，不会落水；但边缘是否算障碍物碰撞未确认
        （见 E1），所以策略上仍按危险区处理。
        """
        w = self.game_map.width if self.game_map else RULE_MAP_WIDTH
        h = self.game_map.height if self.game_map else RULE_MAP_HEIGHT
        return min(point[0], point[1], w - point[0], h - point[1])

    def map_center(self) -> g.Point:
        w = self.game_map.width if self.game_map else RULE_MAP_WIDTH
        h = self.game_map.height if self.game_map else RULE_MAP_HEIGHT
        return (w / 2.0, h / 2.0)

    def safe_point_near(self, point: g.Point, clearance: float) -> g.Point:
        """把一个目标点推到障碍物外面，至少留出 ``clearance`` 的间隙。

        R4 ⭐ 为什么必须有这个函数：现场实测 ``map_center()`` = (720, 410) 到最近
        石头只有 **51.8px**，而避障的触发半径是 49.5(精灵) + 26(余量) = **75.5px**。
        也就是说**巡航的目标点本身就永久落在危险区里** —— 我们一路开过去，进入
        警戒圈、切向绕开、又被目标点拉回来，反复磨。这解释了 15 局里 83 次撞障碍
        有 **71% 发生在 patrol** 意图下。

        把目标点沿「远离石头」的方向推出去就打断了这个循环。推不动（四周都是
        障碍）时原样返回，让避障层去处理，绝不返回地图外的点。
        """
        w = self.game_map.width if self.game_map else RULE_MAP_WIDTH
        h = self.game_map.height if self.game_map else RULE_MAP_HEIGHT
        margin = 80.0
        current = point
        for _ in range(6):
            gap, hull = self.obstacle_clearance(current)
            if hull is None or gap >= clearance:
                return current
            near = min(hull, key=lambda p: g.distance(current, p))
            away = g.normalize(g.sub(current, near))
            if away == (0.0, 0.0):
                away = (1.0, 0.0)
            moved = g.add(current, g.scale(away, clearance - gap + 24.0))
            # 夹回场内，否则会把巡航目标推到边界外，换成一直贴边
            current = (min(max(moved[0], margin), w - margin),
                       min(max(moved[1], margin), h - margin))
        return current

    def rally_point(self) -> g.Point:
        """巡航/集结用的中场点：地图中心，但保证不在石头的警戒圈里。"""
        return self.safe_point_near(self.map_center(), 90.0)

    def path_blocked(
        self, start: g.Point, end: g.Point, radius: float, samples: int = 14
    ) -> bool:
        """从 ``start`` 直线走到 ``end``，这条走廊上有没有石头。

        R10 ⭐ 为什么需要「走廊」而不是「外推点」：``_imminent_obstacle`` 沿
        **当前速度**外推 1.2s，那只回答「照现在这个方向开会不会撞」。但我们大部分
        撞击发生在 ``ram`` 里 —— 车头正在**转向目标**，石头是被我们自己拐进来的，
        所以外推点直到最后一刻才进入警戒圈。实测 v5 四局 34 次撞击，**连续预警
        中位只有 0.32s、66% 不足 0.5s**，而切向脱离需要约 1.6s：预警时间根本不是
        「不够早」，是**物理上来不及**。

        走廊检查换了个问法：「我要去的**那个地方**，路上有没有石头」。这个答案在
        目标出现的那一刻就成立，与车头当前朝哪无关，所以预警时间由距离决定而不是
        由转向速度决定。实测回溯：34 次撞击里有 13 次（38%）在撞击前 1.5s 时直线
        已经被石头挡住了 —— 这些本来就该早早绕开。
        """
        if self.game_map is None or not self.game_map.block_hulls:
            return False
        for i in range(1, max(2, samples) + 1):
            k = i / float(samples)
            probe = (start[0] + (end[0] - start[0]) * k,
                     start[1] + (end[1] - start[1]) * k)
            gap, hull = self.obstacle_clearance(probe)
            if hull is not None and gap < radius:
                return True
        return False

    def clear_direction(
        self, start: g.Point, desired: g.Point, reach: float, radius: float
    ) -> g.Point:
        """把方向 ``desired`` 掰到一条**走廊干净**的方向上，返回单位向量。

        从直连方向开始，左右对称地逐档加大偏角（20°…120°），取**第一个**走廊干净
        的方向 —— 也就是偏离最小的那条。这样绕行是渐进的：石头刚进入走廊时只偏
        20°，通常连方向盘都不用打满就擦过去了，不会像反应式避障那样临门急转。

        全都堵死时返回原方向，交给运动层的避障滤波兜底（那一层还有刹车）。
        """
        unit = g.normalize(desired)
        if unit == (0.0, 0.0):
            return (1.0, 0.0)
        if not self.path_blocked(start, g.add(start, g.scale(unit, reach)), radius):
            return unit
        base = math.atan2(unit[1], unit[0])
        for deg in (20.0, 40.0, 60.0, 80.0, 100.0, 120.0):
            for sign in (1.0, -1.0):
                a = base + sign * math.radians(deg)
                cand = (math.cos(a), math.sin(a))
                end = g.add(start, g.scale(cand, reach))
                if self.path_blocked(start, end, radius):
                    continue
                # 绕出来的方向也不能直接指向场外，否则等于换成一路贴边
                if self.border_clearance(end) < 40.0:
                    continue
                return cand
        return unit

    def heart_preposition_point(self, me: Sprite, grid: float = 100.0) -> g.Point:
        """森林之心刷新前的最优「卡位」点。

        R5 ⭐ 思路：森林之心的位置我们事先不知道，但它的**分布**是已知的
        （``RULE_HEART_SPAWN_BOX``，实测只落在中央区域）。所以要选的不是「离某个
        点最近」，而是**让「我比所有对手先到」的那块区域尽可能大** —— 也就是把
        自己 Voronoi 单元在生成区里的面积做到最大。

        做法是直接的最大覆盖搜索：在场上撒一批候选站位，对每个候选点，用生成区里
        的采样点数一数「我方 ETA < 所有对手 ETA」的比例，取最高者。这样它会自动
        产生「对手都挤在左上角缠斗 → 我站到他们外侧」的行为，而不需要把那个特例
        写死成规则。

        为什么用**最大覆盖**而不是固定站在质心：固定点在 15 次实测样本上评分更低
        （质心 47% vs 自适应最优 67%），而且固定点无法利用对手的扎堆。反过来，
        直接把网格最优的 (880,540) 写死则是对 n=15 的过拟合 —— 自适应版本对每一
        局当下的对手站位重新求解，不依赖那 15 个样本的具体位置。

        ETA 用 :meth:`nominal_speed`（本局观测最大速度），不用瞬时速度 —— 否则
        反弹和转向会让排序每隔几帧翻转。
        """
        x0, y0, x1, y1 = RULE_HEART_SPAWN_BOX
        # 生成区采样点：用来近似「生成位置」的概率分布（实测近似均匀）
        samples = [(x0 + (x1 - x0) * (i + 0.5) / 6.0,
                    y0 + (y1 - y0) * (j + 0.5) / 5.0)
                   for i in range(6) for j in range(5)]
        rivals = [r for r in self.rivals if r.alive]
        my_speed = self.nominal_speed(me.id)

        best_point = self.rally_point()
        best_score = -1.0
        step = max(40.0, grid)
        x = x0
        while x <= x1:
            y = y0
            while y <= y1:
                cand = (x, y)
                y += step
                # 站在石头里等于站在扣分区，直接跳过
                gap, hull = self.obstacle_clearance(cand)
                if hull is not None and gap < 90.0:
                    continue
                # 先要来得及走过去，否则算出来的优势是假的
                won = 0
                for s in samples:
                    mine = self.eta(cand, s, my_speed)
                    if all(mine < self.eta_for(r, s) for r in rivals):
                        won += 1
                score = won / float(len(samples))
                # 同分时偏向离当前位置近的，避免每帧在等价点之间来回跑
                score -= 1e-4 * g.distance(me.position, cand) / 1000.0
                if score > best_score:
                    best_score, best_point = score, cand
            x += step
        return best_point

    def nominal_speed(self, sprite_id: str) -> float:
        """精灵的「巡航速度」估计，单位 px/frame。

        **不要用瞬时 speed 算 ETA。** 碰撞反弹、转向和加速都会让瞬时速度在
        6 → 2 之间跳，用它算 ETA 会让「抢/不抢森林之心」的判断每隔几帧翻转一次
        （沙盒里实测到 seek_heart 与 yield_heart 反复抖动）。这里用本局观测到的
        最大速度作为巡航速度，得到的 ETA 基本只反映距离，稳定得多。
        """
        observed = self._max_speed.get(sprite_id, 0.0)
        return max(observed, _MIN_NOMINAL_SPEED)

    def eta(self, frm: g.Point, to: g.Point, speed: float) -> float:
        """直线到达时间估计，单位**秒**。

        ``speed`` 是 px/frame，所以 dist/speed 得到的是帧数，需要乘帧间隔。
        """
        dist = g.distance(frm, to)
        if speed < _MIN_NOMINAL_SPEED:
            speed = _MIN_NOMINAL_SPEED
        return (dist / speed) * RULE_FRAME_INTERVAL

    def eta_for(self, sprite: Sprite, to: g.Point) -> float:
        """用巡航速度算某个精灵到某点的 ETA（秒）。"""
        return self.eta(sprite.position, to, self.nominal_speed(sprite.id))

    def nearest_obstacle_point(self, frm: g.Point) -> Optional[g.Point]:
        """最近障碍物凸块的一个顶点，用作「主动撞墙保活」的目标。"""
        _, hull = self.obstacle_clearance(frm)
        if not hull:
            return None
        return min(hull, key=lambda p: g.distance(frm, p))

    def summary(self) -> Dict[str, object]:
        """写进 replay 的一行快照。"""
        me = self.me
        return {
            "frame": self.frame_index,
            "elapsed": round(self.elapsed, 2),
            "score": me.score if me else None,
            "energy": me.energy if me else None,
            "invincible": me.invincible if me else None,
            "to_reset": round(self.seconds_to_energy_reset, 1),
            "idle_for": round(self.seconds_since_self_collision, 1),
            "threat": round(self.threat_level(), 1),
            "rivals": len(self.rivals),
            "heart": self.gold_carrot,
        }
