# TEMPLATE — 项目声明段与配置

> 复制到项目 `AGENTS.md`（声明段）＋ 项目根 `.http-probe.toml`（可选配置）。

## 一、`AGENTS.md` 声明段

> **只写本 skill 独有取值**。落库分流（决策台账／计划／设计稿／时间线／环境事实）**归
> `agent-pipeline` 的 `## 工作流水线` 声明段**，本节**不重复**——两处都写＝双真源。

```markdown
## 接口调试

> 判据见 `http-probe` skill。

- 后端 base_url：`http://localhost:8080`（机器可读配置 `.http-probe.toml`）
- 鉴权：用户通道 `Authorization: Bearer ${API_TOKEN}`
- 响应契约：`{code,message,data}`，`code == 0` 成功
- 门禁：`http-probe get /actuator/health`
```

**字段含义**：这条声明段是给 **agent／人**读的**自然语言取值**；**CLI 本身不读** `AGENTS.md`
（它只读 `.http-probe.toml` 与命令行参数）。未声明则走内置默认（`http://localhost:8080`，超时 15）。

## 二、`.http-probe.toml`（项目根，可选）

```toml
[client]
base_url = "${API_BASE}"        # 支持 ${ENV} 展开；来源 env_file / 进程环境
timeout = 15
env_file = ""                   # 可选：shell 风格 .env

[auth]
# token = "${API_TOKEN}"                          # → Authorization: Bearer <token>
# headers = { X-Api-Key = "${API_KEY}" }          # 静态鉴权头（值支持 ${ENV} 展开）

[response]
# 项目响应契约（如 Q21）。配了 code_field 才启用解包。
# code_field = "code"
# success_value = 0
# data_field = "data"
```

## 三、最小可用步骤

```bash
http-probe get /actuator/health                          # 探活
http-probe get /api/users --param page=1                 # 带 query
http-probe post /api/users --data '{"name":"alice"}'     # 带 JSON 体
http-probe --json get /actuator/health                   # 机器可读
http-probe --base-url http://10.0.0.5:8080 get /health   # 临时换 base
```
