# TEMPLATE — 项目声明段与配置

> 复制到项目 `AGENTS.md`（声明段）＋ 项目根 `.mysql-cli.toml`（可选配置）。

## 一、`AGENTS.md` 声明段

> **只写本 skill 独有取值**。落库分流（决策台账／计划／设计稿／时间线／环境事实）**归
> `agent-pipeline` 的 `## 工作流水线` 声明段**，本节**不重复**——两处都写＝双真源。

```markdown
## 数据库

> 判据见 `mysql-cli` skill。

- 项目库：`app`（本机 `127.0.0.1:3306`）
- 连接来源：`--env-file infra/.env.local`（变量 `MYSQL_*`）；机器可读配置 `.mysql-cli.toml`
- 写闸：仅本地库可写（`[write_gate] allow_hosts`）
- 迁移目录：`db/migration/app`（`mysql-cli migrate-check` 自检）
- 门禁：`mysql-cli migrate-check`
```

**字段含义**：这条声明段是给 **agent／人**读的**自然语言取值**；**CLI 本身不读** `AGENTS.md`
（它只读 `.mysql-cli.toml` 与命令行参数）。未声明则走内置默认（`127.0.0.1:3306`、user `root`、无口令）。

## 二、`.mysql-cli.toml`（项目根，可选）

```toml
[connection]
env_file = "infra/.env.local"   # 可选：shell 风格 .env；CLI 也会读进程环境
host = "127.0.0.1"
port = 3306
user = "root"
# password 建议留空、走环境变量或 --password，避免明文入仓
timeout = 30
# 变量名覆盖（默认 MYSQL_HOST / MYSQL_PORT / MYSQL_USER / MYSQL_PASSWORD）
# host_var = ["MT_DB_HOST", "MYSQL_HOST"]
# port_var = "MT_DB_PORT"
# user_var = "MYSQL_ROOT_USER"
# password_var = "MYSQL_ROOT_PASSWORD"

[write_gate]
# 非空时：import / script 仅允许写这些 host（其余拒绝）；留空／不写＝不设闸
allow_hosts = ["127.0.0.1", "localhost"]

[migrations]
# 库名 → 迁移目录（相对项目根）；migrate-check 无 --dir 时按此逐库自检
app = "db/migration/app"
```

## 三、最小可用步骤

```bash
mysql-cli ping                          # 探连通
mysql-cli query "SELECT 1" --db app     # 查一条
mysql-cli import db/seed app            # 预演生成的 DDL
mysql-cli import db/seed app --apply    # 确认后落库
mysql-cli migrate-check                 # 迁移 checksum 自检
```
