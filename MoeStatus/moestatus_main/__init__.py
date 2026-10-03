"""MoeStatus 命令入口。

前缀：moe / 萌（``Plugins(force_prefix=["moe", "萌"])``），所以用户实际发送的是
``moe状态`` / ``萌状态`` 这样的形式。
"""

from __future__ import annotations

import re
import asyncio

from playwright.async_api import Error as PlaywrightError

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment

from ..moestatus_data import build_view, build_monitor_view
from ..utils.raw_cache import get_raw_image, save_raw_image
from ..moestatus_config import cfg_bool
from ..moestatus_render import render_status_image, render_monitor_image
from ..moestatus_data.debug import CollectTimer
from ..moestatus_render.themes import pick_theme, theme_label

sv = SV("萌状态", pm=6, priority=5, area="ALL")

# 同一时刻只允许一张图在渲染，Chromium 很吃内存
_render_lock = asyncio.Lock()
_STATE_RE = re.compile(r"^(?:状态|体检)(pro)?(debug)?$")
_STATE_COMMANDS = (
    "状态",
    "状态pro",
    "状态debug",
    "状态prodebug",
    "体检",
    "体检pro",
    "体检debug",
    "体检prodebug",
)

# 渲染链路里可能抛出的外部异常：磁盘 / 浏览器 / 超时 / 数据形态。
# 单次出图失败只回一句提示，不能把异常抛回 Core 的事件循环。
_RENDER_ERRORS = (OSError, RuntimeError, ValueError, TimeoutError, PlaywrightError)


@sv.on_fullmatch(_STATE_COMMANDS, block=True)
async def handle_state(bot: Bot, ev: Event) -> None:
    matched = _STATE_RE.match((ev.command or "").strip())
    if matched is None:
        return
    is_pro = bool(matched.group(1))
    is_debug = bool(matched.group(2))

    if is_pro and cfg_bool("noPro"):
        await bot.send("状态Pro 已经被主人关掉了")
        return

    if _render_lock.locked():
        await bot.send("上一张体检报告还在画，稍等一下下～")
        return

    async with _render_lock:
        timer = CollectTimer(is_debug)
        # 皮肤在进入渲染前定下来，保证同一张报告只用一套
        theme = pick_theme()
        try:
            view = await build_view(is_pro=is_pro, is_debug=is_debug, ev=ev, timer=timer)
            image, raw = await render_status_image(view, theme)
            msg_ids = await bot.send(MessageSegment.image(image), wait_recall=True)
        except _RENDER_ERRORS as exc:
            logger.exception(f"[MoeStatus] 状态图生成失败: {exc}")
            await bot.send("体检报告没画出来，看看后台日志吧")
            return

        if is_debug:
            await bot.send(f"{timer.render()}\n皮肤: {theme_label(theme)}")

        recall_ids = [ev.msg_id]
        if msg_ids:
            recall_ids.extend(str(item) for item in msg_ids)
        await save_raw_image(recall_ids, raw)


@sv.on_fullmatch("监控", block=True)
async def handle_monitor(bot: Bot, ev: Event) -> None:
    try:
        view = await build_monitor_view()
        image, _ = await render_monitor_image(view, pick_theme())
    except _RENDER_ERRORS as exc:
        logger.exception(f"[MoeStatus] 趋势图生成失败: {exc}")
        await bot.send("趋势图没画出来，看看后台日志吧")
        return
    await bot.send(MessageSegment.image(image))


@sv.on_fullmatch("原图", block=True)
async def handle_raw(bot: Bot, ev: Event) -> None:
    """引用一条状态消息后发送，取回未压缩的原始 PNG。"""
    raw = await get_raw_image(ev.reply or "")
    if raw is None:
        await bot.send("没找到这张图，或者已经过期了（只保留两小时）")
        return
    await bot.send(MessageSegment.image(raw))


@sv.on_fullmatch("帮助", block=True)
async def handle_help(bot: Bot, ev: Event) -> None:
    await bot.send(
        "萌状态 · 早柚体检所\n"
        "moe状态 / moe体检 —— 出一张体检报告\n"
        "moe状态pro —— 全量体检（含站点探测、进程清单）\n"
        "moe状态debug —— 附带各模块采集耗时\n"
        "moe监控 —— CPU / 内存 / 网络 / 磁盘的历史曲线\n"
        "moe原图 —— 引用状态消息，取回未压缩原图\n"
        "moe帮助 —— 这份说明\n"
        "皮肤有三套（纯白气泡 / 奶白便签 / 浅灰蓝云朵），在控制台"
        "「MoeStatus → 界面皮肤」里选，默认每次随机。"
    )
