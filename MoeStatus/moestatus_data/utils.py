"""MoeStatus 数据层通用纯函数：字节 / 时长格式化与占用等级判定。"""

from __future__ import annotations

from .types import Level

_UNITS: tuple[str, ...] = ("B", "K", "M", "G", "T", "P")


def format_bytes(size: float, *, decimal_places: int = 1) -> str:
    """把字节数格式化成 12.3G / 512B 这种短文本。"""
    value = max(0.0, float(size))
    if value < 1024:
        return f"{int(value)}B"
    unit_index = 0
    while value >= 1024 and unit_index < len(_UNITS) - 1:
        value /= 1024
        unit_index += 1
    return f"{value:.{decimal_places}f}{_UNITS[unit_index]}"


def format_rate(bytes_per_sec: float) -> str:
    """把每秒字节数格式化成 1.2M/s。"""
    return f"{format_bytes(bytes_per_sec)}/s"


def format_duration(seconds: float) -> str:
    """把秒数格式化成 1天02:03:04，不足一天时省略天数。"""
    total = max(0, int(seconds))
    days, rest = divmod(total, 86400)
    hours, rest = divmod(rest, 3600)
    minutes, secs = divmod(rest, 60)
    if days:
        return f"{days}天{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def clamp_ratio(value: float) -> float:
    """把占用比例夹到 0~1，供 Gauge / DiskCard 的 value 使用。"""
    return max(0.0, min(float(value), 1.0))


def judge_level(value: float) -> Level:
    """0~1 占用比例 → low(<70%) / mid(70~89%) / high(>=90%)。"""
    percent = max(0.0, float(value)) * 100
    if percent >= 90:
        return "high"
    if percent >= 70:
        return "mid"
    return "low"
