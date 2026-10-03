r"""生成插件图标 ICON.png（256×256），用 Playwright 渲染，保证和状态图同一套视觉。

& <core-venv>\Scripts\python.exe tools\make_icon.py
"""

from __future__ import annotations

import sys
import asyncio
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
CORE_ROOT = Path(r"D:\122\bot\xiaoyu\botkj\gsuid_core")

sys.path.insert(0, str(CORE_ROOT))
sys.path.insert(0, str(PLUGIN_ROOT.parent))

from MoeStatus.MoeStatus.moestatus_render.browser import screenshot  # noqa: E402

ICON_SVG = """
<svg viewBox="0 0 160 160" width="256" height="256" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#8f7cf0"/>
      <stop offset="100%" stop-color="#f990bd"/>
    </linearGradient>
  </defs>
  <rect width="160" height="160" rx="36" fill="url(#bg)"/>

  <path d="M80 40 C 74 24, 58 18, 46 22 C 50 38, 64 46, 80 40 Z"
        fill="#9ed996" stroke="#2e2a3b" stroke-width="4" stroke-linejoin="round"/>
  <path d="M78 39 C 68 35, 58 30, 50 24" fill="none" stroke="#2e2a3b" stroke-width="2.2"
        stroke-linecap="round" opacity=".5"/>
  <path d="M80 40 L 80 50" stroke="#2e2a3b" stroke-width="5" stroke-linecap="round"/>

  <circle cx="80" cy="104" r="50" fill="#f7eaad" stroke="#2e2a3b" stroke-width="4.5"/>
  <path d="M42 80 C 53 69, 73 65, 94 69" fill="none" stroke="#ffffff" stroke-width="7"
        stroke-linecap="round" opacity=".55"/>

  <ellipse cx="48" cy="116" rx="10" ry="7" fill="#ff9fc4" opacity=".85"/>
  <ellipse cx="112" cy="116" rx="10" ry="7" fill="#ff9fc4" opacity=".85"/>

  <path d="M58 100 q 9 -11 18 0" fill="none" stroke="#2e2a3b" stroke-width="4.4" stroke-linecap="round"/>
  <path d="M84 100 q 9 -11 18 0" fill="none" stroke="#2e2a3b" stroke-width="4.4" stroke-linecap="round"/>
  <path d="M70 122 q 10 9 20 0" fill="none" stroke="#2e2a3b" stroke-width="4" stroke-linecap="round"/>
</svg>
"""

HTML = f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
  html,body{{margin:0;padding:0;background:transparent}}
  #container{{width:256px;height:256px;overflow:hidden}}
  svg{{display:block}}
</style></head>
<body><div id="container">{ICON_SVG}</div></body></html>
"""


async def main() -> int:
    scratch = PLUGIN_ROOT / "preview"
    scratch.mkdir(parents=True, exist_ok=True)
    html_path = scratch / "icon.html"
    html_path.write_text(HTML, encoding="utf-8")
    png = await screenshot(html_path, scale=1.0)
    (PLUGIN_ROOT / "ICON.png").write_bytes(png)
    print(f"[ok] ICON.png {len(png):,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
