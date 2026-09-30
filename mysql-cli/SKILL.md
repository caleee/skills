---
name: mysql-cli
description: MySQL 访问与管理 CLI — 复用本机 mysql/mysqldump 零依赖，口令走 MYSQL_PWD 不落 history；连通性/查询/脚本/表清单/采样/备份/批量导入（由 INSERT 推断建表 DDL）/Flyway checksum 自检
user-invocable: true
---

# mysql-cli — MySQL 访问与管理

用**零依赖**（复用系统 `mysql` / `mysqldump`）的方式让 agent 连库、查数、导入、备份，
并复算 Flyway 迁移 checksum。

> **一句话原则**：口令**只经子进程环境变量**注入，不落 shell history；**判据来自本 skill**，
> 连接取值与迁移目录**来自项目声明段**（模板见 [`TEMPLATE.md`](TEMPLATE.md)）。

## 定位与边界

- **管「访问与搬运」**：连通探测、单条/脚本 SQL、表清单、采样、导出、批量导入、迁移 checksum 自检。
- **不管「编排与建库策略」**：服务起停、库的 provisioning、多环境切换归项目层（如 `svc-ops`／工程脚本）。
- **零依赖**：只调本机 `mysql` / `mysqldump`（需已在 `PATH`）。**不引** Python 数据库驱动。
- **零项目路径假设**：本文件不出现任何具体项目路径；取值走 `AGENTS.md` 声明段 ＋ 项目根 `.mysql-cli.toml`。

---

## §1 安全基线（不可妥协）

1. **口令不落 history**：口令只经 `subprocess(env=)` 注入 `MYSQL_PWD`；**禁止**写成命令行前缀
   （`MYSQL_PWD=x mysql …` 会进 shell history 与进程列表）。
2. **写操作默认预演**：批量 `import` 默认只打印将执行的 DDL，须显式 `--apply` 才落库；
   `--dry-run` 可对 `script` 生效。
3. **可选写闸**：项目若在 `[write_gate] allow_hosts` 列出白名单，则写类命令（`import` / `script`）
   在**非白名单 host** 上直接拒绝——把「只写本地库」的纪律放进工具而非靠人记。
4. **标识符先校验再拼串**：库名/表名拼入 SQL 前过 `[A-Za-z0-9_]` 白名单。

---

## §2 命令面（`cli/mysql-cli`）

本体 **stdlib-only**，所有命令共用一套连接取值（§3）。

| 命令 | 作用 |
|---|---|
| `ping` | 连通探测（返回服务器版本） |
| `query <SQL> [--db D] [--no-header]` | 执行单条 SQL（默认 TSV 原样输出；`--json` 结构化） |
| `script <文件.sql> [--db D]` | 执行整段脚本（多条语句 / DDL） |
| `tables [--db D]` | 列出目标库的表 |
| `sample <表> [N] [--db D]` | 采样 N 行（默认 10） |
| `backup --db D --tables a,b --out F` | 用 `mysqldump` 导出表（`--single-transaction`） |
| `import <sql目录> <库名> [--drop] [--apply]` | 批量导入；由 `INSERT INTO t(cols)` 推断建表 DDL |
| `migrate-check [--dir DIR] [--db D]` | Flyway 迁移 checksum 自检（本地复算 ↔ 库记账） |

**全局旗标**：`--root DIR`（钉项目根）／`--env-file F`（可多次）／`--host/--port/--user/--password/--timeout`／
`--db D`（目标库）／`--json`／`--dry-run`。

> **旗标以 `mysql-cli <子命令> --help` 与 `mysql-cli --help` 为准**——本表只给命令面与作用，**不复述逐条旗标**。

---

## §3 配置（判据 vs 取值分离）

- **判据**只在本 skill（本文件）。
- **取值**：项目 `AGENTS.md` 的 `## 数据库` 声明段（自然语言；**CLI 不读**）＋ 项目根
  `.mysql-cli.toml`（**机器可读**；CLI 读）。

```toml
[connection]
# 可选：加载 shell 风格 .env（相对项目根）；CLI 也会读进程环境
env_file = ""
host = "127.0.0.1"
port = 3306
user = "root"
# password 建议留空、走环境变量或 --password，避免明文入仓
timeout = 30
# 变量名覆盖（默认 MYSQL_HOST / MYSQL_PORT / MYSQL_USER / MYSQL_PASSWORD）
# host_var = ["MT_DB_HOST", "MYSQL_HOST"]

[write_gate]
# 非空时：import / script 仅允许写这些 host（其余拒绝）
allow_hosts = ["127.0.0.1", "localhost"]

[migrations]
# 库名 → 迁移目录（相对项目根）；migrate-check 无 --dir 时按此逐库自检
# mt_platform = "db/migration/platform"
# mt_org = "db/migration/org"
```

**连接取值优先级（高→低）**：命令行 `--host …` → `--env-file`／进程环境 → `.mysql-cli.toml [connection]`
→ 内置默认（`127.0.0.1:3306`，user `root`，无口令）。项目根定位：`--root` → `MYSQL_CLI_ROOT`
环境变量 → 向上查找 `.mysql-cli.toml` → `.git`。

---

## §4 Flyway checksum 算法（`migrate-check` 的判据）

**算法真源**（Flyway 12 `ChecksumCalculator`）：对迁移文件**逐行** `rstrip()`（只去行尾、**不去行首**）
后按 UTF-8 累积 CRC32，末尾截为 signed int32。

- ⚠️ **注释与空行均计入** ⇒ 改注释与改 DDL 等价，同样触发 `Migration checksum mismatch`
  （已执行迁移**定版冻结**：改源即起不来）。
- 行分隔按 Java `readLine()`（`\r\n` / `\n` / `\r`），**不用** `str.splitlines()`（后者还认 `\x0b`/`\x85` 等边界）。
- 早期 Flyway 用 `trim()`（行首也去），12 起为 `rstrip()`——复算须对齐当前版本。

**判定**（本地实算值 ↔ `flyway_schema_history` 记账）：

| 结论 | 含义 | 计错 |
|---|---|---|
| `一致` | 实算 ＝ 记账 | 否 |
| `记账 NULL（不校验）` | Flyway 本不校验该行 | 否 |
| `未应用` | 本地有、库无该版本记录（新迁移的正常态） | 否 |
| `失配` | 实算 ≠ 记账 | **是** |
| `本地缺文件` | 库有记录、本地无对应文件 | **是** |
| `执行失败(success=0)` | 库记账 success=0 | **是** |

退出码：**0** 全通过／**1** 任一库有异常／**2** 全部库都无法校验（不可达、缺凭证）——无法判定 ≠ 有问题。

---

## §5 边界

| skill | 管什么 | 交叉点 |
|---|---|---|
| `svc-ops` | 服务起停 / 健康检查 | 起服务前的库连通预检可用 `mysql-cli ping` |
| `office-docs` | 办公文档 | 无 |
| `llm-wiki` | 文档知识库 | 无 |

落地检查：

1. 本 skill 无任何项目路径（取值全在声明段／`.toml`）。
2. 导入前先 `import …`（不带 `--apply`）看生成的 DDL；确认后再 `--apply`。
3. 迁移失败提示「已执行迁移不可改（含注释）」——还原为已应用版本，或改落对应 MD。
