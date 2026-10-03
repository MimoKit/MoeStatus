"""MoeStatus 出图入口。

两个渲染函数都返回 ``(发给 bot 的最终图, 未压缩的原始 PNG)``：
最终图交给 convert_img 统一处理（bytes 入参时它只做 base64，不再压缩），
原始 PNG 留给 ``moe原图`` 缓存。

``theme`` 传 None 时按配置决定；调用方若要保证同一张报告用同一套皮肤，
应先用 ``themes.pick_theme()`` 取定再显式传进来。
"""

from __future__ import annotations

from gsuid_core.utils.image.convert import convert_img

from .browser import MAX_SCALE, MIN_SCALE, DEFAULT_SCALE, screenshot, clamp_scale
from .template import render_status_page, render_monitor_page
from ..moestatus_config import cfg_int
from ..moestatus_data.types import StatusView, MonitorView


def render_scale() -> float:
    """图片清晰度倍数，读配置并夹到合法区间。"""
    value = cfg_int("renderScale")
    return clamp_scale(value if value else DEFAULT_SCALE)


async def render_status_image(view: StatusView, theme: str | None = None) -> tuple[bytes | str, bytes]:
    html_path = await render_status_page(view, theme)
    png = await screenshot(html_path, scale=render_scale())
    return await convert_img(png), png


async def render_monitor_image(view: MonitorView, theme: str | None = None) -> tuple[bytes | str, bytes]:
    html_path = await render_monitor_page(view, theme)
    png = await screenshot(html_path, scale=render_scale())
    return await convert_img(png), png


__all__ = [
    "MAX_SCALE",
    "MIN_SCALE",
    "render_monitor_image",
    "render_scale",
    "render_status_image",
]
