"""采集已连接 Bot 的展示卡数据（头像 / 昵称 / 平台 / 运行时长 / 消息与联系人）。"""

from __future__ import annotations

import time
import base64
import asyncio
from typing import TypeAlias

import httpx
import psutil

from gsuid_core.bot import _Bot
from gsuid_core.gss import gss
from gsuid_core.models import Event

from .types import BotCard
from .utils import format_duration
from ..moestatus_config import cfg_bool

# 第三方适配器字段的形态集合：递归收窄，故意不用 Any
BotProbeValue: TypeAlias = "str | int | float | list[BotProbeValue] | dict[str, BotProbeValue] | None"

_DEFAULT_NICKNAME = "GsCore Bot"
_DEFAULT_PLATFORM = "GsCore"
_DEFAULT_VERSION = "GsCore"

# 关注这些键名：不同适配器对同一语义用过不同拼写
_SELF_ID_KEYS = ("bot_self_id", "self_id")
_NICKNAME_KEYS = ("nickname", "name")
_PLATFORM_KEYS = ("platform", "bot_id")
_START_TIME_KEYS = ("start_time",)
_SENT_KEYS = ("sent_msg_cnt", "sent")
_RECV_KEYS = ("recv_msg_cnt", "recv")
_FRIEND_KEYS = ("fl", "friends")
_GROUP_KEYS = ("gl", "groups")
_MEMBER_KEYS = ("gml", "group_members")


def _probe(adapter: _Bot, name: str) -> BotProbeValue:
    """有意为之的鸭子类型探测，仅此一处。

    第三方 Bot 适配器会把 nickname / stat / fl / gl 等字段直接挂在 ``_Bot`` 上，
    核心没有统一接口，无法从类型层面描述；这里做一次存在性守卫后取值，
    返回值立刻由下面的窄化函数收敛成具体类型，Any 不向下游传播。
    """
    if not hasattr(adapter, name):
        return None
    return getattr(adapter, name)


def _probe_first(adapter: _Bot, names: tuple[str, ...]) -> BotProbeValue:
    for name in names:
        value = _probe(adapter, name)
        if value is not None:
            return value
    return None


def _as_text(value: BotProbeValue) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, int | float):
        return str(value)
    return ""


def _as_number(value: BotProbeValue, keys: tuple[str, ...]) -> float:
    if not isinstance(value, dict):
        return 0.0
    for key in keys:
        item = value[key] if key in value else None
        if isinstance(item, int | float) and not isinstance(item, bool):
            return float(item)
    return 0.0


def _as_count(value: BotProbeValue) -> int:
    if isinstance(value, list | dict):
        return len(value)
    return 0


def _as_member_count(value: BotProbeValue) -> int:
    if not isinstance(value, dict):
        return 0
    total = 0
    for item in value.values():
        if isinstance(item, list | dict):
            total += len(item)
    return total


def _version_text(value: BotProbeValue) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, dict):
        for key in ("name", "version"):
            text = _as_text(value[key]) if key in value else ""
            if text:
                return text
    return _DEFAULT_VERSION


def _system_uptime() -> float:
    try:
        return max(0.0, time.time() - psutil.boot_time())
    except (psutil.Error, OSError):
        return 0.0


async def _resolve_avatar(url: str) -> str:
    if not url:
        return ""
    if not cfg_bool("avatarDownloader") or not url.startswith("http"):
        return url
    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError:
        return url
    content_type = response.headers["content-type"] if "content-type" in response.headers else "image/jpeg"
    mime = content_type.split(";", 1)[0].strip()
    encoded = base64.b64encode(response.content).decode()
    return f"data:{mime};base64,{encoded}"


def _default_card() -> BotCard:
    return BotCard(
        nickname=_DEFAULT_NICKNAME,
        avatar="",
        platform=_DEFAULT_PLATFORM,
        version=_DEFAULT_VERSION,
        uptime="",
        sent="",
        recv="",
        friends="",
        groups="",
        members="",
    )


def _text_or(value: BotProbeValue, fallback: str) -> str:
    text = _as_text(value)
    return text if text else fallback


def _count_text(count: int) -> str:
    """数量为 0 视为未知，展示为空串而不是 0。"""
    return str(count) if count > 0 else ""


def _resolve_bots(ev: Event, is_pro: bool) -> list[_Bot]:
    active = gss.active_bot
    if not active:
        return []
    if is_pro:
        return list(active.values())
    if ev.WS_BOT_ID and ev.WS_BOT_ID in active:
        return [active[ev.WS_BOT_ID]]
    first_id = next(iter(active))
    return [active[first_id]]


async def _build_card(adapter: _Bot, ev: Event) -> BotCard:
    self_id = _text_or(_probe_first(adapter, _SELF_ID_KEYS), ev.bot_self_id)
    nickname = _text_or(_probe_first(adapter, _NICKNAME_KEYS), _DEFAULT_NICKNAME)
    platform = _text_or(_probe_first(adapter, _PLATFORM_KEYS), ev.bot_id or _DEFAULT_PLATFORM)
    version = _version_text(_probe(adapter, "version"))

    avatar_url = _as_text(_probe(adapter, "avatar"))
    if not avatar_url and self_id.isdigit():
        avatar_url = f"https://q1.qlogo.cn/g?b=qq&s=0&nk={self_id}"

    stats = _probe(adapter, "stat")
    start_time = _as_number(stats, _START_TIME_KEYS)
    if start_time <= 0:
        start_time = time.time() - await asyncio.to_thread(_system_uptime)
    sent = _as_number(stats, _SENT_KEYS)
    recv = _as_number(stats, _RECV_KEYS)

    friends = _as_count(_probe_first(adapter, _FRIEND_KEYS))
    groups = _as_count(_probe_first(adapter, _GROUP_KEYS))
    members = _as_member_count(_probe_first(adapter, _MEMBER_KEYS))

    return BotCard(
        nickname=nickname,
        avatar=await _resolve_avatar(avatar_url),
        platform=platform,
        version=version,
        uptime=format_duration(time.time() - start_time),
        sent=_count_text(int(sent)),
        recv=_count_text(int(recv)),
        friends=_count_text(friends),
        groups=_count_text(groups),
        members=_count_text(members),
    )


async def build_bots(ev: Event | None, is_pro: bool) -> list[BotCard]:
    """无 Bot 上下文（开发预览）或没有连接时回退成一张默认占位卡。"""
    if ev is None:
        return [_default_card()]
    adapters = _resolve_bots(ev, is_pro)
    if not adapters:
        return [_default_card()]
    cards: list[BotCard] = []
    for adapter in adapters:
        cards.append(await _build_card(adapter, ev))
    return cards
