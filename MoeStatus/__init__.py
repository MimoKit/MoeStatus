"""MoeStatus —— 可爱风服务器体检报告。"""

from gsuid_core.sv import Plugins

Plugins(
    name="MoeStatus",
    force_prefix=["moe", "萌"],
    allow_empty_prefix=False,
    alias=["moestatus"],
)
