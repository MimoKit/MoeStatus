# MoeStatus

<p align="center">
  <a href="https://github.com/KimigaiiWuyi/GenshinUID/"><img src="./ICON.png" width="256" height="256" alt="MoeStatus"></a>
</p>
<h1 align = "center">萌状态 MoeStatus 1.0.0</h1>
<h4 align = "center">🚧基于GsCore的系统状态出图插件，支持OneBot(QQ)、QQ频道、微信、KOOK、Telegram、飞书、DoDo、Discord🚧</h4>
<div align = "center">
        <a href="http://docs.gsuid.gbots.work/#/" target="_blank">安装文档</a>
</div>

## 丨安装提醒

> **注意：该插件为[早柚核心(gsuid_core)](https://github.com/Genshin-bots/gsuid_core)的扩展，具体安装方式可参考[GenshinUID](https://github.com/KimigaiiWuyi/GenshinUID)**
>
> **如果已经是最新版本的`gsuid_core`, 可以直接对bot发送`core安装插件MoeStatus`，然后重启core以应用安装**
>
> 出图使用Playwright + Chromium真实浏览器渲染，需要额外安装浏览器内核，见安装方式第3步

## 丨安装方式

1. 发送`core安装插件MoeStatus`
2. 安装依赖（打开**自动安装依赖功能**或者 根据包管理工具（PDM/Poetry/uv）选择执行下面一个）
   1. `pdm run python -m pip install playwright psutil httpx jinja2`
   2. `poetry run pip install playwright psutil httpx jinja2`
   3. `uv run python -m pip install playwright psutil httpx jinja2`
3. 安装`playwright`的浏览器内核
   1. `playwright install chromium`（不装的话出图会报找不到Chromium）
   2. 容器内已有`/ms-playwright/chromium-*`或已设置`PLAYWRIGHT_BROWSERS_PATH`时可跳过
   3. Chromium在非标准位置时，用环境变量`MOESTATUS_CHROMIUM_PATH`指定可执行文件
4. 发送`gs重启`应用插件

## 丨命令

强制前缀`moe` / `萌`，不允许空前缀触发。

| 命令 | 说明 |
|------|------|
| `moe状态` / `moe体检` | 出一张状态图 |
| `moe状态pro` | 全量状态图（含站点探测、进程清单） |
| `moe状态debug` | 普通状态图 + 各模块采集耗时 |
| `moe状态prodebug` | Pro + 采集耗时 |
| `moe监控` | CPU / 内存 / 网络 / 磁盘IO的历史曲线 |
| `moe原图` | **引用一条状态消息**后发送，取回未经处理的原始PNG |
| `moe帮助` | 命令说明 |

## 丨配置

| 配置项 | 说明 | 默认 |
|------|------|------|
| `renderScale` | 出图清晰度倍数，允许1~4 | `3` |
| `mascotName` | 状态图抬头和结论中的称呼 | `早柚` |
| `noPro` | 禁用`moe状态pro` | `false` |
| `avatarDownloader` | 用httpx下载Bot头像并转base64 | `false` |
| `gauge_list` | 量表项，可选`CPU`/`RAM`/`SWAP`/`GPU`/`Python` | `CPU,RAM,SWAP,GPU` |
| `siteTest_show` | 站点探测显示，`true`/`false`/`pro` | `pro` |
| `siteTest_timeout` | 单站超时(ms) | `5000` |
| `siteTest_concur` | 探测并发数 | `5` |
| `siteTest_list` | 探测站点，格式`name\|url\|useProxy` | 百度、谷歌 |
| `monitor_open` | 开启后台采样任务 | `true` |
| `monitor_interval` | 采样间隔(ms) | `60000` |
| `monitor_points` | 历史点数，超出丢弃最旧 | `60` |
| `monitor_persist` | 采样数据写入文件 | `true` |
| `proc_show` | 进程清单显示，`true`/`false`/`pro` | `pro` |
| `proc_topN` | 进程清单最多显示条数 | `6` |
| `proc_order` | 进程排序，`cpu`/`mem`/`cpu_mem` | `mem` |
| `proc_showCmd` | 显示完整命令行 | `false` |
| `proc_watch` | 关注进程名，无论排名都追加 | python等 |
| `proc_filter` | 过滤进程名，不参与统计 | System Idle Process |
| `chart_show` | 历史曲线显示，`true`/`false`/`pro` | `true` |
| `showFastFetch` | FastFetch显示，`true`/`false`/`pro`/`default` | `default` |
| `showSysInfo` | 显示系统信息 | `true` |

### 关于清晰度

状态图按900px版心排版，再按`renderScale`倍像素渲染，输出PNG。

- `renderScale`为`3`时出图约2700px宽、1.3~1.9MB；调成`2`体积减少约40%
- 输出是无损PNG，`convert_img`对bytes入参只做base64，不会二次压缩
- 截图时关闭了LCD次像素抗锯齿（截图里只会变成彩边）与字体hinting（放大后偏毛糙），并锁定sRGB

## 丨运行时路径

数据目录为`get_res_path("MoeStatus")`，即`data/MoeStatus/`：

```text
data/MoeStatus/
├── config.json          # 插件配置
├── chart_data.json      # 采样历史（monitor_persist开启时）
├── cache/               # 渲染用的临时HTML，1小时过期
└── orig_img/            # moe原图的PNG缓存，2小时过期
```

## 丨计算公式

健康分 = 100 − 压力，压力取CPU、内存、交换区×2、占用最高的磁盘四者的最大值。

- 交换区单独乘2：开始吃交换区时性能已经明显下降
- 显卡不参与计算：显卡长期满载是常态，内存和磁盘写满才会真正影响运行
- 得分 ≥60 为「良好」，30~59 为「注意」，<30 为「过载」

## 丨其他

+ 如果对本插件有功能建议&Bug报告，欢迎提Issue & Pr，每一条都会详细看过
+ 如果本插件对你有帮助，不要忘了点个Star~
+ 本项目仅供学习使用，请勿用于商业用途
+ [MIT License](./LICENSE)
