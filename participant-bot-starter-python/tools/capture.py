"""把官方 ``bot.py`` 的采集目录翻译成 ``analyze.py`` 能读的记录流。

## 为什么需要这个文件

现场实际跑的是官方 ``bot.py``，它把一局比赛落在
``runtime/matches/<matchCode-matchId>/`` 下：

===================== ==========================================================
``frames.jsonl``      逐帧**原始转储**：``{receivedAt, sourceTimestamp,
                      commandType, data}``，commandType ∈ startGame / refreshData
                      / closeGame（见 bot.py 的 ``capture.append``）
``commands.jsonl``    我方每一条实际发出的指令 ``{sentAt, command}``
``metadata.json``     botId / botName / strategyHash / matchCode / matchType …
``settlement.json``   ``matchFinished`` 原文（正式赛的权威结果）
``replay.ccreplay.json`` 给 replay.html 看的可视化回放
===================== ==========================================================

而 ``tools/analyze.py`` 读的是 ``firefly/telemetry.py`` 那套 JSONL：记录靠
``type`` 字段分派（``match_start`` / ``frame`` / ``collision`` / ``result`` /
``match_end``），并且要求**派生字段** ``score_delta`` / ``energy_spent`` /
``kind`` / ``is_self``。

两边对不上。而且 ``analyze.py`` 拿 ``frames.jsonl`` 时**不会报错** ——
每条记录都没有 ``type``，于是所有分支都不命中，静默输出「帧数 0 / 碰撞 0 次」，
还会附带一条错误诊断「整局只碰撞 0 次 → 调低 idle_seek_at」。
**会说谎的裁判比没有裁判更危险**，所以这个适配层是现场 Loop 的前提。

好消息是原始转储的信息量比 telemetry 更大：``frames.jsonl`` 有逐帧
``rabbits``（``score`` / ``energy`` / ``invincible``），碰撞可以离线重建；
``commands.jsonl`` 有**实测**的 ``setAttackValue``，比策略自报更可信。

## 重建出来的东西

除了碰撞，还顺手把三条现场待验证项（docs/EXPERIMENTS.md）变成自动输出：

*   **E1/E2** —— 扣分事件按幅度分类：``-1`` 且不耗能 → 撞障碍；``-3`` 且不耗能
    → 无碰撞惩罚。于是「第几秒掉 3」和「贴边到底扣不扣分」直接看报表。
*   **E5** —— 对手出价 = 能量跌幅，直接给出分布。是干净整数就说明反推有效。
*   **E12** —— 服务端时间戳与本地接收时间的偏移，用来判断本地时钟相位漂了多少。

判定逻辑**刻意镜像** :meth:`firefly.worldmodel.WorldModel._diff_sprites`，
并直接复用它的两个阈值常量，避免线上推断与离线复盘各说一套。
"""

from __future__ import annotations

import bisect
import json
import os
import re
import sys
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 复用线上推断的阈值：离线复盘和实时判定必须是同一套标准，否则复盘结论不可信。
from firefly.constants import RULE_ENERGY_RESET_VALUE, RULE_IDLE_PENALTY_FRUIT
from firefly.worldmodel import _COLLISION_DROP_EPSILON, _RESET_JUMP_EPSILON

FRAMES_FILE = "frames.jsonl"
COMMANDS_FILE = "commands.jsonl"
METADATA_FILE = "metadata.json"
SETTLEMENT_FILE = "settlement.json"

#: FIREFLY_DEBUG=1 的行长这样：``[firefly]   12.3s [ram] 进攻 … -> goForward``
_DEBUG_LINE = re.compile(r"^\[firefly\]\s+([0-9.]+)s\s+\[([a-z_]+)\]")


# ---------------------------------------------------------------------------
# 读盘（一律容错：现场的文件可能被 Ctrl-C 截断在半行）
# ---------------------------------------------------------------------------

def _number(value: Any) -> Optional[float]:
    """等价于 JS 的 Number(...)：解析不了或不是有限值就返回 None。"""
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if result == result and abs(result) != float("inf") else None


