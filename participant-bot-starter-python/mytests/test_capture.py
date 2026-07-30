"""tools/capture.py 的回归用例 —— 保证「裁判」读的是真实产物格式。

这些用例钉住的是一件事：**离线复盘的判定必须和线上
``worldmodel._diff_sprites`` 一致**。如果哪天两边漂了，这里先红。

顺带钉住 ``analyze.py`` 端到端能吃采集目录 —— 现场如果它静默输出「碰撞 0 次」，
会直接把 Loop 引向错误的参数。
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "tools"))

import analyze                      # noqa: E402
import capture                      # noqa: E402

MY_ID = "1819"


def rabbit(rid, score, energy, invincible=False, x=100.0, y=100.0):
    return {
        "id": rid,
        "score": score,
        "energy": energy,
        "invincible": invincible,
        "active": True,
        "position": {"x": x, "y": y},
        "velocity": {"x": 1.0, "y": 0.0},
        "speed": 1.0,
    }


class CaptureDir:
    """按 bot.py 的真实 schema 造一个采集目录。

    schema 来源：``bot.py`` 的 ``capture.append("frames.jsonl", …)``（第 297/510 行）
    与 ``write_json(… "metadata.json")``（第 279 行）。
    """

    def __init__(self, bot_id=MY_ID, settlement=None):
        self.root = tempfile.mkdtemp(prefix="capture-test-")
        self.frames = []
        self.t = 0
        self._write_json("metadata.json", {
            "matchCode": "forest-test",
            "matchId": "m1",
            "botId": bot_id,
            "botName": "白板",
            "matchType": "PRACTICE",
            "strategyHash": "deadbeefcafe1234",
        })
        if settlement is not None:
            self._write_json("settlement.json", settlement)
        self.frames.append({
            "receivedAt": 1_000,
            "sourceTimestamp": 0,
            "commandType": "startGame",
            "data": {"map": {"width": 1440, "height": 820}, "rabbits": []},
        })

    def _write_json(self, name, value):
        with open(os.path.join(self.root, name), "w", encoding="utf-8") as fh:
            json.dump(value, fh)

    def frame(self, rabbits, gold_carrot=None, step_ms=100):
        self.t += step_ms
        self.frames.append({
            "receivedAt": 1_000 + self.t,
            "sourceTimestamp": self.t,
            "commandType": "refreshData",
            "data": {"rabbits": rabbits, "goldCarrot": gold_carrot or {}},
        })
        return self

    def finish(self):
        with open(os.path.join(self.root, "frames.jsonl"), "w", encoding="utf-8") as fh:
            for record in self.frames:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        return self.root

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)


class TestCaptureRecognition(unittest.TestCase):

    def test_is_capture_dir_requires_frames_jsonl(self):
        empty = tempfile.mkdtemp(prefix="capture-empty-")
        try:
            self.assertFalse(capture.is_capture_dir(empty))
        finally:
            shutil.rmtree(empty, ignore_errors=True)

        cap = CaptureDir()
        try:
            root = cap.frame([rabbit(MY_ID, 10, 1000)]).finish()
            self.assertTrue(capture.is_capture_dir(root))
        finally:
            cap.cleanup()

    def test_find_captures_walks_runtime_layout(self):
        """现场敲的是 `analyze.py runtime/`，要能找到 runtime/matches/<code>/。"""
        root = tempfile.mkdtemp(prefix="runtime-")
        try:
            nested = os.path.join(root, "matches", "forest-1")
            os.makedirs(nested)
            with open(os.path.join(nested, "frames.jsonl"), "w") as fh:
                fh.write("{}\n")
            self.assertEqual(capture.find_captures(root), [nested])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_resolve_self_id_accepts_ai_prefix(self):
        self.assertEqual(capture.resolve_self_id(["1819", "7"], "1819"), "1819")
        self.assertEqual(capture.resolve_self_id(["ai:1819", "7"], "1819"), "ai:1819")
        self.assertIsNone(capture.resolve_self_id(["7", "8"], "1819"))
        self.assertIsNone(capture.resolve_self_id(["7"], None))


class TestEventReconstruction(unittest.TestCase):
    """碰撞重建 —— 判定必须镜像 worldmodel._diff_sprites。"""

    def setUp(self):
        self.cap = CaptureDir()

    def tearDown(self):
        self.cap.cleanup()

    def _events(self, kind=None, mine_only=True):
        records = capture.load_capture(self.cap.finish())
        out = [r for r in records if r.get("type") == "collision"]
        if mine_only:
            out = [r for r in out if r.get("is_self")]
        if kind is not None:
            out = [r for r in out if r.get("kind") == kind]
        return out

    def test_win_is_sprite_collision_with_energy_spent(self):
        """赢：耗能 + 果实 +1。能量跌幅就是我方的 actualAttack。"""
        self.cap.frame([rabbit(MY_ID, 10, 1000)])
        self.cap.frame([rabbit(MY_ID, 11, 860)])
        events = self._events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["kind"], "sprite")
        self.assertEqual(events[0]["score_delta"], 1)
        self.assertAlmostEqual(events[0]["energy_spent"], 140.0)

    def test_tie_is_sprite_collision_with_zero_delta(self):
        """平局：耗能但果实不变。这类必须被记成 sprite，否则「平局不丢果实」
        这条策略在复盘里看不见。"""
        self.cap.frame([rabbit(MY_ID, 10, 1000)])
        self.cap.frame([rabbit(MY_ID, 10, 800)])
        events = self._events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["kind"], "sprite")
        self.assertEqual(events[0]["score_delta"], 0)
        self.assertAlmostEqual(events[0]["energy_spent"], 200.0)

    def test_obstacle_is_minus_one_without_energy(self):
        """撞障碍：-1 果实、不耗能。"""
        self.cap.frame([rabbit(MY_ID, 10, 500)])
        self.cap.frame([rabbit(MY_ID, 9, 500)])
        events = self._events()
        self.assertEqual([e["kind"] for e in events], ["obstacle"])
        self.assertEqual(events[0]["score_delta"], -1)

    def test_idle_penalty_is_minus_three_and_not_obstacle(self):
        """E2 的自动化判据：-3 且不耗能 = 空转惩罚，绝不能混进「撞障碍」。"""
        self.cap.frame([rabbit(MY_ID, 10, 500)])
        self.cap.frame([rabbit(MY_ID, 7, 500)])
        events = self._events()
        self.assertEqual([e["kind"] for e in events], ["idle_penalty"])
        self.assertEqual(events[0]["score_delta"], -3)
        self.assertEqual(self._events(kind="obstacle"), [])

    def test_energy_reset_is_not_a_collision(self):
        """能量上涨是 30s 周期重置，不是碰撞。误判会污染对手模型。"""
        self.cap.frame([rabbit(MY_ID, 10, 120)])
        self.cap.frame([rabbit(MY_ID, 10, 1000)])
        self.assertEqual(self._events(), [])
        records = capture.load_capture(self.cap.root)
        end = [r for r in records if r.get("type") == "match_end"][0]
        self.assertEqual(len(end["energy_resets"]), 1)

    def test_idle_penalty_survives_an_energy_reset_on_the_same_frame(self):
        """能量重置和空转惩罚都是 30s 量级，撞在同一帧是常态。

        重置只盖掉 energy 信号，score 仍然可靠 —— 所以 -3 必须还能认出来。
        这个洞会恰好在最需要 E2 结论的时刻让它消失，所以单独钉一条。
        """
        self.cap.frame([rabbit(MY_ID, 10, 120)])
        self.cap.frame([rabbit(MY_ID, 7, 1000)])      # 同帧：重置 + 空转 -3
        events = self._events()
        self.assertEqual([e["kind"] for e in events], ["idle_penalty"])
        self.assertTrue(events[0]["energy_masked"])

    def test_minus_one_on_reset_frame_is_not_claimed_as_obstacle(self):
        """-1 撞在重置帧上时，分不清是撞障碍还是输掉一局 —— 不许假装是障碍。"""
        self.cap.frame([rabbit(MY_ID, 10, 300)])
        self.cap.frame([rabbit(MY_ID, 9, 1000)])
        events = self._events()
        self.assertEqual([e["kind"] for e in events], ["unknown"])
        self.assertEqual(self._events(kind="obstacle"), [])

    def test_energy_resets_are_deduplicated_per_timestamp(self):
        """一次重置会被 4 个精灵各记一遍，报表里应该只出现一次。"""
        self.cap.frame([rabbit(MY_ID, 10, 100), rabbit("7", 10, 100),
                        rabbit("8", 10, 100), rabbit("9", 10, 100)])
        self.cap.frame([rabbit(MY_ID, 10, 1000), rabbit("7", 10, 1000),
                        rabbit("8", 10, 1000), rabbit("9", 10, 1000)])
        records = capture.load_capture(self.cap.finish())
        end = [r for r in records if r.get("type") == "match_end"][0]
        self.assertEqual(len(end["energy_resets"]), 1)

    def test_invincible_score_drop_is_not_blamed_on_obstacle(self):
        """持森林之心时撞障碍不扣果实，所以此时的掉分不能归因成障碍。"""
        self.cap.frame([rabbit(MY_ID, 10, 500, invincible=True)])
        self.cap.frame([rabbit(MY_ID, 9, 500, invincible=True)])
        self.assertEqual([e["kind"] for e in self._events()], ["unknown"])

    def test_rival_spend_is_extracted(self):
        """E5：对手能量跌幅 = 他这次的实际出价。这是最大的信息优势。"""
        self.cap.frame([rabbit(MY_ID, 10, 1000), rabbit("7", 10, 1000)])
        self.cap.frame([rabbit(MY_ID, 9, 900), rabbit("7", 11, 500)])
        rivals = [e for e in self._events(mine_only=False) if not e["is_self"]]
        self.assertEqual(len(rivals), 1)
        self.assertEqual(rivals[0]["sprite"], "7")
        self.assertAlmostEqual(rivals[0]["energy_spent"], 500.0)

    def test_no_event_when_nothing_changes(self):
        self.cap.frame([rabbit(MY_ID, 10, 1000)])
        self.cap.frame([rabbit(MY_ID, 10, 1000)])
        self.cap.frame([rabbit(MY_ID, 10, 1000)])
        self.assertEqual(self._events(), [])

    def test_float_noise_below_epsilon_is_ignored(self):
        """浮点噪声不能被当成碰撞（阈值复用 worldmodel 的常量）。"""
        self.cap.frame([rabbit(MY_ID, 10, 1000.0)])
        self.cap.frame([rabbit(MY_ID, 10, 999.6)])
        self.assertEqual(self._events(), [])


class TestClockAndMeta(unittest.TestCase):

    def tearDown(self):
        if hasattr(self, "cap"):
            self.cap.cleanup()

    def test_elapsed_uses_source_timestamp_when_monotonic(self):
        self.cap = CaptureDir()
        self.cap.frame([rabbit(MY_ID, 10, 1000)], step_ms=1000)
        self.cap.frame([rabbit(MY_ID, 9, 1000)], step_ms=1000)
        records = capture.load_capture(self.cap.finish())
        start = [r for r in records if r["type"] == "match_start"][0]
        self.assertEqual(start["clock"], "sourceTimestamp")
        event = [r for r in records if r["type"] == "collision"][0]
        self.assertAlmostEqual(event["at_seconds"], 1.0)

    def test_falls_back_to_received_at_when_source_missing(self):
        """sourceTimestamp 缺失时整体回落，而不是逐帧混用两种时钟。"""
        self.cap = CaptureDir()
        self.cap.frame([rabbit(MY_ID, 10, 1000)])
        self.cap.frame([rabbit(MY_ID, 9, 1000)])
        for record in self.cap.frames:
            record.pop("sourceTimestamp", None)
        records = capture.load_capture(self.cap.finish())
        start = [r for r in records if r["type"] == "match_start"][0]
        self.assertEqual(start["clock"], "receivedAt")

    def test_rank_falls_back_to_frame_when_settlement_absent(self):
        self.cap = CaptureDir()
        self.cap.frame([rabbit(MY_ID, 9, 500), rabbit("7", 12, 500),
                        rabbit("8", 3, 500)])
        records = capture.load_capture(self.cap.finish())
        result = [r for r in records if r["type"] == "result"][0]
        self.assertEqual(result["rank"], 2)          # 12 > 9 > 3
        self.assertIn("推算", result["rank_source"])

    def test_rank_prefers_settlement(self):
        self.cap = CaptureDir(settlement={
            "rankings": [{"botId": "7", "rank": 1}, {"botId": MY_ID, "rank": 2}],
            "advancementStatus": "ADVANCED",
        })
        self.cap.frame([rabbit(MY_ID, 9, 500), rabbit("7", 12, 500)])
        records = capture.load_capture(self.cap.finish())
        result = [r for r in records if r["type"] == "result"][0]
        self.assertEqual(result["rank"], 2)
        self.assertEqual(result["rank_source"], "settlement")
        self.assertEqual(result["advancement"], "ADVANCED")

    def test_truncated_last_line_does_not_crash(self):
        """现场 Ctrl-C 会把 jsonl 截断在半行，不能因此炸掉整次分析。"""
        self.cap = CaptureDir()
        self.cap.frame([rabbit(MY_ID, 10, 1000)])
        root = self.cap.finish()
        with open(os.path.join(root, "frames.jsonl"), "a") as fh:
            fh.write('{"receivedAt": 99, "commandTy')
        records = capture.load_capture(root)
        self.assertTrue(any(r["type"] == "frame" for r in records))


class TestAnalyzeEndToEnd(unittest.TestCase):
    """analyze.py 必须能吃采集目录 —— 这是本次改动的全部意义。"""

    def tearDown(self):
        if hasattr(self, "cap"):
            self.cap.cleanup()

    def test_analyze_reads_capture_dir(self):
        self.cap = CaptureDir()
        self.cap.frame([rabbit(MY_ID, 10, 1000), rabbit("7", 10, 1000)])
        self.cap.frame([rabbit(MY_ID, 11, 860), rabbit("7", 9, 700)])   # 我赢
        self.cap.frame([rabbit(MY_ID, 10, 860), rabbit("7", 9, 700)])   # 撞障碍
        self.cap.frame([rabbit(MY_ID, 7, 860), rabbit("7", 9, 700)])    # 空转 -3
        data = analyze.analyze(self.cap.finish())

        self.assertGreater(data["frames"], 0, "帧数为 0 说明又在静默失败")
        self.assertEqual(data["self_id"], MY_ID)
        self.assertEqual(data["wins"], 1)
        self.assertEqual(data["obstacle_hits"], 1)
        self.assertEqual(data["idle_penalties"], 1)
        self.assertEqual(data["final_score"], 7)
        self.assertEqual(data["version"], "deadbeef")
        self.assertIn("7", data["rival_spends"])

    def test_obstacle_and_idle_are_not_counted_as_duel_losses(self):
        """旧逻辑把任何负分都算 loss，会让「输多于赢 → 调高 bid_margin」指错方向。"""
        self.cap = CaptureDir()
        self.cap.frame([rabbit(MY_ID, 10, 1000)])
        self.cap.frame([rabbit(MY_ID, 9, 1000)])     # 障碍 -1
        self.cap.frame([rabbit(MY_ID, 6, 1000)])     # 空转 -3
        data = analyze.analyze(self.cap.finish())
        self.assertEqual(data["losses"], 0)
        self.assertEqual(data["duels"], 0)
        self.assertEqual(data["obstacle_hits"], 1)
        self.assertEqual(data["idle_penalties"], 1)

    def test_missing_self_id_is_surfaced(self):
        """认错自己是最危险的失败，必须能从数据里看出来。"""
        self.cap = CaptureDir(bot_id="9999")
        self.cap.frame([rabbit(MY_ID, 10, 1000)])
        self.cap.frame([rabbit(MY_ID, 11, 900)])
        data = analyze.analyze(self.cap.finish())
        self.assertIsNone(data["self_id"])
        self.assertEqual(data["sprite_ids"], [MY_ID])

    def test_report_does_not_crash(self):
        """报表里有不少可选字段，缺失时不能抛 —— 现场没时间修分析器。"""
        import io
        import contextlib
        self.cap = CaptureDir()
        self.cap.frame([rabbit(MY_ID, 10, 1000)])
        self.cap.frame([rabbit(MY_ID, 11, 860)])
        data = analyze.analyze(self.cap.finish())
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            analyze.report(data)
            analyze.compare([data, data])
        self.assertIn("果实净变", buffer.getvalue())

    def test_legacy_telemetry_jsonl_still_works(self):
        """备用的独立 runner 路径写的是另一套格式，不能被这次改动搞坏。"""
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=".jsonl", delete=False, encoding="utf-8")
        try:
            for record in [
                {"type": "match_start", "bot_version": "firefly-v1"},
                {"type": "frame", "decision": "[ram] 进攻", "elapsed": 1.0},
                {"type": "collision", "is_self": True, "sprite": MY_ID,
                 "kind": "sprite", "score_delta": 1, "energy_spent": 140},
                {"type": "result", "rank": 1, "advancement": "ADVANCED"},
                {"type": "match_end", "final_score": 12, "heart_pickups": 1},
            ]:
                handle.write(json.dumps(record) + "\n")
            handle.close()
            data = analyze.analyze(handle.name)
            self.assertEqual(data["version"], "firefly-v1")
            self.assertEqual(data["frames"], 1)
            self.assertEqual(data["wins"], 1)
            self.assertEqual(data["final_score"], 12)
            self.assertEqual(data["intents"]["ram"], 1)
        finally:
            os.unlink(handle.name)


if __name__ == "__main__":
    unittest.main()
