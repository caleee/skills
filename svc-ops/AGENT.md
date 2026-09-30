# AGENT.md — svc-ops

> 判据见 [`SKILL.md`](SKILL.md)；项目声明模板见 [`TEMPLATE.md`](TEMPLATE.md)。

## 何时用本 skill

| 场景 | 动作 |
|---|---|
| 起本地服务 | `svc-ops start`（默认 all；或 `svc-ops start api`） |
| 改配置后重启 | `svc-ops restart api`（先停后起、等端口释放） |
| 停服务 | `svc-ops stop` |
| 看进程/端口/健康 | `svc-ops status` |
| 只探就绪 | `svc-ops health api` |
| 预演（不起） | `svc-ops --dry-run start` |

## 快速开始

```bash
# 1) 建服务表（项目根 .svc-ops.toml，机器可读取值）
cat > .svc-ops.toml <<'TOML'
[run]
pid_dir = ".svc-ops/run"
log_dir = ".svc-ops/logs"

[services.api]
port = 8080
command = ["mvn", "-B", "spring-boot:run"]
cwd = "service"
health = "http://localhost:8080/actuator/health"
env_file = "infra/.env.local"          # 可选：注入 shell 风格 .env
env = { SPRING_PROFILES_ACTIVE = "local" }

[services.web]
port = 5173
command = ["pnpm", "run", "dev"]
cwd = "web"
health = "http://localhost:5173"
TOML

# 2) 起 / 看 / 停
svc-ops start
svc-ops status
svc-ops restart api
svc-ops stop
```

## 架构

```
svc-ops/
├── SKILL.md      判据（零项目路径假设）
├── TEMPLATE.md   项目声明段 + .svc-ops.toml 模板
├── AGENT.md      本文件（运行时指引）
├── VERSION       semver（发布用）
└── cli/svc-ops   CLI：单文件 stdlib-only（服务表驱动的本地进程编排）
```

- **单文件自包含**：`cli/svc-ops` 由 tenant `tzkit.proc` ＋ `tzkit.mt.svc`（通用部分）＋ `tzkit.envcmd` 汇聚而成。
- **配置双路径**：CLI（机器值）读 `--root`／`.svc-ops.toml`；`AGENTS.md` 声明段**只给 agent／人读**，CLI 不读。
- **写动作**：`start`／`stop`／`restart`（`--dry-run` 只预演）；`status`／`health` 只读。

## 扩展点

- **新增服务**：往 `.svc-ops.toml` 的 `[services.<名>]` 加一节，无需改代码。
- **注入环境**：服务级 `env`（静态）＋ `env_file`（shell 风格 .env）＋ `[run] env_file`（共享）；
  叠加顺序＝本机环境 → `[run] env_file` → 服务 `env_file` → 服务 `env`（后者覆盖前者）。
- **改就绪判据**：`_ready_probe`（有 `health` 用 GET，否则 TCP 探 port）。

## 注意事项

- **不要**在本 skill 里写任何具体项目路径——那会立刻造成「判据 vs 取值」双真源。
- 回收端口**只杀监听者**（`-sTCP:LISTEN`）；裸 `lsof -ti tcp:<port>` 会连坐无关进程。
- `start` 幂等：服务已在运行则跳过，不重复起。
- 日志**追加**、起停留事件注记——别改成覆盖，那会抹掉上次失败现场。
