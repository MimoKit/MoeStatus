"""Playwright 截图层。

本插件刻意走浏览器渲染（HTML/CSS/字体/SVG），不用 PIL / pytakumi：
版式、渐变、内嵌字体和手写风排版只有完整排版引擎才做得出来。

清晰度靠 ``device_scale_factor``：CSS 仍然按 900px 版心排版，
按 N 倍像素渲染就能拿到 N 倍分辨率的位图，字缘不会被拉毛。
"""

from __future__ import annotations

import os
from pathlib import Path

from playwright.async_api import Error as PlaywrightError, async_playwright

from gsuid_core.logger import logger

VIEWPORT_WIDTH = 900
VIEWPORT_HEIGHT = 1400
DEFAULT_SCALE = 2.0
MIN_SCALE = 1.0
MAX_SCALE = 4.0

# headless 截图专用：关掉 LCD 次像素（截图里只会变成彩边），
# 关掉字体 hinting（hinting 是按像素网格对齐的，放大后会显得毛糙），
# 锁 sRGB 避免不同机器上色偏。
_LAUNCH_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--allow-file-access-from-files",
    "--font-render-hinting=none",
    "--disable-lcd-text",
    "--force-color-profile=srgb",
]


def clamp_scale(scale: float) -> float:
    return min(max(float(scale), MIN_SCALE), MAX_SCALE)


def _chromium_override() -> str | None:
    """允许用 MOESTATUS_CHROMIUM_PATH 指定一个非标准位置的 Chromium。"""
    override = os.environ.get("MOESTATUS_CHROMIUM_PATH", "").strip()
    return override or None


async def screenshot(html_path: Path, *, scale: float = DEFAULT_SCALE) -> bytes:
    executable = _chromium_override()
    device_scale = clamp_scale(scale)

    async with async_playwright() as playwright:
        try:
            if executable is None:
                browser = await playwright.chromium.launch(headless=True, args=_LAUNCH_ARGS)
            else:
                browser = await playwright.chromium.launch(
                    headless=True,
                    args=_LAUNCH_ARGS,
                    executable_path=executable,
                )
        except PlaywrightError as exc:
            raise RuntimeError("无法启动 Chromium，请先在运行 GsCore 的环境执行: playwright install chromium") from exc

        try:
            context = await browser.new_context(
                viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
                device_scale_factor=device_scale,
            )
            page = await context.new_page()
            await page.goto(html_path.as_uri(), wait_until="load", timeout=60000)
            await page.wait_for_selector("#container", timeout=15000)
            await page.evaluate("() => document.fonts.ready")
            png = await page.locator("#container").screenshot(type="png")
            await context.close()
            logger.debug(f"[MoeStatus] 渲染完成: {html_path.name} @ {device_scale}x")
            return png
        finally:
            await browser.close()
