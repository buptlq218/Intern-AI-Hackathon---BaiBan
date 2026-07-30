"""几何工具用例。这些是避障和碰撞预判的地基，错了会表现为「莫名其妙撞墙」。"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firefly import geometry as g


SQUARE = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]


class TestAngles(unittest.TestCase):
    def test_normalize_angle_range(self):
        for raw in (0.0, 3.0, -3.0, 7.0, -7.0, math.pi, -math.pi, 100.0):
            out = g.normalize_angle(raw)
            self.assertTrue(-math.pi < out <= math.pi + 1e-9,
                            "{} -> {}".format(raw, out))

    def test_normalize_angle_wraps(self):
        self.assertAlmostEqual(g.normalize_angle(2 * math.pi + 0.5), 0.5)
        self.assertAlmostEqual(g.normalize_angle(-2 * math.pi - 0.5), -0.5)

    def test_bearing_axes(self):
        self.assertAlmostEqual(g.bearing((0, 0), (1, 0)), 0.0)
        self.assertAlmostEqual(g.bearing((0, 0), (0, 1)), math.pi / 2)

    def test_heading_error_takes_short_way(self):
        """朝向 +3.0 rad、目标在 -3.0 rad 方向，应该走短路（跨越 ±pi）。"""
        err = g.heading_error(3.0, (0, 0), (math.cos(-3.0), math.sin(-3.0)))
        self.assertLess(abs(err), math.pi / 2,
                        "必须走短路，否则会绕一大圈")

    def test_heading_error_zero_when_aligned(self):
        err = g.heading_error(0.0, (0, 0), (5, 0))
        self.assertAlmostEqual(err, 0.0)


class TestSAT(unittest.TestCase):
    def test_overlapping_squares(self):
        other = [(5.0, 5.0), (15.0, 5.0), (15.0, 15.0), (5.0, 15.0)]
        self.assertTrue(g.polygons_intersect(SQUARE, other))
        self.assertIsNotNone(g.sat_overlap(SQUARE, other))

    def test_separated_squares(self):
        other = [(20.0, 20.0), (30.0, 20.0), (30.0, 30.0), (20.0, 30.0)]
        self.assertFalse(g.polygons_intersect(SQUARE, other))
        self.assertIsNone(g.sat_overlap(SQUARE, other))

    def test_touching_counts_as_intersecting(self):
        other = [(10.0, 0.0), (20.0, 0.0), (20.0, 10.0), (10.0, 10.0)]
        self.assertTrue(g.polygons_intersect(SQUARE, other))

    def test_rotated_obb_detected(self):
        """旋转 45 度的 OBB 与方块相交 —— 用轴对齐盒子会漏判。"""
        rot = g.obb_corners((12.0, 5.0), 6.0, 6.0, math.pi / 4)
        self.assertTrue(g.polygons_intersect(SQUARE, rot))

    def test_overlap_depth_is_non_negative(self):
        other = [(9.0, 0.0), (19.0, 0.0), (19.0, 10.0), (9.0, 10.0)]
        depth = g.sat_overlap(SQUARE, other)
        self.assertIsNotNone(depth)
        self.assertGreaterEqual(depth, 0.0)


class TestOBB(unittest.TestCase):
    def test_four_corners(self):
        self.assertEqual(len(g.obb_corners((0, 0), 10, 4, 0.0)), 4)

    def test_unrotated_corners_match_expectation(self):
        corners = g.obb_corners((0.0, 0.0), 10.0, 4.0, 0.0)
        xs = sorted(round(c[0], 6) for c in corners)
        ys = sorted(round(c[1], 6) for c in corners)
        self.assertEqual(xs, [-5.0, -5.0, 5.0, 5.0])
        self.assertEqual(ys, [-2.0, -2.0, 2.0, 2.0])

    def test_rotation_preserves_bounding_radius(self):
        r = g.bounding_radius(10.0, 4.0)
        for angle in (0.0, 0.7, 1.9, 3.3):
            for corner in g.obb_corners((0.0, 0.0), 10.0, 4.0, angle):
                self.assertAlmostEqual(g.length(corner), r, places=6)


class TestDistances(unittest.TestCase):
    def test_point_inside_polygon_distance_zero(self):
        self.assertEqual(g.point_polygon_distance((5.0, 5.0), SQUARE), 0.0)

    def test_point_outside_polygon_distance(self):
        self.assertAlmostEqual(g.point_polygon_distance((15.0, 5.0), SQUARE), 5.0)

    def test_point_in_polygon(self):
        self.assertTrue(g.point_in_polygon((5.0, 5.0), SQUARE))
        self.assertFalse(g.point_in_polygon((15.0, 5.0), SQUARE))

    def test_point_segment_distance_degenerate(self):
        self.assertAlmostEqual(
            g.point_segment_distance((3.0, 4.0), (0.0, 0.0), (0.0, 0.0)), 5.0
        )


class TestPrediction(unittest.TestCase):
    def test_extrapolate(self):
        self.assertEqual(g.extrapolate((0.0, 0.0), (2.0, 3.0), 2.0), (4.0, 6.0))

    def test_closest_approach_head_on(self):
        """两点对撞，最近距离应约为 0。"""
        t, dist = g.closest_approach((0, 0), (5, 0), (100, 0), (-5, 0), horizon=30)
        self.assertLess(dist, 1e-6)
        self.assertAlmostEqual(t, 10.0, places=3)

    def test_closest_approach_parallel(self):
        """同向同速，永远保持初始距离。"""
        t, dist = g.closest_approach((0, 0), (5, 0), (0, 50), (5, 0), horizon=10)
        self.assertAlmostEqual(dist, 50.0)

    def test_closest_approach_clamped_to_horizon(self):
        t, _ = g.closest_approach((0, 0), (1, 0), (1000, 0), (-1, 0), horizon=5)
        self.assertLessEqual(t, 5.0)

    def test_closest_approach_never_negative_time(self):
        """已经错身而过时，t 应夹到 0 而不是给出过去的时刻。"""
        t, _ = g.closest_approach((0, 0), (5, 0), (-100, 0), (-5, 0), horizon=10)
        self.assertGreaterEqual(t, 0.0)


class TestRebound(unittest.TestCase):
    def test_matches_documented_formula(self):
        """细则 §6: vA' = 0.02(pA-pB) - 0.3vA + 0.7vB"""
        pa, pb = (100.0, 0.0), (0.0, 0.0)
        va, vb = (-5.0, 0.0), (5.0, 0.0)
        out = g.rebound_velocity(pa, va, pb, vb, 0.02, -0.3, 0.7)
        expected_x = 0.02 * 100.0 + (-0.3) * (-5.0) + 0.7 * 5.0
        self.assertAlmostEqual(out[0], expected_x)

    def test_stationary_opponent_compensated(self):
        """一方速度为零时引擎会用对方运动方向的反向量补偿，不应得到 0 结果。"""
        out = g.rebound_velocity((10.0, 0.0), (5.0, 0.0), (0.0, 0.0), (0.0, 0.0),
                                 0.02, -0.3, 0.7)
        self.assertNotEqual(out, (0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
