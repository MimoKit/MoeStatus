"""按配置 gauge_list 采集 CPU / RAM / SWAP / GPU / Python 量表。"""

from __future__ import annotations

import os
import re
import asyncio

import psutil

from .types import Gauge
from .utils import clamp_ratio, judge_level, format_bytes
from ..moestatus_config import cfg_list

_LABELS: dict[str, str] = {
    "CPU": "处理器",
    "RAM": "内存",
    "SWAP": "交换",
    "GPU": "显卡",
    "PYTHON": "进程",
}

_GPU_QUERY = "name,utilization.gpu,memory.used,memory.total,temperature.gpu"
_NUMBER_RE = re.compile(r"^-?\d+(?:\.\d+)?$")


def _parse_float(text: str) -> float | None:
    """nvidia-smi 在无传感器时返回 [N/A]，只接受纯数字形态。"""
    raw = text.strip().rstrip("%").strip()
    if not _NUMBER_RE.match(raw):
        return None
    return float(raw)


def _cpu_note() -> str:
    parts: list[str] = []
    cores = psutil.cpu_count(logical=True)
    if cores:
        parts.append(f"{cores}核")
    freq = psutil.cpu_freq()
    if freq is not None and freq.current > 0:
        parts.append(f"{freq.current / 1000:.2f}GHz")
    return " ".join(parts)


def _collect_cpu() -> tuple[float, str]:
    usage = float(psutil.cpu_percent(interval=0.3))
    return usage, _cpu_note()


async def _cpu_gauge() -> Gauge:
    usage, note = await asyncio.to_thread(_collect_cpu)
    level_value = clamp_ratio(usage / 100)
    return Gauge(
        key="CPU",
        label=_LABELS["CPU"],
        value=level_value,
        text=f"{round(usage)}%",
        note=note,
        level=judge_level(level_value),
    )


async def _ram_gauge() -> Gauge:
    mem = await asyncio.to_thread(psutil.virtual_memory)
    total = float(mem.total)
    active = float(mem.active) if hasattr(mem, "active") else float(mem.used)
    level_value = clamp_ratio(active / total) if total > 0 else 0.0
    return Gauge(
        key="RAM",
        label=_LABELS["RAM"],
        value=level_value,
        text=f"{round(level_value * 100)}%",
        note=f"已用 {format_bytes(active)} / {format_bytes(total)}",
        level=judge_level(level_value),
    )


async def _swap_gauge() -> Gauge:
    swap = await asyncio.to_thread(psutil.swap_memory)
    total = float(swap.total)
    used = float(swap.used)
    level_value = clamp_ratio(used / total) if total > 0 else 0.0
    return Gauge(
        key="SWAP",
        label=_LABELS["SWAP"],
        value=level_value,
        text=f"{round(level_value * 100)}%",
        note=f"已用 {format_bytes(used)} / {format_bytes(total)}",
        level=judge_level(level_value),
    )


async def _gpu_gauge() -> Gauge | None:
    args = [
        "nvidia-smi",
        f"--query-gpu={_GPU_QUERY}",
        "--format=csv,noheader,nounits",
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
    except (FileNotFoundError, OSError, NotImplementedError):
        return None
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=3.0)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return None
    if proc.returncode != 0:
        return None
    lines = stdout.decode(encoding="utf-8", errors="ignore").splitlines()
    if not lines:
        return None
    parts = [part.strip() for part in lines[0].split(",")]
    if len(parts) < 5:
        return None
    util = _parse_float(parts[1])
    mem_used = _parse_float(parts[2])
    mem_total = _parse_float(parts[3])
    if util is None or mem_used is None or mem_total is None:
        return None
    level_value = clamp_ratio(util / 100)
    note = f"显存 {format_bytes(mem_used * 1024 * 1024)} / {format_bytes(mem_total * 1024 * 1024)}"
    temperature = parts[4]
    if temperature and temperature != "[N/A]":
        note = f"{note} · {temperature}℃"
    return Gauge(
        key="GPU",
        label=_LABELS["GPU"],
        value=level_value,
        text=f"{round(util)}%",
        note=note,
        level=judge_level(level_value),
    )


def _collect_python() -> tuple[float, float]:
    rss = float(psutil.Process().memory_info().rss)
    used = float(psutil.virtual_memory().used)
    return rss, used


async def _python_gauge() -> Gauge:
    rss, used = await asyncio.to_thread(_collect_python)
    level_value = clamp_ratio(rss / used) if used > 0 else 0.0
    return Gauge(
        key="Python",
        label=_LABELS["PYTHON"],
        value=level_value,
        text=f"{round(level_value * 100)}%",
        note=f"PID {os.getpid()}",
        level=judge_level(level_value),
    )


async def _build_one(name: str) -> Gauge | None:
    key = name.strip().upper()
    if key == "CPU":
        return await _cpu_gauge()
    if key == "RAM":
        return await _ram_gauge()
    if key == "SWAP":
        return await _swap_gauge()
    if key == "GPU":
        return await _gpu_gauge()
    if key == "PYTHON":
        return await _python_gauge()
    return None


async def build_gauges() -> list[Gauge]:
    """按配置顺序采集量表，GPU 拿不到时不产出占位项。"""
    results = await asyncio.gather(*(_build_one(name) for name in cfg_list("gauge_list")))
    return [item for item in results if item is not None]
