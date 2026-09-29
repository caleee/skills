# AGENT.md — obscura

## 运行命令

```bash
# 安装与自检（brew 视角，唯一支持路径）
brew install obscura
brew list obscura && brew info obscura
obscura --help
obscura fetch --help
obscura scrape --help
obscura serve --help
obscura mcp --help

# 单页抓取
obscura fetch https://example.com --dump text
obscura fetch https://example.com --dump markdown --timeout 30
obscura fetch https://example.com --eval "document.title"
obscura fetch https://example.com --screenshot /tmp/page.png

# 批量
obscura scrape https://a.example https://b.example --format json
obscura fetch --file urls.txt --concurrency 4          # raw 批量，每 URL 一行 JSON 状态

# 隐身（全局 flag，子命令前后均可）
obscura --stealth fetch https://example.com --dump text
obscura serve --stealth --port 9222

# 本地调试（默认拦截私网地址，见注意事项）
obscura fetch http://localhost:3000/ --dump text --allow-private-network

# CDP / MCP 服务
obscura serve --port 9222                              # Puppeteer 用 puppeteer-core，Playwright 用 chromium.connectOverCDP
obscura mcp                                            # stdio
obscura mcp --http --port 3000                         # HTTP
```

## 架构

### 子命令分工

```
fetch   单 URL：渲染抓取 + 可选 eval/screenshot；--file 时切换为 raw 批量（original + JSON 状态行）
scrape  多 URL：渲染/DOM 批量输出（输出不要求 one-screenshot-per-URL 时的首选）
serve   CDP 服务器：V8 isolate 按连接隔离，--max-connections 界定线程/内存 footprint
mcp     MCP 服务器：stdio 或 HTTP，先导航后 snapshot/操作；无 screencast 串流
```

### 能力门控

| 能力 | 门控 | 说明 |
|------|------|------|
| `--screenshot` / `page.screenshot()` | render 特性 | brew 官方瓶自带 |
| `page.pdf()` / `browser_pdf` | render 特性 | 光栅 print 输出，无可选文本 |
| `browser_screenshot`（MCP PNG） | render 构建的 MCP | 同上 |
| 完整 TLS 伪装 + tracker 拦截 | render+stealth 构建 + 运行时 `--stealth` | browser 级指纹一致性 |

### fetch vs scrape 决策

- 1 个 URL，或要截图 → `fetch`。
- N 个 URL，要渲染后文本/DOM → `scrape`。
- N 个 URL，只要原始响应 + 状态行 → `fetch --file`。

## 重要文件路径

- `obscura/SKILL.md` — skill 定义（触发条件、流程、参数、注意事项，完整内容）
- `obscura.md` — 根索引（frontmatter + 指引）
- 上游原文：`https://github.com/h4ckf0r0day/obscura/blob/main/skills/obscura/SKILL.md`

## 跟进上游（扩展指南）

上游 skill 随 obscura 演进，本 skill 是其 brew 视角改编本。同步步骤：

1. 取回原文（注意：直连 raw.githubusercontent 可能被本地 TUN 的 fake-IP 段拦截，改走落盘）：
   ```bash
   curl -sL --max-time 30 -o /tmp/obscura_upstream_SKILL.md \
     https://raw.githubusercontent.com/h4ckf0r0day/obscura/main/skills/obscura/SKILL.md
   ```
2. diff 上游新增的 dump 形态 / flag / CDP-MCP 能力，同步到 `obscura/SKILL.md` 的流程与参数表。
3. 上游的 cargo 构建变体如有新增，按下面附录格式更新，**不要**搬回 SKILL.md 主体（brew 用户不需要）。
4. `description` 保持单行；改动后跑一遍根 `AGENTS.md` 完成检查清单。

### 附录：源码构建变体（仅维护者）

官方 release 归档与 Docker 镜像自带渲染；源码 checkout 才需以下命令，
日常使用忽略，命令中的二进制为 `./target/release/obscura`：

```bash
# 渲染
CARGO_INCREMENTAL=0 CARGO_BUILD_JOBS=2 cargo build --release -p obscura-cli --bins --features render
# 渲染 + 隐身（wreq/BoringSSL 传输、浏览器身份保护、tracker 拦截）
CARGO_INCREMENTAL=0 CARGO_BUILD_JOBS=2 cargo build --release -p obscura-cli --bins --features render,stealth
# 无渲染（仅 DOM/提取/CDP 自动化）
CARGO_INCREMENTAL=0 CARGO_BUILD_JOBS=2 cargo build --release -p obscura-cli --bins --no-default-features
CARGO_INCREMENTAL=0 CARGO_BUILD_JOBS=2 cargo build --release -p obscura-cli --bins --no-default-features --features stealth
```

## 注意事项

- 版本号以 `brew info obscura` 为准：实测瓶 0.2.2 的 `obscura --version` 仍报 0.1.0，
  上游版本字符串滞后，不要据此判断功能有无。
- 默认拦截私网地址（上游 SSRF fix #4）：本地 `http://localhost:N` / `192.168.x.y`
  必须加 `--allow-private-network`。
- 自带网络栈，不自动跟随系统代理/TUN：在代理环境抓公网请显式 `--proxy`。
- `--allow-file-access`（serve）默认关：CDP 端可读任意本地文件，开服于可信网络、
  仅本地 HTML 测试时才开。
- `serve` 的 `--max-connections` 超限时直接 503 拒绝，不排队；压测前先调 `--workers`。
- PDF 无可选文本/大纲/页眉页脚：要文本走 `--dump text`，不要对 PDF 做文本断言。
- 上游 benchmark 口径：改上游文档时保留其定位与已发布数据，新增数据必须用
  benchmark 套件 + 对齐输入重测（见 SKILL.md §8）。
