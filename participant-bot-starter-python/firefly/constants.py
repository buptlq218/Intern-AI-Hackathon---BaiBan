"""萤火森林 Agent — 规则常量与可调参数。

常量分两类，改动纪律不同：

*   ``RULE_*`` 是官方《技术编程细则说明》给出的引擎事实。**不要为了调参而改这里** —— 改
    它等于假设规则变了。若现场 replay 与这里不符，先在 docs/EXPERIMENTS.md 记录证据，
    确认后再改，并同步更新注释里的出处。
*   ``TUNE`` 里的是我们自己的策略参数。Loop 迭代只动这一处，每轮只动一个。

单位：坐标 px，角度 rad，时间 s（除注明 ms）。
"""

from dataclasses import dataclass
from typing import Tuple

# ---------------------------------------------------------------------------
# 一、引擎事实（来自技术编程细则 §1.3 / §5 / §6）
# ---------------------------------------------------------------------------

RULE_MAP_WIDTH = 1440
RULE_MAP_HEIGHT = 820

RULE_MATCH_SECONDS = 180          # 单局最长时长
RULE_INITIAL_FRUIT = 10           # 初始发光果实
RULE_INITIAL_ENERGY = 1000        # 初始能量
RULE_DEFAULT_ATTACK = 50          # 未调用 setAttackValue 时的默认攻击强度

RULE_ENERGY_RESET_PERIOD = 30     # 每 30s 能量「重置」为 1000（不是累加）
RULE_ENERGY_RESET_VALUE = 1000

RULE_HEART_DURATION = 10          # 森林之心增益持续时间
# 通常在第 30/90/150s 附近生成，生成前约 5s 有画面提示。
# 细则明确要求「以实时字段为准，不要仅依赖本地计时器」——这里只用于预定位。
#
# ✅ E6 已用现场 15 局 replay 验证：``goldCarrot`` 首次出现的时刻是
# **30.0s（15/15 局，误差 ≤0.1s）**，第二次出现在 90.0s。相位确认无误。
RULE_HEART_SPAWN_HINTS: Tuple[int, ...] = (30, 90, 150)

# 森林之心的生成范围 —— **不是全图随机**。
#
# 现场 15 次生成的实测包络：x ∈ [423, 1079]、y ∈ [255, 629]，质心 (779, 420)。
# 地图是 1440×820，也就是说它只落在**中央约 46% 宽 × 46% 高**的区域里。
# 这一条是「卡位」策略成立的前提：如果真是全图随机，站位的边际收益会小得多。
#
# ⚠️ n=15 的包络必然偏小（极值需要更多样本才收敛），所以下面刻意往外放宽约
# 60px 再使用；策略里只用它当**采样分布**，真实位置一律以实时 goldCarrot 为准。
RULE_HEART_SPAWN_BOX = (360.0, 195.0, 1140.0, 690.0)   # (x0, y0, x1, y1)

RULE_IDLE_PENALTY_PERIOD = 30     # 连续 30s 无碰撞
RULE_IDLE_PENALTY_FRUIT = 3       # 扣 3 果实
RULE_OBSTACLE_PENALTY_FRUIT = 1   # 撞障碍物扣 1 果实

RULE_COLLISION_COOLDOWN = 1.5     # 同一对象连续接触的碰撞冷却
RULE_FRAME_INTERVAL = 0.1         # refreshData 约 100ms 一帧
RULE_MIN_ACTION_INTERVAL_MS = 100 # 动作指令发送频率下限；不得更快

RULE_TURN_RATE_MIN = 0.01         # turnLeft/turnRight data 合法范围
RULE_TURN_RATE_MAX = 0.1
RULE_TURN_RATE_DEFAULT = 0.05     # 前端缺省值；我们始终显式传值

# 反弹速度模型（细则 §6）。仅用于短期预测与风险评估，不取代实时观测。
#   vA' = REBOUND_POS_K * (pA - pB) + REBOUND_SELF_K * vA + REBOUND_OTHER_K * vB
RULE_REBOUND_POS_K = 0.02
RULE_REBOUND_SELF_K = -0.3
RULE_REBOUND_OTHER_K = 0.7
RULE_REBOUND_DECAY_PER_FRAME = 0.15   # 反弹速度每帧衰减约 0.15 px
RULE_HEART_REBOUND_MULTIPLIER = 1.5   # 持心方作为撞击方时对手反弹约 1.5 倍

