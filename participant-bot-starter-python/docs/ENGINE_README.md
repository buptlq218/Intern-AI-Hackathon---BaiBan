# 萤火森林 Agent 挑战赛 —— 策略引擎

2026-07-30 INTERN AI HACKATHON 参赛代码。Python 3.9+，**核心零依赖**。

配套文档：
- [参赛指导手册（钉钉）](https://alidocs.dingtalk.com/i/nodes/MNDoBb60VLYDGNPytma6vE3AJlemrZQ3) —— 规则、策略与现场流程
- [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md) —— 现场待验证的规则不确定点（**开场先做这个**）
- [`docs/LOOP_LOG.md`](docs/LOOP_LOG.md) —— 每轮实验记录

---

## 30 秒上手

```bash
# 1. 自检：不需要 SDK、不需要网络，验证策略链路
python sdk_adapter.py --selftest

# 2. 回归：71 个单测
python -m unittest discover -s tests

# 3. 离线沙盒：刷参数不占用联调平台
python tools/sim.py --matches 20
python tools/sim.py --matches 1 --seed 3 --verbose     # 看单局事件流
```

正式跑（AK 只从环境变量读）：

```bash
export FIREFLY_ACCESS_KEY='报名平台发放的AK'
python -m firefly.runner          # 兜底客户端；有官方 SDK 时改用 sdk_adapter.py
```

---

## 接官方 SDK

**只改 `sdk_adapter.py` 一个文件。** 策略引擎刻意不认识 SDK，所以 SDK 的 API 长什么样
都不影响策略逻辑和单测。

`sdk_adapter.py` 里针对三种常见 SDK 形态各准备了一个接法（策略回调 / 原始消息回调 /
继承基类），照注释填 TODO 即可，约 5 分钟。接完先跑 `--selftest`。

⚠️ 细则硬约束：不要修改 SDK 的 100ms 动作间隔、5 秒心跳与限频逻辑，也不要自建
WebSocket 或定时器绕过 SDK。

---

## 目录结构

```
firefly/               策略引擎（核心零依赖）
├── constants.py        规则常量 + Tune 参数 —— Loop 只改 TUNE
├── geometry.py         2D 几何：SAT、OBB、外推
├── protocol.py         消息解析与动作构造（容错）
├── worldmodel.py       世界模型：地图缓存、对手攻击力推断、两个 30s 周期
├── attack.py           攻击力经济学（出价策略）
├── control.py          运动控制：单动作限制、转向符号在线标定
├── strategy.py         决策阶梯
├── agent.py            会话状态机 ← 接 SDK 的地方
├── telemetry.py        replay 落盘（含 AK 脱敏）
└── runner.py           独立 WebSocket 兜底客户端

sdk_adapter.py          官方 SDK 接入层 ← 拿到 SDK 只改这里
tools/sim.py            离线沙盒
tools/analyze.py        replay 分析（Loop 的 Checker）
tools/debug_frames.py   逐帧决策打印，定位「为什么它一直撞墙」这类问题
tests/                  71 个单测
```

---

## 策略要点

三条引擎事实推出了整套出价策略：

1. `actualAttack = min(setValue, energy)`，按实际值结算并消耗等量能量
2. 能量每 30s **重置**为 1000（不是累加）→ 窗口末没花掉的能量是纯浪费
3. 胜负只看谁高，**赢多少不影响收益**（高 1 点和高 900 点都是 +1 果实）

因此：

- **出价 = 压过对手一点点。** 再高全是浪费，再低就是白扔能量还倒扣分。
- **对手出价是可以精确反推的。** 实时协议不广播 `setAttackValue`，但碰撞会精确
  扣掉 `actualAttack` 的能量，而能量逐帧广播 —— **能量跌幅就是对手这次的攻击强度**。
  这是本方案最大的信息优势，见 `worldmodel._diff_sprites`。
- **不要按次摊薄预算。** 能量不够全赢时，仍应出 `T+ε` 拿下 `floor(E/T)` 次，
  比每次都出 `E/k` 然后全输严格更优。有单测守着这条结论。
- **-1 优于 -3。** 实在找不到安全目标时主动撞障碍买掉无碰撞惩罚，净赚 2 分。
- **森林之心是全局最高价值目标。** 10s 内碰撞不耗能、对未持心者必胜、撞障碍不扣果实；
  配合 1.5s 冷却，理论上能白拿 +3~+6。反过来，对手持心时我方必输且对方零成本，
  唯一正确反应是躲。

避障是 `plan_motion` 里的**运动层滤波**，而不是优先级阶梯里的一根横杆 ——
放在阶梯里会被排在它前面的意图绕过（这个坑沙盒实测过，见 `docs/LOOP_LOG.md` R0）。

---

## 安全

技术编程细则 §1.2：**AK 不得出现在日志、报错、截图、代码仓库和比赛数据文件中。**

本仓库的对策：
- AK 只从环境变量 `FIREFLY_ACCESS_KEY` 读，只在首条 `botConnect` 出现一次
- `telemetry.redact()` 对所有写盘内容递归脱敏（敏感键名 + 长随机串）
- `.gitignore` 排除 `.env`、`runs/`、`*.jsonl`

同一 AK 同时只允许一条有效连接，第二条会收到 `BOT_ALREADY_ONLINE` 并被以 1008 关闭。
**现场确认只有一个进程在跑。**
