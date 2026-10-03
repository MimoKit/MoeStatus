"""把采样点数与采样任务状态挂到 Core 的 ``core状态`` 汇总图。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from gsuid_core.status.plugin_status import register_status

from ..moestatus_data.monitor import monitor

_PLUGIN_ROOT = Path(__file__).resolve().parents[2]


async def _sample_points() -> int:
    return len(monitor.chart_data["cpu"])


async def _monitor_state() -> str:
    return "开" if monitor.running else "关"


register_status(
    Image.open(_PLUGIN_ROOT / "ICON.png"),
    "MoeStatus",
    {
        "采样点数": _sample_points,
        "采样任务": _monitor_state,
    },
)
