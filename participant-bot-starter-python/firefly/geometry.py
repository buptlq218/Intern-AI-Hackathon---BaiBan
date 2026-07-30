"""零依赖 2D 几何工具：向量、OBB、凸多边形 SAT、点到多边形距离、轨迹外推。

现场不装任何三方库，避免 pip 失败卡住 Loop。全部纯 Python + math。

约定：
*   多边形一律是「顶点按序排列的凸多边形」，与细则 §4.2 一致
    （凹形物体已被物理引擎拆成多个凸块，所以每个凸块都可以直接做 SAT）。
*   角度 rad，屏幕坐标系（y 向下），因此 ``angle`` 增大方向由引擎决定，
    我们只用相对量（航向误差），不假设正负号对应视觉上的顺/逆时针。
"""

from __future__ import annotations

import math
from typing import Iterable, List, Optional, Sequence, Tuple

Point = Tuple[float, float]
Polygon = Sequence[Point]

TAU = math.pi * 2.0


# ---------------------------------------------------------------------------
# 向量
# ---------------------------------------------------------------------------

def add(a: Point, b: Point) -> Point:
    return (a[0] + b[0], a[1] + b[1])


def sub(a: Point, b: Point) -> Point:
    return (a[0] - b[0], a[1] - b[1])


def scale(a: Point, k: float) -> Point:
    return (a[0] * k, a[1] * k)


def dot(a: Point, b: Point) -> float:
    return a[0] * b[0] + a[1] * b[1]


def length(a: Point) -> float:
    return math.hypot(a[0], a[1])


def distance(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def normalize(a: Point) -> Point:
    n = length(a)
    if n < 1e-9:
        return (0.0, 0.0)
    return (a[0] / n, a[1] / n)


def normalize_angle(theta: float) -> float:
    """把角度归一化到 (-pi, pi]，用于计算最短转向方向。"""
    theta = math.fmod(theta, TAU)
    if theta <= -math.pi:
        theta += TAU
    elif theta > math.pi:
        theta -= TAU
    return theta


def bearing(frm: Point, to: Point) -> float:
    """从 frm 指向 to 的方位角。"""
    d = sub(to, frm)
    return math.atan2(d[1], d[0])


def heading_error(current_angle: float, frm: Point, to: Point) -> float:
    """当前朝向与「指向目标」之间的最短角差，正负号表示需要往哪边转。

    调用方用 ``dirState`` / 实测来确定正号对应 turnLeft 还是 turnRight——
    见 firefly/control.py 里的 ``TURN_SIGN`` 标定开关。
    """
    return normalize_angle(bearing(frm, to) - current_angle)


# ---------------------------------------------------------------------------
# OBB（精灵外形）
# ---------------------------------------------------------------------------

def obb_corners(center: Point, width: float, height: float, angle: float) -> List[Point]:
    """精灵的有向包围盒四角。细则要求把精灵当凸多边形而不是单点。"""
    hw, hh = width / 2.0, height / 2.0
    ca, sa = math.cos(angle), math.sin(angle)
    out: List[Point] = []
    for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)):
        out.append((center[0] + dx * ca - dy * sa, center[1] + dx * sa + dy * ca))
    return out


def bounding_radius(width: float, height: float) -> float:
    """外接圆半径，用于快速粗筛。"""
    return math.hypot(width, height) / 2.0


# ---------------------------------------------------------------------------
# SAT：凸多边形相交判定
# ---------------------------------------------------------------------------

def _axes(poly: Polygon) -> Iterable[Point]:
    n = len(poly)
    for i in range(n):
        edge = sub(poly[(i + 1) % n], poly[i])
        # 边的法线
        axis = normalize((-edge[1], edge[0]))
        if axis != (0.0, 0.0):
            yield axis


def _project(poly: Polygon, axis: Point) -> Tuple[float, float]:
    vals = [dot(p, axis) for p in poly]
    return min(vals), max(vals)


def sat_overlap(a: Polygon, b: Polygon) -> Optional[float]:
    """SAT 相交判定。

    返回 None 表示不相交；否则返回最小重叠深度（>=0），可用作「撞得多深」的
    严重程度指标。
    """
    if len(a) < 3 or len(b) < 3:
        return None
    best = float("inf")
    for axis in list(_axes(a)) + list(_axes(b)):
        amin, amax = _project(a, axis)
        bmin, bmax = _project(b, axis)
        if amax < bmin or bmax < amin:
            return None  # 找到分离轴 → 一定不相交
        best = min(best, min(amax - bmin, bmax - amin))
    return max(0.0, best)


