r"""开发预览：用假数据渲染状态页 / 趋势页，产出 PNG 供设计评审。

不改动任何业务逻辑，只走真实的 template + browser 两个模块。
用法（在 Core 的 venv 里跑）：

    $env:PLAYWRIGHT_BROWSERS_PATH = 'D:\122\bot\xiaoyu\.playwright-browsers'
    & <core-venv>\Scripts\python.exe tools\preview.py
"""

from __future__ import annotations

import sys
import math
import asyncio
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PLUGIN_ROOT.parents[1]
CORE_ROOT = WORKSPACE_ROOT / "botkj" / "gsuid_core"

sys.path.insert(0, str(CORE_ROOT))
sys.path.insert(0, str(PLUGIN_ROOT.parent))

from MoeStatus.MoeStatus.moestatus_render import render_scale  # noqa: E402
from MoeStatus.MoeStatus.moestatus_data.types import (  # noqa: E402
    Gauge,
    BotCard,
    InfoRow,
    NetCard,
    ProcRow,
    Verdict,
    DiskCard,
    DiskIoRow,
    SiteProbe,
    StatusView,
    ChartSeries,
    MonitorView,
    ProcSummary,
)
from MoeStatus.MoeStatus.moestatus_render.browser import screenshot  # noqa: E402
from MoeStatus.MoeStatus.moestatus_render.template import (  # noqa: E402
    render_status_page,
    render_monitor_page,
)

OUT = PLUGIN_ROOT / "preview"


def _series(name: str, unit: str, color: str, values: list[float], ceiling: float) -> ChartSeries:
    width, height = 100.0, 40.0
    peak = max(values) if values else 0.0
    scale = ceiling if ceiling > 0 else 1.0
    step = width / max(len(values) - 1, 1)
    points = [(i * step, height - min(v / scale, 1.0) * (height - 4) - 2) for i, v in enumerate(values)]
    line = " ".join(f"{'M' if i == 0 else 'L'}{x:.2f} {y:.2f}" for i, (x, y) in enumerate(points))
    area = f"{line} L{width:.2f} {height:.2f} L0 {height:.2f} Z"
    ticks = ["09:20", "10:05", "10:50", "11:35"]
    return ChartSeries(
        name=name,
        unit=unit,
        color=color,
        line_path=line,
        area_path=area,
        latest=f"{values[-1]:.1f}{unit}" if values else "—",
        peak=f"{peak:.1f}{unit}",
        ticks=ticks,
    )


def _wave(base: float, amp: float, n: int, phase: float = 0.0) -> list[float]:
    return [max(0.0, base + amp * math.sin(i / 2.6 + phase)) for i in range(n)]


