"""磁盘容量卡与磁盘 IO 速度行采集。"""

from __future__ import annotations

import asyncio

import psutil

from .types import DiskCard, DiskIoRow
from .utils import clamp_ratio, format_rate, judge_level, format_bytes
from .monitor import monitor


def _collect_disks() -> list[DiskCard]:
    cards: list[DiskCard] = []
    seen: set[tuple[int, int, int, int]] = set()
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except (psutil.Error, OSError):
            continue
        if usage.total <= 0:
            continue
        # 同一块盘会被挂载多次（bind / overlay），按容量指纹去重
        key = (int(usage.total), int(usage.used), int(usage.free), round(float(usage.percent)))
        if key in seen:
            continue
        seen.add(key)
        level_value = clamp_ratio(float(usage.percent) / 100)
        mount = f"{part.mountpoint}（根目录）" if part.mountpoint == "/" else part.mountpoint
        cards.append(
            DiskCard(
                mount=mount,
                fstype=part.fstype,
                used=format_bytes(float(usage.used)),
                total=format_bytes(float(usage.total)),
                free=format_bytes(float(usage.free)),
                value=level_value,
                text=f"{round(float(usage.percent))}%",
                level=judge_level(level_value),
            )
        )
    return cards


async def build_disks() -> list[DiskCard]:
    return await asyncio.to_thread(_collect_disks)


async def build_disk_io() -> list[DiskIoRow]:
    """磁盘 IO 速度来自 monitor 的最近一次采样，没采样过就是空列表。"""
    sample = monitor.disk_io
    if sample is None:
        return []
    return [
        DiskIoRow(
            name=sample["name"],
            read=format_rate(sample["read"]),
            write=format_rate(sample["write"]),
            total=format_rate(sample["total"]),
        )
    ]
