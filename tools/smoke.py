r"""真实数据链路冒烟测试：build_view → 渲染 → 出图。

& <core-venv>\Scripts\python.exe tools\smoke.py
"""

from __future__ import annotations

import sys
import asyncio
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
CORE_ROOT = Path(r"D:\122\bot\xiaoyu\botkj\gsuid_core")

sys.path.insert(0, str(CORE_ROOT))
sys.path.insert(0, str(PLUGIN_ROOT.parent))

from MoeStatus.MoeStatus.moestatus_data import build_view, build_monitor_view  # noqa: E402
from MoeStatus.MoeStatus.moestatus_render import render_scale  # noqa: E402
from MoeStatus.MoeStatus.moestatus_data.debug import CollectTimer  # noqa: E402
from MoeStatus.MoeStatus.moestatus_render.browser import screenshot  # noqa: E402
from MoeStatus.MoeStatus.moestatus_render.template import (  # noqa: E402
    render_status_page,
    render_monitor_page,
)


async def main() -> int:
    out = PLUGIN_ROOT / "preview"
    out.mkdir(parents=True, exist_ok=True)

    timer = CollectTimer(True)
    view = await build_view(is_pro=True, is_debug=False, ev=None, timer=timer)

    print(timer.render())
    print()
    print("verdict     :", dict(view["verdict"]))
    print("gauges      :", [(g["key"], g["text"], g["level"], g["note"]) for g in view["gauges"]])
    print("bots        :", [(b["nickname"], b["platform"], b["uptime"]) for b in view["bots"]])
    print("disks       :", [(d["mount"], d["text"]) for d in view["disks"]])
    print("disk_io     :", view["disk_io"])
    print("net         :", dict(view["net"]))
    print("sites       :", view["sites"])
    print("procs       :", len(view["procs"]), dict(view["proc_summary"]))
    print("sysinfo     :", view["sysinfo"])
    print("fastfetch   :", len(view["fastfetch"]), "行")
    print("charts      :", [(c["name"], c["latest"], c["peak"]) for c in view["charts"]])
    print("mascot_name :", view["mascot_name"])
    print("generated_at:", view["generated_at"])

    monitor_view = await build_monitor_view()
    scale = render_scale()
    print(f"\n渲染倍率: {scale}x")

    html = await render_status_page(view)
    (out / "real-status.html").write_bytes(html.read_bytes())
    (out / "real-status.png").write_bytes(await screenshot(html, scale=scale))
    print("[ok] real-status.png")

    monitor_html = await render_monitor_page(monitor_view)
    (out / "real-monitor.png").write_bytes(await screenshot(monitor_html, scale=scale))
    print("[ok] real-monitor.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
