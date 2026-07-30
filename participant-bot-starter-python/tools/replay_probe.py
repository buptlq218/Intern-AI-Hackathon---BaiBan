"""把采集到的 replay 重新喂进**真实策略代码**，逐帧观察它的内部决策。

## 为什么需要它，以及它修掉的那个坑

`analyze.py` 只能看「发生了什么」（果实怎么变的），看不到「策略当时在想什么」。
意图分布、避障是否报警、出价按谁算的 —— 这些只存在于运行时。

第一版的做法是直接循环调 `strategy.choose_command(...)`，**结果是错的**：
`strategy.py` 的 `_Session.elapsed()` 用 `time.monotonic()` 算本局秒数，而回放
1400 帧只花几十毫秒，于是策略内部的 `elapsed` 永远停在 0.1s 左右。后果是所有
和时间有关的分支全部失真：

*   `seconds_to_heart_spawn` 恒为 30 → 卡位永不触发
*   `seconds_carrot_unclaimed` 恒为 0 → 「无人认领就去拿」永不触发
*   `seconds_since_self_collision` 恒为 0 → 保活永不触发
*   `can_collide_with` 的冷却判断错乱 → 所有对手都被判成「在冷却中」

我因此得出过「conserve 占 76%」这种数字，**那是量具坏了，不是策略坏了**。
所以这里在每帧前把 `started_at` 往回拨，让策略看到的 elapsed 与 replay 的
时间轴一致。**回放型量具的第一要务是让被测代码相信自己在实时运行。**

用法::

    from tools.replay_probe import ReplayProbe
    for probe in ReplayProbe.walk("runtime/matches"):
        for snap in probe:
            print(snap.t, snap.intent.kind)
"""

from __future__ import annotations

import glob
import math
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import capture as C
import strategy as S
from firefly import geometry as g
from firefly.protocol import parse_gold_carrot


@dataclass
class Snapshot:
    """某一帧的「外部事实 + 策略内心」。"""

    t: float
    me: Any
    intent: Any
    attack: Any
    desired: Any
    hazard: Optional[Any]
    carrot: Optional[Any]
    raw: Dict[str, Any]


class ReplayProbe:
    """一局 replay 的逐帧探针。"""

    def __init__(self, directory: str) -> None:
        self.directory = directory
        frames = list(C.read_jsonl(os.path.join(directory, C.FRAMES_FILE)))
        self.meta = C.read_json(os.path.join(directory, C.METADATA_FILE))
        self.bot_id = self.meta.get("botId")
        self.refresh = [f for f in frames if f.get("commandType") == "refreshData"]
        self.start = next(
            (f for f in frames if f.get("commandType") == "startGame"), None)
        self.hash = str(self.meta.get("strategyHash") or "")[:8]
        if self.refresh:
            self.clock, _ = C._choose_clock(self.refresh)
            self.t0 = self.clock(self.refresh[0])
        else:
            self.clock, self.t0 = (lambda f: 0.0), 0.0
        ids: List[str] = []
        for f in self.refresh:
            for sid in C._sprites(f):
                if sid not in ids:
                    ids.append(sid)
        self.sprite_ids = ids
        self.self_id = C.resolve_self_id(ids, self.bot_id)

    @property
    def duration(self) -> float:
        if not self.refresh:
            return 0.0
        return (self.clock(self.refresh[-1]) - self.t0) / 1000.0

    @property
    def name(self) -> str:
        return os.path.basename(self.directory.rstrip("/"))

    @classmethod
    def walk(cls, root: str, hash_prefix: Optional[str] = None) -> List["ReplayProbe"]:
        out = []
        for d in C.find_captures(root):
            probe = cls(d)
            if not probe.refresh:
                continue
            if hash_prefix and not probe.hash.startswith(hash_prefix):
                continue
            out.append(probe)
        return out

    def __iter__(self) -> Iterator[Snapshot]:
        if self.start is not None:
            S.on_start_game(self.start.get("data") or {})
        session = S._session
        world = session.world
        strat = session.strategy

        for f in self.refresh:
            t = (self.clock(f) - self.t0) / 1000.0
            # ⭐ 关键：把本局起点往回拨，让 session.elapsed() 返回 replay 的时刻。
            session.started_at = time.monotonic() - t
            data = f.get("data") or {}
            S.choose_command(data, self.bot_id)
            me = world.me
            if me is None:
                continue
            hazard = None
            try:
                hazard = strat._imminent_obstacle(me)
            except Exception:
                hazard = None
            desired = None
            try:
                if strat.last_intent is not None:
                    desired = strat.plan_motion(me, strat.last_intent)
            except Exception:
                desired = None
            yield Snapshot(
                t=t, me=me, intent=strat.last_intent, attack=strat.last_attack,
                desired=desired, hazard=hazard,
                carrot=parse_gold_carrot(data.get("goldCarrot")), raw=data,
            )

    # -- 便利统计 -------------------------------------------------------

    def intent_share(self) -> Dict[str, float]:
        from collections import Counter
        counts: Counter = Counter()
        for snap in self:
            if snap.intent is not None:
                counts[snap.intent.kind] += 1
        total = max(1, sum(counts.values()))
        return {k: v / total for k, v in counts.most_common()}


def sanity_check(directory: str) -> None:
    """自检：策略内部的 elapsed 必须跟得上 replay 的时间轴。"""
    probe = ReplayProbe(directory)
    world = S._session.world
    worst = 0.0
    last_t = 0.0
    for snap in probe:
        worst = max(worst, abs(world.elapsed - snap.t))
        last_t = snap.t
    print("自检 {}: replay 走到 {:.1f}s，策略内部 elapsed 最大偏差 {:.2f}s → {}".format(
        probe.name[-20:], last_t, worst,
        "✅ 时钟对齐" if worst < 1.0 else "❌ 时钟没对上，统计不可信"))


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    for p in ReplayProbe.walk(root)[:3]:
        sanity_check(p.directory)
