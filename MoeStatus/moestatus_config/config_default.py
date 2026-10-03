"""MoeStatus 配置项定义。"""

from __future__ import annotations

from typing import Dict

from gsuid_core.utils.plugins_config.models import (
    GSC,
    GsDivider,
    GsIntConfig,
    GsStrConfig,
    GsBoolConfig,
    GsListStrConfig,
)

CONFIG_DEFAULT: Dict[str, GSC] = {
    "Base": GsDivider("基础", "总开关"),
    "noPro": GsBoolConfig("禁用状态Pro", "开启后 moe状态pro 直接拒绝", False),
    "avatarDownloader": GsBoolConfig(
        "内置头像下载",
        "开启后用 httpx 拉取 Bot 头像并转 base64，关闭则直接把 URL 交给浏览器",
        False,
    ),
    "mascotName": GsStrConfig("吉祥物名字", "显示在体检报告抬头和结论里的称呼", "早柚"),
    "skin": GsStrConfig(
        "界面皮肤",
        "random = 每次出图随机挑一套；a = 纯白气泡；b = 奶白便签；c = 浅灰蓝云朵",
        "random",
        options=["random", "a", "b", "c"],
    ),
    "Gauges": GsDivider("体检量表", "试管量表里放哪些资源"),
    "gauge_list": GsListStrConfig(
        "量表项",
        "可选 CPU / RAM / SWAP / GPU / Python，顺序即展示顺序",
        ["CPU", "RAM", "SWAP", "GPU"],
    ),
    "Network": GsDivider("网络", "实时速率与站点连通性"),
    "siteTest_show": GsStrConfig(
        "站点探测显示",
        "true 总是显示 / false 从不显示 / pro 仅 Pro 显示",
        "pro",
        options=["true", "false", "pro"],
    ),
    "siteTest_timeout": GsIntConfig("探测超时(ms)", "单个站点超时毫秒", 5000),
    "siteTest_concur": GsIntConfig("探测并发", "同时探测的站点数", 5),
    "siteTest_list": GsListStrConfig(
        "探测站点",
        "格式 name|url|useProxy(true/false)",
        [
            "百度|https://baidu.com|false",
            "谷歌|https://google.com|true",
        ],
    ),
    "Monitor": GsDivider("监控采样", "历史曲线数据来源"),
    "monitor_open": GsBoolConfig("开启采样任务", "后台定时采集 CPU / 内存 / 网络 / 磁盘 IO", True),
    "monitor_interval": GsIntConfig("采样间隔(ms)", "默认 60000", 60000),
    "monitor_points": GsIntConfig("历史点数", "超出后丢弃最旧的点", 60),
    "monitor_persist": GsBoolConfig("持久化采样", "写入 data/MoeStatus/chart_data.json", True),
    "Process": GsDivider("进程负载", "进程清单"),
    "proc_show": GsStrConfig(
        "进程显示",
        "true 总是显示 / false 从不显示 / pro 仅 Pro 显示",
        "pro",
        options=["true", "false", "pro"],
    ),
    "proc_topN": GsIntConfig("最多显示", "按排序取前 N 个", 6),
    "proc_order": GsStrConfig(
        "排序依据",
        "cpu / mem / cpu_mem（cpu_mem 表示各取一半）",
        "mem",
        options=["cpu", "mem", "cpu_mem"],
    ),
    "proc_showCmd": GsBoolConfig("显示完整命令行", "关闭时只显示进程名", False),
    "proc_watch": GsListStrConfig(
        "关注进程",
        "精确匹配进程名，无论排名都会追加到清单末尾",
        ["python", "redis-server", "chromium", "uv"],
    ),
    "proc_filter": GsListStrConfig("过滤进程", "名单内的进程不参与统计", ["System Idle Process"]),
    "Charts": GsDivider("历史曲线", "状态图下方的趋势区"),
    "chart_show": GsStrConfig(
        "曲线显示",
        "true 总是显示 / false 从不显示 / pro 仅 Pro 显示",
        "true",
        options=["true", "false", "pro"],
    ),
    "Display": GsDivider("显示项", "其余信息块"),
    "renderScale": GsIntConfig(
        "渲染倍率",
        "出图清晰度倍数：按 3 倍像素渲染就是 3 倍分辨率，字缘不会被拉毛，"
        "发到 QQ 再压一次也还清楚。允许 1~4；嫌文件大就调到 2",
        3,
    ),
    "showFastFetch": GsStrConfig(
        "FastFetch",
        "true / false / pro / default（default 表示总是尝试，取不到就隐藏）",
        "default",
        options=["true", "false", "pro", "default"],
    ),
    "showSysInfo": GsBoolConfig("系统信息", "操作系统 / 主机名 / 开机时长 / 插件数", True),
}
