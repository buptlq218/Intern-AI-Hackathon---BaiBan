"""世界模型 + 决策阶梯的用例。

重点覆盖两类容易悄悄错掉的东西：
1.  对手攻击力推断（本方案的核心信息优势，错了整个出价体系失效）；
2.  优先级阶梯的顺序（比如「对手持心」必须压过「主动进攻」）。
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firefly.constants import Tune
from firefly.control import Controller
from firefly.protocol import Frame, parse_gold_carrot
from firefly.strategy import Strategy
from firefly.worldmodel import WorldModel

MAP_PAYLOAD = {
    "width": 1440,
    "height": 820,
    "borders": [],
    "blocks": [[[{"x": 400, "y": 300}, {"x": 520, "y": 300},
                 {"x": 520, "y": 420}, {"x": 400, "y": 420}]]],
}


def sprite(sid, x, y, *, score=10, energy=1000, invincible=False,
           vx=0.0, vy=0.0, angle=0.0, name=None):
    return {
        "id": sid, "name": name or sid,
        "position": {"x": x, "y": y},
        "velocity": {"x": vx, "y": vy},
        "angle": angle, "speed": (vx ** 2 + vy ** 2) ** 0.5,
        "width": 70, "height": 64,
        "score": score, "energy": energy,
        "active": True, "invincible": invincible, "deathCount": 0,
    }


def frame(sprites, *, elapsed=1.0, carrot=None):
    return {
        "commandType": "refreshData",
        "timestamp": int(elapsed * 1000),
        "data": {
            "rabbits": sprites,
            "goldCarrot": ({"x": carrot[0], "y": carrot[1]} if carrot else {}),
            "elapsedSeconds": elapsed,
            "remainingTime": 180 - elapsed,
        },
    }


def feed_recent_collision(world, sprites, elapsed, my_index=0):
    """把世界推进到 ``elapsed``，并让「我」在紧邻的过去刚发生过一次碰撞。

    为什么需要它：无碰撞惩罚是 -3，比一次不利碰撞（-1）更糟，所以「保活」在
    优先级阶梯里**故意**排在避战和保成果之前。如果测试夹具直接把 elapsed 设成
    165 而从未碰撞过，空转计时就是 165 秒，保活分支会抢占一切，
    根本测不到终局姿态。所以这里先造一次碰撞把计时清零。
    """
    before = [dict(s) for s in sprites]
    world.on_frame(Frame.parse(frame(before, elapsed=max(0.0, elapsed - 0.4))))
    # 我方能量下降 → 引擎判定为一次精灵间碰撞 → 空转计时归零
    during = [dict(s) for s in sprites]
    during[my_index] = dict(during[my_index],
                            energy=max(0.0, during[my_index]["energy"] - 200))
    world.on_frame(Frame.parse(frame(during, elapsed=max(0.0, elapsed - 0.2))))
    world.on_frame(Frame.parse(frame(sprites, elapsed=elapsed)))


def build(tune=None):
    tune = tune or Tune()
    world = WorldModel(tune=tune)
    world.on_start_game(Frame.parse({
        "commandType": "startGame", "timeStamp": 0,
        "data": {"map": MAP_PAYLOAD, "rabbits": []},
    }))
    world.identify_self(sprite_id="me")
    controller = Controller(tune)
    return world, Strategy(tune, world, controller)


class TestProtocolParsing(unittest.TestCase):
    def test_gold_carrot_empty_means_none(self):
        """细则 §4.4：{} 或 null 都表示当前没有森林之心。"""
        self.assertIsNone(parse_gold_carrot({}))
        self.assertIsNone(parse_gold_carrot(None))

    def test_gold_carrot_top_level_xy(self):
        self.assertEqual(parse_gold_carrot({"x": 720, "y": 410}), (720.0, 410.0))

    def test_map_only_in_start_game(self):
        """map 只在 startGame 下发；refreshData 里没有，必须靠缓存。"""
        world, _ = build()
        self.assertIsNotNone(world.game_map)
        world.on_frame(Frame.parse(frame([sprite("me", 100, 100)])))
        self.assertEqual(len(world.game_map.block_hulls), 1,
                         "refreshData 不带 map，缓存必须还在")

    def test_flattens_nested_hulls(self):
        """borders/blocks 是 [物体][凸块][顶点]；凹形物体会被拆成多块。"""
        payload = {
            "width": 1440, "height": 820, "borders": [],
            "blocks": [[
                [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}],
                [{"x": 20, "y": 20}, {"x": 30, "y": 20}, {"x": 30, "y": 30}],
            ]],
        }
        f = Frame.parse({"commandType": "startGame", "timeStamp": 0,
                         "data": {"map": payload, "rabbits": []}})
        self.assertEqual(len(f.game_map.block_hulls), 2,
                         "同一物体的多个凸块都要读到，不能只取 [i][0]")

    def test_timestamp_case_variants(self):
        """startGame 用 timeStamp，refreshData 用 timestamp。"""
        a = Frame.parse({"commandType": "startGame", "timeStamp": 123, "data": {}})
        b = Frame.parse({"commandType": "refreshData", "timestamp": 456, "data": {}})
        self.assertEqual(a.timestamp_ms, 123.0)
        self.assertEqual(b.timestamp_ms, 456.0)

    def test_tolerates_unknown_and_missing_fields(self):
        f = Frame.parse({
            "commandType": "refreshData", "timestamp": 1,
            "data": {"rabbits": [{"id": "x", "brandNewField": 1}]},
        })
        self.assertEqual(len(f.sprites), 1)
        self.assertEqual(f.sprites[0].width, 70.0)   # 安全默认值

    def test_move_state_accepts_number_or_string(self):
        """文档表格写 string，示例给的是 0 —— 两种都不能崩。"""
        for value in (0, "0", "IDLE", None):
            f = Frame.parse({"commandType": "refreshData", "timestamp": 1,
                             "data": {"rabbits": [{"id": "x", "moveState": value}]}})
            self.assertEqual(len(f.sprites), 1)


class TestOpponentInference(unittest.TestCase):
    """能量跌幅 == 对手本次 actualAttack，这是最重要的信息优势。"""

    def test_infers_attack_from_energy_drop(self):
        world, _ = build()
        world.on_frame(Frame.parse(frame(
            [sprite("me", 100, 100), sprite("op", 200, 200)], elapsed=1.0)))
        world.on_frame(Frame.parse(frame(
            [sprite("me", 100, 100, energy=700, score=9),
             sprite("op", 200, 200, energy=750, score=11)], elapsed=1.2)))

        model = world.opponents.get("op")
        self.assertIsNotNone(model)
        self.assertIn(250.0, model.observed_attacks,
                      "对手能量 1000->750，实际攻击强度就是 250")

    def test_threat_level_uses_observation_over_prior(self):
        world, _ = build()
        prior = world.threat_level()
        world.on_frame(Frame.parse(frame(
            [sprite("me", 100, 100), sprite("op", 200, 200)], elapsed=1.0)))
        world.on_frame(Frame.parse(frame(
            [sprite("me", 100, 100, energy=500),
             sprite("op", 200, 200, energy=400)], elapsed=1.2)))
        self.assertGreater(world.threat_level(), prior,
                           "观测到 600 的高出价后，威胁估计必须上调")

    def test_energy_reset_not_counted_as_collision(self):
        """能量重置是上涨，不能被当成碰撞，否则对手模型会被污染。"""
        world, _ = build()
        world.on_frame(Frame.parse(frame(
            [sprite("me", 100, 100, energy=200), sprite("op", 200, 200, energy=100)],
            elapsed=29.9)))
        world.on_frame(Frame.parse(frame(
            [sprite("me", 100, 100, energy=1000), sprite("op", 200, 200, energy=1000)],
            elapsed=30.1)))
        model = world.opponents.get("op")
        self.assertTrue(model is None or not model.observed_attacks)

    def test_energy_reset_recalibrates_window(self):
        world, _ = build()
        world.on_frame(Frame.parse(frame([sprite("me", 100, 100, energy=200)],
                                         elapsed=29.9)))
        world.on_frame(Frame.parse(frame([sprite("me", 100, 100, energy=1000)],
                                         elapsed=30.1)))
        self.assertAlmostEqual(world.seconds_to_energy_reset, 30.0, places=1)

    def test_win_loss_tracked(self):
        world, _ = build()
        world.on_frame(Frame.parse(frame(
            [sprite("me", 100, 100), sprite("op", 200, 200)], elapsed=1.0)))
        world.on_frame(Frame.parse(frame(
            [sprite("me", 100, 100, energy=700, score=9),
             sprite("op", 200, 200, energy=750, score=11)], elapsed=1.2)))
        self.assertEqual(world.opponents["op"].total_wins, 1)


class TestTimers(unittest.TestCase):
    def test_idle_timer_advances(self):
        world, _ = build()
        world.on_frame(Frame.parse(frame([sprite("me", 100, 100)], elapsed=25.0)))
        self.assertAlmostEqual(world.seconds_since_self_collision, 25.0)
        self.assertAlmostEqual(world.seconds_to_idle_penalty, 5.0)

    def test_self_collision_resets_idle_timer(self):
        world, _ = build()
        world.on_frame(Frame.parse(frame([sprite("me", 100, 100)], elapsed=20.0)))
        world.on_frame(Frame.parse(frame(
            [sprite("me", 100, 100, energy=800, score=11)], elapsed=20.2)))
        self.assertLess(world.seconds_since_self_collision, 1.0)

    def test_collision_cooldown_blocks_repeat(self):
        """同一对象 1.5s 冷却内再贴上去不结算，不该选它当目标。"""
        world, _ = build()
        world.on_frame(Frame.parse(frame(
            [sprite("me", 100, 100), sprite("op", 200, 200)], elapsed=10.0)))
        world.on_frame(Frame.parse(frame(
            [sprite("me", 100, 100, energy=800),
             sprite("op", 200, 200, energy=900)], elapsed=10.2)))
        self.assertFalse(world.can_collide_with("op"))
        world.on_frame(Frame.parse(frame(
            [sprite("me", 100, 100, energy=800),
             sprite("op", 200, 200, energy=900)], elapsed=12.0)))
        self.assertTrue(world.can_collide_with("op"))


class TestPriorityLadder(unittest.TestCase):
    def test_holding_heart_beats_everything(self):
        world, strat = build()
        world.on_frame(Frame.parse(frame([
            sprite("me", 700, 400, invincible=True, energy=0),
            sprite("op", 760, 410),
        ], elapsed=40.0)))
        intent = strat.choose_intent(world.me)
        self.assertEqual(intent.kind, "heart_rampage")

    def test_flees_invincible_opponent(self):
        """对手持心时我方必输且对方零成本，没有博弈空间，只能躲。"""
        world, strat = build()
        world.on_frame(Frame.parse(frame([
            sprite("me", 700, 400),
            sprite("op", 740, 400, invincible=True),
        ], elapsed=40.0)))
        intent = strat.choose_intent(world.me)
        self.assertEqual(intent.kind, "flee_invincible")

    def test_contests_nearby_heart(self):
        world, strat = build()
        world.on_frame(Frame.parse(frame(
            [sprite("me", 700, 400, vx=5), sprite("op", 100, 100)],
            elapsed=31.0, carrot=(720, 410))))
        intent = strat.choose_intent(world.me)
        self.assertEqual(intent.kind, "seek_heart")

    def test_yields_hopeless_heart_and_retreats(self):
        """抢不到还赖在附近，等于给持心者送分。"""
        world, strat = build()
        world.on_frame(Frame.parse(frame(
            [sprite("me", 1400, 800, vx=1), sprite("op", 720, 415, vx=6)],
            elapsed=31.0, carrot=(720, 410))))
        intent = strat.choose_intent(world.me)
        self.assertEqual(intent.kind, "yield_heart")
        self.assertIsNotNone(intent.hazard)

    def test_low_energy_triggers_avoidance(self):
        world, strat = build()
        world.on_frame(Frame.parse(frame([
            sprite("me", 700, 400, energy=5),
            sprite("op", 900, 400, energy=1000),
        ], elapsed=10.0)))
        intent = strat.choose_intent(world.me)
        self.assertEqual(intent.kind, "conserve")

    def test_idle_pressure_forces_interaction(self):
        world, strat = build()
        world.on_frame(Frame.parse(frame([
            sprite("me", 700, 400), sprite("op", 900, 400),
        ], elapsed=26.0)))
        intent = strat.choose_intent(world.me)
        self.assertTrue(intent.kind.startswith("idle_"),
                        "空转 26s 必须主动找碰撞，得到的是 {}".format(intent.kind))
        self.assertTrue(intent.commit_contact)

    def test_idle_fallback_hits_obstacle_when_no_target(self):
        """找不到精灵目标就撞障碍：-1 优于 -3。"""
        world, strat = build()
        world.on_frame(Frame.parse(frame([sprite("me", 460, 500)], elapsed=27.0)))
        intent = strat.choose_intent(world.me)
        self.assertEqual(intent.kind, "idle_hit_obstacle")
        self.assertIsNotNone(intent.target)

    def test_attacks_when_healthy(self):
        world, strat = build()
        world.on_frame(Frame.parse(frame([
            sprite("me", 700, 400, energy=1000),
            sprite("op", 800, 400, energy=1000),
        ], elapsed=5.0)))
        intent = strat.choose_intent(world.me)
        self.assertEqual(intent.kind, "ram")


class TestActionOutput(unittest.TestCase):
    def test_emits_at_most_one_action_per_frame(self):
        """细则：每次策略回调最多返回一个动作。"""
        world, strat = build()
        for i in range(30):
            world.on_frame(Frame.parse(frame([
                sprite("me", 700 + i, 400, energy=1000),
                sprite("op", 900, 400),
            ], elapsed=1.0 + i * 0.1)))
            action = strat.decide()
            self.assertTrue(action is None or hasattr(action, "command_type"))

    def test_first_action_sets_attack_value(self):
        """默认攻击强度只有 50，开局第一件事必须是设出价。"""
        world, strat = build()
        world.on_frame(Frame.parse(frame([
            sprite("me", 700, 400), sprite("op", 900, 400),
        ], elapsed=0.5)))
        action = strat.decide()
        self.assertIsNotNone(action)
        self.assertEqual(action.command_type, "setAttackValue")

    def test_attack_value_is_non_negative_numeric_string(self):
        world, strat = build()
        world.on_frame(Frame.parse(frame([
            sprite("me", 700, 400, energy=0), sprite("op", 900, 400),
        ], elapsed=0.5)))
        action = strat.decide()
        self.assertEqual(action.command_type, "setAttackValue")
        self.assertGreaterEqual(float(action.data), 0.0)

    def test_turn_rate_within_protocol_range(self):
        """turnLeft/turnRight 的 data 必须落在 0.01~0.1。"""
        world, strat = build()
        seen_turn = False
        for i in range(40):
            world.on_frame(Frame.parse(frame([
                sprite("me", 700, 400, angle=3.0, energy=1000),
                sprite("op", 200, 700),
            ], elapsed=1.0 + i * 0.1)))
            action = strat.decide()
            if action and action.command_type in ("turnLeft", "turnRight"):
                seen_turn = True
                self.assertGreaterEqual(float(action.data), 0.01)
                self.assertLessEqual(float(action.data), 0.1)
        self.assertTrue(seen_turn, "应至少发出过一次转向指令")

    def test_no_action_when_eliminated(self):
        """果实为 0 即淘汰，不该再发指令。"""
        world, strat = build()
        world.on_frame(Frame.parse(frame([sprite("me", 700, 400, score=0)],
                                         elapsed=50.0)))
        self.assertIsNone(strat.decide())

    def test_does_not_repeat_identical_commands(self):
        """细则：相同指令仅在策略状态变化时发送。"""
        world, strat = build()
        emitted = []
        for i in range(60):
            world.on_frame(Frame.parse(frame([
                sprite("me", 700, 400, angle=0.0, energy=1000, vx=0.0),
                sprite("op", 1000, 400, energy=1000),
            ], elapsed=1.0 + i * 0.1)))
            action = strat.decide()
            if action:
                emitted.append((action.command_type, action.data))
        # 状态稳定后应收敛到不再发送
        self.assertLess(len(emitted), 20,
                        "状态不变却持续发指令，说明变化检测失效：{}".format(emitted))


class TestTurnCalibration(unittest.TestCase):
    def test_learns_sign_from_observation(self):
        from firefly.control import LEFT, TurnCalibration

        calib = TurnCalibration()
        self.assertFalse(calib.calibrated)
        for _ in range(4):
            calib.observe(LEFT, -0.05)      # 左转让 angle 减小
        self.assertTrue(calib.calibrated)
        self.assertEqual(calib.sign, -1)
        # 想让 angle 减小，就应该发左转
        self.assertEqual(calib.command_for(-0.5), LEFT)

    def test_ignores_noise(self):
        from firefly.control import LEFT, TurnCalibration

        calib = TurnCalibration()
        calib.observe(LEFT, 0.0)
        calib.observe("straight", 0.5)
        self.assertFalse(calib.calibrated)


if __name__ == "__main__":
    unittest.main()


class TestEndgamePosture(unittest.TestCase):
    """积分规则驱动的终局姿态。

    每轮按名次积 3/2/1/0 分，同分取果实多者，4 进 2 —— 收益是不对称的：
    领先时「少输」比「多赢」值钱；眼看垫底时没有下行空间，该赌。
    """

    def test_normal_when_time_remains(self):
        world, strat = build()
        world.on_frame(Frame.parse(frame([
            sprite("me", 700, 400, score=20), sprite("op", 760, 400, score=2),
        ], elapsed=10.0)))
        self.assertEqual(strat.endgame_posture(world.me), "normal",
                         "还剩很多时间就不该进入终局姿态")

    def test_protect_when_leading_late(self):
        world, strat = build()
        world.on_frame(Frame.parse(frame([
            sprite("me", 700, 400, score=18),
            sprite("op1", 760, 400, score=4),
            sprite("op2", 300, 300, score=3),
        ], elapsed=165.0)))
        self.assertEqual(strat.endgame_posture(world.me), "protect")

    def test_desperate_when_below_cutoff_late(self):
        world, strat = build()
        world.on_frame(Frame.parse(frame([
            sprite("me", 700, 400, score=3),
            sprite("op1", 760, 400, score=14),
            sprite("op2", 300, 300, score=12),
        ], elapsed=165.0)))
        self.assertEqual(strat.endgame_posture(world.me), "desperate")

    def test_protect_avoids_unnecessary_contact(self):
        world, strat = build()
        feed_recent_collision(world, [
            sprite("me", 700, 400, score=18, energy=1000),
            sprite("op1", 780, 400, score=4),
            sprite("op2", 300, 300, score=3),
        ], elapsed=165.0)
        self.assertEqual(strat.choose_intent(world.me).kind, "protect_lead")

    def test_desperate_attacks_despite_bad_odds(self):
        """能量不足平时会避战，但垫底时应该照打 —— 第 4 名已经是 0 分。"""
        world, strat = build()
        feed_recent_collision(world, [
            sprite("me", 700, 400, score=2, energy=10),
            sprite("op1", 780, 400, score=15, energy=1000),
            sprite("op2", 300, 300, score=13, energy=1000),
        ], elapsed=165.0)
        self.assertEqual(strat.choose_intent(world.me).kind, "ram",
                         "垫底且时间不够时不该继续避战")

    def test_low_energy_still_conserves_in_midgame(self):
        """回归：中局能量不足仍然必须避战，别被终局逻辑带跑。"""
        world, strat = build()
        feed_recent_collision(world, [
            sprite("me", 700, 400, score=8, energy=5),
            sprite("op", 900, 400, energy=1000),
        ], elapsed=40.0)
        self.assertEqual(strat.choose_intent(world.me).kind, "conserve")


class TestRanking(unittest.TestCase):
    def test_my_rank(self):
        world, _ = build()
        world.on_frame(Frame.parse(frame([
            sprite("me", 700, 400, score=9),
            sprite("op1", 100, 100, score=15),
            sprite("op2", 200, 200, score=3),
        ], elapsed=50.0)))
        self.assertEqual(world.my_rank(), 2)

    def test_eliminated_rivals_rank_below_alive(self):
        world, _ = build()
        world.on_frame(Frame.parse(frame([
            sprite("me", 700, 400, score=1),
            sprite("op1", 100, 100, score=0),
        ], elapsed=50.0)))
        self.assertEqual(world.my_rank(), 1, "果实归零的对手应排在存活者之后")

    def test_margin_positive_when_above_cutoff(self):
        world, _ = build()
        world.on_frame(Frame.parse(frame([
            sprite("me", 700, 400, score=12),
            sprite("op1", 100, 100, score=14),
            sprite("op2", 200, 200, score=5),
            sprite("op3", 300, 300, score=4),
        ], elapsed=50.0)))
        # 4 进 2：我要压过第 2 名对手（5 分）→ 领先 7
        self.assertAlmostEqual(world.score_margin_to_cutoff(), 7.0)

    def test_margin_negative_when_below_cutoff(self):
        world, _ = build()
        world.on_frame(Frame.parse(frame([
            sprite("me", 700, 400, score=3),
            sprite("op1", 100, 100, score=14),
            sprite("op2", 200, 200, score=9),
            sprite("op3", 300, 300, score=8),
        ], elapsed=50.0)))
        self.assertAlmostEqual(world.score_margin_to_cutoff(), -6.0)


class TestEnergyCappedThreat(unittest.TestCase):
    """对手当前能量是他攻击强度的硬上限（actualAttack = min(设定, 能量)）。

    这是最有实战价值的一条修正：只看历史出价会把「已经花光能量的梭哈型对手」
    一直当成 1000 的威胁，于是全场躲着一个空壳打。
    """

    def _observe_big_bid(self, world):
        """让对手暴露一次 600 的出价。"""
        world.on_frame(Frame.parse(frame(
            [sprite("me", 700, 400), sprite("op", 900, 400)], elapsed=1.0)))
        world.on_frame(Frame.parse(frame(
            [sprite("me", 700, 400, energy=500),
             sprite("op", 900, 400, energy=400)], elapsed=1.2)))

    def test_threat_capped_by_current_energy(self):
        world, _ = build()
        self._observe_big_bid(world)
        # 对手历史出价 600，但当前只剩 400 能量
        self.assertAlmostEqual(world.threat_of("op"), 400.0)

    def test_drained_rival_is_harmless(self):
        world, _ = build()
        self._observe_big_bid(world)
        world.on_frame(Frame.parse(frame(
            [sprite("me", 700, 400, energy=1000),
             sprite("op", 900, 400, energy=0)], elapsed=2.0)))
        self.assertAlmostEqual(world.threat_of("op"), 0.0,
                               msg="能量为 0 的对手打不出任何攻击强度")

    def test_threat_recovers_after_energy_reset(self):
        """能量重置回 1000 后，威胁应该恢复到历史出价水平。"""
        world, _ = build()
        self._observe_big_bid(world)
        world.on_frame(Frame.parse(frame(
            [sprite("me", 700, 400, energy=1000),
             sprite("op", 900, 400, energy=1000)], elapsed=30.1)))
        self.assertAlmostEqual(world.threat_of("op"), 600.0)

    def test_prefers_drained_target(self):
        """两个对手一样远时，优先打能量见底的那个。"""
        world, strat = build()
        world.on_frame(Frame.parse(frame([
            sprite("me", 700, 400, energy=1000),
            sprite("rich", 700, 300, energy=1000),
            sprite("poor", 700, 500, energy=20),
        ], elapsed=5.0)))
        target = strat._best_target(world.me)
        self.assertIsNotNone(target)
        self.assertEqual(target.id, "poor",
                         "能量枯竭的对手是白送的果实，应优先")

    def test_engages_instead_of_fleeing_when_tie_possible(self):
        """打不赢但能打平时不该避战 —— 平局不丢果实，还免费重置空转计时。"""
        world, strat = build()
        feed_recent_collision(world, [
            sprite("me", 700, 400, score=10, energy=1000),
            sprite("op", 820, 400, score=10, energy=1000),
        ], elapsed=40.0)
        # 让对手暴露一个我方压不过的出价（1000）
        world.opponents.setdefault("op", None)
        model = world.opponents.get("op")
        if model is not None:
            model.observed_attacks.append(1000.0)
        intent = strat.choose_intent(world.me)
        self.assertNotEqual(intent.kind, "conserve",
                            "能打平就不该全场避战")


class TestR3PerTargetThreat(unittest.TestCase):
    """R3：出价按「将要撞的那个对手」算，不是全场最大威胁。

    现场证据：出价序列 154→212→285→326 一路被最凶的那个对手抬着走，
    即使我们冲着一个能量见底的弱敌去，也照样按强敌的价出 —— 能量因此归零。
    """

    def _world(self, rivals):
        """rivals: [(id, energy, x, y)]，我方固定在 (100, 100)。"""
        world = WorldModel(tune=Tune())
        rabbits = [{"id": "me", "position": {"x": 100, "y": 100}, "energy": 1000,
                    "score": 10, "active": True}]
        for rid, energy, x, y in rivals:
            rabbits.append({"id": rid, "position": {"x": x, "y": y},
                            "energy": energy, "score": 10, "active": True})
        world.identify_self(sprite_id="me")
        world.on_frame(Frame.parse(
            {"commandType": "refreshData", "timestamp": 0,
             "data": {"rabbits": rabbits}}), elapsed=1.0)
        return world

    def test_bids_against_the_drained_target_not_the_strong_bystander(self):
        """⭐ 强敌在远处、弱敌在眼前 → 按弱敌出价。"""
        # weak 能量 0 且贴身；strong 满能量但很远
        world = self._world([("weak", 0, 140, 100), ("strong", 1000, 1300, 700)])
        me = world.me
        per_target = world.threat_for_contact("weak", me)
        globally = world.threat_level()
        self.assertLess(per_target, globally,
                        "按目标出价必须低于全场最大威胁，否则这条修正没生效")
        self.assertLessEqual(per_target, 1.0, "对手能量 0 → 威胁应≈0")

    def test_closer_stronger_rival_is_still_counted(self):
        """但不能被偷袭：比目标更近的强敌要算进威胁。"""
        # strong 贴身，weak 在远处
        world = self._world([("weak", 0, 1300, 700), ("strong", 900, 130, 100)])
        me = world.me
        threat = world.threat_for_contact("weak", me)
        self.assertGreater(threat, 100.0,
                           "贴身强敌必须被计入，否则会被以为在打弱敌时偷袭")

    def test_energy_caps_the_threat(self):
        """actualAttack = min(设定, 能量) → 对手能量是硬上限。"""
        world = self._world([("a", 30, 200, 100)])
        self.assertLessEqual(world.threat_for_contact("a", world.me), 30.0)
