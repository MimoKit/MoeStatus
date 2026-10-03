"""原始出图缓存：``moe原图`` 用的未压缩 PNG，两小时过期。

convert_img 会按框架配置压缩 / 转 base64，画质有损；这里另存一份原始字节，
引用状态消息即可取回满分辨率的那张图。
"""

from __future__ import annotations

import time
import asyncio
from pathlib import Path

from .resource import ORIG_IMG_PATH

TTL_SECONDS = 2 * 60 * 60
_SUFFIX = ".png"
_STAMP_SUFFIX = ".ts"


def _safe_name(msg_id: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "_" for char in str(msg_id))


def _path_for(msg_id: str) -> Path:
    return ORIG_IMG_PATH / f"{_safe_name(msg_id)}{_SUFFIX}"


def _stamp_for(msg_id: str) -> Path:
    return ORIG_IMG_PATH / f"{_safe_name(msg_id)}{_STAMP_SUFFIX}"


def _cleanup_sync() -> None:
    if not ORIG_IMG_PATH.exists():
        return
    now = time.time()
    for stamp_path in ORIG_IMG_PATH.glob(f"*{_STAMP_SUFFIX}"):
        try:
            age = now - float(stamp_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if age <= TTL_SECONDS:
            continue
        try:
            stamp_path.unlink(missing_ok=True)
            stamp_path.with_suffix(_SUFFIX).unlink(missing_ok=True)
        except OSError:
            continue


def _save_sync(msg_ids: list[str], data: bytes) -> None:
    if not data:
        return
    ORIG_IMG_PATH.mkdir(parents=True, exist_ok=True)
    stamp = str(time.time())
    for msg_id in msg_ids:
        if not msg_id:
            continue
        _path_for(msg_id).write_bytes(data)
        _stamp_for(msg_id).write_text(stamp, encoding="utf-8")
    _cleanup_sync()


def _get_sync(msg_id: str) -> bytes | None:
    path = _path_for(msg_id)
    if not path.exists():
        return None
    stamp_path = _stamp_for(msg_id)
    if not stamp_path.exists():
        return path.read_bytes()
    try:
        age = time.time() - float(stamp_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return path.read_bytes()
    if age <= TTL_SECONDS:
        return path.read_bytes()
    try:
        path.unlink(missing_ok=True)
        stamp_path.unlink(missing_ok=True)
    except OSError:
        pass
    return None


async def save_raw_image(msg_ids: list[str], data: bytes) -> None:
    await asyncio.to_thread(_save_sync, msg_ids, data)


async def get_raw_image(msg_id: str | None) -> bytes | None:
    if not msg_id:
        return None
    return await asyncio.to_thread(_get_sync, str(msg_id))