def read_jsonl(path: str) -> Iterator[Dict[str, Any]]:
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue        # 截断的尾行：跳过而不是炸掉整次分析
            if isinstance(record, dict):
                yield record


def read_json(path: str) -> Dict[str, Any]:
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            value = json.load(fh)
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def is_capture_dir(path: str) -> bool:
    """判断是不是 ``bot.py`` 的采集目录。判据是 frames.jsonl 存在。"""
    return os.path.isdir(path) and os.path.isfile(os.path.join(path, FRAMES_FILE))


def find_captures(root: str) -> List[str]:
    """在 ``runtime/`` 或 ``runtime/matches/`` 下找出所有采集目录，按名字排序。"""
    if is_capture_dir(root):
        return [root]
    found: List[str] = []
    for base, dirs, _files in os.walk(root):
        dirs.sort()
        if is_capture_dir(base):
            found.append(base)
            dirs[:] = []        # 采集目录内部不再往下找
    return found


# ---------------------------------------------------------------------------
# 时钟
# ---------------------------------------------------------------------------

def _choose_clock(refresh: List[Dict[str, Any]]) -> Tuple[Callable[[Dict], float], str]:
    """挑一个**贯穿全局**的时钟，而不是每帧各取其一。

    ``sourceTimestamp``（服务端）更准，但可能缺失或非单调；``receivedAt``（本地
    接收）总是有，代价是带网络抖动。混用两者会让时间轴出现跳变，所以这里先整体
    校验 source 可用且非递减，不合格就整体回落到 received。
    """
    source = [_number(f.get("sourceTimestamp")) for f in refresh]
    usable = bool(source) and all(v is not None for v in source)
    monotonic = usable and all(b >= a for a, b in zip(source, source[1:]))
    if usable and monotonic:
        return (lambda f: _number(f.get("sourceTimestamp")) or 0.0), "sourceTimestamp"
    return (lambda f: _number(f.get("receivedAt")) or 0.0), "receivedAt"


def _clock_skew(refresh: List[Dict[str, Any]]) -> Optional[float]:
    """服务端时长与本地接收时长的差（秒），用于 E12（本地时钟相位是否漂）。

    我们用本地单调时钟推算两个 30s 周期，其中**无碰撞惩罚周期没有可观测锚点**，
    只能靠本地时钟。所以这个偏移值直接决定 ``Tune.idle_seek_at`` 该不该更保守。
    """
    if len(refresh) < 2:
        return None
    src_a, src_b = _number(refresh[0].get("sourceTimestamp")), _number(refresh[-1].get("sourceTimestamp"))
    rcv_a, rcv_b = _number(refresh[0].get("receivedAt")), _number(refresh[-1].get("receivedAt"))
    if None in (src_a, src_b, rcv_a, rcv_b):
        return None
    return ((src_b - src_a) - (rcv_b - rcv_a)) / 1000.0


# ---------------------------------------------------------------------------
# 自身识别
# ---------------------------------------------------------------------------

def resolve_self_id(sprite_ids: List[str], bot_id: Any) -> Optional[str]:
    """在帧里找到「我」。与 ``strategy._resolve_self_id`` 保持一致。

    认错自己 = 策略/复盘都作用在别人身上，所以这里和线上必须同一套判据：
    ``str(botId)``，本地 sample 服务会加 ``ai:`` 前缀。
    """
    if bot_id is None:
        return None
    expected = str(bot_id)
    prefixed = "ai:" + expected
    for sid in sprite_ids:
        if sid == expected or sid == prefixed:
            return sid
    return None


# ---------------------------------------------------------------------------
# 事件重建
# ---------------------------------------------------------------------------

