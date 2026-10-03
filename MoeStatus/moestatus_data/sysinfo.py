"""系统信息行与 FastFetch 行采集（插件数按插件目录一级子目录统计）。"""

from __future__ import annotations

import re
import time
import shutil
import socket
import asyncio
import platform
from pathlib import Path

import psutil

from .types import InfoRow
from .utils import format_duration
from ..moestatus_config import cfg_str, cfg_bool, show_allowed

# fastfetch 会给带颜色的转义序列，取值前先剥掉
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_FASTFETCH_TIMEOUT = 8.0
_PLUGIN_ROOT = Path(__file__).resolve().parents[3]


def _system_uptime() -> float:
    try:
        return max(0.0, time.time() - psutil.boot_time())
    except (psutil.Error, OSError):
        return 0.0


def _count_plugins() -> int:
    if not _PLUGIN_ROOT.is_dir():
        return 0
    try:
        entries = list(_PLUGIN_ROOT.iterdir())
    except OSError:
        return 0
    total = 0
    for item in entries:
        if not item.is_dir():
            continue
        if item.name.startswith(("_", ".")):
            continue
        total += 1
    return total


async def count_plugins() -> int:
    return await asyncio.to_thread(_count_plugins)


async def build_sysinfo(plugin_total: int) -> list[InfoRow]:
    if not cfg_bool("showSysInfo"):
        return []
    uptime = await asyncio.to_thread(_system_uptime)
    return [
        InfoRow(key="操作系统", value=f"{platform.system()} {platform.release()}"),
        InfoRow(key="主机名", value=socket.gethostname()),
        InfoRow(key="开机时长", value=format_duration(uptime)),
        InfoRow(key="插件数", value=str(plugin_total)),
    ]


async def build_fastfetch(is_pro: bool) -> list[InfoRow]:
    """default 表示总是尝试；找不到可执行文件或非 0 退出就返回空列表。"""
    flag = cfg_str("showFastFetch").strip().lower()
    if flag != "default" and not show_allowed(flag, is_pro):
        return []
    executable = await asyncio.to_thread(shutil.which, "fastfetch")
    if executable is None:
        return []
    try:
        proc = await asyncio.create_subprocess_exec(
            executable,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
    except (FileNotFoundError, OSError):
        return []
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=_FASTFETCH_TIMEOUT)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return []
    if proc.returncode != 0:
        return []
    text = _ANSI_RE.sub("", stdout.decode(encoding="utf-8", errors="ignore"))
    rows: list[InfoRow] = []
    for raw_line in text.splitlines():
        if ":" not in raw_line:
            continue
        key, _, value = raw_line.partition(":")
        key = key.strip()
        value = value.strip()
        if key and value:
            rows.append(InfoRow(key=key, value=value))
    return rows
