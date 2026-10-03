"""MoeStatus 数据采集层聚合入口：并发采集各区块并装配成 StatusView。"""

from __future__ import annotations

import asyncio
from datetime import datetime

from gsuid_core.logger import logger
from gsuid_core.models import Event

from .debug import CollectTimer
from .procs import build_procs
from .types import StatusView, MonitorView
from .charts import build_charts
from .gauges import build_gauges
from .botinfo import build_bots
from .monitor import monitor  # noqa: F401  导入即注册 on_core_start / on_core_shutdown 钩子
from .network import build_net, build_sites
from .storage import build_disks, build_disk_io
from .sysinfo import build_sysinfo, count_plugins, build_fastfetch
from .verdict import build_verdict
from ..moestatus_config import cfg_str

__all__ = ["CollectTimer", "build_monitor_view", "build_view"]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


async def build_view(*, is_pro: bool, is_debug: bool, ev: Event | None, timer: CollectTimer) -> StatusView:
    """并发采集各区块；每块的耗时都记进 timer，is_debug 时再落一条日志。"""
    plugin_task = asyncio.create_task(timer.track("plugin_total", count_plugins()))
    gauges_task = asyncio.create_task(timer.track("gauges", build_gauges()))
    bots_task = asyncio.create_task(timer.track("botinfo", build_bots(ev, is_pro)))
    disks_task = asyncio.create_task(timer.track("disks", build_disks()))
    disk_io_task = asyncio.create_task(timer.track("disk_io", build_disk_io()))
    net_task = asyncio.create_task(timer.track("network", build_net()))
    sites_task = asyncio.create_task(timer.track("sites", build_sites(is_pro)))
    procs_task = asyncio.create_task(timer.track("procs", build_procs(is_pro)))
    fastfetch_task = asyncio.create_task(timer.track("fastfetch", build_fastfetch(is_pro)))
    charts_task = asyncio.create_task(timer.track("charts", build_charts(is_pro)))

    plugin_total = await plugin_task
    sysinfo_task = asyncio.create_task(timer.track("sysinfo", build_sysinfo(plugin_total)))

    gauges = await gauges_task
    bots = await bots_task
    disks = await disks_task
    disk_io = await disk_io_task
    net = await net_task
    sites = await sites_task
    procs, proc_summary = await procs_task
    sysinfo = await sysinfo_task
    fastfetch = await fastfetch_task
    charts = await charts_task

    if is_debug:
        logger.debug(timer.render())

    return StatusView(
        verdict=build_verdict(gauges, disks),
        gauges=gauges,
        bots=bots,
        disks=disks,
        disk_io=disk_io,
        net=net,
        sites=sites,
        procs=procs,
        proc_summary=proc_summary,
        sysinfo=sysinfo,
        fastfetch=fastfetch,
        charts=charts,
        plugin_total=plugin_total,
        mascot_name=cfg_str("mascotName"),
        generated_at=_now(),
        is_pro=is_pro,
    )


async def build_monitor_view() -> MonitorView:
    """监控历史页：只给曲线，图表开关按 Pro 身份判定。"""
    charts = await build_charts(True)
    return MonitorView(
        charts=charts,
        mascot_name=cfg_str("mascotName"),
        generated_at=_now(),
    )
