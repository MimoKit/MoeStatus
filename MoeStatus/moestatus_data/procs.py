"""进程负载排行与状态分布统计。"""

from __future__ import annotations

import time
import asyncio
from typing import NamedTuple

import psutil

from .types import ProcRow, ProcSummary
from .utils import format_bytes
from ..moestatus_config import cfg_int, cfg_str, cfg_bool, cfg_list, show_allowed

_SLEEPING_STATES = (psutil.STATUS_SLEEPING, psutil.STATUS_IDLE, psutil.STATUS_WAITING)
_ORDER_CPU = "cpu"
_ORDER_MEM = "mem"
_ORDER_MIXED = "cpu_mem"


class _Proc(NamedTuple):
    name: str
    display: str
    pid: int
    cpu: float
    mem: float


def _prime_cpu_percent() -> None:
    # psutil 首次 cpu_percent 恒为 0，先扫一遍预热再取差值
    for proc in psutil.process_iter(["cpu_percent"]):
        _ = proc.info


def _collect(filters: set[str], show_cmd: bool) -> tuple[list[_Proc], ProcSummary]:
    _prime_cpu_percent()
    time.sleep(0.15)
    processes: list[_Proc] = []
    running = 0
    sleeping = 0
    attrs = ["pid", "name", "cmdline", "cpu_percent", "memory_info", "status"]
    for proc in psutil.process_iter(attrs):
        try:
            info = proc.info
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        raw_name = info["name"]
        if raw_name is None:
            continue
        name = str(raw_name)
        if name in filters:
            continue
        pid = info["pid"]
        if pid is None:
            continue
        status = str(info["status"]) if info["status"] is not None else ""
        if status == psutil.STATUS_RUNNING:
            running += 1
        elif status in _SLEEPING_STATES:
            sleeping += 1
        cpu = float(info["cpu_percent"]) if info["cpu_percent"] is not None else 0.0
        memory_info = info["memory_info"]
        mem = float(memory_info.rss) if memory_info is not None else 0.0
        cmdline = info["cmdline"]
        command = " ".join(str(part) for part in cmdline) if cmdline else name
        processes.append(
            _Proc(
                name=name,
                display=command if show_cmd else name,
                pid=int(pid),
                cpu=cpu,
                mem=mem,
            )
        )
    summary = ProcSummary(total=len(processes), running=running, sleeping=sleeping)
    return processes, summary


def _extend_unique(selected: list[_Proc], chosen: set[int], items: list[_Proc]) -> None:
    for item in items:
        if item.pid in chosen:
            continue
        chosen.add(item.pid)
        selected.append(item)


def _select(processes: list[_Proc], *, order: str, top_n: int, watch: set[str]) -> list[ProcRow]:
    selected: list[_Proc] = []
    chosen: set[int] = set()
    if order == _ORDER_MIXED:
        # cpu_mem：一半按 CPU 取，一半按内存取，重复的顺延给另一侧
        cpu_n = (top_n + 1) // 2
        mem_n = max(0, top_n - cpu_n)
        _extend_unique(selected, chosen, sorted(processes, key=lambda item: item.cpu, reverse=True)[:cpu_n])
        _extend_unique(selected, chosen, sorted(processes, key=lambda item: item.mem, reverse=True)[:mem_n])
    else:
        if order == _ORDER_CPU:
            ranked = sorted(processes, key=lambda item: item.cpu, reverse=True)
        else:
            ranked = sorted(processes, key=lambda item: item.mem, reverse=True)
        _extend_unique(selected, chosen, ranked[:top_n])

    watched = [item for item in processes if item.name in watch and item.pid not in chosen]
    _extend_unique(selected, chosen, watched)

    return [
        ProcRow(
            name=item.display,
            pid=str(item.pid),
            cpu=f"{item.cpu:.1f}%",
            mem=format_bytes(item.mem),
        )
        for item in selected
    ]


async def build_procs(is_pro: bool) -> tuple[list[ProcRow], ProcSummary]:
    """返回过滤后的进程清单与总数统计；配置隐藏时给空清单与零统计。"""
    if not show_allowed(cfg_str("proc_show"), is_pro):
        return [], ProcSummary(total=0, running=0, sleeping=0)
    filters = set(cfg_list("proc_filter"))
    watch = set(cfg_list("proc_watch"))
    processes, summary = await asyncio.to_thread(_collect, filters, cfg_bool("proc_showCmd"))
    rows = _select(
        processes,
        order=cfg_str("proc_order").strip().lower(),
        top_n=max(1, cfg_int("proc_topN")),
        watch=watch,
    )
    return rows, summary
