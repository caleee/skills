---
name: redis-cli
description: Redis 访问 CLI — 复用本机 redis-cli 零依赖，口令走 REDISCLI_AUTH 不落 history；连通探测、任意命令透传、键枚举
user-invocable: true
---

# redis-cli — Redis 访问

用**零依赖**（复用系统 `redis-cli`）的方式让 agent 探连通、跑任意 Redis 命令、枚举键。

> **一句话原则**：口令**只经子进程环境变量** `REDISCLI_AUTH` 注入，不落 shell history；
> **判据来自本 skill**，连接取值**来自项目声明段**（模板见 [`TEMPLATE.md`](TEMPLATE.md)）。

## 定位与边界

- **管「访问」**：连通探测、任意命令透传、键枚举。
- **不管「编排」**：Redis 的部署 / 主从 / 集群管理归项目层或运维工具。
- **零依赖**：只调本机 `redis-cli`（需已在 `PATH`）。**不引** Python redis 客户端。
- **零项目路径假设**：本文件不出现任何具体项目路径；取值走 `AGENTS.md` 声明段 ＋ 项目根 `.redis-cli.toml`。

---

## §1 安全基线

1. **口令不落 history**：口令只经 `subprocess(env=)` 注入 `REDISCLI_AUTH`（redis-cli ≥ 5），
   **禁止**写成命令行参数（`redis-cli -a <口令>` 会进进程列表 / history）。
2. **`KEYS` 慎用**：`keys` 子命令会阻塞大库；生产环境改用 `exec SCAN <游标> MATCH <pattern>`。

---

## §2 命令面（`cli/redis-cli`）

本体 **stdlib-only**，所有命令共用一套连接取值（§3）。

| 命令 | 作用 |
|---|---|
| `ping` | 连通探测（`PONG` 即通；失败退出码 1） |
| `exec <命令...> [--db N]` | 任意 Redis 命令透传（`exec GET key` / `exec SET k v` / `exec DBSIZE`） |
| `keys <pattern> [--db N]` | 枚举匹配键（等价 `KEYS <pattern>`；大库请用 `exec SCAN`） |

**全局旗标**：`--root DIR`／`--env-file F`（可多次）／`--host/--port/--password/--db/--timeout`／`--json`。

> **旗标以 `redis-cli --help` 为准**——本表只给命令面与作用，**不复述逐条旗标**。

---

## §3 配置（判据 vs 取值分离）

- **判据**只在本 skill（本文件）。
- **取值**：项目 `AGENTS.md` 的 `## 缓存` 声明段（自然语言；**CLI 不读**）＋ 项目根
  `.redis-cli.toml`（**机器可读**；CLI 读）。

```toml
[connection]
# 可选：加载 shell 风格 .env（相对项目根）；CLI 也会读进程环境
env_file = ""
host = "127.0.0.1"
port = 6379
# password 建议留空、走环境变量或 --password，避免明文入仓
timeout = 8
db = 0            # 默认逻辑库（-n）
# 变量名覆盖（默认 REDIS_HOST / REDIS_PORT / REDIS_PASSWORD）
# password_var = "REDISCLI_AUTH"
```

**连接取值优先级（高→低）**：命令行 `--host …` → `--env-file`／进程环境 → `.redis-cli.toml [connection]`
→ 内置默认（`127.0.0.1:6379`，无口令）。项目根定位：`--root` → `REDIS_CLI_ROOT`
环境变量 → 向上查找 `.redis-cli.toml` → `.git`。

---

## §4 边界

| skill | 管什么 | 交叉点 |
|---|---|---|
| `svc-ops` | 服务起停 / 健康检查 | 起服务前的 Redis 连通预检可用 `redis-cli ping` |
| `mysql-cli` | MySQL 访问 | 同属「数据类」，连接取值各自独立 |
| `llm-wiki` | 文档知识库 | 无 |

落地检查：

1. 本 skill 无任何项目路径（取值全在声明段／`.toml`）。
2. 枚举键优先 `exec SCAN`，避免大库被 `KEYS` 阻塞。
