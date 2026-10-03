"""采集耗时计时器：按模块记录耗时并渲染成多行文本。"""

from __future__ import annotations

import time
from collections.abc import Awaitable


class CollectTimer:
    """记录每个采集模块的耗时；enabled=False 时只透传不记录。"""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled
        self._records: list[tuple[str, int]] = []
        self._start = time.perf_counter()

    async def track[T](self, name: str, coro: Awaitable[T]) -> T:
        if not self.enabled:
            return await coro
        start = time.perf_counter()
        result = await coro
        elapsed = int((time.perf_counter() - start) * 1000)
        self._records.append((name, elapsed))
        return result

    def render(self) -> str:
        total = int((time.perf_counter() - self._start) * 1000)
        lines = [
            "--------MoeStatus 采集耗时--------",
            *(f"{name}: {elapsed} ms" for name, elapsed in self._records),
            f"总计: {total} ms",
            "--------------END--------------",
        ]
        return "\n".join(lines)
