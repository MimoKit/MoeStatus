"""MoeStatus 运行时路径常量：数据、配置、缓存与内置资源。"""

from __future__ import annotations

from pathlib import Path

from gsuid_core.data_store import get_res_path

MAIN_PATH = get_res_path("MoeStatus")
CONFIG_PATH = MAIN_PATH / "config.json"
CACHE_PATH = MAIN_PATH / "cache"
ORIG_IMG_PATH = MAIN_PATH / "orig_img"
CHART_DATA_PATH = MAIN_PATH / "chart_data.json"

for _runtime_path in (CACHE_PATH, ORIG_IMG_PATH):
    _runtime_path.mkdir(parents=True, exist_ok=True)

INNER_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = Path(__file__).resolve().parents[2]
RESOURCE_PATH = INNER_ROOT / "resources"
VIEW_PATH = RESOURCE_PATH / "view"
FONT_PATH = RESOURCE_PATH / "fonts"
