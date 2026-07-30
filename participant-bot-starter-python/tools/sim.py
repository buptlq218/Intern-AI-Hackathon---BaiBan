"""离线沙盒：按细则的公式近似复现引擎，用来在不占用联调平台的情况下刷参数。

**这不是引擎的复刻，只是一个够用的代理。** 已知不保真的地方：

*   物理步进用简单的匀速 + 反弹公式（细则 §6），没有真实的刚体求解；
*   碰撞判定用膨胀圆而不是 SAT（沙盒里够了，线上策略用的是 SAT）；
*   森林之心生成时间用 30/90/150s 的提示值，真实是服务端下发；
*   对手是脚本 bot，不是真实参赛策略。

所以：**沙盒只用来排除明显愚蠢的参数组合和回归崩溃，不能用来宣布策略更强。**
真实结论必须来自联调平台的 replay。

用法::

    python tools/sim.py --matches 30
    python tools/sim.py --matches 30 --opponent aggressive --seed 7
"""

from __future__ import annotations

import argparse
import math
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firefly import geometry as g  # noqa: E402
from firefly.constants import (  # noqa: E402
    RULE_COLLISION_COOLDOWN,
    RULE_ENERGY_RESET_PERIOD,
    RULE_ENERGY_RESET_VALUE,
    RULE_FRAME_INTERVAL,
    RULE_HEART_DURATION,
    RULE_HEART_SPAWN_HINTS,
    RULE_IDLE_PENALTY_FRUIT,
    RULE_IDLE_PENALTY_PERIOD,
    RULE_INITIAL_ENERGY,
    RULE_INITIAL_FRUIT,
    RULE_MAP_HEIGHT,
    RULE_MAP_WIDTH,
    RULE_MATCH_SECONDS,
    RULE_OBSTACLE_PENALTY_FRUIT,
    RULE_REBOUND_OTHER_K,
    RULE_REBOUND_POS_K,
    RULE_REBOUND_SELF_K,
    TUNE,
    Tune,
)
from firefly.control import Controller  # noqa: E402
from firefly.protocol import Frame  # noqa: E402
from firefly.strategy import Strategy  # noqa: E402
from firefly.worldmodel import WorldModel  # noqa: E402

SPRITE_W, SPRITE_H = 70.0, 64.0
MAX_SPEED = 6.0
ACCEL = 0.6


@dataclass
class SimSprite:
    id: str
    name: str
    x: float
    y: float
    angle: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    score: float = float(RULE_INITIAL_FRUIT)
    energy: float = float(RULE_INITIAL_ENERGY)
    attack: float = 50.0
    invincible_until: float = -1.0
    last_collision_at: float = 0.0
    pair_cooldown: Dict[str, float] = field(default_factory=dict)
    move: str = "forward"
    turn: str = "straight"
    turn_rate: float = 0.05
    alive: bool = True

    def invincible(self, now: float) -> bool:
        return now < self.invincible_until

    def as_dict(self, now: float) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "position": {"x": self.x, "y": self.y},
            "velocity": {"x": self.vx, "y": self.vy},
            "angle": self.angle,
            "speed": math.hypot(self.vx, self.vy),
            "angularSpeed": self.turn_rate if self.turn != "straight" else 0.0,
            "dirState": {"left": -1, "right": 1, "straight": 0}[self.turn],
            "width": SPRITE_W,
            "height": SPRITE_H,
            "score": self.score,
            "energy": self.energy,
            "active": self.alive,
            "invincible": self.invincible(now),
            "rebounding": False,
            "deathCount": 0 if self.alive else 1,
        }


# ---------------------------------------------------------------------------
# 脚本对手
# ---------------------------------------------------------------------------

