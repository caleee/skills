# TEMPLATE — 项目声明段与配置

> 复制到项目 `AGENTS.md`（声明段）＋ 项目根 `.svc-ops.toml`（必需——无服务表则 CLI 报错）。

## 一、`AGENTS.md` 声明段

> **只写本 skill 独有取值**。落库分流（决策台账／计划／设计稿／时间线／环境事实）**归
> `agent-pipeline` 的 `## 工作流水线` 声明段**，本节**不重复**——两处都写＝双真源。

```markdown
## 本地服务

> 判据见 `svc-ops` skill。

- 服务表：`.svc-ops.toml`（api :8080 / web :5173）
- PID/日志：`.svc-ops/run`、`.svc-ops/logs`（不入仓）
- 启动：`svc-ops start`；状态：`svc-ops status`
```

**字段含义**：这条声明段是给 **agent／人**读的**自然语言取值**；**CLI 本身不读** `AGENTS.md`
（它只读 `.svc-ops.toml` 与命令行参数）。

## 二、`.svc-ops.toml`（项目根，必需）

```toml
[run]
pid_dir = ".svc-ops/run"        # PID 文件目录（相对项目根）
log_dir = ".svc-ops/logs"       # 服务日志目录（相对项目根）
ready_timeout = 90              # 默认就绪等待秒数
probe_timeout = 2               # 单次健康探针超时
# env_file = "infra/.env"       # 可选：所有服务共享的 shell 风格 .env

[services.api]
port = 8080                              # 必填：端口回收 + 就绪探测
command = ["mvn", "-B", "spring-boot:run"]  # 必填：数组或 shell 串
cwd = "service"                          # 相对项目根，默认项目根
health = "http://localhost:8080/actuator/health"   # 就绪 URL；缺省则 TCP 探 port
env_file = "infra/.env.local"            # 可选
env = { SPRING_PROFILES_ACTIVE = "local" }          # 可选：静态注入
ready_timeout = 120                      # 覆盖 [run] 默认

[services.web]
port = 5173
command = ["pnpm", "run", "dev"]
cwd = "web"
health = "http://localhost:5173"
```

## 三、最小可用步骤

```bash
svc-ops --dry-run start   # 预演将启动什么
svc-ops start             # 起全部
svc-ops status            # 进程/端口/健康一览
svc-ops restart api       # 改配置后重启
svc-ops stop              # 停
```
