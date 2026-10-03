"""Jinja2 装配层：把视图数据塞进模板，落盘成一份自包含的 HTML。"""

from __future__ import annotations

import time
import asyncio
import platform
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..version import MoeStatus_version
from ..utils.resource import VIEW_PATH, CACHE_PATH, RESOURCE_PATH
from ..moestatus_data.types import StatusView, MonitorView

_env = Environment(
    loader=FileSystemLoader(str(VIEW_PATH)),
    autoescape=select_autoescape(enabled_extensions=()),
    enable_async=False,
)

_CACHE_TTL_SECONDS = 60 * 60
_RES_URI = RESOURCE_PATH.as_uri().rstrip("/") + "/"


def _cleanup_cache_sync() -> None:
    if not CACHE_PATH.exists():
        return
    now = time.time()
    for path in CACHE_PATH.glob("*.html"):
        if now - path.stat().st_mtime > _CACHE_TTL_SECONDS:
            path.unlink(missing_ok=True)


def _write_html_sync(out: Path, html: str) -> None:
    CACHE_PATH.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    _cleanup_cache_sync()


def _base_context() -> dict[str, object]:
    return {
        "res": _RES_URI,
        "version": MoeStatus_version,
        "footer_right": f"Python {platform.python_version()} · GsCore",
    }


async def _dump_html(prefix: str, template_name: str, context: dict[str, object]) -> Path:
    template = _env.get_template(template_name)
    html = template.render(**context)
    out = CACHE_PATH / f"{prefix}_{int(time.time() * 1000)}.html"
    await asyncio.to_thread(_write_html_sync, out, html)
    return out


async def render_status_page(view: StatusView) -> Path:
    context: dict[str, object] = {**_base_context(), **view}
    return await _dump_html("status", "status.html.j2", context)


async def render_monitor_page(view: MonitorView) -> Path:
    context: dict[str, object] = {**_base_context(), **view}
    return await _dump_html("monitor", "monitor.html.j2", context)
