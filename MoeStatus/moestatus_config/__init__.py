"""MoeStatus 配置读写门面。"""

from __future__ import annotations

from typing import List

from gsuid_core.utils.plugins_config.gs_config import StringConfig

from .config_default import CONFIG_DEFAULT
from ..utils.resource import CONFIG_PATH

MOESTATUS_CONFIG = StringConfig("MoeStatus", CONFIG_PATH, CONFIG_DEFAULT)


def cfg_bool(key: str) -> bool:
    return bool(MOESTATUS_CONFIG.get_config(key).data)


def cfg_int(key: str) -> int:
    return int(MOESTATUS_CONFIG.get_config(key).data)


def cfg_str(key: str) -> str:
    return str(MOESTATUS_CONFIG.get_config(key).data)


def cfg_list(key: str) -> List[str]:
    data = MOESTATUS_CONFIG.get_config(key).data
    return list(data) if data else []


def show_allowed(flag: str, is_pro: bool) -> bool:
    """把 true / false / pro 三态配置解析成当前请求下是否展示。"""
    text = flag.strip().lower()
    if text == "true":
        return True
    if text == "pro":
        return is_pro
    return False
