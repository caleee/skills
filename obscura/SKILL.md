---
name: obscura
description: 轻量隐身无头浏览器 — JS 渲染抓取、截图对比、CDP/MCP 自动化与反指纹采集
user-invocable: true
---

# obscura — 隐身无头浏览器

## 概述

Obscura 是轻量隐身无头浏览器：内嵌 V8、自有 DOM 与渲染管线，直接暴露
Chrome DevTools Protocol（CDP）工作流，无需启动 Chromium。
把**渲染**与**隐身**当作并列的一等能力：渲染负责 JS 加载后的真实页面，
隐身负责一致的浏览器指纹、反检测与 tracker 拦截。

```bash
brew install obscura
obscura --help
```

> 本 skill 改编自上游 `h4ckf0r0day/obscura` 的 `skills/obscura/SKILL.md`，
> 按本仓规范重写为 brew 安装视角；源码构建说明见 `AGENT.md` 附录。

## 触发条件

用户有以下任一需求时触发本 skill：

- 抓取需要 JS 渲染才能加载的页面（SPA、懒加载、反爬页面）
- 对抗指纹检测 / tracker（stealth 浏览、一致性指纹）
- 截图与视觉对比（viewport / 全页 / 滚动后 capture）
- 用 Puppeteer / Playwright 经 CDP 驱动浏览器自动化
- 录屏式 screencast、PDF 导出
- 经 MCP 与浏览器交互（先导航后检查/操作当前页）
- 批量提取多 URL 的文本 / markdown / 链接

## 流程

### 1. 确认安装

```bash
brew list obscura && obscura --help
```

### 2. 单页抓取（fetch）

```bash
obscura fetch https://example.com --dump text
obscura fetch https://example.com --dump markdown
obscura fetch https://example.com --dump links
obscura fetch https://example.com --eval "document.title"
obscura fetch https://example.com --screenshot page.png
obscura fetch https://example.com \
  --eval "window.scrollTo(0, document.documentElement.scrollHeight)" \
  --screenshot bottom.png
```

- `--dump` 输出形态：`html` / `text` / `links` / `markdown`；
  `original` 直通原始 HTTP 响应体（ bypass DOM/JS，用于图片、JSON、JS、CSS 等二进制或非 HTML 资源）；
  `assets` 逐行输出渲染页引用的全部子资源 URL（script / link / img / iframe / 媒体源）；
  `cookies` 以 JSON 数组导出浏览器 jar 内全部 cookie（含 `document.cookie` 拿不到的 HttpOnly，可提取反爬挑战种下的会话 token）。
- `--screenshot` 写单张 PNG，只接受单个 URL，需要 render 特性（brew 官方瓶自带）。
- 省略 `--wait` 时为自适应 settle（5 秒封顶，静默即返）；显式 `--wait N` 为固定等待 N 秒；
  `--timeout` 单位同样是秒，只约束导航阶段。
- 要看页面下半部分：先 `--eval` 执行滚动 JS，再做 viewport capture。

### 3. 批量抓取（scrape vs fetch --file）

```bash
# 多 URL 渲染/DOM 批量输出用 scrape
obscura scrape https://a.example https://b.example --format json

# fetch --file 是 raw 批量：每 URL 按 --dump original 抓取，每行一个 JSON 状态
obscura fetch --file urls.txt --concurrency 4
```

- 需要的输出是渲染后文本/DOM 且 URL 很多 → 用 `scrape`。
- 只是批量拉原始响应（每 URL 一行 JSON 状态行）→ 用 `fetch --file`（文件每行一 URL，空行与 `#` 开头跳过，`-` 表示 stdin）。
- 当输出不需要“每个 URL 一张截图”时用 `scrape`，不要逐个调 fetch 截图。

### 4. 隐身（stealth）

```bash
obscura --stealth fetch https://example.com --screenshot page.png
obscura serve --stealth --port 9222
```

- 全局 `--stealth` 适用于 `fetch` / `serve` / `scrape` / `mcp`，放子命令前后均可。
- 效果：TLS、HTTP 头、UA、navigator、WebGL 一致的浏览器指纹；抹掉
  `navigator.webdriver`；掩盖被 patch 的原生函数；拦截内置 tracker 域名列表。
- 完整传输层伪装需要 render+stealth 构建（brew 瓶行为见 `AGENT.md` 注意事项）。

### 5. 驱动 CDP（serve）

```bash
obscura serve --port 9222
```

- Puppeteer 用 `puppeteer-core`、Playwright 用 `chromium.connectOverCDP` 连上来。
- 标准 `page.screenshot()` 支持 viewport 与全页；`page.pdf()` 为光栅化 print 输出。
- 原生 CDP 用 `Page.captureScreenshot` / `Page.startScreencast` / `Page.printToPDF`；
  screencast 客户端必须对每个 `Page.screencastFrame` 回 `Page.screencastFrameAck`，
  帧由页面活动驱动，不是固定帧率的桌面录制。
