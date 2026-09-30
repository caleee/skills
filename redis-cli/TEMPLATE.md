# TEMPLATE — 项目声明段与配置

> 复制到项目 `AGENTS.md`（声明段）＋ 项目根 `.redis-cli.toml`（可选配置）。

## 一、`AGENTS.md` 声明段

> **只写本 skill 独有取值**。落库分流（决策台账／计划／设计稿／时间线／环境事实）**归
> `agent-pipeline` 的 `## 工作流水线` 声明段**，本节**不重复**——两处都写＝双真源。

```markdown
## 缓存

> 判据见 `redis-cli` skill。

- 项目缓存：本机 `127.0.0.1:6379`（逻辑库 0）
- 连接来源：`--env-file infra/.env.local`（变量 `REDIS_*`）；机器可读配置 `.redis-cli.toml`
- 门禁：`redis-cli ping`
```

**字段含义**：这条声明段是给 **agent／人**读的**自然语言取值**；**CLI 本身不读** `AGENTS.md`
（它只读 `.redis-cli.toml` 与命令行参数）。未声明则走内置默认（`127.0.0.1:6379`、无口令）。

## 二、`.redis-cli.toml`（项目根，可选）

```toml
[connection]
env_file = "infra/.env.local"   # 可选：shell 风格 .env；CLI 也会读进程环境
host = "127.0.0.1"
port = 6379
# password 建议留空、走环境变量或 --password，避免明文入仓
timeout = 8
db = 0
# 变量名覆盖（默认 REDIS_HOST / REDIS_PORT / REDIS_PASSWORD）
# password_var = "REDISCLI_AUTH"
```

## 三、最小可用步骤

```bash
redis-cli ping                     # 探连通
redis-cli exec DBSIZE              # 跑命令
redis-cli exec SCAN 0 MATCH 'k:*'  # 枚举键（大库用 SCAN）
```
