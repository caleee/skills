# AGENT.md — http-probe

> 判据见 [`SKILL.md`](SKILL.md)；项目声明模板见 [`TEMPLATE.md`](TEMPLATE.md)。

## 何时用本 skill

| 场景 | 动作 |
|---|---|
| 调一个 GET 接口 | `http-probe get /api/users/1` |
| POST JSON | `http-probe post /api/users --data '{"name":"a"}'` |
| 任意方法 | `http-probe request DELETE /api/users/1` |
| 带 query | `http-probe get /api/users --param page=1 --param size=20` |
| 临时换 base_url | `http-probe --base-url http://10.0.0.5:8080 get /health` |
| 机器可读 | `http-probe --json get /health` |

## 快速开始

```bash
# 1) 建配置（项目根 .http-probe.toml，机器可读取值）
cat > .http-probe.toml <<'TOML'
[client]
base_url = "http://localhost:8080"
timeout = 15

[auth]
# token = "${API_TOKEN}"

[response]
# code_field = "code"
# success_value = 0
# data_field = "data"
TOML

# 2) 调接口
http-probe get /actuator/health
http-probe post /api/login --data '{"username":"admin","password":"x"}'
```

## 架构

```
http-probe/
├── SKILL.md      判据（零项目路径假设）
├── TEMPLATE.md   项目声明段 + .http-probe.toml 模板
├── AGENT.md      本文件（运行时指引）
├── VERSION       semver（发布用）
└── cli/http-probe CLI：单文件 stdlib-only（urllib 封装）
```

- **单文件自包含**：`cli/http-probe` 由 tenant `tzkit.http`（`ApiClient`）通用化而成。
- **配置双路径**：CLI（机器值）读 `--root`／`--base-url`／`--token`／`.http-probe.toml`；
  `AGENTS.md` 声明段**只给 agent／人读**，CLI 不读。
- **响应契约参数化**：默认按 HTTP 状态判成败；`.toml [response]` 配 `code_field` 后按项目契约解包。

## 扩展点

- **新增鉴权方式**：改 `Context.headers()`（如 cookie、自定义 scheme）。
- **改契约解包**：`Context.resp` 驱动——`code_field`/`success_value`/`data_field`。
- **body 处理**：`_build_url`（query）、`http_request`（体与超时）。

## 注意事项

- **不要**在本 skill 里写任何具体项目路径——那会立刻造成「判据 vs 取值」双真源。
- `urllib` **默认无超时**：一律显式传 timeout（已内建），别去掉。
- 非 2xx **不吞响应体**——业务错误细节常在那。
- `--token`/`[auth]` 值只发请求头、不回显。
