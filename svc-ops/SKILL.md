---
name: svc-ops
description: 服务生命周期编排 CLI — 服务表驱动 start/stop/restart/status/health；后台起进程、PID/日志落盘、等就绪、端口只回收监听者
user-invocable: true
---

# svc-ops — 服务生命周期编排

按**服务表**后台起停一组本地服务（后端／前端／微服务），等就绪、留日志、按需回收端口。
命令名对齐 **systemd**（`start`/`stop`/`restart`/`status`）。

> **一句话原则**：**判据来自本 skill，服务取值来自项目声明段**（[`TEMPLATE.md`](TEMPLATE.md)）；
> 端口回收**只杀监听者**、进程归属靠**进程组**辨认。

## 定位与边界

- **管「本地进程编排」**：起／停／重启／状态／就绪探测、PID 与日志落盘、端口回收。
- **不管「编排之外」**：容器编排（compose/k8s）／远程部署／构建与测试命令——那些归项目脚本或其它 skill。
- **零依赖**：只用标准库（`subprocess`/`socket`/`urllib`）与系统 `lsof`/`ps`。
- **零项目路径假设**：本文件不出现任何具体项目路径；服务表与取值走 `AGENTS.md` 声明段 ＋ 项目根 `.svc-ops.toml`。

---

## §1 命令面（`cli/svc-ops`）

| 命令 | 作用 |
|---|---|
| `start [名\|all]` | 后台起服务（写 pidfile、追加日志、等就绪；已在运行则跳过） |
| `stop [名\|all]` | 杀进程组 + 回收**监听**端口 + 删 pidfile + **等端口释放** |
| `restart [名\|all]` | 先停后起（等端口真正释放，避免与旧实例撞端口而静默换端口） |
| `status [名\|all]` | 进程 / 端口 / 健康 / 归属一览 |
| `health [名\|all]` | 仅就绪探测（GET 健康 URL 或 TCP 探端口） |

**全局旗标**：`--root DIR`（钉项目根）／`--json`／`--dry-run`（start/stop/restart 只预演）。
`up`／`down` 是 `start`／`stop` 的**兼容别名**。

> **旗标以 `svc-ops --help` 为准**——本表只给命令面与作用，**不复述逐条旗标**。

---

## §2 服务表（判据 vs 取值分离）

- **判据**只在本 skill（本文件）。
- **取值**：项目 `AGENTS.md` 的 `## 本地服务` 声明段（自然语言；**CLI 不读**）＋ 项目根
  `.svc-ops.toml`（**机器可读**；CLI 读）。

每个 `[services.<名>]` 一组：`port`（**必填**，用于端口回收与就绪探测）、`command`（**必填**，
数组或 shell 串）、`cwd`（相对项目根）、`health`（就绪 URL，缺省则 TCP 探 `port`）、
`env`／`env_file`（注入进程环境）、`ready_timeout`（就绪等待秒数）。`[run]` 段给
`pid_dir`／`log_dir`（默认 `.svc-ops/run`／`.svc-ops/logs`）与共享 `env_file`。

项目根定位：`--root` → `SVC_OPS_ROOT` 环境变量 → 向上查找 `.svc-ops.toml` → `.git`。

---

## §3 安全要点（不可妥协）

1. **端口回收只杀监听者**：`_free_port` **必须**带 `-sTCP:LISTEN`。裸 `lsof -ti tcp:<port>`
   会把**与该端口相连的客户端**（浏览器页签、连后端的代理）也列出来并 SIGTERM——
   表现为「停一个服务顺带杀掉无关进程」，前端**静默消失、日志无报错**。
2. **进程归属靠进程组**：`start` 用 `Popen(start_new_session=True)` 让服务自成进程组
   （pgid ＝ pidfile 里的 pid）；`status` 据此区分「我们启动的那一支」与「别人的残留」。
3. **日志追加、留事件注记**：起／停都往日志追加一行带时间的事件注记——**留证优先于干净**
   （用 `"w"` 覆盖会把上次失败现场抹掉，事后无从回溯）。
4. **失败带回日志尾**：起服务等就绪时若**子进程已退出**，立即判失败并回显日志末尾若干行，
   不盲等满超时。

---

## §4 就绪判据

- 服务配了 `health` → GET 该 URL，**2xx 即就绪**（任何异常视为不通）。
- 未配 `health` → **TCP 探 `port`**（`connect_ex` 成功即就绪）。
- 就绪等待最多 `ready_timeout` 秒；其间**每秒**检查进程存活 ＋ 探针。
- `restart` 在停后**等端口真正释放**（最多 15s）再起——SIGTERM 到进程退出有间隙，不等会「刚停又撞」。

---

## §5 边界

| skill | 管什么 | 交叉点 |
|---|---|---|
| `http-probe` | HTTP 探测 | 服务就绪后的接口调试用 `http-probe` |
| `mysql-cli` | MySQL 访问 | 起服务前的库连通预检可用 `mysql-cli ping` |
| `llm-wiki` | 文档知识库 | 无 |

落地检查：

1. 本 skill 无任何项目路径（取值全在声明段／`.toml`）。
2. 服务已在运行时 `start` **跳过**，不重复起（幂等）。
3. `stop` 后端口若 15s 未释放会告警——查是不是「非本进程组」的进程占着。
