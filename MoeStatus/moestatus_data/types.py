"""MoeStatus 视图数据契约。

模板只认这里的结构：数据层负责把真实采集结果填成这些 TypedDict，
渲染层只做搬运和拼装，不做业务判断。任何字段缺失都是 bug，不允许 `dict.get` 兜底。
"""

from __future__ import annotations

from typing import Literal, TypedDict

Level = Literal["low", "mid", "high"]
VerdictLevel = Literal["good", "warn", "bad"]


class Gauge(TypedDict):
    """一根「试管」量表。value 决定液面高度，text 是给用户看的数字。"""

    key: str
    label: str
    value: float
    text: str
    note: str
    level: Level


class BotCard(TypedDict):
    """一台已连接 Bot 的体检卡。"""

    nickname: str
    avatar: str
    platform: str
    version: str
    uptime: str
    sent: str
    recv: str
    friends: str
    groups: str
    members: str


class DiskCard(TypedDict):
    """一块磁盘的容量卡。"""

    mount: str
    fstype: str
    used: str
    total: str
    free: str
    value: float
    text: str
    level: Level


class DiskIoRow(TypedDict):
    """磁盘读写速度行。"""

    name: str
    read: str
    write: str
    total: str


class NetCard(TypedDict):
    """网络速率与累计流量。"""

    down_speed: str
    up_speed: str
    down_total: str
    up_total: str


class SiteProbe(TypedDict):
    """单个站点连通性探测结果。"""

    name: str
    ok: bool
    detail: str


class ProcRow(TypedDict):
    """一行进程负载。"""

    name: str
    pid: str
    cpu: str
    mem: str


class ProcSummary(TypedDict):
    """进程总数与状态分布。"""

    total: int
    running: int
    sleeping: int


class InfoRow(TypedDict):
    """通用键值行（系统信息 / FastFetch）。"""

    key: str
    value: str


class ChartSeries(TypedDict):
    """历史曲线：服务端预先算好 SVG 路径，页面不需要 JS 图表库。"""

    name: str
    unit: str
    color: str
    line_path: str
    area_path: str
    latest: str
    peak: str
    ticks: list[str]


class Verdict(TypedDict):
    """体检结论。level 同时决定吉祥物表情与印章颜色。"""

    level: VerdictLevel
    title: str
    line: str
    score: int


class StatusView(TypedDict):
    """整张状态图的数据。"""

    verdict: Verdict
    gauges: list[Gauge]
    bots: list[BotCard]
    disks: list[DiskCard]
    disk_io: list[DiskIoRow]
    net: NetCard
    sites: list[SiteProbe]
    procs: list[ProcRow]
    proc_summary: ProcSummary
    sysinfo: list[InfoRow]
    fastfetch: list[InfoRow]
    charts: list[ChartSeries]
    plugin_total: int
    mascot_name: str
    generated_at: str
    is_pro: bool


class MonitorView(TypedDict):
    """监控历史图页面数据。"""

    charts: list[ChartSeries]
    mascot_name: str
    generated_at: str
