"""replay 分析器：把一局比赛变成「每次得失分的解释」。

这是 Loop 里的 Checker。现场流程：跑一局 → ``python tools/analyze.py runtime/`` →
看哪一类损失最大 → 只改一个参数 → 再跑。

**两种输入都吃**：

*   官方 ``bot.py`` 的采集目录（正式赛走这条）：``runtime/matches/<matchCode-id>/``。
    它落的是原始帧转储，碰撞事件由 :mod:`tools.capture` 离线重建。
*   ``firefly/telemetry.py`` 写的 JSONL（备用的独立 runner 路径）。

用法::

    python tools/analyze.py runtime/                      # 自动找出所有采集目录
    python tools/analyze.py runtime/matches/<code>/       # 指定一局
    python tools/analyze.py runtime/ --compare            # 只看多局对比
    python tools/analyze.py runtime/ --debug-log runtime/debug.log   # 补上意图分布

意图（``[ram]`` / ``[seek_heart]`` …）是**运行时决策**，回放里没有，只能从
``FIREFLY_DEBUG=1`` 的 stderr 日志补。所以现场建议这样起 BOT::

    FIREFLY_DEBUG=1 ... ./.venv/bin/python bot.py 2> runtime/debug.log
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, Iterator, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import capture as capture_mod


def read_jsonl(path: str) -> Iterator[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except ValueError:
                continue


def analyze(path: str, debug_log: Optional[str] = None) -> Dict[str, Any]:
    """分析一局。``path`` 可以是采集目录，也可以是 telemetry 的 JSONL 文件。"""
    if capture_mod.is_capture_dir(path):
        records: Iterable[Dict[str, Any]] = capture_mod.load_capture(
            path, debug_log=debug_log)
    else:
        records = read_jsonl(path)
    return _analyze_records(records, path)


def _analyze_records(records: Iterable[Dict[str, Any]], path: str) -> Dict[str, Any]:
    frames: List[Dict[str, Any]] = []
    collisions: List[Dict[str, Any]] = []
    result: Optional[Dict[str, Any]] = None
    end: Optional[Dict[str, Any]] = None
    start: Dict[str, Any] = {}
    version = "?"

    for record in records:
        kind = record.get("type")
        if kind == "match_start":
            start = record
            version = record.get("bot_version", "?")
        elif kind == "frame":
            frames.append(record)
        elif kind == "collision":
            collisions.append(record)
        elif kind == "result":
            result = record
        elif kind == "match_end":
            end = record

    mine = [c for c in collisions if c.get("is_self")]
    # 「赢/输」只统计**精灵间碰撞**。撞障碍和空转惩罚也是负分，但它们和竞价高低
    # 无关 —— 混进 losses 会让「输多于赢 → 调高 bid_margin」这条诊断指错方向。
    duels = [c for c in mine if c.get("kind") == "sprite"]
    wins = [c for c in duels if (c.get("score_delta") or 0) > 0]
    losses = [c for c in duels if (c.get("score_delta") or 0) < 0]
    ties = [c for c in duels if (c.get("score_delta") or 0) == 0]
    obstacle = [c for c in mine if c.get("kind") == "obstacle"]
    idle_hits = [c for c in mine if c.get("kind") == "idle_penalty"]

    # 决策分布：时间都花在哪个意图上
    intents: Counter = Counter()
    for f in frames:
        decision = str(f.get("decision", ""))
        if decision.startswith("["):
            intents[decision[1:decision.find("]")]] += 1

    # 我方每次碰撞的出价分布
    my_spends = [c["energy_spent"] for c in mine
                 if c.get("kind") == "sprite" and c.get("energy_spent")]

    # 对手出价（用于判断我们的竞价余量是否够）
    rival_spends = defaultdict(list)
    for c in collisions:
        if not c.get("is_self") and c.get("kind") == "sprite" and c.get("energy_spent"):
            rival_spends[c["sprite"]].append(c["energy_spent"])

    return {
        "path": path,
        "version": version,
        "frames": len(frames),
        "final_score": (end or {}).get("final_score"),
        "rank": (result or {}).get("rank"),
        "advancement": (result or {}).get("advancement"),
        "heart_pickups": (end or {}).get("heart_pickups"),
        "my_collisions": len(mine),
        "duels": len(duels),
        "wins": len(wins),
        "losses": len(losses),
        "ties": len(ties),
        "obstacle_hits": len(obstacle),
        "idle_penalties": len(idle_hits),
        "idle_penalty_times": [c.get("at_seconds") for c in idle_hits],
        "obstacle_times": [c.get("at_seconds") for c in obstacle],
        "energy_resets": (end or {}).get("energy_resets") or [],
        "zero_energy_share": (end or {}).get("zero_energy_share"),
        "rank_source": (result or {}).get("rank_source"),
        "clock": start.get("clock"),
        "clock_skew_seconds": start.get("clock_skew_seconds"),
        "self_id": start.get("self_id"),
        "sprite_ids": start.get("sprite_ids") or [],
        "duration_seconds": (end or {}).get("duration_seconds"),
        "intents": intents,
        "my_spends": my_spends,
        "rival_spends": dict(rival_spends),
        "collisions": collisions,
    }


def _fmt_spends(values: List[float]) -> str:
    if not values:
        return "无"
    ordered = sorted(values)
    return "n={} 最小={:.0f} 中位={:.0f} 最大={:.0f}".format(
        len(ordered), ordered[0], ordered[len(ordered) // 2], ordered[-1]
    )


def report(data: Dict[str, Any]) -> None:
    print("=" * 68)
    print("replay : {}".format(os.path.basename(data["path"].rstrip("/")) or data["path"]))
    print("版本   : {}（strategyHash）  帧数: {}  时长: {}s".format(
        data["version"], data["frames"], data["duration_seconds"]))
    rank_note = "（{}）".format(data["rank_source"]) if data.get("rank_source") else ""
    print("结果   : 果实={} 名次={}{} 晋级={} 森林之心={} 次".format(
        data["final_score"], data["rank"], rank_note, data["advancement"],
        data["heart_pickups"]))

    # 认错自己 = 策略和复盘都作用在别人身上，所以这条要最显眼（E4）。
    if data.get("sprite_ids") and not data.get("self_id"):
        print("⚠️⚠️ 没能在帧里认出我方精灵！场上 id={}。"
              "先查 botId 与 rabbits[].id 是否对得上，其余数字全部不可信。".format(
                  data["sprite_ids"]))
    print("-" * 68)

    print("我方事件: 精灵碰撞 {} 次 → 赢 {} / 平 {} / 输 {}；撞障碍 {}；空转惩罚 {}".format(
        data["duels"], data["wins"], data["ties"], data["losses"],
        data["obstacle_hits"], data["idle_penalties"]))

    # 平局不丢果实，所以不进净分；空转惩罚每次 -3。
    net = (data["wins"] - data["losses"] - data["obstacle_hits"]
           - 3 * data["idle_penalties"])
    print("果实净变: {:+d}  (+{} 赢 / -{} 输 / -{} 障碍 / -{} 空转×3)".format(
        net, data["wins"], data["losses"], data["obstacle_hits"],
        3 * data["idle_penalties"]))

    # R3 指标：归零后 actualAttack 恒为 0，此后每次碰撞都是确定的 -1。
    share = data.get("zero_energy_share")
    if share is not None:
        verdict = "正常" if share < 0.05 else (
            "⚠️ 偏高" if share < 0.15 else "⚠️⚠️ 在白送果实")
        print("我方能量=0 的帧占比: {:.0%}  → {}".format(share, verdict))

    print("\n我方出价: {}".format(_fmt_spends(data["my_spends"])))
    if data["rival_spends"]:
        print("对手出价:")
        for rid, spends in sorted(data["rival_spends"].items()):
            print("  {:<10} {}".format(rid, _fmt_spends(spends)))
        all_rival = [v for vs in data["rival_spends"].values() for v in vs]
        if all_rival and data["my_spends"]:
            my_med = sorted(data["my_spends"])[len(data["my_spends"]) // 2]
            rv_max = max(all_rival)
            verdict = "够" if my_med > rv_max else "⚠️ 不够，考虑调高 bid_margin"
            print("  → 我方中位出价 {:.0f} vs 对手最高 {:.0f}：{}".format(
                my_med, rv_max, verdict))

    print("\n时间分配（各意图占帧数）:")
    total = max(1, sum(data["intents"].values()))
    if not data["intents"]:
        print("  （无数据：意图只存在于运行时。加 --debug-log，"
              "并用 FIREFLY_DEBUG=1 ... 2> runtime/debug.log 起 BOT）")
    for kind, count in data["intents"].most_common():
        print("  {:<20} {:>5}  {:>5.1%}".format(kind, count, count / total))

    # 现场待验证项（docs/EXPERIMENTS.md）—— 能自动判的就别靠人肉数帧
    print("\n现场实验证据:")
    print("  E1 撞障碍 -1  : {} 次 @ {}".format(
        data["obstacle_hits"], data["obstacle_times"][:8] or "—"))
    print("  E2 空转 -3    : {} 次 @ {}  → 首次时刻决定 idle_seek_at".format(
        data["idle_penalties"], data["idle_penalty_times"][:8] or "—"))
    print("  E5 对手出价   : {}".format(
        "干净整数即说明能量跌幅反推有效，见上「对手出价」一节"
        if data["rival_spends"] else "无数据（对手整局没发生耗能碰撞？）"))
    resets = data["energy_resets"]
    print("  E-能量重置    : {} 次 @ {}（应约每 30s 一次）".format(
        len(resets), resets[:8] or "—"))
    skew = data.get("clock_skew_seconds")
    if skew is None:
        print("  E12 时钟偏移  : 无法计算（用的是 {}）".format(data.get("clock")))
    else:
        verdict = "正常" if abs(skew) <= 2.0 else "⚠️ 超过 2s，把 idle_seek_at 调保守"
        print("  E12 时钟偏移  : {:+.2f}s（服务端 vs 本地接收）→ {}".format(skew, verdict))

    # 最该盯的三件事
    print("\n诊断:")
    hints: List[str] = []
    if data["obstacle_hits"] >= 3:
        hints.append(
            "撞障碍 {} 次是纯损失 → 调大 obstacle_safety_margin / "
            "obstacle_lookahead_seconds".format(data["obstacle_hits"]))
    if data["losses"] > data["wins"]:
        hints.append("输多于赢 → 竞价偏低（bid_margin_pct/abs）或低能量时没避战")
    # 用**实际观测到的 -3**判断，而不是拿碰撞次数猜。碰撞少但一次没被罚，
    # 说明保活是有效的，此时去调 idle_seek_at 就是在追一个不存在的问题。
    if data["idle_penalties"] > 0:
        hints.append(
            "吃到 {} 次空转 -3（@{}）→ 保活失效，调低 idle_seek_at / "
            "idle_obstacle_fallback_at".format(
                data["idle_penalties"], data["idle_penalty_times"][:5]))
    elif data["duels"] < 6:
        hints.append(
            "精灵碰撞只有 {} 次，但没吃到 -3 → 保活是有效的，别动 idle_seek_at；"
            "要提高收益该看竞价和目标选择".format(data["duels"]))
    idle_share = data["intents"].get("conserve", 0) / total
    if idle_share > 0.35:
        hints.append("{:.0%} 的时间在避战 → 能量策略过保守".format(idle_share))
    if not hints:
        hints.append("没有明显单点问题，看趋势和方差而不是单局")
    for h in hints:
        print("  - " + h)
    print("=" * 68)


def compare(datasets: List[Dict[str, Any]]) -> None:
    print("\n多局对比（关注趋势、方差和最差情况，不要只看最好那局）")
    print("-" * 78)
    print("{:<26} {:>6} {:>6} {:>5} {:>5} {:>6} {:>6}".format(
        "replay", "果实", "名次", "赢", "输", "撞障碍", "心"))
    for d in datasets:
        print("{:<26} {:>6} {:>6} {:>5} {:>5} {:>6} {:>6}".format(
            os.path.basename(d["path"])[:26],
            str(d["final_score"]), str(d["rank"]),
            d["wins"], d["losses"], d["obstacle_hits"],
            str(d["heart_pickups"])))

    scores = [d["final_score"] for d in datasets
              if isinstance(d["final_score"], (int, float))]
    if len(scores) >= 2:
        mean = sum(scores) / len(scores)
        worst = min(scores)
        print("-" * 78)
        print("平均 {:.2f}   最差 {:.0f}   极差 {:.0f}".format(
            mean, worst, max(scores) - worst))
        print("锁版看的是「最差情况可接受」，不是「最好情况亮眼」。")


def main() -> None:
    ap = argparse.ArgumentParser(description="萤火森林 replay 分析")
    ap.add_argument("paths", nargs="+",
                    help="采集目录（runtime/ 或 runtime/matches/<code>/）或 telemetry JSONL，支持通配")
    ap.add_argument("--compare", action="store_true", help="只输出多局对比表")
    ap.add_argument("--debug-log", default=None,
                    help="FIREFLY_DEBUG=1 的 stderr 日志，用来补上「时间分配」一节")
    args = ap.parse_args()

    expanded: List[str] = []
    for p in args.paths:
        for candidate in (sorted(glob.glob(p)) or [p]):
            if os.path.isfile(candidate):
                expanded.append(candidate)
            elif os.path.isdir(candidate):
                # 目录：可能本身就是采集目录，也可能是 runtime/ 这种上层目录
                expanded.extend(capture_mod.find_captures(candidate))
    # 去重但保持顺序（runtime/ 与 runtime/matches/x 同时传入时会重合）
    seen: set = set()
    expanded = [p for p in expanded if not (p in seen or seen.add(p))]
    if not expanded:
        raise SystemExit(
            "没有找到可分析的产物。\n"
            "  正式赛：跑一局后产物在 runtime/matches/<matchCode-matchId>/ 下，"
            "直接 `python tools/analyze.py runtime/`\n"
            "  独立 runner：产物是 runs/*.jsonl")

    datasets = [analyze(p, debug_log=args.debug_log) for p in expanded]
    if not args.compare:
        for d in datasets:
            report(d)
    if args.compare or len(datasets) > 1:
        compare(datasets)


if __name__ == "__main__":
    main()