# 场地边缘：当前版本无落水机制，会被强制拉回可行驶区，不增加 deathCount。
# ⚠️ 未确认：边缘接触是否算「障碍物碰撞」（即是否 -1 果实、是否重置无碰撞计时）。
# 这是现场第一个要验证的实验，见 docs/EXPERIMENTS.md 的 E1。
RULE_BORDER_IS_OBSTACLE_UNKNOWN = True

RULE_TABLE_SIZE = 4               # 每桌 4 队
RULE_ADVANCE_PER_TABLE = 2        # 4 进 2


# ---------------------------------------------------------------------------
# 二、协议字符串（避免全项目散落裸字符串拼错）
# ---------------------------------------------------------------------------

class Cmd:
    """commandType 取值。"""

    # 我们发出的
    BOT_CONNECT = "botConnect"
    BOT_HEARTBEAT = "botHeartbeat"
    AI_ENTER_ROOM = "aiEnterRoom"
    READY_FOR_NEXT_MATCH = "readyForNextMatch"
    GET_MY_BATTLE_DATA = "getMyBattleData"

    GO_FORWARD = "goForward"
    GO_BACK = "goBack"
    TURN_LEFT = "turnLeft"
    TURN_RIGHT = "turnRight"
    STOP = "stop"
    STEER_BACK = "steerBack"
    SET_ATTACK_VALUE = "setAttackValue"

    # 服务端发来的
    BOT_CONNECTED = "botConnected"
    BOT_READY = "botReady"
    ROUND_ASSIGNED = "roundAssigned"
    ROUND_STARTED = "roundStarted"
    ROOM_ENTERED = "roomEntered"
    START_GAME = "startGame"
    REFRESH_DATA = "refreshData"
    CLOSE_GAME = "closeGame"
    MATCH_FINISHED = "matchFinished"
    ROUND_FINISHED = "roundFinished"
    MY_BATTLE_DATA = "myBattleData"
    ERROR = "error"


class ErrCode:
    BOT_ALREADY_ONLINE = "BOT_ALREADY_ONLINE"
    BOT_CONNECT_REQUIRED = "BOT_CONNECT_REQUIRED"
    BOT_NOT_ASSIGNED = "BOT_NOT_ASSIGNED"
    ROOM_NOT_OPEN = "ROOM_NOT_OPEN"
    BOT_STILL_BATTLING = "BOT_STILL_BATTLING"


AGENT_WS_URL = "wss://pre-young-hackathon.alibaba-inc.com/ai"


# ---------------------------------------------------------------------------
# 三、策略参数 —— Loop 只改这里，每轮只改一个
# ---------------------------------------------------------------------------

