# AGENT.md — mysql-cli

> 判据见 [`SKILL.md`](SKILL.md)；项目声明模板见 [`TEMPLATE.md`](TEMPLATE.md)。

## 何时用本 skill

| 场景 | 动作 |
|---|---|
| 探连通 / 版本 | `mysql-cli ping` |
| 查一条 SQL | `mysql-cli query "SELECT ..." --db <库>`（`--json` 结构化） |
| 跑迁移 / DDL 脚本 | `mysql-cli script db/migration/V14__x.sql --db <库>` |
| 看库有哪些表 | `mysql-cli tables --db <库>` |
| 采样看数据 | `mysql-cli sample <表> 20 --db <库>` |
| 导出表备份 | `mysql-cli backup --db <库> --tables a,b --out /tmp/a.sql` |
| 批量导入一段 dump | `mysql-cli import <sql目录> <库名>`（预演）→ `--apply`（落库） |
| 迁移失配自检 | `mysql-cli migrate-check`（或 `--db <库>` / `--dir <目录>`） |

## 快速开始

```bash
# 1) 探连通（连接取值见 .mysql-cli.toml / --env-file / --host…）
mysql-cli ping

# 2) 查询
mysql-cli query "SELECT COUNT(*) FROM t_user" --db app

# 3) 导入：先看生成的 DDL，确认后再落库
mysql-cli import db/seed app            # 预演
mysql-cli import db/seed app --apply    # 落库（受 [write_gate] 约束）

# 4) 迁移 checksum 自检
mysql-cli migrate-check --dir db/migration/app
```

## 架构

```
mysql-cli/
├── SKILL.md      判据（零项目路径假设）
├── TEMPLATE.md   项目声明段 + .mysql-cli.toml 模板
├── AGENT.md      本文件（运行时指引）
├── VERSION       semver（发布用）
└── cli/mysql-cli CLI：单文件 stdlib-only（复用 mysql / mysqldump）
```

- **单文件自包含**：`cli/mysql-cli` 由 tenant `tzkit.{sql,dbimport,mt/migrate}` 合并而成，`git archive`
  单 skill 打包即完整可复现。
- **配置双路径**：CLI（机器值）读 `--root`／`--env-file`／`--host…`／`.mysql-cli.toml`；`AGENTS.md`
  声明段**只给 agent／人读**，CLI 不读。
- **写类命令**：`import`（默认预演，`--apply` 落库）、`script`（`--dry-run` 可预演）；其余只读。
- **口令安全**：只经子进程 `env=` 注入 `MYSQL_PWD`，不写命令行。

## 扩展点

- **新增子命令**：在 `cli/mysql-cli` 的 `_COMMANDS` 表登记 ＋ 写 `cmd_*`；连接统一走 `ctx.connection()`。
- **新增配置键**：加进 `DEFAULTS`／`ENV_VARS`，并在 `Context.pick` 的取值环里自然生效。
- **改写入策略**：`_write_gate`（host 白名单）／`cmd_import`（预演 → `--apply`）。

## 注意事项

- **不要**在本 skill 里写任何具体项目路径——那会立刻造成「判据 vs 取值」双真源。
- 迁移文件**改注释也算改**（checksum 复算把注释计入）——已执行的迁移定版冻结。
- `--json` 是机器可读出口；人读默认表格／TSV，两者别互相依赖。
