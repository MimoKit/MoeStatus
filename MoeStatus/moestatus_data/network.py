"""网络实时速率 / 累计流量卡与站点连通性探测。"""

from __future__ import annotations

import time
import asyncio
from typing import NamedTuple

import httpx

from .types import NetCard, SiteProbe
from .utils import format_rate, format_bytes
from .monitor import monitor
from ..moestatus_config import cfg_int, cfg_str, cfg_list, show_allowed


class _Site(NamedTuple):
    name: str
    url: str
    use_proxy: bool


def _parse_sites(raw: list[str]) -> list[_Site]:
    """解析 name|url|useProxy(true/false) 形式的站点配置。"""
    sites: list[_Site] = []
    for line in raw:
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 2 or not parts[0] or not parts[1]:
            continue
        use_proxy = parts[2].lower() == "true" if len(parts) > 2 else False
        sites.append(_Site(name=parts[0], url=parts[1], use_proxy=use_proxy))
    return sites


async def _probe_site(site: _Site, timeout_ms: int) -> SiteProbe:
    start = time.perf_counter()
    try:
        # useProxy=false 时 trust_env=False，显式忽略环境变量里的代理
        async with httpx.AsyncClient(
            timeout=timeout_ms / 1000,
            follow_redirects=True,
            trust_env=site.use_proxy,
        ) as client:
            await client.get(site.url)
    except httpx.TimeoutException:
        return SiteProbe(name=site.name, ok=False, detail="超时")
    except httpx.HTTPError:
        return SiteProbe(name=site.name, ok=False, detail="失败")
    elapsed = int((time.perf_counter() - start) * 1000)
    return SiteProbe(name=site.name, ok=True, detail=f"{elapsed}ms")


async def build_net() -> NetCard:
    """实时速率与累计流量来自 monitor 的最近一次采样。"""
    sample = monitor.net
    if sample is None:
        return NetCard(down_speed="0B/s", up_speed="0B/s", down_total="0B", up_total="0B")
    return NetCard(
        down_speed=format_rate(sample["down_speed"]),
        up_speed=format_rate(sample["up_speed"]),
        down_total=format_bytes(sample["down_total"]),
        up_total=format_bytes(sample["up_total"]),
    )


async def build_sites(is_pro: bool) -> list[SiteProbe]:
    if not show_allowed(cfg_str("siteTest_show"), is_pro):
        return []
    sites = _parse_sites(cfg_list("siteTest_list"))
    if not sites:
        return []
    timeout_ms = max(1, cfg_int("siteTest_timeout"))
    semaphore = asyncio.Semaphore(max(1, cfg_int("siteTest_concur")))

    async def limited(site: _Site) -> SiteProbe:
        async with semaphore:
            return await _probe_site(site, timeout_ms)

    results = await asyncio.gather(*(limited(site) for site in sites))
    return list(results)
