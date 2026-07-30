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

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from . import geometry as g
from .constants import (
    RULE_ENERGY_RESET_PERIOD,
    RULE_ENERGY_RESET_VALUE,
    RULE_FRAME_INTERVAL,
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
