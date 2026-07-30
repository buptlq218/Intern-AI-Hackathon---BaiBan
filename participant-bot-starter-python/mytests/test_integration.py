"""strategy.py 与官方 SDK 契约的集成测试。

这里守的是「比赛中不能崩、不能发非法指令」。引擎逻辑本身由其它用例覆盖；
这个文件专门针对 bot.py 的调用方式和校验规则：

*   ``normalize_command`` 对非 dict 会抛 ValueError → **绝不能返回 None**
*   ``setAttackValue.data`` 必须落在 0～1000
*   ``turnLeft/turnRight.data`` 必须落在 0.01～0.1
*   找不到本人 / 本人已淘汰 → 必须恰好返回 ``{"commandType": "stop"}``
*   帧里没有 ``elapsedSeconds``，时间要靠本地时钟
*   帧里没有 ``map``，靠 ``on_start_game`` hook
"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import strategy as strat

SIMPLE = {"goForward", "goBack", "stop", "steerBack"}
TURNS = {"turnLeft", "turnRight"}

MAP_DATA = {
    "width": 1440, "height": 820, "borders": [],
    "blocks": [[[{"x": 400, "y": 300}, {"x": 520, "y": 300},
                 {"x": 520, "y": 420}, {"x": 400, "y": 420}]]],
}


def rabbit(rid, x, y, **kw):
    base = {
        "id": rid, "name": str(rid),
        "position": {"x": x, "y": y},
        "velocity": {"x": kw.get("vx", 0.0), "y": kw.get("vy", 0.0)},
        "angle": kw.get("angle", 0.0), "speed": kw.get("speed", 0.0),
        "angularSpeed": 0, "dirState": 0, "moveState": 0,
        "width": 70, "height": 64,
        "score": kw.get("score", 10), "energy": kw.get("energy", 1000),
        "active": kw.get("active", True), "invincible": kw.get("invincible", False),
        "attacking": False, "rebounding": False, "reboundAngle": 0,
        "deathCount": 0, "survivalTime": 12,
    }
    return base


def state(rabbits, carrot=None):
    return {"rabbits": rabbits, "goldCarrot": (carrot or {})}


def assert_legal(case, command):
    """复制 bot.py::normalize_command 的校验规则。"""
    case.assertIsInstance(command, dict, "策略必须返回 dict，返回 None 会被判为非法")
    ctype = command.get("commandType")
    if ctype in SIMPLE:
        return
    if ctype in TURNS:
        case.assertIn("data", command, "转向指令必须带 data")
        value = float(command["data"])
        case.assertGreaterEqual(value, 0.01)
        case.assertLessEqual(value, 0.1)
        return
    if ctype == "setAttackValue":
        value = float(command["data"])
        case.assertGreaterEqual(value, 0)
        case.assertLessEqual(value, 1000, "bot.py 要求攻击强度 ≤ 1000")
        return
    raise AssertionError("非法 commandType: {}".format(ctype))


class TestContract(unittest.TestCase):
    def setUp(self):
        strat.on_start_game({"map": MAP_DATA, "rabbits": []})

    # -- 必须返回合法 dict -------------------------------------------

    def test_never_returns_none(self):
        """引擎在「状态无变化」时返回 None，但契约不允许 —— 必须被填充掉。"""
        st = state([rabbit(1001, 700, 400), rabbit(1002, 900, 400)])
        for _ in range(60):
            command = strat.choose_command(st, 1001)
            self.assertIsNotNone(command)
            assert_legal(self, command)

    def test_all_commands_legal_over_long_run(self):
        """连续跑几百帧，位置和能量都在变，所有指令都必须合法。"""
        for i in range(300):
            st = state(
                [
                    rabbit(1001, 200 + (i * 4) % 1000, 150 + (i * 3) % 600,
                           angle=(i * 0.1) % 6.28, speed=(i % 7),
                           vx=(i % 5) - 2, vy=(i % 3) - 1,
                           energy=max(0, 1000 - (i * 7) % 1100),
                           score=max(1, 10 - (i // 50))),
                    rabbit(1002, 900, 400, energy=(i * 13) % 1000),
                    rabbit(1003, 500, 300, invincible=(i % 90 < 10)),
                ],
                carrot=({"x": 720, "y": 410} if i % 70 < 20 else None),
            )
            assert_legal(self, strat.choose_command(st, 1001))

    # -- 边界场景 -----------------------------------------------------

    def test_stop_when_self_missing(self):
        self.assertEqual(strat.choose_command(state([]), 1001),
                         {"commandType": "stop"})
        self.assertEqual(
            strat.choose_command(state([rabbit(9999, 100, 100)]), 1001),
            {"commandType": "stop"})

    def test_stop_when_eliminated(self):
        dead = rabbit(1001, 700, 400, active=False, score=0, energy=0)
        self.assertEqual(strat.choose_command(state([dead]), 1001),
                         {"commandType": "stop"})

    def test_handles_ai_prefixed_id(self):
        """本地 sample 服务会给 id 加 ai: 前缀。"""
        st = state([rabbit("ai:1001", 700, 400), rabbit(1002, 900, 400)])
        command = strat.choose_command(st, 1001)
        self.assertNotEqual(command, {"commandType": "stop"})
        assert_legal(self, command)

    def test_survives_garbage_input(self):
        """脏数据不能让策略抛异常 —— bot.py 会把异常降级成 stop 并刷日志。"""
        for bad in (
            {},
            {"rabbits": None},
            {"rabbits": "nope"},
            {"rabbits": [None, 3, "x"]},
            {"rabbits": [{"id": 1001}]},
            {"rabbits": [{"id": 1001, "position": None}]},
            {"rabbits": [{"id": 1001, "position": {"x": None, "y": None}}]},
            {"rabbits": [rabbit(1001, 700, 400)], "goldCarrot": "bad"},
            {"rabbits": [rabbit(1001, 700, 400)], "goldCarrot": {"x": None}},
        ):
            command = strat.choose_command(bad, 1001)
            assert_legal(self, command)

    def test_missing_optional_fields(self):
        """细则：忽略未知字段、为可选字段设安全默认值。"""
        minimal = {"id": 1001, "position": {"x": 700, "y": 400}, "active": True}
        command = strat.choose_command({"rabbits": [minimal]}, 1001)
        assert_legal(self, command)

    def test_unknown_extra_fields_ignored(self):
        r = rabbit(1001, 700, 400)
        r["brandNewFieldFromFutureVersion"] = {"nested": [1, 2, 3]}
        assert_legal(self, strat.choose_command(state([r]), 1001))

    # -- 攻击强度 -----------------------------------------------------

    def test_sets_attack_before_default_50_can_hurt(self):
        """默认攻击强度只有 50，第一个动作就该把它改掉。"""
        strat.on_start_game({"map": MAP_DATA, "rabbits": []})
        st = state([rabbit(1001, 700, 400), rabbit(1002, 900, 400)])
        first = strat.choose_command(st, 1001)
        self.assertEqual(first["commandType"], "setAttackValue")
        self.assertGreater(float(first["data"]), 50,
                           "出价必须高于默认值 50，否则开局白输")

    def test_attack_never_exceeds_energy(self):
        """actualAttack = min(设定, 能量)，出价超过能量没有意义。"""
        strat.on_start_game({"map": MAP_DATA, "rabbits": []})
        st = state([rabbit(1001, 700, 400, energy=120),
                    rabbit(1002, 760, 400, energy=1000)])
        for _ in range(20):
            command = strat.choose_command(st, 1001)
            if command["commandType"] == "setAttackValue":
                self.assertLessEqual(float(command["data"]), 120 + 1e-6)

    def test_attack_zero_energy_is_zero_not_negative(self):
        strat.on_start_game({"map": MAP_DATA, "rabbits": []})
        st = state([rabbit(1001, 700, 400, energy=0),
                    rabbit(1002, 900, 400)])
        for _ in range(20):
            command = strat.choose_command(st, 1001)
            if command["commandType"] == "setAttackValue":
                self.assertGreaterEqual(float(command["data"]), 0)

    # -- 地图 hook ----------------------------------------------------

    def test_on_start_game_caches_map(self):
        strat.on_start_game({"map": MAP_DATA, "rabbits": []})
        world = strat._session.world
        self.assertIsNotNone(world.game_map)
        self.assertEqual(len(world.game_map.block_hulls), 1)

    def test_works_without_map_hook(self):
        """没有 hook 也不能崩，只是退化成不躲石头。"""
        session = strat._Session()
        original = strat._session
        try:
            strat._session = session
            st = state([rabbit(1001, 700, 400), rabbit(1002, 900, 400)])
            for _ in range(20):
                assert_legal(self, strat.choose_command(st, 1001))
        finally:
            strat._session = original

    def test_on_start_game_resets_between_games(self):
        """三局制：每局都会重新 startGame，状态必须清干净。"""
        st = state([rabbit(1001, 700, 400, energy=300, score=4),
                    rabbit(1002, 900, 400)])
        for _ in range(10):
            strat.choose_command(st, 1001)
        strat.on_start_game({"map": MAP_DATA, "rabbits": []})
        self.assertEqual(strat._session.frames, 0)
        self.assertEqual(len(strat._session.world.collisions), 0)
        self.assertEqual(strat._session.world.opponents, {})

    def test_on_start_game_tolerates_junk(self):
        for bad in (None, {}, {"map": None}, {"map": "x"}, {"map": {}}):
            strat.on_start_game(bad)
            assert_legal(self, strat.choose_command(
                state([rabbit(1001, 700, 400)]), 1001))

    # -- 时钟 ---------------------------------------------------------

    def test_clock_advances_without_elapsed_field(self):
        """官方帧里没有 elapsedSeconds，时间必须靠本地时钟推进。"""
        strat.on_start_game({"map": MAP_DATA, "rabbits": []})
        st = state([rabbit(1001, 700, 400)])
        strat.choose_command(st, 1001)
        first = strat._session.world.elapsed
        import time
        time.sleep(0.05)
        strat.choose_command(st, 1001)
        self.assertGreater(strat._session.world.elapsed, first,
                           "本地时钟必须推进，否则两个 30s 周期全部失效")


class TestOpponentInferenceEndToEnd(unittest.TestCase):
    """核心信息优势：能量跌幅 → 对手实际攻击强度。走完整的 choose_command 链路。"""

    def test_infers_rival_attack_through_public_api(self):
        strat.on_start_game({"map": MAP_DATA, "rabbits": []})
        before = state([rabbit(1001, 700, 400, energy=1000),
                        rabbit(1002, 760, 400, energy=1000)])
        strat.choose_command(before, 1001)

        # 对手能量 1000 → 640，说明这次出价 360
        after = state([rabbit(1001, 700, 400, energy=800, score=9),
                       rabbit(1002, 760, 400, energy=640, score=11)])
        strat.choose_command(after, 1001)

        model = strat._session.world.opponents.get("1002")
        self.assertIsNotNone(model, "应该已经建立对手模型")
        self.assertIn(360.0, model.observed_attacks,
                      "能量跌幅 360 就是对手的实际攻击强度")

    def test_bid_rises_to_beat_observed_rival(self):
        """观测到对手出高价后，我方出价必须跟上。"""
        strat.on_start_game({"map": MAP_DATA, "rabbits": []})
        st_a = state([rabbit(1001, 700, 400, energy=1000),
                      rabbit(1002, 900, 400, energy=1000)])
        strat.choose_command(st_a, 1001)

        # 对手花掉 600 后只剩 400 能量。actualAttack = min(设定, 能量)，
        # 所以他这一刻最多只能打出 400 —— 出价只要压过 400 就够，
        # 压过历史值 600 是纯浪费。
        st_b = state([rabbit(1001, 700, 400, energy=1000),
                      rabbit(1002, 900, 400, energy=400)])

        # 从观测到威胁的那一帧开始就收集。单动作限制下，出价更新会排在
        # 移动/转向之后几帧才发出，所以要给它几帧时间，但不能太久。
        bids = []
        for _ in range(12):
            command = strat.choose_command(st_b, 1001)
            if command["commandType"] == "setAttackValue":
                bids.append(float(command["data"]))
        self.assertTrue(bids, "威胁上升后应该重新设置攻击强度")
        self.assertGreater(max(bids), 400,
                           "必须压过对手当前能量允许的 400，否则这次碰撞白输")
        self.assertLess(max(bids), 600,
                        "对手只剩 400 能量，出到 600 是纯浪费")

    def test_bid_respects_rival_energy_cap(self):
        """对手能量枯竭时，出价应该跟着降下来 —— 空壳不值得梭哈。

        这是最有价值的一条：每次梭哈 1000 的队伍花完之后，整个 30s 窗口剩余时间
        能量都是 0，此时随便一个最小出价就能白拿 +1。
        """
        strat.on_start_game({"map": MAP_DATA, "rabbits": []})
        rich = state([rabbit(1001, 700, 400, energy=1000),
                      rabbit(1002, 900, 400, energy=1000)])
        strat.choose_command(rich, 1001)

        # 对手梭哈 1000 之后变成空壳
        drained = state([rabbit(1001, 700, 400, energy=1000),
                         rabbit(1002, 900, 400, energy=0)])
        bids = []
        for _ in range(12):
            command = strat.choose_command(drained, 1001)
            if command["commandType"] == "setAttackValue":
                bids.append(float(command["data"]))
        self.assertTrue(bids, "对手威胁变化后应该重设出价")
        self.assertLessEqual(min(bids), 200,
                             "对手能量为 0，不该再出高价（min(设定,能量)=0，必胜）")

    def test_bid_update_is_not_starved_by_movement(self):
        """单动作限制下，出价更新不能被移动/转向无限期挤掉。

        出价过时会直接输掉碰撞，所以必须在少数几帧内发出。
        """
        strat.on_start_game({"map": MAP_DATA, "rabbits": []})
        st_a = state([rabbit(1001, 700, 400, energy=1000),
                      rabbit(1002, 900, 400, energy=1000)])
        strat.choose_command(st_a, 1001)

        st_b = state([rabbit(1001, 700, 400, energy=1000),
                      rabbit(1002, 900, 400, energy=400)])
        for _ in range(6):
            command = strat.choose_command(st_b, 1001)
            if command["commandType"] == "setAttackValue":
                self.assertGreater(float(command["data"]), 400)
                return
        self.fail("6 帧内没有更新出价，说明出价被移动指令饿死了")


if __name__ == "__main__":
    unittest.main()
