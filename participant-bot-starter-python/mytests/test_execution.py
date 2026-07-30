"""R4/R5/R6 的用例：避障刹车、卡位、以及「想法与动作一致」。

这一批全部来自**督战时的现场观察 + replay 反算**，不是理论推导：

*   R4 —— 15 局 83 次撞障碍，危险检测 83/83 都报了警（100%），但连续预警只有
    0.30s，而切向脱离要 1.6s。而且 ``map_center()`` 到石头只有 51.8px < 触发半径
    75.5px，巡航目标点本身就在危险区里（71% 的撞击发生在 patrol）。
*   R5 —— 森林之心固定在 30.0s 刷新（15/15），且只落在中央区。不卡位时我方平均
    排名 2.57（四人局随机 = 2.50，等于毫无优势）。
*   R6 —— 追击帧里 17% 车头背对目标、逃跑帧里 39% 车头还朝着追我的人。根因是
    倒车判据要求 ``speed < 1.0``，导致 4817 条移动指令里只有 25 条（0.5%）倒车。
"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firefly import geometry as g
from firefly.constants import RULE_HEART_SPAWN_BOX, Tune
from firefly.control import BACKWARD, FORWARD, Controller
from firefly.protocol import GameMap, Sprite


def _sprite(x, y, angle=0.0, speed=5.0, **kw):
    kw.setdefault("width", 70.0)
    kw.setdefault("height", 70.0)
    return Sprite(id="me", position=(x, y), angle=angle, speed=speed,
                  velocity=(speed * math.cos(angle), speed * math.sin(angle)), **kw)


class TestR6ReverseWhenTargetBehind(unittest.TestCase):
    """目标在身后就该倒车 —— 判据是几何，不是「已经快停下了」。"""

    def setUp(self):
        self.tune = Tune()
        self.ctl = Controller(self.tune)

    def test_reverses_when_target_is_behind_even_at_full_speed(self):
        """⭐ 核心回归：旧代码要求 speed<1.0，全速时永不倒车，于是一路朝反方向开。"""
        me = _sprite(700, 400, angle=0.0, speed=5.0)     # 车头朝 +x
        move, _turn, _rate = self.ctl.steer_towards(me, (300, 400))  # 目标在正后方
        self.assertEqual(move, BACKWARD,
                         "目标在正后方且倒车不减速（实测同为 5px/帧），必须倒车")

    def test_goes_forward_when_target_is_ahead(self):
        me = _sprite(700, 400, angle=0.0, speed=5.0)
        move, _t, _r = self.ctl.steer_towards(me, (1100, 400))
        self.assertEqual(move, FORWARD)

    def test_commanded_motion_always_reduces_distance(self):
        """不论目标在哪个方位，发出的指令都必须让距离**变小**。

        这就是「思想与行为一致」的可执行定义：意图说要靠近，那么这一帧的位移
        投影到「指向目标」的方向上必须为正。
        """
        me_pos = (700.0, 400.0)
        for deg in range(0, 360, 15):
            target = (me_pos[0] + 400 * math.cos(math.radians(deg)),
                      me_pos[1] + 400 * math.sin(math.radians(deg)))
            ctl = Controller(self.tune)          # 每次新建，避免迟滞状态串味
            me = _sprite(*me_pos, angle=0.0, speed=5.0)
            move, _t, _r = ctl.steer_towards(me, target)
            nose = (math.cos(me.angle), math.sin(me.angle))
            step = nose if move == FORWARD else (-nose[0], -nose[1])
            want = g.normalize(g.sub(target, me.position))
            # 正好 90°（deg=90/270）时前进和倒车都不靠近，允许为 0
            self.assertGreaterEqual(
                g.dot(step, want), -1e-9,
                "方位 {}° 时指令 {} 在让距离变大".format(deg, move))

    def test_hysteresis_prevents_command_thrash(self):
        """90° 附近不能每帧翻转指令 —— 细则要求仅状态变化时发送，抖动白吃动作位。"""
        ctl = Controller(self.tune)
        me = _sprite(700, 400, angle=0.0, speed=5.0)
        # 先进入倒车（120°）
        target_back = (700 + 400 * math.cos(math.radians(120)),
                       400 + 400 * math.sin(math.radians(120)))
        self.assertEqual(ctl.steer_towards(me, target_back)[0], BACKWARD)
        # 回到 85°：在 80~100 的死区内，应保持倒车而不是立刻翻回前进
        target_mid = (700 + 400 * math.cos(math.radians(85)),
                      400 + 400 * math.sin(math.radians(85)))
        self.assertEqual(ctl.steer_towards(me, target_mid)[0], BACKWARD,
                         "死区内应保持上一状态")
        # 降到 60°：退出倒车
        target_fwd = (700 + 400 * math.cos(math.radians(60)),
                      400 + 400 * math.sin(math.radians(60)))
        self.assertEqual(ctl.steer_towards(me, target_fwd)[0], FORWARD)

    def test_reset_clears_reverse_state(self):
        """迟滞状态跨帧保留，所以必须能被 reset() 清掉，否则会污染下一局。"""
        ctl = Controller(self.tune)
        me = _sprite(700, 400, angle=0.0, speed=5.0)
        ctl.steer_towards(me, (300, 400))
        self.assertTrue(ctl._reversing)
        ctl.reset()
        self.assertFalse(ctl._reversing)


class TestR6FleeDirection(unittest.TestCase):
    """逃跑不能只会「朝正反方向跑」——那样会把自己逼进墙角。"""

    def setUp(self):
        self.tune = Tune()
        self.ctl = Controller(self.tune)

    def test_flee_moves_away_from_hazard(self):
        for deg in range(0, 360, 30):
            hazard = (700 + 200 * math.cos(math.radians(deg)),
                      400 + 200 * math.sin(math.radians(deg)))
            ctl = Controller(self.tune)
            me = _sprite(700, 400, angle=0.0, speed=5.0)
            move, _t, _r = ctl.evade_point(me, hazard)
            nose = (math.cos(me.angle), math.sin(me.angle))
            step = nose if move == FORWARD else (-nose[0], -nose[1])
            away = g.normalize(g.sub(me.position, hazard))
            self.assertGreaterEqual(
                g.dot(step, away), -1e-9,
                "危险在 {}° 时指令 {} 反而在靠近它".format(deg, move))

    def test_flee_blend_never_points_at_the_hazard(self):
        """掺入「往空旷处」的分量后，也绝不能把逃跑方向掰成朝着危险。"""
        me = _sprite(120, 120, angle=0.0, speed=5.0)   # 贴左上角
        hazard = (60, 60)                              # 危险在角落方向
        open_space = (720, 410)                        # 空旷处在反方向
        move, _t, _r = self.ctl.evade_point(me, hazard, open_space)
        nose = (math.cos(me.angle), math.sin(me.angle))
        step = nose if move == FORWARD else (-nose[0], -nose[1])
        away = g.normalize(g.sub(me.position, hazard))
        self.assertGreater(g.dot(step, away), -1e-9)


class TestR4ObstacleBrake(unittest.TestCase):
    """转不出去就先刹车；但只在真的转不出去时刹，否则白丢进攻时间。"""

    def setUp(self):
        self.tune = Tune()
        self.ctl = Controller(self.tune)

    def test_brakes_when_obstacle_is_dead_ahead_and_inside_turn_radius(self):
        # 转弯半径 = 速度/角速度 = 5/0.1 = 50px；石头在正前方 60px（净间隙 ~25px）
        me = _sprite(700, 400, angle=0.0, speed=5.0)
        move, _t, _r = self.ctl.avoid_obstacle(me, (760, 400), goal=(1100, 400))
        self.assertEqual(move, BACKWARD, "正前方且已在转弯半径内 → 必须先减速")

    def test_does_not_brake_when_obstacle_is_off_to_the_side(self):
        """擦着走的时候刹车是纯损失 —— 实测第一版有 49% 的追击报警帧被误伤。"""
        me = _sprite(700, 400, angle=0.0, speed=5.0)
        move, _t, _r = self.ctl.avoid_obstacle(me, (700, 460), goal=(1100, 400))
        self.assertEqual(move, FORWARD, "石头在侧面，打方向就能过，不该刹车")

    def test_does_not_brake_when_obstacle_is_far(self):
        me = _sprite(700, 400, angle=0.0, speed=5.0)
        move, _t, _r = self.ctl.avoid_obstacle(me, (1100, 400), goal=(1200, 400))
        self.assertEqual(move, FORWARD, "还远着，转向足够")

    def test_zero_speed_does_not_crash(self):
        me = _sprite(700, 400, angle=0.0, speed=0.0)
        move, _t, rate = self.ctl.avoid_obstacle(me, (700, 400), goal=(1100, 400))
        self.assertIn(move, (FORWARD, BACKWARD))
        self.assertGreater(rate, 0.0)


class TestR4SafeRallyPoint(unittest.TestCase):
    """巡航目标点不能落在障碍物的警戒圈里。"""

    def setUp(self):
        from firefly.worldmodel import WorldModel
        self.tune = Tune()
        self.world = WorldModel(tune=self.tune)
        # 一块正好压在地图中心的石头 —— 现场那个木墩就是这样
        stump = [(660.0, 360.0), (780.0, 360.0), (780.0, 470.0), (660.0, 470.0)]
        self.world.game_map = GameMap(width=1440.0, height=820.0,
                                      block_hulls=[stump], border_hulls=[])

    def test_map_center_may_be_unsafe(self):
        gap, hull = self.world.obstacle_clearance(self.world.map_center())
        self.assertIsNotNone(hull)
        self.assertLess(gap, 75.5, "本用例的前提：中心点确实在危险区内")

    def test_rally_point_is_clear_of_obstacles(self):
        point = self.world.rally_point()
        gap, hull = self.world.obstacle_clearance(point)
        self.assertTrue(hull is None or gap >= 75.5,
                        "集结点间隙只有 {:.1f}px，仍在警戒圈内".format(gap))

    def test_rally_point_stays_inside_the_map(self):
        point = self.world.rally_point()
        self.assertGreater(point[0], 0.0)
        self.assertLess(point[0], 1440.0)
        self.assertGreater(point[1], 0.0)
        self.assertLess(point[1], 820.0)

    def test_safe_point_near_is_idempotent_when_already_safe(self):
        safe = (200.0, 200.0)
        self.assertEqual(self.world.safe_point_near(safe, 90.0), safe)


class TestR5HeartPreposition(unittest.TestCase):
    """卡位：让「我方最先到达」的区域最大，而不是站在某个写死的点上。"""

    def setUp(self):
        from firefly.worldmodel import WorldModel
        from firefly.protocol import Frame
        self.tune = Tune()
        self.world = WorldModel(tune=self.tune)
        self.world.game_map = GameMap(width=1440.0, height=820.0,
                                      block_hulls=[], border_hulls=[])

    def _place(self, me_pos, rival_positions):
        from firefly.protocol import Frame
        sprites = [Sprite(id="me", position=me_pos, angle=0.0, speed=5.0,
                          velocity=(5.0, 0.0), width=70.0, height=70.0)]
        for i, p in enumerate(rival_positions):
            sprites.append(Sprite(id="r%d" % i, position=p, angle=0.0, speed=5.0,
                                  velocity=(5.0, 0.0), width=70.0, height=70.0))
        self.world.frame = Frame(command_type="refreshData", timestamp_ms=0.0,
                                 sprites=sprites)
        self.world.identify_self("me")
        for s in sprites:
            self.world._max_speed[s.id] = 5.0
        return sprites[0]

    def test_point_is_inside_the_spawn_box(self):
        me = self._place((100.0, 100.0), [(1300.0, 700.0)])
        x0, y0, x1, y1 = RULE_HEART_SPAWN_BOX
        spot = self.world.heart_preposition_point(me, grid=100.0)
        self.assertGreaterEqual(spot[0], x0)
        self.assertLessEqual(spot[0], x1)
        self.assertGreaterEqual(spot[1], y0)
        self.assertLessEqual(spot[1], y1)

    def test_moves_away_from_a_rival_cluster(self):
        """⭐ 用户提的那个场景：三个对手挤在左上角缠斗 → 我们该站到他们外侧。

        判据不是「站在某个具体坐标」，而是**我方选点比对手那一坨更靠生成区中心**，
        这样生成区里绝大多数位置都由我们先到。
        """
        cluster = [(430.0, 210.0), (470.0, 250.0), (450.0, 200.0)]
        me = self._place((700.0, 400.0), cluster)
        spot = self.world.heart_preposition_point(me, grid=100.0)
        cx = sum(p[0] for p in cluster) / 3.0
        cy = sum(p[1] for p in cluster) / 3.0
        x0, y0, x1, y1 = RULE_HEART_SPAWN_BOX
        box_center = ((x0 + x1) / 2.0, (y0 + y1) / 2.0)
        self.assertLess(g.distance(spot, box_center), g.distance((cx, cy), box_center),
                        "选点应该比对手扎堆处更能覆盖生成区")

    def test_avoids_standing_on_an_obstacle(self):
        x0, y0, x1, y1 = RULE_HEART_SPAWN_BOX
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        blob = [(cx - 60, cy - 60), (cx + 60, cy - 60),
                (cx + 60, cy + 60), (cx - 60, cy + 60)]
        self.world.game_map = GameMap(width=1440.0, height=820.0,
                                      block_hulls=[blob], border_hulls=[])
        me = self._place((200.0, 200.0), [(1300.0, 700.0)])
        spot = self.world.heart_preposition_point(me, grid=100.0)
        gap, hull = self.world.obstacle_clearance(spot)
        self.assertTrue(hull is None or gap >= 90.0,
                        "卡位点不能落在石头上（那是扣分区）")

    def test_survives_having_no_rivals(self):
        me = self._place((200.0, 200.0), [])
        spot = self.world.heart_preposition_point(me, grid=100.0)
        self.assertEqual(len(spot), 2)


if __name__ == "__main__":
    unittest.main()


class TestR7EngageWeakestNotStrongest(unittest.TestCase):
    """「该不该避战」要问「打得赢谁」，不是「压不压得过最强的」。"""

    def setUp(self):
        from firefly.control import Controller
        from firefly.protocol import Frame
        from firefly.strategy import Strategy
        from firefly.worldmodel import WorldModel
        self.tune = Tune()
        self.world = WorldModel(tune=self.tune)
        self.world.game_map = GameMap(width=1440.0, height=820.0,
                                      block_hulls=[], border_hulls=[])
        self.strategy = Strategy(self.tune, self.world, Controller(self.tune))

    def _setup(self, my_energy, rival_energies, positions=None):
        from firefly.protocol import Frame
        sprites = [Sprite(id="me", position=(700.0, 400.0), angle=0.0, speed=5.0,
                          velocity=(5.0, 0.0), width=70.0, height=70.0,
                          score=10.0, energy=my_energy)]
        for i, e in enumerate(rival_energies):
            pos = positions[i] if positions else (800.0 + 60 * i, 400.0)
            sprites.append(Sprite(id="r%d" % i, position=pos,
                                  angle=0.0, speed=5.0, velocity=(5.0, 0.0),
                                  width=70.0, height=70.0, score=10.0, energy=e))
        self.world.frame = Frame(command_type="refreshData", timestamp_ms=0.0,
                                 sprites=sprites)
        self.world.identify_self("me")
        for s in sprites:
            self.world._max_speed[s.id] = 5.0
            if s.id != "me":
                self.world._opponent(s)          # 建模，供 _note 使用
        return sprites[0]

    def _note(self, rival_id, value):
        """记录一次「观测到该对手出价 value」，用于抬高它的 threat_of。"""
        sprite = self.world.sprite_by_id(rival_id)
        self.world._opponent(sprite).note_attack(value)

    def test_engages_when_one_rival_is_weak_even_if_another_is_strong(self):
        """⭐ 核心回归：一个强敌 + 两个软柿子时，绝不能整窗避战。

        真机上这条链把「有产出的帧」压到 35%：全场最高威胁 → 我方能量不够 →
        starved → worth_engaging=False → conserve 整个窗口，而软柿子一直没人打。

        注意强敌要放**远处**（>260px）。``threat_for_contact`` 会把「比目标更近的
        强敌」也算进威胁，那是 R3 刻意加的防偷袭保护：强敌就贴在旁边时，去打软柿子
        确实有风险，此时避战是对的。这条用例针对的是强敌在场地另一头的情形。
        """
        me = self._setup(my_energy=200.0, rival_energies=[1000.0, 30.0, 20.0],
                         positions=[(1350.0, 750.0), (790.0, 400.0), (700.0, 500.0)])
        # 让强敌的观测威胁真的很高（_opponent 收的是 Sprite，不是 id）
        self._note("r0", 900.0)
        self.assertTrue(self.strategy._can_beat_anyone(me),
                        "还有能量 20/30 的软柿子，必须认为可以开打")

    def test_conserves_only_when_nobody_is_beatable(self):
        me = self._setup(my_energy=5.0, rival_energies=[1000.0, 900.0, 800.0])
        for rid in ("r0", "r1", "r2"):
            self._note(rid, 700.0)
        self.assertFalse(self.strategy._can_beat_anyone(me),
                         "能量 5 面对三个满能量高出价对手，才该避战")

    def test_cooldown_does_not_make_us_flee(self):
        """冷却是暂时的。所有对手都在冷却时该继续巡航，而不是判成「打不赢」。"""
        me = self._setup(my_energy=1000.0, rival_energies=[50.0])
        self.world.last_self_collision_at = self.world.elapsed
        for rid in ("r0",):
            self.world.opponents[rid].last_collision_at = self.world.elapsed
        self.assertTrue(self.strategy._can_beat_anyone(me),
                        "能量 1000 打能量 50，冷却过去就能赢，不该判成打不赢")


class TestR8UnclaimedHeart(unittest.TestCase):
    """ETA 竞速只在刷新那一瞬间有意义；没人捡的心是免费道具。"""

    def setUp(self):
        from firefly.control import Controller
        from firefly.strategy import Strategy
        from firefly.worldmodel import WorldModel
        self.tune = Tune()
        self.world = WorldModel(tune=self.tune)
        self.world.game_map = GameMap(width=1440.0, height=820.0,
                                      block_hulls=[], border_hulls=[])
        self.strategy = Strategy(self.tune, self.world, Controller(self.tune))

    def _setup(self):
        from firefly.protocol import Frame
        # 我远、对手近 —— 纯 ETA 竞速一定判「抢不到」
        sprites = [
            Sprite(id="me", position=(200.0, 200.0), angle=0.0, speed=5.0,
                   velocity=(5.0, 0.0), width=70.0, height=70.0,
                   score=7.0, energy=1000.0),
            Sprite(id="r0", position=(900.0, 600.0), angle=0.0, speed=5.0,
                   velocity=(5.0, 0.0), width=70.0, height=70.0,
                   score=7.0, energy=1000.0),
        ]
        self.world.frame = Frame(command_type="refreshData", timestamp_ms=0.0,
                                 sprites=sprites, gold_carrot=(958.0, 608.0))
        self.world.identify_self("me")
        for s in sprites:
            self.world._max_speed[s.id] = 5.0
        return sprites[0], (958.0, 608.0)

    def test_yields_right_after_spawn(self):
        """刚刷新、对手更近 → 让掉是对的（抢不到还赖着会被当免费果实）。"""
        me, carrot = self._setup()
        self.world.elapsed = 30.0
        self.world.carrot_since = 30.0
        intent = self.strategy._contest_heart(me, carrot)
        self.assertEqual(intent.kind, "yield_heart")

    def test_takes_it_once_clearly_nobody_came(self):
        """⭐ 核心回归：放了很久还在原地 → 对手没在抢 → 去拿。

        真机 b068：90s 刷出的心一直放到 174s 结束都没人捡，而我们连续 84s
        执行 yield_heart，果实从 7 掉到 2。
        """
        me, carrot = self._setup()
        self.world.elapsed = 60.0
        self.world.carrot_since = 30.0      # 已经放了 30s
        intent = self.strategy._contest_heart(me, carrot)
        self.assertEqual(intent.kind, "seek_heart")
        self.assertEqual(intent.target, carrot)

    def test_unclaimed_timer_resets_when_carrot_disappears(self):
        from firefly.protocol import Frame
        me, carrot = self._setup()
        self.world.elapsed = 60.0
        self.world.carrot_since = 30.0
        self.assertGreater(self.world.seconds_carrot_unclaimed, 0.0)
        self.world.on_frame(Frame(command_type="refreshData", timestamp_ms=0.0,
                                  sprites=[me], gold_carrot=None), elapsed=61.0)
        self.assertIsNone(self.world.carrot_since)
        self.assertEqual(self.world.seconds_carrot_unclaimed, 0.0)


class TestR9TangentialFlee(unittest.TestCase):
    """狮子与人：切向逃跑优于径向后退 —— 但位移方向要单独判。"""

    def setUp(self):
        self.tune = Tune()

    def test_never_closes_distance_from_any_angle(self):
        """不变量：任何相对方位下，这一帧位移在「远离」方向的投影都不为负。"""
        for deg in range(0, 360, 10):
            for my_angle_deg in (0, 45, 90, 180, 270):
                ctl = Controller(self.tune)
                me = _sprite(700, 400, angle=math.radians(my_angle_deg), speed=5.0)
                hazard = (700 + 200 * math.cos(math.radians(deg)),
                          400 + 200 * math.sin(math.radians(deg)))
                move, _t, _r = ctl.evade_point(me, hazard, (720.0, 410.0))
                nose = (math.cos(me.angle), math.sin(me.angle))
                step = nose if move == FORWARD else (-nose[0], -nose[1])
                away = g.normalize(g.sub(me.position, hazard))
                self.assertGreaterEqual(
                    g.dot(step, away), -1e-9,
                    "追兵方位 {}°、车头 {}° 时指令 {} 在靠近追兵".format(
                        deg, my_angle_deg, move))

    def test_reverses_when_pursuer_is_ahead(self):
        """追兵在正前方时必须倒车 —— 掉头 180° 的那 1.6s 是往对方怀里送。"""
        ctl = Controller(self.tune)
        me = _sprite(700, 400, angle=0.0, speed=5.0)
        move, _t, _r = ctl.evade_point(me, (900.0, 400.0), (720.0, 410.0))
        self.assertEqual(move, BACKWARD)

    def test_steers_tangentially_not_straight_back(self):
        """转向目标应偏向切向，而不是纯 180° 反方向。

        判据：给出的转向指令不是 STRAIGHT —— 纯径向逃跑在追兵正前方时会要求
        原地掉头，切向则总有一个可转的方向。
        """
        from firefly.control import STRAIGHT
        ctl = Controller(self.tune)
        me = _sprite(700, 400, angle=0.0, speed=5.0)
        _m, turn, _r = ctl.evade_point(me, (900.0, 400.0), (720.0, 410.0))
        self.assertNotEqual(turn, STRAIGHT, "应该往切向掰方向盘")
