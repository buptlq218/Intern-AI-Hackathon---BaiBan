"""replay 分析器：把一局 JSONL 变成「每次得失分的解释」。

这是 Loop 里的 Checker。现场流程：跑一局 → ``python tools/analyze.py runs/最新.jsonl``
→ 看哪一类损失最大 → 只改一个参数 → 再跑。

用法::

    python tools/analyze.py runs/20260730-141530_firefly-v1_forest.jsonl
    python tools/analyze.py runs/*.jsonl --compare
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, Iterator, List, Optional


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


def analyze(path: str) -> Dict[str, Any]:
    frames: List[Dict[str, Any]] = []
    collisions: List[Dict[str, Any]] = []
    result: Optional[Dict[str, Any]] = None
    end: Optional[Dict[str, Any]] = None
    version = "?"

    for record in read_jsonl(path):
        kind = record.get("type")
        if kind == "match_start":
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
    wins = [c for c in mine if (c.get("score_delta") or 0) > 0]
    losses = [c for c in mine if (c.get("score_delta") or 0) < 0]
    obstacle = [c for c in mine if c.get("kind") == "obstacle"]

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
        "wins": len(wins),
        "losses": len(losses),
        "obstacle_hits": len(obstacle),
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
    print("replay : {}".format(os.path.basename(data["path"])))
    print("版本   : {}   帧数: {}".format(data["version"], data["frames"]))
    print("结果   : 果实={} 名次={} 晋级={} 森林之心={} 次".format(
        data["final_score"], data["rank"], data["advancement"],
        data["heart_pickups"]))
    print("-" * 68)

    print("我方碰撞: {} 次  → 赢 {} / 输 {} / 撞障碍 {}".format(
        data["my_collisions"], data["wins"], data["losses"], data["obstacle_hits"]))

    net = data["wins"] - data["losses"] - data["obstacle_hits"]
    print("碰撞净分: {:+d}（不含无碰撞惩罚）".format(net))

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
    for kind, count in data["intents"].most_common():
        print("  {:<20} {:>5}  {:>5.1%}".format(kind, count, count / total))

    # 最该盯的三件事
    print("\n诊断:")
    hints: List[str] = []
    if data["obstacle_hits"] >= 3:
        hints.append(
            "撞障碍 {} 次是纯损失 → 调大 obstacle_safety_margin / "
            "obstacle_lookahead_seconds".format(data["obstacle_hits"]))
    if data["losses"] > data["wins"]:
        hints.append("输多于赢 → 竞价偏低（bid_margin_pct/abs）或低能量时没避战")
    if data["my_collisions"] < 6:
        hints.append(
            "整局只碰撞 {} 次 → 可能在吃无碰撞惩罚，调低 idle_seek_at".format(
                data["my_collisions"]))
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
    ap.add_argument("paths", nargs="+", help="JSONL 路径，支持通配")
    ap.add_argument("--compare", action="store_true", help="只输出多局对比表")
    args = ap.parse_args()

    expanded: List[str] = []
    for p in args.paths:
        expanded.extend(sorted(glob.glob(p)) or [p])
    expanded = [p for p in expanded if os.path.isfile(p)]
    if not expanded:
        raise SystemExit("没有找到 replay 文件。先跑一局，产物在 runs/ 下。")

    datasets = [analyze(p) for p in expanded]
    if not args.compare:
        for d in datasets:
            report(d)
    if args.compare or len(datasets) > 1:
        compare(datasets)


if __name__ == "__main__":
    main()
