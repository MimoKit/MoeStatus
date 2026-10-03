"""MoeStatus 后台采样任务：CPU / 内存 / 网络 / 磁盘 IO 历史，带文件持久化。"""

from __future__ import annotations

import json
import math
import time
import asyncio
from typing import Literal, TypedDict

import psutil

from gsuid_core.logger import logger
from gsuid_core.server import on_core_start, on_core_shutdown

from ..utils.resource import CHART_DATA_PATH
from ..moestatus_config import cfg_int, cfg_bool

ChartKey = Literal["cpu", "ram", "net_down", "net_up", "disk_read", "disk_write"]

CHART_KEYS: tuple[ChartKey, ...] = ("cpu", "ram", "net_down", "net_up", "disk_read", "disk_write")

# 上限保护：坏掉的持久化文件不允许把采样点时间戳 / 间隔撑到离谱
_MAX_TIMESTAMP_MS = 4_102_444_800_000.0
_MAX_INTERVAL_MS = 3_600_000


class ChartStore(TypedDict):
    """历史采样序列，每条形如 [[毫秒时间戳, 数值], ...]。"""

    cpu: list[list[float]]
    ram: list[list[float]]
    net_down: list[list[float]]
    net_up: list[list[float]]
    disk_read: list[list[float]]
    disk_write: list[list[float]]


class NetSample(TypedDict):
    """最近一次网络采样：速率(字节/秒) 与累计流量(字节)。"""

    down_speed: float
    up_speed: float
    down_total: float
    up_total: float


class DiskIoSample(TypedDict):
    """最近一次磁盘 IO 采样，速度单位字节/秒。"""

    name: str
    read: float
    write: float
    total: float


def empty_chart_store() -> ChartStore:
    return ChartStore(
        cpu=[],
        ram=[],
        net_down=[],
        net_up=[],
        disk_read=[],
        disk_write=[],
    )


def _parse_points(raw: object) -> list[list[float]]:
    """校验来自磁盘的采样点，坏点直接丢弃而不是抛异常。"""
    if not isinstance(raw, list):
        return []
    points: list[list[float]] = []
    for item in raw:
        if not isinstance(item, list) or len(item) != 2:
            continue
        stamp = item[0]
        value = item[1]
        if isinstance(stamp, bool) or isinstance(value, bool):
            continue
        if not isinstance(stamp, int | float) or not isinstance(value, int | float):
            continue
        stamp_f = float(stamp)
        value_f = float(value)
        if not math.isfinite(stamp_f) or not math.isfinite(value_f):
            continue
        if not 0 < stamp_f < _MAX_TIMESTAMP_MS or value_f < 0:
            continue
        points.append([stamp_f, value_f])
    return points


def _parse_store(raw: object) -> ChartStore:
    store = empty_chart_store()
    if not isinstance(raw, dict):
        return store
    for key in CHART_KEYS:
        store[key] = _parse_points(raw[key]) if key in raw else []
    return store