class ScriptedBot:
    """简单对手。三种档位覆盖现场可能遇到的典型策略。"""

    PROFILES = {
        # 不调参，用默认 50 —— 现场一定有队伍是这样
        "default": dict(attack=50.0, aggression=0.5),
        # 中庸固定值
        "steady": dict(attack=200.0, aggression=0.8),
        # 激进大额出价，容易前期赢后期没能量
        "aggressive": dict(attack=400.0, aggression=1.0),
        # 梭哈型：每次全押
        "allin": dict(attack=1000.0, aggression=1.0),
    }

    def __init__(self, sprite: SimSprite, profile: str, rng: random.Random) -> None:
        self.sprite = sprite
        self.cfg = self.PROFILES[profile]
        self.profile = profile
        self.rng = rng
        self.sprite.attack = self.cfg["attack"]

    def step(self, world: "Sim") -> None:
        s = self.sprite
        s.attack = min(self.cfg["attack"], s.energy)

        target: Optional[Tuple[float, float]] = None
        if world.carrot is not None and self.rng.random() < 0.7:
            target = world.carrot
        else:
            others = [o for o in world.sprites if o.id != s.id and o.alive]
            if others and self.rng.random() < self.cfg["aggression"]:
                target = min(
                    ((o.x, o.y) for o in others),
                    key=lambda p: g.distance((s.x, s.y), p),
                )
        if target is None:
            target = (world.rng.uniform(100, RULE_MAP_WIDTH - 100),
                      world.rng.uniform(100, RULE_MAP_HEIGHT - 100))

        err = g.heading_error(s.angle, (s.x, s.y), target)
        s.turn = "straight" if abs(err) < 0.1 else ("left" if err > 0 else "right")
        s.turn_rate = min(0.1, max(0.01, abs(err) / math.pi * 0.1))
        s.move = "forward"


# ---------------------------------------------------------------------------
# 沙盒
# ---------------------------------------------------------------------------