@dataclass
class Tune:
    """策略可调参数。

    每个字段的注释写清「它控制什么」和「调高/调低的后果」，方便现场在
    replay 里定位到具体某一个参数，而不是凭感觉乱改。
    """

    # --- 攻击力竞价 -------------------------------------------------------
    # 对手攻击力未知时的先验。细则说默认 50，但主动调参的队伍会更高；
    # 取略高于默认值，避免开局白送前几次碰撞。
    assumed_opponent_attack: float = 120.0
    # 竞价加成：bid = threat * (1 + pct) + abs。
    # 调高 → 更稳赢但更快烧完能量预算；调低 → 可能被对手反超一点点而全输。
    bid_margin_pct: float = 0.12
    # R3：绝对余量 20 → 3。对手能量见底时威胁≈0，旧值会让我们仍然出 20+，
    # 而出 1 就能赢 —— 白扔 19 倍的能量。百分比余量仍然负责按威胁规模缩放。
    bid_margin_abs: float = 3.0
    # 单次碰撞攻击力下限/上限（上限是「单窗口预算占比」，不是绝对值）。
    # R3：下限 60 → 2。60 的下限正好挡死了「对手归零 → 出最小值白拿 +1」这条
    # 最便宜的收益路径。威胁未知时由 assumed_opponent_attack 兜底，不靠这个下限。
    min_attack: float = 2.0
    max_attack_fraction_of_energy: float = 0.55
    # 估计对手攻击力时用的分位数（1.0 = 取历史最大值，更保守更稳）。
    threat_quantile: float = 0.9

    # --- 能量窗口 ---------------------------------------------------------
    # 一个 30s 窗口内预期还能打几次的估算间隔；用于把能量摊到每次碰撞。
    expected_seconds_per_collision: float = 5.0
    # 距能量重置还剩这么多秒时进入「花光模式」：反正要重置，把花不掉的花掉。
    # 注意 attack.py 里还会按碰撞冷却扣一份保留额，所以这个值不必压得很小。
    spenddown_seconds: float = 4.0
    # 能量低于「打得起一次的竞价」时视为低能量 → 避战。
    low_energy_flee: bool = True
    # R3 ⭐ 能量底线：「把它当成 0」。
    #
    # 适用范围**只有两条浪费路径**：窗口末尾倾倒盈余（spenddown）、和注定要输的
    # 赌注（starved）。它**不**挡住能赢的出价 —— 底线的目的是保住「赢的能力」，
    # 不是囤能量。能量 25 / 威胁 10 时就该出 14 拿下 +1，而不是守着 20 输掉 -1。
    #
    # 为什么留一手：actualAttack = min(设定, 能量)。能量真的归零后，我方
    # actualAttack 恒为 0，**每一次碰撞都是确定的 -1**（除非对手也是 0 才平）。
    #
    # 20 这个值是从现场 8 局 replay 反推的，不是拍脑袋：把我方能量为 0 时挨的
    # 每一次 -1 拿出来，看「要赢下它需要出多少」（= 对手当次实际出价 + 1）：
    #
    #     底线  5 → 救回  5/20 次
    #     底线 20 → 救回 15/20 次   ← 拐点
    #     底线 50 → 救回 15/20 次   （加到 50 一次都不多救）
    #     底线100 → 救回 18/20 次   （代价是 10% 的窗口预算）
    #
    # 因为对手多数只出 10~50（能量高但出价低），20 就能压过绝大多数。
    # 再往上边际收益为零而占用预算线性上升，所以停在 20。
    energy_floor: float = 20.0

    # --- 无碰撞惩罚兜底 ---------------------------------------------------
    # 无互动达到该秒数就进入保活模式，主动找碰撞。
    # 细则建议留出寻找和移动时间，不要等到第 29s。
    idle_seek_at: float = 20.0
    # 达到该秒数仍没有精灵目标 → 主动撞障碍物（-1 优于 -3）。
    idle_obstacle_fallback_at: float = 25.0

    # --- 森林之心 ---------------------------------------------------------
    # R5 ⭐ 卡位：森林之心刷新前这么多秒开始抢占「离生成区最有利」的位置。
    #
    # 依据（现场 15 次生成的实测反算，见 docs/LOOP_LOG.md R5）：
    #   现状（不卡位）           平均排名 2.47   抢到第一 20%   平均距离 519px
    #   站在生成点质心 (780,420) 平均排名 1.67   抢到第一 47%   平均距离 223px
    # 四人局里「随机」就是 2.50 —— 也就是说我们目前的站位**一点优势都没有**。
    #
    # 8s 是**实测扫出来的**，不是估的。第一版拍了 6s，结果反算发现要走的距离中位数
    # 是 334px，而 6s×50px/s 只有 300px —— 只有 29% 的情况真能站到位。扫了一遍：
    #
    #     lead   平均排名   抢到第一   真能走到   （基线不卡位：2.57 / 14%）
    #      4s     1.86      36%        7%
    #      6s     1.79      36%       29%
    #      8s     1.46      62%       77%   ← 选它
    #     10s     1.77      38%       69%
    #     12s     1.92      31%       92%
    #     15s     1.46      69%      100%
    #
    # 排名一列在 8/10/12/15s 之间是**非单调**的，n=14 撑不起这种差异，所以不拿它
    # 选参数；能信的是「真能走到」那一列（单调上升）。8s 正好吃下 29%→77% 那一跳，
    # 而且是所有候选里放弃进攻时间最少的。15s 看着也好，若现场 8s 不灵就试 12~15s。
    #
    # 安全性：卡位排在阶梯第 7.5 位，在「无碰撞保活」（第 5 位，20s 触发）**之后**，
    # 所以即使卡位期间一直没碰撞，保活也会抢先接管，不会因为卡位吃 -3。
    heart_preposition_lead: float = 8.0
    # 卡位候选点的网格步长（px）。越小越精确、越费 CPU；100px 时 ~7×5=35 个候选
    # × 40 个采样点 = 1400 次距离运算，只在刷新前那几帧算，可以忽略。
    heart_preposition_grid: float = 100.0
    # 我方 ETA 不超过最快对手 ETA 的这个倍数时才去抢，否则撤离。
    heart_contest_eta_ratio: float = 1.35
    # 持心时的追击半径（px）；超过就换目标或回中场。
    heart_chase_radius: float = 900.0
    # 对手持心时的逃离半径（px）。
    flee_invincible_radius: float = 320.0

    # --- 运动控制 ---------------------------------------------------------
    # 航向误差小于该值就算对准，回正方向盘。
    heading_tolerance: float = 0.12
    # 航向误差大于该值认为目标在身后，考虑倒车。
    reverse_threshold: float = 2.5
    # 角速度分档，避免每帧微调造成指令抖动（细则要求仅状态变化时发送）。
    #
    # R2：从 (0.02, 0.05, 0.1) 改成**单一最大档**。原因见 docs/LOOP_LOG.md R2 ——
    # control.py 的 desired_rate = abs_err/π × 0.1 增益太低，45° 误差要 3.9s、
    # 57° 要 5.0s 才转得过来，而离石头只有约 1 秒反应时间 → 避障物理上来不及，
    # 现场 4 局练习赛撞障碍 36 次 > 赢 21 次。单一档位让 bucket_turn_rate 恒返回
    # 0.1，绕过那条坏公式，同时消掉「速率变了要重发指令」浪费的动作位。
    # 过冲不是问题：heading_tolerance=0.12 rad 而每帧只转 0.1 rad。
    turn_rate_buckets: Tuple[float, ...] = (0.1,)

    # --- 避障 -------------------------------------------------------------
    # 沿当前航向前瞻这么多秒做障碍预测。
    obstacle_lookahead_seconds: float = 1.2
    # 障碍安全余量（px），叠加在精灵外形半径之上。
    obstacle_safety_margin: float = 26.0
    # 距场地边缘小于该值就往内收（边缘是否扣分未确认，先当危险区处理）。
    border_keepout: float = 70.0

    # --- 终局名次感知 -----------------------------------------------------
    # 积分规则：每轮按名次积 3/2/1/0 分，总分相同取果实多者，4 进 2。
    # 所以「稳住不垫底」比「冲第一」更值钱：3 名→2 名和 2 名→1 名都只值 1 分，
    # 但掉到第 4 名会直接拿 0 分。
    # 剩余时间少于此值时进入终局姿态。
    endgame_seconds: float = 30.0
    # 领先晋级线这么多果实就转为「保成果」：少打不必要的架。
    protect_margin: float = 3.0
    # 落后晋级线这么多果实就转为「拼一把」：接受不利赔率，因为垫底就是 0 分。
    desperate_margin: float = -1.0

    # --- 目标选择权重 -----------------------------------------------------
    # 目标打分：越近越好、对手果实越少越好（可能打到淘汰）、赢面越大越好。
    w_distance: float = 1.0
    w_target_fruit: float = 0.35
    w_winrate: float = 2.0
    # 优先打能量枯竭的对手。actualAttack = min(设定, 能量)，所以能量见底的对手
    # 几乎是白送的 +1 —— 尤其是那些每次梭哈的队伍，花完后整个窗口都是空壳。
    w_target_drained: float = 1.2

    def bucket_turn_rate(self, desired: float) -> float:
        """把连续角速度需求量化到最近的档位，并夹到协议合法范围。"""
        desired = abs(desired)
        best = min(self.turn_rate_buckets, key=lambda b: abs(b - desired))
        return max(RULE_TURN_RATE_MIN, min(RULE_TURN_RATE_MAX, best))


TUNE = Tune()


# ---------------------------------------------------------------------------
# 四、版本标识（写进 botConnect 与 replay，方便对齐 replay 与代码）
# ---------------------------------------------------------------------------

#: 现场每次改策略都手动 bump。replay 里会记录这个值，用来把某局表现对回某版代码。
#
#: ⚠️ 但采集目录 metadata.json 里的 ``strategyHash`` **不看这里** —— 它只对顶层
#: ``strategy.py`` 做哈希。所以每轮还要同步改 ``strategy.py`` 的
#: ``STRATEGY_REVISION``，否则 replay 上的版本号会骗人（现场已踩过：23 局同一个
#: hash，一度误判成「改动没生效」）。
BOT_VERSION = "firefly-v5"