def mock_status_view() -> StatusView:
    gauges: list[Gauge] = [
        Gauge(key="CPU", label="处理器", value=0.42, text="42%", note="16核 5.70GHz", level="low"),
        Gauge(key="RAM", label="内存", value=0.61, text="61%", note="已用 19.4G / 31.9G", level="low"),
        Gauge(key="SWAP", label="交换", value=0.06, text="6%", note="已用 1.9G / 32.0G", level="low"),
        Gauge(key="GPU", label="显卡", value=0.93, text="93%", note="显存 18.2G / 24.0G · 71℃", level="high"),
    ]
    bots: list[BotCard] = [
        BotCard(
            nickname="早柚",
            avatar="",
            platform="QQ 群聊",
            version="v0.10.5",
            uptime="3天04:12:33",
            sent="128,431",
            recv="96,208",
            friends="212",
            groups="48",
            members="13,904",
        ),
        BotCard(
            nickname="小柚备用机",
            avatar="",
            platform="Telegram",
            version="v0.10.5",
            uptime="00:41:07",
            sent="1,204",
            recv="986",
            friends="12",
            groups="3",
            members="140",
        ),
    ]
    disks: list[DiskCard] = [
        DiskCard(
            mount="/ (根目录)",
            fstype="ext4",
            used="412.6G",
            total="931.5G",
            free="518.9G",
            value=0.44,
            text="44%",
            level="low",
        ),
        DiskCard(
            mount="/data",
            fstype="xfs",
            used="1.3T",
            total="1.8T",
            free="512.4G",
            value=0.71,
            text="71%",
            level="mid",
        ),
    ]
    disk_io: list[DiskIoRow] = [
        DiskIoRow(name="nvme0n1", read="12.4M", write="3.1M", total="15.5M"),
        DiskIoRow(name="sda", read="0B", write="148K", total="148K"),
    ]
    net = NetCard(
        down_speed="2.4M",
        up_speed="318K",
        down_total="1.21T",
        up_total="88.4G",
    )
    sites: list[SiteProbe] = [
        SiteProbe(name="百度", ok=True, detail="38ms"),
        SiteProbe(name="谷歌", ok=False, detail="超时"),
        SiteProbe(name="GitHub", ok=True, detail="412ms"),
    ]
    procs: list[ProcRow] = [
        ProcRow(name="python", pid="20418", cpu="62.4%", mem="1.8G"),
        ProcRow(name="chromium", pid="9112", cpu="11.2%", mem="644.0M"),
        ProcRow(name="redis-server", pid="1042", cpu="2.4%", mem="88.1M"),
        ProcRow(name="mysqld", pid="1088", cpu="1.9%", mem="512.4M"),
        ProcRow(name="node", pid="7731", cpu="0.8%", mem="204.9M"),
        ProcRow(name="uv", pid="2210", cpu="0.4%", mem="96.2M"),
    ]
    proc_summary = ProcSummary(total=214, running=6, sleeping=201)
    sysinfo: list[InfoRow] = [
        InfoRow(key="操作系统", value="Windows 11"),
        InfoRow(key="主机名", value="ZAYOU-HOST"),
        InfoRow(key="开机时长", value="11天06:41:02"),
        InfoRow(key="插件", value="18 个"),
    ]
    fastfetch: list[InfoRow] = [
        InfoRow(key="Kernel", value="10.0.26100"),
        InfoRow(key="Shell", value="PowerShell 7.4.6"),
        InfoRow(key="Terminal", value="Windows Terminal"),
        InfoRow(key="CPU", value="AMD Ryzen 9 7950X (32) @ 5.7GHz"),
    ]
    charts: list[ChartSeries] = [
        _series("处理器占用", "%", "#7b67d4", _wave(38, 22, 42), 100),
        _series("内存占用", "%", "#f9a8c4", _wave(70, 9, 42, 1.1), 100),
        _series("下行速率", "/s", "#4fc3a1", _wave(4.2e6, 3.4e6, 42, 2.2), 9e6),
        _series("磁盘读取", "/s", "#ee9c3f", _wave(6.0e6, 5.1e6, 42, 0.6), 1.4e7),
    ]
    verdict = Verdict(
        level="warn",
        title="注意",
        line="有指标跑到高位了，盯着点，别让它继续涨。",
        score=29,
    )
    return StatusView(
        verdict=verdict,
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
        plugin_total=18,
        mascot_name="早柚",
        generated_at="2026-10-03 11:42:07",
        is_pro=True,
    )


def mock_monitor_view() -> MonitorView:
    charts: list[ChartSeries] = [
        _series("处理器占用", "%", "#7b67d4", _wave(38, 22, 60), 100),
        _series("内存占用", "%", "#f9a8c4", _wave(70, 9, 60, 1.1), 100),
        _series("下行速率", "/s", "#4fc3a1", _wave(4.2e6, 3.4e6, 60, 2.2), 9e6),
        _series("上行速率", "/s", "#7b67d4", _wave(0.9e6, 0.8e6, 60, 0.4), 2e6),
        _series("磁盘读取", "/s", "#ee9c3f", _wave(6.0e6, 5.1e6, 60, 0.6), 1.4e7),
        _series("磁盘写入", "/s", "#4fc3a1", _wave(2.4e6, 2.1e6, 60, 1.7), 6e6),
    ]
    return MonitorView(charts=charts, mascot_name="早柚", generated_at="2026-10-03 11:42:07")


async def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    scale = render_scale()
    print(f"渲染倍率: {scale}x")

    status_html = await render_status_page(mock_status_view())
    (OUT / "status.html").write_bytes(status_html.read_bytes())
    (OUT / "mock-status.png").write_bytes(await screenshot(status_html, scale=scale))
    print("[ok] mock-status.png")

    monitor_html = await render_monitor_page(mock_monitor_view())
    (OUT / "monitor.html").write_bytes(monitor_html.read_bytes())
    (OUT / "mock-monitor.png").write_bytes(await screenshot(monitor_html, scale=scale))
    print("[ok] mock-monitor.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