def polygons_intersect(a: Polygon, b: Polygon) -> bool:
    return sat_overlap(a, b) is not None


# ---------------------------------------------------------------------------
# 点 / 多边形距离
# ---------------------------------------------------------------------------

def point_segment_distance(p: Point, a: Point, b: Point) -> float:
    ab = sub(b, a)
    denom = dot(ab, ab)
    if denom < 1e-9:
        return distance(p, a)
    t = max(0.0, min(1.0, dot(sub(p, a), ab) / denom))
    proj = add(a, scale(ab, t))
    return distance(p, proj)


def point_in_polygon(p: Point, poly: Polygon) -> bool:
    """射线法。多边形是凸的，但射线法对凹的也成立，便宜且够快。"""
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > p[1]) != (y2 > p[1]):
            xint = x1 + (p[1] - y1) * (x2 - x1) / (y2 - y1 + 1e-12)
            if p[0] < xint:
                inside = not inside
    return inside


def point_polygon_distance(p: Point, poly: Polygon) -> float:
    """点到多边形的距离；点在内部时返回 0。"""
    if len(poly) < 2:
        return distance(p, poly[0]) if poly else float("inf")
    if len(poly) >= 3 and point_in_polygon(p, poly):
        return 0.0
    n = len(poly)
    return min(
        point_segment_distance(p, poly[i], poly[(i + 1) % n]) for i in range(n)
    )


# ---------------------------------------------------------------------------
# 轨迹外推
# ---------------------------------------------------------------------------

def extrapolate(position: Point, velocity: Point, frames: float) -> Point:
    """匀速外推。

    ⚠️ **单位陷阱**：实时数据里的 ``velocity`` / ``speed`` 是**每帧**位移（px/frame），
    不是每秒。官方示例 ``velocity={x:4.8,y:-0.7}`` 配 ``speed:5``，在 100ms 一帧下
    对应 50px/s。所以这里第三个参数是**帧数**，不是秒数。
    秒 → 帧请用 :func:`seconds_to_frames`。把秒直接传进来会让前瞻距离缩水 10 倍，
    表现为「明明在避障却还是撞墙」。

    细则 §6 也提醒：网络延迟、多车连撞、边界修正和离散帧都会让预测偏差，
    每帧必须用真实数据纠偏，不要长期纯积分推演。所以只用于 ~1s 内的短期预测。
    """
    return (position[0] + velocity[0] * frames, position[1] + velocity[1] * frames)


def seconds_to_frames(seconds: float, frame_interval: float) -> float:
    """秒 → 帧。避免调用方手写除法时又把单位弄反。"""
    if frame_interval <= 0:
        return seconds
    return seconds / frame_interval


def closest_approach(
    pa: Point, va: Point, pb: Point, vb: Point, horizon: float
) -> Tuple[float, float]:
    """两个匀速点在 [0, horizon] 帧内的最近接近时刻与距离。

    返回 ``(frames, dist)``。``horizon`` 与返回的时刻都以**帧**为单位
    （见 :func:`extrapolate` 的单位说明）。
    """
    dp = sub(pa, pb)
    dv = sub(va, vb)
    denom = dot(dv, dv)
    if denom < 1e-9:
        return 0.0, length(dp)
    t = -dot(dp, dv) / denom
    t = max(0.0, min(horizon, t))
    at_t = sub(extrapolate(pa, va, t), extrapolate(pb, vb, t))
    return t, length(at_t)


def rebound_velocity(
    pa: Point, va: Point, pb: Point, vb: Point,
    pos_k: float, self_k: float, other_k: float,
) -> Point:
    """细则 §6 的反弹初速度模型（对 A 方）。

    vA' = pos_k * (pA - pB) + self_k * vA + other_k * vB

    细则补充：若一方速度为零，引擎会用对方运动方向的反向量补偿；这里对 vb≈0
    的情况做同样处理，让离线模拟不至于给出 0 速度的假结果。
    """
    if length(vb) < 1e-6 and length(va) > 1e-6:
        vb = scale(normalize(va), -length(va))
    return add(
        add(scale(sub(pa, pb), pos_k), scale(va, self_k)),
        scale(vb, other_k),
    )
