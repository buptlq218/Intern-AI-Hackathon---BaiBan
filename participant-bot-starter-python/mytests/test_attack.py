"""攻击力经济学的用例。

每个用例对应 firefly/attack.py 文档里的一条结论 —— 现场改参数时这些必须仍然通过，
否则说明改动破坏了策略的核心假设。
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firefly.attack import affordable_collisions, decide_attack
from firefly.constants import Tune


class TestAttackEconomics(unittest.TestCase):
    def setUp(self):
        self.tune = Tune()

    # -- 出价应压过威胁，但不应远超 ------------------------------------

    def test_bid_exceeds_threat(self):
        d = decide_attack(self.tune, energy=1000, threat=200, seconds_to_reset=20)
        self.assertGreater(d.value, 200, "出价必须压过对手，否则白扔能量还倒扣分")
        self.assertTrue(d.can_win)
        self.assertEqual(d.mode, "bid")

    def test_bid_is_not_wasteful(self):
        """赢多少不影响收益，所以不该出远超必要的价。"""
        d = decide_attack(self.tune, energy=1000, threat=200, seconds_to_reset=20)
        self.assertLess(d.value, 400, "高出太多是纯浪费，会减少本窗口可赢次数")

    def test_bid_scales_with_threat(self):
        low = decide_attack(self.tune, energy=1000, threat=100, seconds_to_reset=20)
        high = decide_attack(self.tune, energy=1000, threat=500, seconds_to_reset=20)
        self.assertGreater(high.value, low.value)

    def test_respects_min_attack(self):
        d = decide_attack(self.tune, energy=1000, threat=0, seconds_to_reset=20)
        self.assertGreaterEqual(d.value, self.tune.min_attack)

    # -- 能量不足 -------------------------------------------------------

    def test_starved_reports_cannot_win(self):
        """能量不够压过对手时必须明确告知，让策略层去避战而不是继续送分。"""
        d = decide_attack(self.tune, energy=30, threat=500, seconds_to_reset=20)
        self.assertFalse(d.can_win)
        self.assertEqual(d.mode, "starved")

    def test_starved_still_bids_everything(self):
        """赢不了也要全押：万一威胁估计偏高，全押是唯一的翻盘可能。"""
        d = decide_attack(self.tune, energy=30, threat=500, seconds_to_reset=20)
        self.assertAlmostEqual(d.value, 30)

    def test_never_bids_above_energy(self):
        """actualAttack = min(set, energy)，出价超过能量没有意义。"""
        for energy in (0, 10, 100, 999, 1000):
            d = decide_attack(self.tune, energy=energy, threat=300, seconds_to_reset=15)
            self.assertLessEqual(d.value, max(energy, self.tune.min_attack) + 1e-6)

    def test_never_negative(self):
        d = decide_attack(self.tune, energy=0, threat=100, seconds_to_reset=1)
        self.assertGreaterEqual(d.value, 0.0)

    # -- 窗口末尾梭哈 ---------------------------------------------------

    def test_spenddown_only_when_committing(self):
        """能量马上要被重置清零，且已决定要撞 → 把花不掉的花掉。"""
        committed = decide_attack(
            self.tune, energy=800, threat=100, seconds_to_reset=2,
            committing_to_contact=True,
        )
        self.assertEqual(committed.mode, "spenddown")
        normal = decide_attack(self.tune, energy=800, threat=100, seconds_to_reset=20)
        self.assertGreater(committed.value, normal.value,
                           "窗口末尾应该比平时出得更多")

    def test_spenddown_keeps_reserve_for_another_collision(self):
        """回归：不能梭哈到 0，否则本窗口剩下的碰撞全是白输。

        沙盒实测过这个坑：25.4s 梭哈 1000 赢一次，能量归零后
        26.9/28.4/29.9s 以 0 攻击连输三次，净 -2。
        """
        d = decide_attack(
            self.tune, energy=800, threat=100, seconds_to_reset=2.0,
            committing_to_contact=True,
        )
        self.assertLess(d.value, 800, "距重置 2s 还能再打一次，必须留出下一次的钱")
        leftover = 800 - d.value
        self.assertGreaterEqual(leftover, 100,
                                "保留额至少要够压过对手一次")

    def test_spenddown_goes_all_in_at_the_very_end(self):
        """真的来不及再打一次了，才该全花光。"""
        d = decide_attack(
            self.tune, energy=800, threat=100, seconds_to_reset=0.4,
            committing_to_contact=True,
        )
        self.assertEqual(d.mode, "spenddown")
        self.assertAlmostEqual(d.value, 800,
                               msg="剩 0.4s 放不下另一次结算，留钱就是浪费")

    def test_no_spenddown_when_not_committing(self):
        """没打算撞就梭哈，会被一次意外接触白白清空整窗预算。"""
        passive = decide_attack(
            self.tune, energy=800, threat=100, seconds_to_reset=2,
            committing_to_contact=False,
        )
        self.assertNotEqual(passive.mode, "spenddown")
        self.assertLess(passive.value, 800)

    def test_no_spenddown_early_in_window(self):
        d = decide_attack(
            self.tune, energy=800, threat=100, seconds_to_reset=25,
            committing_to_contact=True,
        )
        self.assertEqual(d.mode, "bid")

    # -- 森林之心 -------------------------------------------------------

    def test_invincible_does_not_waste_energy(self):
        """持心碰撞不耗能且必胜，出价无意义，不该梭哈。"""
        d = decide_attack(
            self.tune, energy=1000, threat=900, seconds_to_reset=3,
            invincible=True, committing_to_contact=True,
        )
        self.assertEqual(d.mode, "free")
        self.assertTrue(d.can_win)
        self.assertLess(d.value, 1000)

    # -- 辅助 -----------------------------------------------------------

    def test_affordable_collisions(self):
        self.assertEqual(affordable_collisions(1000, 250), 4)
        self.assertEqual(affordable_collisions(1000, 1000), 1)
        self.assertEqual(affordable_collisions(100, 250), 0)
        self.assertEqual(affordable_collisions(100, 0), 0)

    def test_bidding_beats_spreading(self):
        """核心结论的回归测试：一直出 T+e 比把预算摊薄到每次更优。

        威胁 300、能量 1000、窗口内预计 6 次碰撞：
          摊薄 → 每次 166，全部输，净 -6
          出价 → 每次 ~356，赢 2 次输 4 次，净 -2
        """
        threat = 300.0
        energy = 1000.0
        collisions = 6

        d = decide_attack(self.tune, energy=energy, threat=threat, seconds_to_reset=25)
        wins_bidding = min(collisions, affordable_collisions(energy, d.value))
        net_bidding = wins_bidding - (collisions - wins_bidding)

        spread = energy / collisions
        wins_spread = collisions if spread > threat else 0
        net_spread = wins_spread - (collisions - wins_spread)

        self.assertGreater(net_bidding, net_spread)


if __name__ == "__main__":
    unittest.main()
