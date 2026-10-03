"""体检结论：由量表与磁盘占用推出综合分、等级与一句中文结论。"""

from __future__ import annotations

from .types import Gauge, Verdict, DiskCard, VerdictLevel

_GOOD_SCORE = 60
_WARN_SCORE = 30

_TITLES: dict[VerdictLevel, str] = {
    "good": "良好",
    "warn": "注意",
    "bad": "过载",
}

_LINES: dict[VerdictLevel, str] = {
    "good": "各项都很稳，继续保持哦～",
    "warn": "有几项偏紧了，留意下高占用吧。",
    "bad": "机器快撑不住啦，赶紧减减负！",
}


def _gauge_percent(gauges: list[Gauge], key: str) -> float:
    for gauge in gauges:
        if gauge["key"].upper() == key:
            return gauge["value"] * 100
    return 0.0


def build_verdict(gauges: list[Gauge], disks: list[DiskCard]) -> Verdict:
    """压力 = max(CPU, 内存, 交换×2, 最满的磁盘)，健康分 = 100 − 压力。

    显卡不参与判定：长期跑满对显卡是常态，真正会把机器撑爆的是内存和磁盘写满。
    交换区单独乘 2：一旦真的开始吃交换，性能已经塌了。
    """
    cpu = _gauge_percent(gauges, "CPU")
    ram = _gauge_percent(gauges, "RAM")
    swap = min(_gauge_percent(gauges, "SWAP") * 2, 100.0)
    disk = max((card["value"] * 100 for card in disks), default=0.0)

    pressure = max(cpu, ram, swap, disk)
    score = round(max(0.0, 100.0 - pressure))

    if score >= _GOOD_SCORE:
        level: VerdictLevel = "good"
    elif score >= _WARN_SCORE:
        level = "warn"
    else:
        level = "bad"
    return Verdict(level=level, title=_TITLES[level], line=_LINES[level], score=score)
