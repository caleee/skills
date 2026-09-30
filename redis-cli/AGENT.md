# AGENT.md — redis-cli

> 判据见 [`SKILL.md`](SKILL.md)；项目声明模板见 [`TEMPLATE.md`](TEMPLATE.md)。

## 何时用本 skill

| 场景 | 动作 |
|---|---|
| 探连通 | `redis-cli ping` |
| 跑任意命令 | `redis-cli exec GET key` / `redis-cli exec DBSIZE` |
| 看某类键（小库） | `redis-cli keys 'user:*'` |
| 看某类键（大库） | `redis-cli exec SCAN 0 MATCH 'user:*' COUNT 100` |
| 指定逻辑库 | `redis-cli exec DBSIZE --db 1` |

## 快速开始

```bash
# 1) 探连通（连接取值见 .redis-cli.toml / --env-file / --host…）
redis-cli ping

# 2) 透传任意命令
redis-cli exec SET demo hello
redis-cli exec GET demo

# 3) 枚举键（大库请改用 exec SCAN）
redis-cli keys 'demo:*'
```

## 架构

```
redis-cli/
├── SKILL.md      判据（零项目路径假设）
├── TEMPLATE.md   项目声明段 + .redis-cli.toml 模板
├── AGENT.md      本文件（运行时指引）
├── VERSION       semver（发布用）
└── cli/redis-cli CLI：单文件 stdlib-only（复用 redis-cli）
```

- **单文件自包含**：`cli/redis-cli` 来自 tenant `tzkit.redis_cli`，`git archive` 单 skill 打包即完整。
- **配置双路径**：CLI（机器值）读 `--root`／`--env-file`／`--host…`／`.redis-cli.toml`；`AGENTS.md`
  声明段**只给 agent／人读**，CLI 不读。
- **口令安全**：只经子进程 `env=` 注入 `REDISCLI_AUTH`，不写命令行。

## 扩展点

- **新增便捷子命令**：在 `cli/redis-cli` 的 `_COMMANDS` 登记；或直接用 `exec` 透传，无需改代码。
- **新增配置键**：加进 `DEFAULTS`／`ENV_VARS`，`Context.pick` 的取值环自动生效。

## 注意事项

- **不要**在本 skill 里写任何具体项目路径——那会立刻造成「判据 vs 取值」双真源。
- `KEYS` 阻塞大库：枚举键优先 `exec SCAN`。
- `--json` 把原始输出按行切成数组；二进制安全的值建议仍用 `exec` 原样看。
