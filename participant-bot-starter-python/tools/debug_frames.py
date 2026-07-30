"""把沙盒里某段时间的逐帧决策打出来，用于定位「为什么它一直撞墙」这类问题。

用法::

    python tools/debug_frames.py --seed 3 --from 33 --to 40
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firefly import geometry as g  # noqa: E402
from firefly.constants import RULE_FRAME_INTERVAL, TUNE  # noqa: E402
from firefly.protocol import Frame  # noqa: E402

from sim import Sim  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--from", dest="start", type=float, default=33.0)
    ap.add_argument("--to", dest="end", type=float, default=40.0)
    ap.add_argument("--opponents", default="default,steady,aggressive")
    args = ap.parse_args()

    sim = Sim(TUNE, [p.strip() for p in args.opponents.split(",")], seed=args.seed)
    steps = int(180 / RULE_FRAME_INTERVAL)

    for _ in range(steps):
        if not sim.me.alive:
            break
        sim._spawn_heart()

        sim.world.on_frame(Frame.parse(sim._frame_message()))
        action = sim.strategy.decide()

        if args.start <= sim.now <= args.end:
            me = sim.world.me
            clearance, hull = sim.world.obstacle_clearance(me.position)
            radius = g.bounding_radius(me.width, me.height)
            intent = sim.strategy.last_intent
            print(
                "{:6.1f}s pos=({:5.0f},{:5.0f}) spd={:4.1f} ang={:5.2f} "
                "clr={:6.1f}/r={:4.1f} | {:<18} | act={:<14} {}".format(
                    sim.now, me.position[0], me.position[1], me.speed, me.angle,
                    clearance, radius,
                    intent.kind if intent else "-",
                    (action.command_type + ":" + str(action.data)) if action else "-",
                    (intent.reason[:52] if intent else ""),
                )
            )

        # 复用 Sim 的推进逻辑
        if action is not None:
            cmd, data = action.command_type, action.data
            if cmd == "goForward":
                sim.me.move = "forward"
            elif cmd == "goBack":
                sim.me.move = "backward"
            elif cmd == "stop":
                sim.me.move = "halt"
            elif cmd == "steerBack":
                sim.me.turn = "straight"
            elif cmd == "turnLeft":
                sim.me.turn, sim.me.turn_rate = "left", float(data or 0.05)
            elif cmd == "turnRight":
                sim.me.turn, sim.me.turn_rate = "right", float(data or 0.05)
            elif cmd == "setAttackValue":
                sim.me.attack = float(data or 0)

        for bot in sim.bots:
            if bot.sprite.alive:
                bot.step(sim)
        sim._physics()
        sim._collisions()
        sim._periodic()
        sim.now += RULE_FRAME_INTERVAL

        if sim.now > args.end:
            break


if __name__ == "__main__":
    main()
