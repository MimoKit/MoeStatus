"""把 MoeStatus 挂到 Core 的插件帮助一览。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from gsuid_core.sv import get_plugin_available_prefix
from gsuid_core.help.utils import register_help

_PLUGIN_ROOT = Path(__file__).resolve().parents[2]
ICON = _PLUGIN_ROOT / "ICON.png"

_prefix = get_plugin_available_prefix("MoeStatus")

register_help(
    "MoeStatus",
    f"{_prefix}状态 / {_prefix}监控 / {_prefix}原图 / {_prefix}帮助",
    Image.open(ICON),
)
