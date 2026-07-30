# 萤火森林 Agent 挑战赛 —— 白板队参赛 BOT

2026-07-30 INTERN AI HACKATHON。基于官方 `participant-bot-starter-python`，
连接层沿用官方 `bot.py`，战斗策略换成自研的 `firefly/` 引擎。

官方原始文档保留在 [`docs/`](docs/)（`OFFICIAL_README.md` / `DEVELOPMENT_GUIDE.md` / `RULES.md`）。

---

## 跑起来

```bash
# macOS 双击 启动BOT.command，或者：
CRAZY_CRASH_ACCESS_KEY='test:你的数字工号' ./.venv/bin/python bot.py
```

**改完策略必须重启 BOT** —— `strategy.py` 只在进程启动时加载一次。

回归（不联网、一秒出结果）：

```bash
python3 mytests/run_all.py      # 106 个自研用例（引擎 + 契约集成）
./.venv/bin/python check.py     # 官方检查：语法 / 动作合法性 / 生命周期
python3 tools/sim.py --matches 40 --opponents default,steady,aggressive
```

现场排查行为偏差：

```bash
# 起 BOT，同时把每帧的决策解释存下来（意图分布只存在于运行时，回放里没有）
FIREFLY_DEBUG=1 ./.venv/bin/python bot.py 2> runtime/debug.log

# replay 分析（Loop 的 Checker）—— 直接指 runtime/，它会找出所有采集目录
python3 tools/analyze.py runtime/ --debug-log runtime/debug.log
python3 tools/analyze.py runtime/ --compare    # 多局趋势/方差/最差情况
```

`analyze.py` 吃两种输入：官方 `bot.py` 的采集目录
（`runtime/matches/<matchCode-matchId>/`，正式赛走这条）和 `firefly/telemetry.py`
写的 `runs/*.jsonl`（备用独立 runner）。前者是**原始帧转储**，碰撞事件由
`tools/capture.py` 离线重建 —— 顺带把 E1/E2/E5/E12 变成报表里的自动结论。

---

## 改哪里

**只改 `firefly/constants.py` 里的 `TUNE`。** 每轮只改一个参数，改完跑
`python3 mytests/run_all.py`，然后按 [`docs/LOOP_LOG.md`](docs/LOOP_LOG.md) 记录结论。

```
bot.py               官方连接层。只加了 1 处：把 startGame 的 data 透传给策略（见下）
strategy.py          官方契约入口 → 转发给 firefly 引擎
firefly/
├── constants.py      规则常量 + TUNE 参数  ← Loop 只改这里
├── geometry.py        SAT / OBB / 轨迹外推（零依赖）
├── protocol.py        帧解析（容错、字段兼容）
├── worldmodel.py      地图缓存、⭐对手攻击力推断、两个 30s 周期、名次感知
├── attack.py          出价经济学
├── control.py         运动控制：单动作限制、转向符号在线标定
├── strategy.py        决策阶梯
├── agent.py / runner.py / telemetry.py   （备用：不依赖官方 SDK 的独立实现）
mytests/             106 个用例
tools/sim.py         离线沙盒
tools/analyze.py     replay 分析
docs/EXPERIMENTS.md  现场待验证清单
```

### 对 `bot.py` 的唯一改动

官方 `choose_command(game_state, bot_id)` 只能拿到 `refreshData.data`，
里面**没有 `map`**（`map` 只在 `startGame` 下发一次）—— 所以避障本来做不了。
因此在 `bot.py` 的 `startGame` 分支加了一个可选 hook，把 `data` 透传给
`strategy.on_start_game()`。没有这个 hook 策略也能跑，只是退化成「只躲边缘、不躲石头」。

**没有改动上报频率、心跳或限频逻辑**（官方红线）。

---

## 策略核心

### 出价：压过对手一点点，且盯住对手的当前能量

三条引擎事实决定一切：

1. `actualAttack = min(设定值, 当前能量)`，按实际值结算并消耗等量能量
2. 能量每 30s **重置**为 1000（不是累加）→ 窗口末没花掉的能量是纯浪费
3. 胜负只看谁高，**赢多少不影响收益**（高 1 点和高 900 点都是 +1 果实）