class Monitor:
    """采样器单例：charts / storage / network 从这里读取最近一次采样结果。"""

    def __init__(self) -> None:
        self.chart_data: ChartStore = empty_chart_store()
        self.net: NetSample | None = None
        self.disk_io: DiskIoSample | None = None
        self._task: asyncio.Task[None] | None = None
        self._prev_net: tuple[float, float] | None = None
        self._prev_disk: tuple[float, float] | None = None
        self._prev_ts: float | None = None

    @property
    def running(self) -> bool:
        """采样任务是否正在运行，供 core状态 汇总图查询。"""
        return self._task is not None and not self._task.done()

    def _append(self, key: ChartKey, stamp_ms: float, value: float) -> None:
        series = self.chart_data[key]
        series.append([stamp_ms, value])
        limit = max(1, cfg_int("monitor_points"))
        while len(series) > limit:
            series.pop(0)

    def _sample_cpu(self, stamp_ms: float) -> None:
        try:
            usage = psutil.cpu_percent(interval=None)
        except (psutil.Error, OSError):
            return
        self._append("cpu", stamp_ms, max(0.0, min(float(usage), 100.0)))

    def _sample_ram(self, stamp_ms: float) -> None:
        try:
            mem = psutil.virtual_memory()
        except (psutil.Error, OSError):
            return
        total = float(mem.total)
        percent = float(mem.percent)
        if hasattr(mem, "active") and total > 0:
            percent = float(mem.active) / total * 100
        self._append("ram", stamp_ms, max(0.0, min(percent, 100.0)))

    def _sample_net(self, stamp_ms: float, now: float) -> None:
        try:
            counters = psutil.net_io_counters()
        except (psutil.Error, OSError):
            return
        current = (float(counters.bytes_recv), float(counters.bytes_sent))
        previous = self._prev_net
        elapsed = now - self._prev_ts if self._prev_ts is not None else 0.0
        self._prev_net = current
        if previous is None or elapsed <= 0:
            return
        down = max(0.0, (current[0] - previous[0]) / elapsed)
        up = max(0.0, (current[1] - previous[1]) / elapsed)
        self.net = NetSample(
            down_speed=down,
            up_speed=up,
            down_total=current[0],
            up_total=current[1],
        )
        self._append("net_down", stamp_ms, down)
        self._append("net_up", stamp_ms, up)

    def _sample_disk(self, stamp_ms: float, now: float) -> None:
        try:
            counters = psutil.disk_io_counters()
        except (psutil.Error, OSError):
            return
        if counters is None:
            return
        current = (float(counters.read_bytes), float(counters.write_bytes))
        previous = self._prev_disk
        elapsed = now - self._prev_ts if self._prev_ts is not None else 0.0
        self._prev_disk = current
        if previous is None or elapsed <= 0:
            return
        read = max(0.0, (current[0] - previous[0]) / elapsed)
        write = max(0.0, (current[1] - previous[1]) / elapsed)
        self.disk_io = DiskIoSample(name="磁盘 IO", read=read, write=write, total=read + write)
        self._append("disk_read", stamp_ms, read)
        self._append("disk_write", stamp_ms, write)

    def sample_once(self) -> None:
        """同步采样一次，调用方负责放进线程池。"""
        now = time.time()
        stamp_ms = float(int(now * 1000))
        self._sample_cpu(stamp_ms)
        self._sample_ram(stamp_ms)
        self._sample_net(stamp_ms, now)
        self._sample_disk(stamp_ms, now)
        self._prev_ts = now
        self._save_to_file()

    def load_from_file(self) -> None:
        if not CHART_DATA_PATH.exists():
            return
        try:
            text = CHART_DATA_PATH.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning(f"[MoeStatus] 读取 chart_data 失败: {exc}")
            return
        try:
            raw: object = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning(f"[MoeStatus] chart_data 解析失败: {exc}")
            return
        self.chart_data = _parse_store(raw)

    def _save_to_file(self) -> None:
        if not cfg_bool("monitor_persist"):
            return
        payload = json.dumps(self.chart_data, ensure_ascii=False)
        tmp_path = CHART_DATA_PATH.with_suffix(".json.tmp")
        try:
            CHART_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
            tmp_path.write_text(payload, encoding="utf-8")
            tmp_path.replace(CHART_DATA_PATH)
        except OSError as exc:
            logger.warning(f"[MoeStatus] 写入 chart_data 失败: {exc}")

    async def _prime_cpu(self) -> None:
        # psutil 首次 cpu_percent 恒为 0，先阻塞采样一次让后续读数有意义
        try:
            await asyncio.to_thread(psutil.cpu_percent, 0.5)
        except (psutil.Error, OSError):
            return

    async def _loop(self) -> None:
        await self._prime_cpu()
        await asyncio.to_thread(self.sample_once)
        while True:
            interval_ms = cfg_int("monitor_interval")
            if not 0 < interval_ms <= _MAX_INTERVAL_MS:
                interval_ms = 60000
            await asyncio.sleep(interval_ms / 1000)
            try:
                await asyncio.to_thread(self.sample_once)
            except (psutil.Error, OSError) as exc:
                logger.warning(f"[MoeStatus] 采样失败: {exc}")

    async def start(self) -> None:
        if not cfg_bool("monitor_open"):
            logger.info("[MoeStatus] 采样任务已按配置关闭")
            return
        if self._task is not None and not self._task.done():
            return
        await asyncio.to_thread(self.load_from_file)
        self._task = asyncio.create_task(self._loop(), name="moestatus-monitor")
        logger.info("[MoeStatus] 采样任务已启动")

    async def stop(self) -> None:
        task = self._task
        self._task = None
        if task is not None and not task.done():
            task.cancel()
            try:
                await asyncio.wait_for(asyncio.gather(task, return_exceptions=True), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("[MoeStatus] 采样任务停止超时")
        await asyncio.to_thread(self._save_to_file)
        logger.info("[MoeStatus] 采样任务已停止")


monitor = Monitor()


@on_core_start
async def _start_moestatus_monitor() -> None:
    await monitor.start()


@on_core_shutdown
async def _stop_moestatus_monitor() -> None:
    await monitor.stop()