class Sim:
    def __init__(self, tune: Tune, opponents: List[str], seed: int = 0) -> None:
        self.tune = tune
        self.rng = random.Random(seed)
        self.now = 0.0
        self.carrot: Optional[Tuple[float, float]] = None
        self.carrot_taken = False
        self.next_heart_idx = 0

        self.blocks = self._make_blocks()
        self.sprites: List[SimSprite] = []
        spawn = [(300, 200), (1140, 200), (300, 620), (1140, 620)]
        self.rng.shuffle(spawn)

        self.me = SimSprite("me", "firefly", *spawn[0])
        self.sprites.append(self.me)
        self.bots: List[ScriptedBot] = []
        for i, profile in enumerate(opponents[:3]):
            sprite = SimSprite("op{}".format(i), profile, *spawn[i + 1])
            self.sprites.append(sprite)
            self.bots.append(ScriptedBot(sprite, profile, self.rng))

        self.world = WorldModel(tune=tune)
        self.controller = Controller(tune)
        self.strategy = Strategy(tune, self.world, self.controller)
        self.world.identify_self(sprite_id="me")
        self.world.on_start_game(Frame.parse(self._start_message()))

        self.log: List[str] = []

    def _make_blocks(self) -> List[List[Tuple[float, float]]]:
        """几块固定障碍。真实地图由服务端下发，这里只要有东西可撞。"""
        rects = [
            (420, 300, 120, 120),
            (900, 300, 120, 120),
            (660, 120, 120, 90),
            (660, 610, 120, 90),
        ]
        out = []
        for x, y, w, h in rects:
            out.append([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
        return out

    def _map_payload(self) -> dict:
        return {
            "width": RULE_MAP_WIDTH,
            "height": RULE_MAP_HEIGHT,
            "borders": [],
            "blocks": [[[{"x": p[0], "y": p[1]} for p in hull]] for hull in self.blocks],
        }

    def _start_message(self) -> dict:
        return {
            "commandType": "startGame",
            "timeStamp": 0,
            "data": {"map": self._map_payload(),
                     "rabbits": [s.as_dict(0.0) for s in self.sprites]},
        }

    def _frame_message(self) -> dict:
        return {
            "commandType": "refreshData",
            "timestamp": int(self.now * 1000),
            "data": {
                "rabbits": [s.as_dict(self.now) for s in self.sprites],
                "goldCarrot": ({"x": self.carrot[0], "y": self.carrot[1]}
                               if self.carrot else {}),
                "elapsedSeconds": self.now,
                "remainingTime": max(0.0, RULE_MATCH_SECONDS - self.now),
            },
        }

    # ------------------------------------------------------------------

    def run(self) -> dict:
        steps = int(RULE_MATCH_SECONDS / RULE_FRAME_INTERVAL)
        for _ in range(steps):
            if not self.me.alive or sum(1 for s in self.sprites if s.alive) <= 1:
                break
            self._spawn_heart()
            self._tick_strategy()
            for bot in self.bots:
                if bot.sprite.alive:
                    bot.step(self)
            self._physics()
            self._collisions()
            self._periodic()
            self.now += RULE_FRAME_INTERVAL
        return self.summary()

    def _tick_strategy(self) -> None:
        self.world.on_frame(Frame.parse(self._frame_message()))
        action = self.strategy.decide()
        if action is None:
            return
        cmd, data = action.command_type, action.data
        if cmd == "goForward":
            self.me.move = "forward"
        elif cmd == "goBack":
            self.me.move = "backward"
        elif cmd == "stop":
            self.me.move = "halt"
        elif cmd == "steerBack":
            self.me.turn = "straight"
        elif cmd == "turnLeft":
            self.me.turn, self.me.turn_rate = "left", float(data or 0.05)
        elif cmd == "turnRight":
            self.me.turn, self.me.turn_rate = "right", float(data or 0.05)
        elif cmd == "setAttackValue":
            self.me.attack = float(data or 0)

    def _physics(self) -> None:
        for s in self.sprites:
            if not s.alive:
                continue
            if s.turn == "left":
                s.angle -= s.turn_rate      # 沙盒约定：left 使 angle 减小
            elif s.turn == "right":
                s.angle += s.turn_rate

            if s.move == "forward":
                tx, ty = math.cos(s.angle) * MAX_SPEED, math.sin(s.angle) * MAX_SPEED
            elif s.move == "backward":
                tx, ty = -math.cos(s.angle) * MAX_SPEED * 0.6, -math.sin(s.angle) * MAX_SPEED * 0.6
            else:
                tx, ty = 0.0, 0.0
            s.vx += (tx - s.vx) * ACCEL
            s.vy += (ty - s.vy) * ACCEL
            s.x += s.vx
            s.y += s.vy

            # 边缘强制拉回可行驶区，不落水
            s.x = min(max(s.x, SPRITE_W / 2), RULE_MAP_WIDTH - SPRITE_W / 2)
            s.y = min(max(s.y, SPRITE_H / 2), RULE_MAP_HEIGHT - SPRITE_H / 2)

    def _collisions(self) -> None:
        radius = g.bounding_radius(SPRITE_W, SPRITE_H)

        # 精灵 vs 精灵
        for i in range(len(self.sprites)):
            for j in range(i + 1, len(self.sprites)):
                a, b = self.sprites[i], self.sprites[j]
                if not (a.alive and b.alive):
                    continue
                if g.distance((a.x, a.y), (b.x, b.y)) > radius * 1.8:
                    continue
                if self.now - a.pair_cooldown.get(b.id, -99) < RULE_COLLISION_COOLDOWN:
                    continue
                self._resolve_pair(a, b)

        # 精灵 vs 障碍
        for s in self.sprites:
            if not s.alive:
                continue
            for k, hull in enumerate(self.blocks):
                key = "block{}".format(k)
                if g.point_polygon_distance((s.x, s.y), hull) > radius:
                    continue
                if self.now - s.pair_cooldown.get(key, -99) < RULE_COLLISION_COOLDOWN:
                    continue
                s.pair_cooldown[key] = self.now
                s.last_collision_at = self.now
                if not s.invincible(self.now):
                    s.score -= RULE_OBSTACLE_PENALTY_FRUIT
                    self._note(s, "撞障碍 -1")
                s.vx, s.vy = -s.vx * 0.6, -s.vy * 0.6
                self._check_death(s)

    def _resolve_pair(self, a: SimSprite, b: SimSprite) -> None:
        a.pair_cooldown[b.id] = self.now
        b.pair_cooldown[a.id] = self.now
        a.last_collision_at = b.last_collision_at = self.now

        a_inv, b_inv = a.invincible(self.now), b.invincible(self.now)
        aa = min(a.attack, a.energy)
        ba = min(b.attack, b.energy)

        if a_inv and not b_inv:
            a.score += 1
            b.score -= 1
        elif b_inv and not a_inv:
            b.score += 1
            a.score -= 1
        elif a_inv and b_inv:
            pass                       # 双方持心，按平局
        else:
            if aa > ba:
                a.score += 1
                b.score -= 1
            elif ba > aa:
                b.score += 1
                a.score -= 1
            a.energy = max(0.0, a.energy - aa)
            b.energy = max(0.0, b.energy - ba)

        self._note(a, "撞 {} 我{:.0f}/他{:.0f}".format(b.id, aa, ba))

        pa, pb = (a.x, a.y), (b.x, b.y)
        va, vb = (a.vx, a.vy), (b.vx, b.vy)
        na = g.rebound_velocity(pa, va, pb, vb, RULE_REBOUND_POS_K,
                                RULE_REBOUND_SELF_K, RULE_REBOUND_OTHER_K)
        nb = g.rebound_velocity(pb, vb, pa, va, RULE_REBOUND_POS_K,
                                RULE_REBOUND_SELF_K, RULE_REBOUND_OTHER_K)
        a.vx, a.vy = na
        b.vx, b.vy = nb
        self._check_death(a)
        self._check_death(b)

    def _periodic(self) -> None:
        # 能量重置（重置为 1000，不是累加）
        prev_window = int((self.now - RULE_FRAME_INTERVAL) // RULE_ENERGY_RESET_PERIOD)
        if int(self.now // RULE_ENERGY_RESET_PERIOD) > prev_window:
            for s in self.sprites:
                if s.alive:
                    s.energy = float(RULE_ENERGY_RESET_VALUE)

        # 无碰撞惩罚
        for s in self.sprites:
            if not s.alive:
                continue
            if self.now - s.last_collision_at >= RULE_IDLE_PENALTY_PERIOD:
                s.score -= RULE_IDLE_PENALTY_FRUIT
                s.last_collision_at = self.now
                self._note(s, "空转 30s -3")
                self._check_death(s)

    def _spawn_heart(self) -> None:
        if self.next_heart_idx >= len(RULE_HEART_SPAWN_HINTS):
            return
        due = RULE_HEART_SPAWN_HINTS[self.next_heart_idx]
        if self.carrot is None and self.now >= due:
            self.carrot = (self.rng.uniform(200, RULE_MAP_WIDTH - 200),
                           self.rng.uniform(150, RULE_MAP_HEIGHT - 150))
            self.next_heart_idx += 1

        if self.carrot is None:
            return
        for s in self.sprites:
            if s.alive and g.distance((s.x, s.y), self.carrot) < 60:
                s.invincible_until = self.now + RULE_HEART_DURATION
                self.carrot = None
                self._note(s, "拿到森林之心")
                break

    def _check_death(self, s: SimSprite) -> None:
        if s.score <= 0:
            s.alive = False
            self._note(s, "果实归零，淘汰")

    def _note(self, s: SimSprite, what: str) -> None:
        if s.id == "me":
            self.log.append("[{:6.1f}s] {} (果实={:.0f} 能量={:.0f})".format(
                self.now, what, s.score, s.energy))

    def summary(self) -> dict:
        ranked = sorted(self.sprites, key=lambda s: (s.alive, s.score), reverse=True)
        return {
            "score": self.me.score,
            "alive": self.me.alive,
            "rank": ranked.index(self.me) + 1,
            "advanced": ranked.index(self.me) < 2,
            "opponents": {s.id: s.score for s in self.sprites if s.id != "me"},
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="萤火森林离线沙盒（近似，非引擎复刻）")
    parser.add_argument("--matches", type=int, default=20)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--opponents", default="default,steady,aggressive",
        help="逗号分隔，可选 {}".format(",".join(ScriptedBot.PROFILES)),
    )
    parser.add_argument("--verbose", action="store_true", help="打印第一局的事件流")
    args = parser.parse_args()

    profiles = [p.strip() for p in args.opponents.split(",") if p.strip()]
    scores: List[float] = []
    ranks: List[int] = []
    advanced = 0

    for m in range(args.matches):
        sim = Sim(TUNE, profiles, seed=args.seed + m)
        result = sim.run()
        scores.append(result["score"])
        ranks.append(result["rank"])
        advanced += 1 if result["advanced"] else 0
        if args.verbose and m == 0:
            print("--- 第 1 局事件流 ---")
            for line in sim.log:
                print(line)
            print("---")

    n = len(scores)
    mean = sum(scores) / n
    variance = sum((s - mean) ** 2 for s in scores) / n
    print("\n对手组合: {}".format(", ".join(profiles)))
    print("局数      : {}".format(n))
    print("平均果实  : {:.2f}  (std {:.2f})".format(mean, math.sqrt(variance)))
    print("最差 / 最好: {:.0f} / {:.0f}".format(min(scores), max(scores)))
    print("平均名次  : {:.2f}".format(sum(ranks) / n))
    print("晋级率    : {:.0%}  ({}/{})".format(advanced / n, advanced, n))
    print("\n⚠️ 沙盒是近似模型，只用于排除坏参数与回归崩溃；真实结论看联调平台 replay。")


if __name__ == "__main__":
    main()