由此得到：

- **对手出价可以精确反推。** 协议不广播 `setAttackValue`，但碰撞精确扣除
  `actualAttack` 等量能量，而 `energy` 逐帧广播 → **能量跌幅就是对手这次的出价**。
- **⭐ 对手的当前能量是他攻击强度的硬上限。** 历史出价只说明「他想出多少」，
  当前能量才决定「他能出多少」。每次梭哈 1000 的队伍花完后整个窗口都是空壳，
  此时最小出价就能白拿 +1。沙盒里这一条把「全员梭哈」场景的晋级率从 23% 拉到 55%。
- **不要按次摊薄预算。** 能量不够全赢时仍应出 `T+ε`，拿下 `floor(E/T)` 次，
  严格优于每次出 `E/k` 然后全输。
- **平局不丢果实，所以「打不赢」≠「该躲」。** 能量够打平就照打：果实不变，
  还免费重置了无碰撞计时，比躲开再靠撞障碍保活（-1）更好。只有连平都做不到才避战。
- **窗口末尾把花不掉的花掉**，但要按碰撞冷却（1.5s）留出保留额，
  否则赢一次后能量归零，剩下的碰撞全是白输。

### -1 优于 -3

无碰撞 30s 罚 3 果实，撞障碍罚 1 果实，**两者都会重置无碰撞计时**。
所以找不到安全目标时主动撞障碍是**净赚 2 分**的保底操作，不是消极行为。
持森林之心时撞障碍不扣果实，保活完全免费。

### 森林之心是全局最高价值目标

10s 内碰撞不耗能、对未持心者必胜、撞障碍不扣果实；配合 1.5s 冷却理论上白拿 +3~+6。
反过来对手持心时我方必输而对方零成本，唯一正确反应是**躲**。
第三种情况最容易忽略：**抢不到还赖在附近是最差选择**，等于给持心者送果实。

### 终局名次感知

积分规则：每轮按名次积 3/2/1/0 分，总分同则取果实多者，4 进 2。收益不对称：

- 领先时「少输」比「多赢」值钱（一次失败碰撞既丢名次分又丢 tiebreak 果实）→ `protect`
- 眼看垫底（0 分）时没有下行空间，不利赔率也该打 → `desperate`

### 避障是运动层滤波，不是优先级阶梯的一根横杆

放进阶梯会被排在它前面的意图绕过。沙盒实测：`抢森林之心` 排在避障之前时，
追道具全程不避障，clearance 从 128px 一路磨到 0，撞墙淘汰 —— 当时最大的单一损失源。

---

## 沙盒基准（各 40 局）

| 对手组合 | 平均果实 | 平均名次 | 晋级率 |
|---|---|---|---|
| 全部默认（不调攻击力） | 11.35 | 1.18 | 92% |
| default / steady / aggressive | 6.90 | 1.68 | 75% |
| steady / aggressive / allin | 3.58 | 2.38 | 52% |
| 全部梭哈 | 1.27 | 2.35 | 55% |

> ⚠️ **沙盒是近似模型，不是引擎复刻**（物理步进、碰撞判定、对手行为都是代理）。
> 这些数字只用于排除坏参数和防回归崩溃，**不能当作策略更强的证据**。
> 真实结论必须来自联调平台 replay。

---

## 安全

细则 §1.2：**AK 不得出现在日志、报错、截图、代码仓库和比赛数据文件中。**

- AK 只从 `CRAZY_CRASH_ACCESS_KEY` 读，官方启动脚本不回显、不落盘
- `firefly/telemetry.py::redact()` 对写盘内容递归脱敏
- `.gitignore` 排除 `runtime/`、`.venv/`、`.env`

**上传 GitHub 前先执行一次**（确认没有 AK 泄漏）：

```bash
git grep -nE 'Agent-[0-9a-f]{8}|CRAZY_CRASH_ACCESS_KEY=[^$]' || echo "未发现 AK 泄漏"
```

同一 AK 同时只允许一条连接 —— 第二条会收到 `BOT_ALREADY_ONLINE` 并被以 1008 关闭。
**确认只有一个 BOT 窗口在跑。**
