"""消息解析与动作构造。

设计原则（对应细则里的坑）：

1.  **容错解析**：细则说「字段可能随版本增加，解析器应忽略未知字段，并为可选字段
    设置安全默认值，不要依赖 JSON 字段顺序」。所以这里全部用 ``.get()`` + 默认值，
    并且对类型做强制转换（``moveState`` 在文档表格里写 string、示例里却是 0）。
2.  **时间戳大小写陷阱**：``startGame`` 用 ``timeStamp``，``refreshData`` 用
    ``timestamp``。两个都读。
3.  **map 只在 startGame 下发一次**，必须缓存 —— 见 worldmodel.py。
4.  **goldCarrot 可能是 {} 或 null**，都表示当前没有森林之心。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .constants import Cmd
from .geometry import Point, Polygon


# ---------------------------------------------------------------------------
# 解析辅助
# ---------------------------------------------------------------------------

def _num(value: Any, default: float = 0.0) -> float:
    """把可能是 number / 数值字符串 / None 的字段转成 float。"""
    if value is None:
        return default
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _flag(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    if text in ("true", "1", "yes"):
        return True
    if text in ("false", "0", "no", ""):
        return False
    return default


def _point(value: Any) -> Point:
    if isinstance(value, dict):
        return (_num(value.get("x")), _num(value.get("y")))
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return (_num(value[0]), _num(value[1]))
    return (0.0, 0.0)


# ---------------------------------------------------------------------------
# 精灵
# ---------------------------------------------------------------------------

@dataclass
class Sprite:
    """一个参赛精灵的实时状态（细则 §4.3 的 rabbits[] 元素）。"""

    id: str
    name: str = ""
    position: Point = (0.0, 0.0)
    velocity: Point = (0.0, 0.0)
    angle: float = 0.0
    speed: float = 0.0
    angular_speed: float = 0.0        # 非负「大小」，方向看 dir_state
    dir_state: int = 0                # -1 左转 / 0 直行 / 1 右转
    width: float = 70.0
    height: float = 64.0
    score: float = 0.0                # 发光果实数量
    energy: float = 0.0
    active: bool = True
    move_state: Any = 0
    attacking: bool = False
    rebounding: bool = False
    rebound_angle: float = 0.0
    invincible: bool = False          # 森林之心增益中
    death_count: int = 0
    survival_time: float = 0.0
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def parse(cls, data: Dict[str, Any]) -> "Sprite":
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            position=_point(data.get("position")),
            velocity=_point(data.get("velocity")),
            angle=_num(data.get("angle")),
            speed=_num(data.get("speed")),
            angular_speed=abs(_num(data.get("angularSpeed"))),
            dir_state=int(_num(data.get("dirState"))),
            width=_num(data.get("width"), 70.0),
            height=_num(data.get("height"), 64.0),
            score=_num(data.get("score")),
            energy=_num(data.get("energy")),
            active=_flag(data.get("active"), True),
            move_state=data.get("moveState", 0),
            attacking=_flag(data.get("attacking")),
            rebounding=_flag(data.get("rebounding")),
            rebound_angle=_num(data.get("reboundAngle")),
            invincible=_flag(data.get("invincible")),
            death_count=int(_num(data.get("deathCount"))),
            survival_time=_num(data.get("survivalTime")),
            raw=data,
        )

    @property
    def alive(self) -> bool:
        """果实为 0 即永久淘汰（细则 §5.3）。"""
        return self.active and self.score > 0


# ---------------------------------------------------------------------------
# 地图
# ---------------------------------------------------------------------------

@dataclass
class GameMap:
    """开局地图。

    ``borders`` / ``blocks`` 是三层数组 [物体][凸块][顶点]。细则特别警告：
    凹形物体会被拆成多个凸块，遍历时**不能只读 [i][0]**。所以这里在解析时
    直接摊平成「凸块列表」，让下游不可能踩这个坑。
    """

    width: float
    height: float
    border_hulls: List[Polygon] = field(default_factory=list)
    block_hulls: List[Polygon] = field(default_factory=list)

    @staticmethod
    def _flatten(raw: Any) -> List[Polygon]:
        hulls: List[Polygon] = []
        if not isinstance(raw, (list, tuple)):
            return hulls
        for body in raw:
            if not isinstance(body, (list, tuple)):
                continue
            for hull in body:
                if not isinstance(hull, (list, tuple)):
                    continue
                pts = [_point(v) for v in hull if isinstance(v, (dict, list, tuple))]
                if len(pts) >= 3:
                    hulls.append(pts)
        return hulls

    @classmethod
    def parse(cls, data: Dict[str, Any], fallback_w: float, fallback_h: float) -> "GameMap":
        return cls(
            width=_num(data.get("width"), fallback_w) or fallback_w,
            height=_num(data.get("height"), fallback_h) or fallback_h,
            border_hulls=cls._flatten(data.get("borders")),
            block_hulls=cls._flatten(data.get("blocks")),
        )

    @property
    def all_hulls(self) -> List[Polygon]:
        return list(self.block_hulls) + list(self.border_hulls)


# ---------------------------------------------------------------------------
# 帧
# ---------------------------------------------------------------------------

@dataclass
class Frame:
    """一帧实时数据（refreshData），或 startGame 的初始快照。"""

    command_type: str
    timestamp_ms: float
    sprites: List[Sprite] = field(default_factory=list)
    gold_carrot: Optional[Point] = None      # 森林之心坐标；无则为 None
    elapsed_seconds: float = 0.0
    remaining_time: float = 0.0
    game_map: Optional[GameMap] = None       # 仅 startGame 有
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def parse(cls, message: Dict[str, Any]) -> "Frame":
        cmd = str(message.get("commandType", ""))
        # startGame 用 timeStamp，refreshData 用 timestamp —— 两个都读。
        ts = _num(message.get("timestamp", message.get("timeStamp")))
        data = message.get("data") or {}
        if not isinstance(data, dict):
            data = {}

        sprites = [
            Sprite.parse(s)
            for s in (data.get("rabbits") or [])
            if isinstance(s, dict)
        ]

        game_map = None
        if isinstance(data.get("map"), dict):
            from .constants import RULE_MAP_HEIGHT, RULE_MAP_WIDTH

            game_map = GameMap.parse(data["map"], RULE_MAP_WIDTH, RULE_MAP_HEIGHT)

        return cls(
            command_type=cmd,
            timestamp_ms=ts,
            sprites=sprites,
            gold_carrot=parse_gold_carrot(data.get("goldCarrot")),
            elapsed_seconds=_num(data.get("elapsedSeconds")),
            remaining_time=_num(data.get("remainingTime")),
            game_map=game_map,
            raw=message,
        )


def parse_gold_carrot(value: Any) -> Optional[Point]:
    """森林之心坐标。

    细则 §4.4：``{}`` 或 ``null`` 都表示当前没有可拾取的森林之心；当前协议
    **不使用** active / position / width / height 字段，坐标直接在顶层 x / y。
    这里额外容忍一层 ``position`` 嵌套，以防版本变化。
    """
    if not isinstance(value, dict) or not value:
        return None
    if "x" in value and "y" in value:
        x, y = _num(value.get("x"), float("nan")), _num(value.get("y"), float("nan"))
        if x == x and y == y:  # NaN 检查
            return (x, y)
    if isinstance(value.get("position"), dict):
        return _point(value["position"])
    return None


# ---------------------------------------------------------------------------
# 动作
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Action:
    """一条控制指令。

    细则约束：每次策略回调**最多返回一个动作**；发送频率不得高于每 100ms 一次；
    相同指令仅在策略状态变化时发送。所以策略层返回 ``Optional[Action]``，
    ``None`` 表示这一帧什么都不用发。
    """

    command_type: str
    data: Optional[str] = None
    reason: str = ""      # 只进本地日志，不上报；用于 replay 里解释每一步

    def to_message(self) -> Dict[str, Any]:
        msg: Dict[str, Any] = {"commandType": self.command_type}
        if self.data is not None:
            msg["data"] = self.data
        return msg


def go_forward(reason: str = "") -> Action:
    return Action(Cmd.GO_FORWARD, reason=reason)


def go_back(reason: str = "") -> Action:
    return Action(Cmd.GO_BACK, reason=reason)


def stop(reason: str = "") -> Action:
    return Action(Cmd.STOP, reason=reason)


def steer_back(reason: str = "") -> Action:
    return Action(Cmd.STEER_BACK, reason=reason)


def turn_left(rate: float, reason: str = "") -> Action:
    return Action(Cmd.TURN_LEFT, _rate_str(rate), reason)


def turn_right(rate: float, reason: str = "") -> Action:
    return Action(Cmd.TURN_RIGHT, _rate_str(rate), reason)


def set_attack_value(value: float, reason: str = "") -> Action:
    """攻击强度。细则：数值字符串，不得为负数。"""
    safe = max(0.0, float(value))
    return Action(Cmd.SET_ATTACK_VALUE, str(int(round(safe))), reason)


def _rate_str(rate: float) -> str:
    """turnLeft/turnRight 的 data：数值字符串，合法范围 0.01~0.1。"""
    from .constants import RULE_TURN_RATE_MAX, RULE_TURN_RATE_MIN

    clamped = max(RULE_TURN_RATE_MIN, min(RULE_TURN_RATE_MAX, abs(float(rate))))
    # 保留两位小数，避免出现 0.030000000000000002 这种脏字符串
    return "{:.2f}".format(clamped)
