# skills

Claude Code skill 集合 — 按需取用的可独立发布技能。

每个 skill 可单独下载安装：根目录 `<name>.md` + 同名目录 `<name>/`，开箱即用。

## Skills

| Skill | 一句话 | 适合谁 |
|-------|--------|--------|
| [sub2cfg](sub2cfg.md) | 订阅链接转 Clash/Sing-box/DAE 完整配置 | 有代理订阅需转配置 |
| [commit-message](commit-message.md) | 按 Conventional Commits 生成提交信息 | 写提交时想规范化 |
| [plan-persist](plan-persist.md) | 复杂任务先落盘再开工，进度可中断续作 | ≥3 步骤或需跨会话执行的任务 |
| [obscura](obscura.md) | 隐身无头浏览器 — JS 渲染抓取、截图对比、CDP/MCP 自动化 | 需渲染抓取/反指纹/浏览器自动化 |
| [agent-doctor](agent-doctor.md) | 本机多 agent 能力自检 — 一条命令核验配置是否真生效 | 装了一堆 agent 工具、担心“装了没生效” |
| [agent-pipeline](agent-pipeline.md) | 跨 agent 工作流水线编排 — 七环闸门、随时中途接入、多计划串行、无人值守托管 | 想让 agent 按固定流程干活、且不污染上下文 |
| [llm-wiki](llm-wiki.md) | 知识库体系与文档站工具链 — 三层模型、目录四理念、落库分流、lint/drift/nav CLI | 文档越用越乱、想目录可导航且能保鲜 |
| [office-docs](office-docs.md) | 办公文档零依赖定点编辑 — PPTX 精确改（文字/形状/表格/连线/图片）、md→xlsx | 改汇报 pptx、做 xlsx 交付表 |
| [mysql-cli](mysql-cli.md) | MySQL 访问与管理 — 连库/查询/脚本/采样/备份/批量导入/迁移 checksum 自检 | agent 需连库查数或导入 |
| [redis-cli](redis-cli.md) | Redis 访问 — 连通探测、任意命令透传、键枚举 | agent 需看/改 Redis 数据 |
| [svc-ops](svc-ops.md) | 服务生命周期编排 — 服务表驱动起停/重启/状态/健康 | 本地多服务要一键起停 |
| [http-probe](http-probe.md) | HTTP 探测与 API 调试 — 任意方法、JSON 体、鉴权头、契约解包 | agent 需调接口/探服务 |

更多能力见各 `SKILL.md`。

## 安装

### 方式一：整包装（适合单机／外部 skill）

1. 打开 [Releases](https://github.com/caleee/skills/releases)，选目标 skill 的版本（`{skill}-v{ver}`）
2. 下载 `*.zip` 并解压，得 `<name>.md` + `<name>/`
3. 放到本地 skill 目录：
   - Claude Code：`~/.claude/skills/`
   - Codex / 通用：`~/.agents/skills/` 或 `~/.config/opencode/skills/`

> 升级已有安装位时请**整目录覆盖**（含 `<name>/VERSION`）——`VERSION` 是版本号的
> 单一真源，只换实现文件会让它停留在旧值，与 Release 页对不上。

### 方式二：按工程软链（推荐，多工程共享单一真源）

clone 本仓后，用 `install.sh` 把 skill **软链**进工程——改库即改所有已装工程（即时生效）：

```bash
git clone https://github.com/caleee/skills ~/repository/skills
~/repository/skills/install.sh --list                  # 看可用 skill
~/repository/skills/install.sh <工程根> office-docs     # 或读 <工程根>/.agents/skills.txt
```

落点：`<工程>/.agents/skills/<skill>` → 本仓；`<工程>/.claude/skills/<skill>` → 兼容链。
**代价**：工程 clone **不自举**（需在有本仓的机器上重跑 `install.sh` 补偿）——换来的是
「一处改、处处新」与零副本漂移。机器可读清单见 [`skills.json`](skills.json)。

## 给维护者

新增 skill 需同时满足仓库规范与发布机制，详见 [AGENTS.md](AGENTS.md) 与 `docs/adr/0001-version-and-release-strategy.md`。

简要步骤：建 `<name>.md`（单行 description）+ `<name>/SKILL.md`/`AGENT.md`/`VERSION`（`0.1.0`）→ `git add` 全部跟踪 → 更新 `AGENTS.md`/`README.md` 索引 → Actions `Release Skill` 填 skill 名发布。

## 词汇

- 协作语言见 [CONTEXT.md](CONTEXT.md)
- 发布机制 ADR 见 [docs/adr/](docs/adr/)

## 许可

[LICENSE](LICENSE)
