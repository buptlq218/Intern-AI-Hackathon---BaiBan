"""攻击力经济学。

## 为什么这套策略是对的

三条引擎事实决定了最优出价形态：

1.  ``actualAttack = min(setValue, energy)``，碰撞按实际值结算并消耗等量能量。
2.  能量每 30s **重置**为 1000，不是累加 —— 所以窗口结束时没花掉的能量是纯浪费。
3.  胜负只看谁高，赢多少不影响收益：高出 1 点和高出 900 点都只是 +1 果实。

由此推出：

*   **出价高于对手 1 点就够了，再高全是浪费。** 所以目标是 ``threat + 一点余量``，
    不是「越高越好」。
*   **出价低于对手一点点，就等于这次白扔能量还倒扣 1 分。** 所以余量不能省。
*   设 30s 窗口内预计发生 k 次碰撞、能量 E、需要压过的阈值 T：
    -   若 ``E/k > T``：出 ``T+ε`` 能把 k 次全赢下来。
    -   若 ``E/k < T``：赢不满。此时**仍然出 T+ε**，能赢 ``floor(E/T)`` 次，
        比摊薄成每次都出 E/k（每次都输）严格更好。净分 ``2m-k`` 在 m 最大时最优。
    -   所以「按次摊薄预算」是错的直觉；正确做法是**一直出 T+ε，直到能量打光**。
*   能量已经不够出一次 ``T+ε`` 时，出价再怎么调都赢不了 → 该做的是**避战**，
    而不是继续送分。同时把攻击强度设成剩余全部能量，万一被迫接触还有一线希望。
*   窗口末尾（``spenddown_seconds`` 内）剩余能量即将被重置清零，此时对**已经
    决定要打**的这一次碰撞梭哈是免费的。

这套逻辑的可测性：见 tests/test_attack.py，每条结论都有对应用例。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .constants import Tune


@dataclass
class AttackDecision:
    """一次出价决策的结果与理由（理由会进 replay，方便复盘）。

    ``can_win`` 和 ``can_tie`` 必须分开看。**平局不丢果实**，所以「打不赢」
    不等于「该躲」：

    *   能压过对手 → 打，+1
    *   压不过但能打平（能量 ≥ 对手出价）→ **照打**。果实不变，还免费重置了
        无碰撞计时；比躲开然后靠撞障碍保活（-1）严格更好。
    *   连平都做不到 → 才该躲。

    这个区分不是理论洁癖：离线沙盒里遇到「三个对手全部每次梭哈 1000」的场面时，
    旧逻辑把它判成「赢不了 → 全场避战」，于是整局靠撞障碍保活，
    平均果实 -0.70、晋级率 27%。而其实我们能用 1000 打平，一分不丢。
    """

    value: float
    can_win: bool          # 以当前能量，能否压过对手
    mode: str              # "bid" | "spenddown" | "tie" | "starved" | "free"
    reason: str = ""
    can_tie: bool = False  # 打不赢但能打平（不丢果实）

    @property
    def worth_engaging(self) -> bool:
        """值不值得主动接触。平局也算值得。"""
        return self.can_win or self.can_tie

    def __str__(self) -> str:  # pragma: no cover - 仅日志
        return "{}({:.0f}) {}".format(self.mode, self.value, self.reason)


def decide_attack(
    tune: Tune,
    energy: float,
    threat: float,
    seconds_to_reset: float,
    invincible: bool = False,
    committing_to_contact: bool = False,
) -> AttackDecision:
    """计算下一次碰撞应设置的攻击强度。

    :param energy: 我方当前能量。
    :param threat: 需要压过的对手攻击强度估计（来自 WorldModel.threat_level）。
    :param seconds_to_reset: 距能量重置剩余秒数。
    :param invincible: 我方是否持有森林之心。
    :param committing_to_contact: 策略层是否**已经决定**要主动去撞。
        梭哈只在真的要打的时候才有意义，否则会被一次意外接触白白清空能量。
    """
    energy = max(0.0, energy)

    # 持森林之心时不消耗能量且对未持心者必胜 —— 出价无意义，留个低值省心。
    if invincible:
        return AttackDecision(
            value=max(tune.min_attack, 0.0),
            can_win=True,
            mode="free",
            reason="持森林之心：碰撞不耗能且必胜，出价无关",
        )

    bid = threat * (1.0 + tune.bid_margin_pct) + tune.bid_margin_abs
    bid = max(bid, tune.min_attack)

    # 出不起「加了余量的价」。分三种，**都不再全押** —— 见 R3：
    # 全押是我方能量归零的主因，而归零之后每一次碰撞都是白送 -1。
    if energy < bid:
        if energy > threat:
            # 能量够压过对手，只是不够加满余量 → 压过就行，剩下的留着。
            # 「赢多少不影响收益」，所以这里出 threat + 最小可分辨量即最优。
            lean = min(energy, max(threat + tune.min_attack, tune.min_attack))
            return AttackDecision(
                value=lean,
                can_win=True,
                mode="lean",
                reason="余量不够但仍能压过 {:.0f} → 出 {:.0f}，留下 {:.0f}".format(
                    threat, lean, energy - lean
                ),
            )
        if energy == threat:
            # 严格相等才是平局：不丢果实，且免费重置无碰撞计时 → 照打。
            return AttackDecision(
                value=energy,
                can_win=False,
                can_tie=True,
                mode="tie",
                reason="{:.0f} 与对手相等 → 平局，不丢果实".format(energy),
            )
        # 连平都做不到。**押上大部分，但留住底线。**
        #
        # 为什么还押：``threat`` 是刻意偏高的估计（0.9 分位数并与最近一次取 max），
        # 所以高估很常见。真实出价可能低于我们剩下的能量 —— 押上去是唯一的翻盘机会。
        # 为什么留底线：真的归零后，我方 actualAttack 恒为 0，**接下来每次碰撞都是
        # 确定的 -1**；留住一点就还能压过任何同样见底的对手。现场实测归零占 22% 的
        # 帧、白送 12 次 -1，所以底线的期望价值高于最后这一点点翻盘概率。
        stake = max(0.0, energy - tune.energy_floor)
        return AttackDecision(
            value=stake,
            can_win=False,
            can_tie=False,
            mode="starved",
            reason="能量 {:.0f} < 对手 {:.0f}，押 {:.0f} 赌估计偏高，留 {:.0f} 底线".format(
                energy, threat, stake, min(energy, tune.energy_floor)
            ),
        )

    # 窗口末尾且已决定要撞：剩余能量马上要被重置清零，梭哈是免费的。
    #
    # ⚠️ 但「免费」有前提：本窗口内不能再发生第二次结算。碰撞冷却约 1.5s，
    # 所以只有当距重置时间短到放不下另一次碰撞时，梭哈才真的没有代价。
    # 离线沙盒里把窗口设成 5s 时出现过：25.4s 梭哈 1000 赢一次，随后能量归零，
    # 26.9/28.4/29.9s 连输三次，净 -2。这就是下面这个保留额的由来。
    if committing_to_contact and seconds_to_reset <= tune.spenddown_seconds:
        reserve = _reserve_for_remaining(tune, bid, seconds_to_reset)
        # R3：梭哈也要留下 energy_floor。「把 10 当成 0」——
        # 保住一点点能量，就保住了「对手归零时用最小出价白拿 +1」的能力；
        # 真的归零则相反：接下来每一次碰撞都是确定的 -1。
        spendable = energy - reserve - tune.energy_floor
        if spendable >= bid:
            return AttackDecision(
                value=spendable,
                can_win=True,
                mode="spenddown",
                reason="距重置 {:.1f}s，保留 {:.0f}+底线 {:.0f} 后花掉 {:.0f}".format(
                    seconds_to_reset, reserve, tune.energy_floor, spendable
                ),
            )

    # 常规：压过对手一点点即可，多出来的全是浪费。
    #
    # ⚠️ 下面这两行是**恒等式**：``min(bid, max(bid, x)) === bid``，所以
    # ``max_attack_fraction_of_energy`` 在这条路径上**完全不起作用**。
    # 沙盒扫过 0.55/0.45/0.35/0.25 四个值，四组结果一模一样（果实 12.22、
    # 垫底 12%，一位都不差）—— 这就是它是死代码的证据。
    #
    # 保留而不删，是因为「按比例封顶」这个想法本身就是**错的**，留个反面记录：
    # 出价低于对手 → 必输 -1。所以把出价压到 threat 以下，等于把一次可能的 +1
    # 主动换成一次确定的 -1；而「留给后续碰撞」并不能弥补，因为后续那几次同样
    # 会因为出价不足而全输（见模块开头的 2m-k 推导）。真正该做的是控制**交战
    # 频率**和**选择对手**，不是压低单次出价。
    ceiling = max(bid, energy * tune.max_attack_fraction_of_energy)
    value = min(bid, ceiling)
    return AttackDecision(
        value=value,
        can_win=True,
        mode="bid",
        reason="压过威胁 {:.0f} → 出 {:.0f}（能量 {:.0f}）".format(threat, value, energy),
    )


def _reserve_for_remaining(tune: Tune, bid: float, seconds_to_reset: float) -> float:
    """窗口结束前可能还要打几次，就得留几次的钱。

    用碰撞冷却当节拍：同一对手 1.5s 内不会重复结算，所以剩余时间能塞进几个
    冷却周期，就大致是还会被结算几次。
    """
    from .constants import RULE_COLLISION_COOLDOWN

    slots = int(max(0.0, seconds_to_reset) // RULE_COLLISION_COOLDOWN)
    return slots * bid


def affordable_collisions(energy: float, bid: float) -> int:
    """以某个出价，剩余能量还能打赢几次。用于风险评估与日志。"""
    if bid <= 0:
        return 0
    return int(energy // bid)


def expected_collisions_left(tune: Tune, seconds_to_reset: float) -> float:
    """本窗口内预计还会发生几次碰撞。

    只用于日志与「能量是否显著过剩」的判断，不参与出价计算 ——
    见模块开头：按次摊薄预算是错的。
    """
    per = max(0.1, tune.expected_seconds_per_collision)
    return max(0.0, seconds_to_reset) / per


def energy_surplus_ratio(
    tune: Tune, energy: float, threat: float, seconds_to_reset: float
) -> float:
    """能量富余程度：>1 表示按当前威胁水平能量花不完，可以更激进。"""
    bid = max(tune.min_attack, threat * (1.0 + tune.bid_margin_pct) + tune.bid_margin_abs)
    need = bid * max(1.0, expected_collisions_left(tune, seconds_to_reset))
    if need <= 0:
        return 1.0
    return energy / need
