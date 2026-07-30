"""萤火森林 Agent 挑战赛 —— 策略引擎。

分层，方便现场只改需要改的那一层：

*   ``constants``  规则常量 + 策略参数（Loop 只改 ``TUNE``）
*   ``geometry``   零依赖 2D 几何（SAT / OBB / 外推）
*   ``protocol``   消息解析与动作构造（容错、字段兼容）
*   ``worldmodel`` 世界模型（地图缓存、对手攻击力推断、两个 30s 周期）
*   ``attack``     攻击力经济学（出价策略）
*   ``control``    运动控制（单动作限制、转向符号在线标定）
*   ``strategy``   决策阶梯
*   ``agent``      会话状态机 —— **接 SDK 就接这里**
*   ``runner``     独立 WebSocket 兜底客户端

最小用法（SDK 只给策略回调时）::

    from firefly.agent import FireflyAgent

    agent = FireflyAgent(access_key=os.environ["FIREFLY_ACCESS_KEY"])
    # 把下面这个函数接到 SDK 的帧回调上
    action = agent.on_strategy_frame(frame_message_dict)   # -> dict | None
"""

from .constants import BOT_VERSION, TUNE, Tune

__all__ = ["BOT_VERSION", "TUNE", "Tune"]
__version__ = BOT_VERSION