def _sprites(frame: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    data = frame.get("data")
    rabbits = data.get("rabbits") if isinstance(data, dict) else None
    if not isinstance(rabbits, list):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for rabbit in rabbits:
        if isinstance(rabbit, dict) and rabbit.get("id") is not None:
            out[str(rabbit.get("id"))] = rabbit
    return out


def _classify(spent: float, d_score: float, prev_invincible: bool,
              energy_usable: bool = True) -> str:
    """给一次状态变化定性。

    镜像 ``worldmodel._diff_sprites``，并额外把无碰撞惩罚从「撞障碍」里分出来 ——
    两者都是「掉分但不耗能」，靠幅度区分：障碍 -1，空转惩罚 -3。这一条分离是
    E1/E2 能自动出结论的关键。

    :param energy_usable: 本帧的能量跌幅是否可信。**能量重置帧上不可信** ——
        重置把能量拉回 1000，会盖掉同帧的扣减。此时 score 信号仍然可靠，所以
        我们只放弃「靠耗能区分精灵碰撞」，不放弃整条记录。这是与
        ``worldmodel._diff_sprites`` 的一处**有意偏离**：线上那边在重置帧直接
        ``continue``，于是同帧的扣分会被整条丢掉。见本文件末尾的说明。
    """
    if spent > 0.0:
        return "sprite"                     # 耗了能量 → 精灵间碰撞
    if prev_invincible:
        return "unknown"                    # 持心时撞障碍不扣果实，别乱归因
    if d_score <= -RULE_IDLE_PENALTY_FRUIT:
        # -3 是无歧义的：任何一次对局都不会一次扣 3 分，所以即使能量信号不可用
        # 也能确定这是空转惩罚。E2 靠的就是这一条。
        return "idle_penalty"
    if d_score < 0:
        if not energy_usable:
            # -1 且能量被重置盖掉：可能是撞障碍，也可能是输掉的一次对局。
            # 分不出来就说分不出来，不要假装是障碍去污染 E1。
            return "unknown"
        return "obstacle"                   # -1：撞障碍/（待确认）贴边
    return "unknown"


def reconstruct_events(
    refresh: List[Dict[str, Any]],
    self_id: Optional[str],
    clock: Callable[[Dict], float],
    t0: float,
) -> Tuple[List[Dict[str, Any]], List[float]]:
    """逐帧 diff 出碰撞/扣分事件与能量重置时刻。

    :return: ``(events, energy_reset_seconds)``
    """
    events: List[Dict[str, Any]] = []
    resets: List[float] = []
    previous: Dict[str, Dict[str, Any]] = {}

    for frame in refresh:
        at = (clock(frame) - t0) / 1000.0
        current = _sprites(frame)
        for sid, sprite in current.items():
            prev = previous.get(sid)
            if prev is None:
                continue

            energy = _number(sprite.get("energy"))
            prev_energy = _number(prev.get("energy"))
            score = _number(sprite.get("score"))
            prev_score = _number(prev.get("score"))
            if None in (energy, prev_energy, score, prev_score):
                continue

            d_energy = energy - prev_energy
            d_score = score - prev_score

            # 能量上涨 → 周期重置（重置为 1000，不是累加）。
            #
            # ⚠️ 重置只污染 **energy** 信号，不污染 **score**。所以这里不像线上
            # 那样整条跳过 —— 否则一次撞在重置边界上的空转惩罚（-3）会被静默吞掉，
            # 而两个周期都是 30s 量级，撞在同一帧是常态，不是边角情况。
            energy_usable = True
            if d_energy > _RESET_JUMP_EPSILON:
                resets.append(round(at, 2))
                if abs(energy - RULE_ENERGY_RESET_VALUE) < _RESET_JUMP_EPSILON:
                    energy_usable = False

            spent = 0.0
            if energy_usable and d_energy < -_COLLISION_DROP_EPSILON:
                spent = -d_energy
            if spent <= 0.0 and d_score == 0.0:
                continue                    # 什么都没发生

            events.append({
                "type": "collision",
                "at_seconds": round(at, 2),
                "sprite": sid,
                "is_self": sid == self_id,
                # 这就是信息优势：能量跌幅 == 对手本次 actualAttack
                "energy_spent": round(spent, 1),
                "score_delta": d_score,
                "kind": _classify(spent, d_score, bool(prev.get("invincible")),
                                  energy_usable=energy_usable),
                # 重置帧上能量不可信，复盘时要知道这条的 energy_spent 不能用
                "energy_masked": not energy_usable,
            })
        previous = current

    # 同一次重置会被每个精灵各记一遍，对人读报表没有意义 —— 按时刻去重。
    unique_resets = sorted(set(resets))
    return events, unique_resets


def _heart_pickups(refresh: List[Dict[str, Any]], self_id: Optional[str]) -> int:
    """我方捡到森林之心的次数 = ``invincible`` 由 False 翻到 True 的次数。"""
    if not self_id:
        return 0
    count = 0
    was = False
    for frame in refresh:
        sprite = _sprites(frame).get(self_id)
        if sprite is None:
            continue
        now = bool(sprite.get("invincible"))
        if now and not was:
            count += 1
        was = now
    return count


# ---------------------------------------------------------------------------
# 意图（可选：来自 FIREFLY_DEBUG=1 的 stderr 日志）
# ---------------------------------------------------------------------------

def load_intents(debug_log: Optional[str]) -> List[Tuple[float, str]]:
    """从 debug 日志里抽出 ``(elapsed, intent)`` 序列。

    意图是**运行时决策**，回放文件里本来就没有，只能从日志补。拿不到也不影响
    其它分析 —— 只是报表里「时间分配」那一节为空。
    """
    if not debug_log or not os.path.isfile(debug_log):
        return []
    out: List[Tuple[float, str]] = []
    with open(debug_log, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            match = _DEBUG_LINE.match(line.strip())
            if match:
                out.append((float(match.group(1)), match.group(2)))
    out.sort(key=lambda item: item[0])
    return out


def _intent_at(intents: List[Tuple[float, str]], keys: List[float],
               elapsed: float) -> str:
    """取该时刻最近的一条意图。debug 日志与帧不是一一对应的，只能就近取。"""
    if not intents:
        return ""
    idx = min(len(intents) - 1, bisect.bisect_left(keys, elapsed))
    return "[{}]".format(intents[idx][1])


# ---------------------------------------------------------------------------
# 结果
# ---------------------------------------------------------------------------

def _rankings(settlement: Dict[str, Any]) -> List[Any]:
    """settlement 的名次列表。两种形态都兼容（同 replay_recorder）。"""
    if isinstance(settlement.get("rankings"), list):
        return settlement["rankings"]
    result = settlement.get("result")
    if isinstance(result, dict) and isinstance(result.get("ranking"), list):
        return result["ranking"]
    return []


def _rank_from_settlement(settlement: Dict[str, Any], bot_id: Any) -> Optional[int]:
    """从结算里找我的名次。

    ⚠️ 结算条目的确切字段现场才能确认，所以这里对 id 与名次字段都做多种猜测，
    并在拿不到时回落到「按最后一帧果实数推算」（报表里会标明是推算的）。
    """
    if bot_id is None:
        return None
    wanted = {str(bot_id), "ai:" + str(bot_id)}
    for index, entry in enumerate(_rankings(settlement)):
        if not isinstance(entry, dict):
            continue
        ids = {str(entry.get(key)) for key in ("botId", "id", "rabbitId", "aiId")}
        if ids & wanted:
            for key in ("rank", "ranking", "place", "position"):
                value = _number(entry.get(key))
                if value is not None:
                    return int(value)
            return index + 1
    return None


def _rank_from_frame(last: Dict[str, Dict[str, Any]], self_id: Optional[str]) -> Optional[int]:
    """按最后一帧的果实数推算名次（存活优先，果实降序）。"""
    if not last or not self_id or self_id not in last:
        return None

    def key(item: Tuple[str, Dict[str, Any]]) -> Tuple[int, float]:
        sprite = item[1]
        alive = 0 if sprite.get("active") is False else 1
        return (alive, _number(sprite.get("score")) or 0.0)

    ordered = sorted(last.items(), key=key, reverse=True)
    for index, (sid, _sprite) in enumerate(ordered):
        if sid == self_id:
            return index + 1
    return None


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def load_capture(directory: str, debug_log: Optional[str] = None) -> List[Dict[str, Any]]:
    """把一个采集目录变成 ``analyze.py`` 能吃的记录列表。"""
    meta = read_json(os.path.join(directory, METADATA_FILE))
    settlement = read_json(os.path.join(directory, SETTLEMENT_FILE))
    frames_raw = list(read_jsonl(os.path.join(directory, FRAMES_FILE)))
    commands = list(read_jsonl(os.path.join(directory, COMMANDS_FILE)))

    refresh = [f for f in frames_raw if f.get("commandType") == "refreshData"]
    clock, clock_name = _choose_clock(refresh)
    t0 = clock(refresh[0]) if refresh else 0.0

    bot_id = meta.get("botId")
    all_ids: List[str] = []
    for frame in refresh:
        for sid in _sprites(frame):
            if sid not in all_ids:
                all_ids.append(sid)
    self_id = resolve_self_id(all_ids, bot_id)

    # 版本标识用 strategyHash 而不是手写的 BOT_VERSION —— 它由 bot.py 自动算，
    # 不会因为「改了策略忘了 bump」而把某局对错代码。
    digest = str(meta.get("strategyHash") or "")
    version = digest[:8] if digest else "?"

    records: List[Dict[str, Any]] = [{
        "type": "match_start",
        "bot_version": version,
        "match_code": meta.get("matchCode"),
        "match_type": meta.get("matchType"),
        "round_no": meta.get("roundNo"),
        "game_no": meta.get("gameNo"),
        "bot_id": bot_id,
        "self_id": self_id,
        "clock": clock_name,
        "clock_skew_seconds": _clock_skew(refresh),
        "commands_logged": len(commands),
        "sprite_ids": all_ids,
    }]

    intents = load_intents(debug_log)
    intent_keys = [item[0] for item in intents]

    for frame in refresh:
        at = (clock(frame) - t0) / 1000.0
        mine = _sprites(frame).get(self_id or "", {})
        records.append({
            "type": "frame",
            "elapsed": round(at, 2),
            "decision": _intent_at(intents, intent_keys, at),
            "score": _number(mine.get("score")),
            "energy": _number(mine.get("energy")),
        })

    events, resets = reconstruct_events(refresh, self_id, clock, t0)
    records.extend(events)

    last = _sprites(refresh[-1]) if refresh else {}
    rank = _rank_from_settlement(settlement, bot_id)
    rank_source = "settlement"
    if rank is None:
        rank = _rank_from_frame(last, self_id)
        rank_source = "推算（最后一帧果实数）"

    records.append({
        "type": "result",
        "rank": rank,
        "rank_source": rank_source,
        "advancement": settlement.get("advancementStatus") or settlement.get("advancement"),
    })

    # R3 的验证指标：我方能量为 0 的帧占比。归零后 actualAttack 恒为 0，
    # 接下来每次碰撞都是确定的 -1，所以这个数字直接对应白送的果实。
    zero = my_frames = 0
    for frame in refresh:
        sprite = _sprites(frame).get(self_id or "")
        if sprite is None:
            continue
        my_frames += 1
        if (_number(sprite.get("energy")) or 0.0) < 1.0:
            zero += 1

    mine_last = last.get(self_id or "", {})
    records.append({
        "type": "match_end",
        "final_score": _number(mine_last.get("score")),
        "heart_pickups": _heart_pickups(refresh, self_id),
        "energy_resets": resets,
        "zero_energy_share": (zero / my_frames) if my_frames else None,
        "duration_seconds": round((clock(refresh[-1]) - t0) / 1000.0, 1) if refresh else 0.0,
    })
    return records
