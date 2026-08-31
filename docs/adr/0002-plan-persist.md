# ADR-0002: 持久化规划 Skill（plan-persist）

- 状态：已接受（grilling 35 决收束）
- 日期：2026-08-31
- 前序：ADR-0001（版本与发布策略）、全局 `~/.claude/CLAUDE.md` Plan 持久化规则、现有实稿 `~/.claude/plans/squishy-weaving-bumblebee.md`

## 背景

全局 `CLAUDE.md` 中的 Plan 持久化规则已验证对“多模块/多步骤”任务的价值（Context + 模块表 + 大计划 + 小计划 + 进度表 + 执行记录，以进度表为准中断续作），但存在三处绑定：

1. 载体绑定于 Muse 全局 `CLAUDE.md`，其他 agent（`~/.agents/skills`、`~/.config/opencode/skills`）不可见；
2. 路径绑定于 `~/.claude/plans/` 全局混池，项目无法归属；
3. 能力绑定于 `EnterPlanMode`，跨 agent 不可用。

调研表明：Muse 原生 `/plan` 仅覆盖“方案确认”交互，不覆盖可续作纪律；`grill-me`/`grill-with-docs` 覆盖“想法成形”上游，不覆盖执行期看板。三段各司其职，空白恰在“执行期可中断续作”。需 skill 化以适配所有项目与所有 agent。

## 决策

### 1. skill 命名与发布

- 名：`plan-persist`（`[a-zA-Z0-9_-]`，与 `sub2cfg`/`commit-message` 并列）。
- 结构：根 `plan-persist.md`（单行 description）+ `plan-persist/SKILL.md`（完整定义）+ `plan-persist/AGENT.md` + `plan-persist/VERSION`（`0.1.0`），遵循 ADR-0001 与 `CLAUDE.md` 结构约束。

### 2. 落盘：纯项目内 + 软链兼容

- 主位：`<project>/.agent/plans/`（gitignore，不跟踪）。
- 兼容：`<project>/.claude/plans → ../.agent/plans` 相对软链，使 Muse 原生路径互通；不双写、不绝对软链。
- 初始化：skill 安装即建 `.agent/plans/` + `archived/` + `index.md` + 软链，不等首 plan 懒创建。
- 存量：`~/.claude/plans/` 按需迁移。

### 3. 何时建 plan（收紧）

- 阈值：**≥3 步骤或用户明示“先规划/做大 plan”** 才建；单行问答/小编辑不建。较原“≥2 模块或 ≥3 步骤或跨文件”收紧。
- 触发：两者兼有 — 模型检测到阈值满足时**直接建**，用户亦可显式 `/plan-persist` 调用。

### 4. plan 内容与粒度

- 骨架：保留 5 段 — Context + 模块归类表 + 大计划 + 各模块小计划 + 进度表 + 执行记录；每 plan 末尾加“验证”段。
- 更新：模块级（每完成一模块改状态 + 补执行记录），不细到任务级。
- 命名：`NN-<slug>.md` 序号+slug 递增，以 agent 省 token（一扫得序）优先于人类一眼序。
- 引用：plan 内写分支名 + 关联文件列表的轻量指针。
- 演进：小改原位编辑留痕；大改另起新 plan，旧 plan 标已废弃并指向新 plan。

### 5. 多 plan 与发现

- 并发：允许多活跃 plan 并行。
- 索引：`.agent/plans/index.md` 极简列表（`NN - 标题 (状态)`），由模型在新建/改状态/废弃时同步维护；新会话自动扫描该索引，以进度表为准，确认后续作。
- 状态机：五态 — `待办 → 进行中 → 已完成 → 已归档 / 已废弃`；已废弃移至 `.agent/plans/archived/`。
- 衔接：不依赖 `EnterPlanMode`，文字约定兜底。

### 6. 模板重量与词汇

- 轻量：仅 `SKILL.md` 文字规范 + 要点清单，**不带**独立模板文件与脚本。
- 词汇：保留“模块”一词；新建 `CONTEXT.md` 统一承载（含原 `docs/glossary.md` 7 词，已合表清理，无跳转）。

### 7. 旧章与 dogfood

- 全局 `~/.claude/CLAUDE.md` 原 Plan 持久化章：删正文留一句路由（指向 `/plan-persist`）。
- 首个 dogfood：本 skill 自身的构建即用新规范建 `01-plan-persist-skill.md` 自举。

### 8. 工程优化（grill-me P1 附加）

- 合表：`docs/glossary.md` 内容合入 `CONTEXT.md`，原文件删除（无跳转）。
- 分工：`README.md` 重塑为人类入口（Skill 表“适合谁”+ 安装三步），`AGENT.md` 专为 agents（硬约束/检查清单），各司其职。
- 软链：项目根 `CLAUDE.md → AGENT.md` 相对软链（`120000`，`cat` 跟随、`git ls-files` 可跟踪），经本地 `git init` 验证，Muse 以常规文件读取会跟随。

## 备选与否决

| 备选 | 否决理由 |
|------|----------|
| 双轨（全局+项目内） | 与“纯项目内”决议冲突，增加混池心智 |
| 保留日期前缀 `YYYY-MM-DD-<slug>` | 不满足“省 token 一扫得序”，序号更省推理 |
| 表格索引 | 过重，极简列表已满足多 plan 发现 |
| 双写双读兼容 | 增加写入负担，相对软链已满足互通 |
| 带模板文件/脚本的重量方案 | 轻量已满足，额外文件增加发布体积与维护 |
| 仅用户显式触发 | 与“两者兼有 + 模型直接建”决议冲突 |

## 后果

- `CONTEXT.md` 为统一词汇单一事实源（原 `docs/glossary.md` 已合表删除）。
- `.agent/plans/` gitignore，需在 `AGENT.md` 指引“安装即初始化”。
- `index.md` 成为多 plan 发现的单一入口，模型承担同步维护职责。
- 根 `CLAUDE.md` 为 `AGENT.md` 的相对软链（`120000`），Muse 以常规文件读取会跟随；检出方需 `core.symlinks=true`（macOS/Linux 默认）。
