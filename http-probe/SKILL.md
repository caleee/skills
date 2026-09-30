---
name: http-probe
description: HTTP 探测与 API 调试 CLI — 零依赖 urllib，显式超时、非 2xx 回显响应体、可选按项目响应契约解包；默认 base_url/鉴权头走项目声明段
user-invocable: true
---

# http-probe — HTTP 探测与 API 调试

用**零依赖**（标准库 `urllib`）的方式发 HTTP 请求、看响应，供 agent 调试 API、探测服务。

> **一句话原则**：**判据来自本 skill，默认 base_url 与鉴权头来自项目声明段**（[`TEMPLATE.md`](TEMPLATE.md)）；
> **非 2xx 也回显响应体**（调试要的是现场，不是「失败了」三个字）。

## 定位与边界

- **管「发请求看响应」**：任意方法、JSON 体、query 参数、鉴权头、响应契约解包。
- **不管「抓页面／渲染」**：JS 渲染抓取归 `obscura`；本 skill 只做 HTTP 层。
- **零依赖**：只用标准库 `urllib`。**不引** `requests`／`httpx`。
- **零项目路径假设**：本文件不出现任何具体项目路径；取值走 `AGENTS.md` 声明段 ＋ 项目根 `.http-probe.toml`。

---

## §1 命令面（`cli/http-probe`）

本体 **stdlib-only**，所有命令共用一套 base_url／鉴权取值（§3）。

| 命令 | 作用 |
|---|---|
| `request <METHOD> <路径>` | 任意方法（GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS） |
| `get <路径>` | `request GET` 便捷别名 |
| `post <路径>` | `request POST` 便捷别名 |

**体与参数**：`--data <json>`（JSON 体）／`--data-file <f>`（从文件读体；非 JSON 原样发送）／
`--param k=v`（query，可多次）。

**全局旗标**：`--root DIR`／`--base-url URL`／`--timeout N`／`--token T`／`--header K:V`（可多次）／
`--env-file F`（可多次）／`--json`。

> **旗标以 `http-probe --help` 为准**——本表只给命令面与作用，**不复述逐条旗标**。

---

## §2 输出与退出码

- 人读：`HTTP <状态>  <方法> <url>`，随后是响应体（JSON 美化；非 JSON 原样）。
- `--json`：`{"method","url","status","content_type","body",…}` 机器可读。
- 退出码：**2xx/3xx** → 0；**其余状态码** → 1。配了响应契约时，业务码非 success → 1。

---

## §3 配置（判据 vs 取值分离）

- **判据**只在本 skill（本文件）。
- **取值**：项目 `AGENTS.md` 的 `## 接口调试` 声明段（自然语言；**CLI 不读**）＋ 项目根
  `.http-probe.toml`（**机器可读**；CLI 读）。

```toml
[client]
base_url = "${API_BASE}"     # 支持 ${ENV} 展开（来源：env_file ／ 进程环境）
timeout = 15
env_file = ""                # 可选：shell 风格 .env

[auth]
# token = "${API_TOKEN}"                 # → Authorization: Bearer <token>
# headers = { X-Api-Key = "${API_KEY}" }  # 静态鉴权头（值支持 ${ENV} 展开）

[response]
# 可选：项目响应契约（如 Q21 风格）。配了 code_field 才启用解包。
# code_field = "code"
# success_value = 0
# data_field = "data"
```

**取值优先级（高→低）**：命令行 `--base-url`/`--token`/`--header` → `--env-file`／进程环境
→ `.http-probe.toml [client]/[auth]` → 内置默认（`http://localhost:8080`，超时 15）。项目根定位：
`--root` → `HTTP_PROBE_ROOT` 环境变量 → 向上查找 `.http-probe.toml` → `.git`。

---

## §4 安全与已知坑

1. **鉴权头不落日志**：`--token`/`[auth]` 值只进请求头；**不回显**到输出（`--json` 的 `headers`
   仅含响应头）。
2. **超时显式**：`urllib` 默认**无超时** → 一律显式传 `timeout`，避免请求挂死。
3. **非 2xx 不吞响应体**：`HTTPError` 的 body 照常读出并回显（业务错误细节在体内）。
4. **`--data` 与 `--data-file` 互斥**；`--data` 必须是合法 JSON。

---

## §5 边界

| skill | 管什么 | 交叉点 |
|---|---|---|
| `obscura` | JS 渲染抓取 / 截图 | 需渲染的页面归 obscura；纯 HTTP 归本 skill |
| `svc-ops` | 服务起停 | 服务起后用本 skill 调接口 |
| `llm-wiki` | 文档知识库 | 无 |

落地检查：

1. 本 skill 无任何项目路径（取值全在声明段／`.toml`）。
2. 写请求（POST/PUT/DELETE）前确认目标 base_url——`--base-url` 可临时覆盖。
3. 契约解包只在 `.toml` 配 `code_field` 后生效，默认按 HTTP 状态判成败。
