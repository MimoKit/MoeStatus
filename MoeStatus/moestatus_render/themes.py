"""主题注册表：三套皮肤都能用，控制台里选一套，或者每次随机。

配置项 ``skin``：``random`` 每次出图随机挑；``a`` / ``b`` / ``c`` 固定用某一套。
"""

from __future__ import annotations

import random

from ..moestatus_config import cfg_str

RANDOM = "random"
THEMES: tuple[str, ...] = ("a", "b", "c")
THEME_LABELS: dict[str, str] = {
    "a": "纯白气泡",
    "b": "奶白便签",
    "c": "浅灰蓝云朵",
}


def theme_label(theme: str) -> str:
    return THEME_LABELS[theme]


def pick_theme() -> str:
    """配置了具体皮肤就用它；``random`` 或写了不存在的值时每次随机。"""
    configured = cfg_str("skin").strip().lower()
    if configured in THEMES:
        return configured
    return random.choice(THEMES)


def normalize_theme(theme: str | None) -> str:
    """调用方显式传入的皮肤若非法，就退回配置 / 随机。"""
    if theme is not None and theme in THEMES:
        return theme
    return pick_theme()
