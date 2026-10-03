"""把 monitor 的历史采样换算成预渲染好的 SVG 折线 / 面积路径。"""

from __future__ import annotations

import time
from typing import NamedTuple

from .types import ChartSeries
from .utils import format_bytes
from .monitor import CHART_KEYS, ChartKey, monitor
from ..moestatus_config import cfg_str, show_allowed

# 虚拟画布：页面按 viewBox 缩放，服务端只负责给出坐标
CANVAS_WIDTH = 100.0
CANVAS_HEIGHT = 40.0
CANVAS_PAD = 2.0
# 速率序列全为 0 时的兜底纵轴上限，避免被 0 除
_MIN_RATE_TOP = 1024.0
_TICK_COUNT = 4
_PERCENT_TOP = 100.0


class _SeriesSpec(NamedTuple):
    key: ChartKey
    name: str
    color: str
    unit: str
    percent: bool


_SERIES: tuple[_SeriesSpec, ...] = (
    _SeriesSpec(key="cpu", name="处理器占用", color="#7b67d4", unit="%", percent=True),
    _SeriesSpec(key="ram", name="内存占用", color="#f9a8c4", unit="%", percent=True),
    _SeriesSpec(key="net_down", name="下行速率", color="#4fc3a1", unit="/s", percent=False),
    _SeriesSpec(key="net_up", name="上行速率", color="#4aa8d8", unit="/s", percent=False),
    _SeriesSpec(key="disk_read", name="磁盘读取", color="#ee9c3f", unit="/s", percent=False),
    _SeriesSpec(key="disk_write", name="磁盘写入", color="#e9607f", unit="/s", percent=False),
)


def _num(value: float) -> str:
    """SVG 坐标只保留两位且不留多余的 0。"""
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text if text else "0"


def _format_value(value: float, percent: bool) -> str:
    if percent:
        return f"{value:.1f}%"
    return f"{format_bytes(value)}/s"


def _nice_ceiling(value: float) -> float:
    """把峰值抬到一个好看的刻度，避免曲线永远顶满画布。"""
    if value <= 0:
        return _MIN_RATE_TOP
    magnitude = 10.0 ** (len(str(int(value))) - 1)
    for factor in (1.0, 2.0, 5.0, 10.0):
        candidate = magnitude * factor
        if value <= candidate:
            return candidate
    return magnitude * 10.0


def _build_ticks(stamps: list[float]) -> list[str]:
    """x 轴取 3~4 个时间标签，形如 HH:MM；点太少时按实际点数退化。"""
    total = len(stamps)
    if total <= _TICK_COUNT:
        indexes = list(range(total))
    else:
        step = (total - 1) / (_TICK_COUNT - 1)
        indexes = [round(step * index) for index in range(_TICK_COUNT)]
    labels: list[str] = []
    for index in indexes:
        label = time.strftime("%H:%M", time.localtime(stamps[index] / 1000))
        if label not in labels:
            labels.append(label)
    return labels


def _build_series(spec: _SeriesSpec) -> ChartSeries | None:
    points = monitor.chart_data[spec.key]
    if len(points) < 2:
        return None

    stamps = [point[0] for point in points]
    values = [point[1] for point in points]
    peak_value = max(values)
    ceiling = _PERCENT_TOP if spec.percent else _nice_ceiling(peak_value)

    span = CANVAS_HEIGHT - CANVAS_PAD * 2
    step = CANVAS_WIDTH / (len(values) - 1)
    coords: list[tuple[float, float]] = []
    for index, value in enumerate(values):
        ratio = min(max(value, 0.0), ceiling) / ceiling
        coords.append((index * step, CANVAS_HEIGHT - CANVAS_PAD - ratio * span))

    line_path = " ".join(f"{'M' if index == 0 else 'L'}{_num(x)} {_num(y)}" for index, (x, y) in enumerate(coords))
    area_path = f"{line_path} L{_num(CANVAS_WIDTH)} {_num(CANVAS_HEIGHT)} L0 {_num(CANVAS_HEIGHT)} Z"

    return ChartSeries(
        name=spec.name,
        unit=spec.unit,
        color=spec.color,
        line_path=line_path,
        area_path=area_path,
        latest=_format_value(values[-1], spec.percent),
        peak=_format_value(peak_value, spec.percent),
        ticks=_build_ticks(stamps),
    )


def has_sampled_data() -> bool:
    """是否已经攒够可以画线的数据。"""
    return any(len(monitor.chart_data[key]) >= 2 for key in CHART_KEYS)


async def build_charts(is_pro: bool) -> list[ChartSeries]:
    if not show_allowed(cfg_str("chart_show"), is_pro):
        return []
    charts: list[ChartSeries] = []
    for spec in _SERIES:
        item = _build_series(spec)
        if item is not None:
            charts.append(item)
    return charts