- PDF 支持纸张尺寸、边距、横向、缩放、背景、页范围；**不**提供可选文本、
  tagged PDF、大纲、页眉页脚、完整 CSS paged-media 行为。

### 6. 驱动 MCP（mcp）

```bash
obscura mcp                        # stdio
obscura mcp --http --port 3000     # HTTP
```

- 先导航，再检查/操作当前页；导航、点击、滚动或框架重渲染后，
  元素引用可能失效，必须刷新 snapshot / 交互元素列表再动手。
- render 构建的 MCP 暴露 `browser_screenshot`（MCP PNG 图片）与
  `browser_pdf`（内嵌 PDF 资源）。
- MCP 不串流 screencast 帧，要录屏式采集走 CDP。

### 7. 视觉验证

1. 先用隔离该行为的**确定性 fixture**复现。
2. 再到真实站点集合测初始与滚动后两种位置；引擎对比时保持
   viewport、device scale、UA、网络输入、settle 策略、滚动、动画时间、
   capture 边界完全一致。
3. 解读 diff 前先确认双方都导航成功且产出非空图；像素指标只是回归
   tripwire，不是 verdict。
4. 按资源完成度、盒几何、换行、结构边缘、裁剪、fixed/sticky 行为逐项检查，
   把真实失败收敛为 fixture。
5. 禁止引入 hostname 特定的渲染逻辑。

### 8. 期望管理

Obscura 支持常见布局与绘制路径，但不是打包的 Chrome：
长尾 CSS、service worker、部分 Web API、原生媒体、GPU/合成器特效、
PDF 结构、平台字体光栅化都可能与 Chromium 有差异。改上游文档时保留其
既有定位与已发布 benchmark 口径；新增或更新性能/保真度数据一律用
benchmark 套件 + 对齐输入重测。

## 参数

| 子命令 | 参数 | 说明 |
|--------|------|------|
| 全局 | `--stealth` | 隐身模式，适用于 fetch/serve/scrape/mcp |
| 全局 | `--proxy <URL>` | 显式代理（自带网络栈，不自动跟随系统代理，见注意事项） |
| 全局 | `--obey-robots` | 导航前尊重 robots.txt（fetch/scrape） |
| 全局 | `--allow-private-network` | 放行 loopback/RFC1918/link-local（默认拦截，本地调试用） |
| 全局 | `--user-agent <UA>` | 覆盖 UA |
| 全局 | `--storage-dir <DIR>` | 存储目录 |
| fetch | `--dump html/text/links/markdown/original/assets/cookies` | 输出形态 |
| fetch | `-e/--eval <JS>` | 抓取前/截图前执行 JS |
| fetch | `-s/--screenshot <FILE>` | 输出单张 PNG（需 render 特性） |
| fetch | `--selector <SEL>` | 限定选择器 |
| fetch | `--wait <秒>` | 省略=自适应 settle（5s 封顶）；显式=固定等待 |
| fetch | `--timeout <秒>` | 导航超时（默认 30） |
| fetch | `--file <FILE>/-` + `--concurrency <N>` | raw 批量模式（默认并发 1） |
| fetch | `-o/--output <FILE>`、`-q/--quiet` | 输出到文件 / 静默 |
| scrape | `[URLS]...`、`--format`（默认 json） | 多 URL 渲染批量输出 |
| scrape | `-e/--eval`、`--concurrency <N>`（默认 10）、`--timeout`（默认 60） | 批量执行控制 |
| serve | `-p/--port`（默认 9222）、`--host`（默认 127.0.0.1） | 监听地址 |
| serve | `--workers`（默认 1）、`--max-connections`（默认 128） | 并发上限（超限连 503 拒绝而非排队） |
| serve | `--allow-file-access` | 允许 CDP 端导航 `file://`（默认关，仅可信网络+本地 HTML 测试开） |
| mcp | `--http`、`--host`（默认 127.0.0.1）、`--port`（默认 3000） | stdio / HTTP 两种形态 |

## 注意事项

- 默认拦截私网地址（SSRF fix）：`http://localhost:N` / `192.168.x.y` 等抓取需加
  `--allow-private-network`（或 `OBSCURA_ALLOW_PRIVATE_NETWORK=1`，前者按进程生效，管道中也有效）。
- 代理环境必须显式传 `--proxy`：Obscura 自带网络栈，不自动跟随系统/TUN 代理。
- 版本号以 `brew info obscura` 为准：`obscura --version` 的输出可能滞后于瓶版本。
- `page.pdf()` / `browser_pdf` 均为光栅输出，无可选文本；要文本走 `--dump text`。
- 各子命令完整参数以 `obscura <serve|fetch|scrape|mcp> --help` 为准。
