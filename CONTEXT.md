# CONTEXT.md — skills

> skills 仓库的共享词汇表与边界。读本文件以对齐术语，写代码/文档/issue 时使用此处定义的词，避免同义词漂移。

## 共享词汇

| 术语 | 定义 | 禁用/易混别名 |
|------|------|---------------|
| **Skill** | 仓库中一个可独立发布的单元 = 根 `<name>.md`（frontmatter `name`/`description`）+ 同名目录 `<name>/`（含 `SKILL.md` + `AGENT.md` + `VERSION`） | — |
| **VERSION 文件** | skill 目录下的纯文本文件，内容为该 skill 的 semver（如 `0.1.0`），是版本号的单一事实来源。首次由作者手动创建 | — |
| **版本号** | semver 格式 `MAJOR.MINOR.PATCH`，无 `v` 前缀；每次发布 PATCH +1 | — |
| **Tag** | git tag，格式 `<skill>-v<version>`（如 `sub2cfg-v0.1.1`），标识某 skill 的一次发布 | — |
| **Release** | GitHub Release，附 zip 资产 + skill 用途简介（来自根 `.md` frontmatter 的 `description`） | — |
| **包（zip）** | Release 的资产，用 `git archive` 生成，含 `<name>.md` + `<name>/` 的所有 git tracked 文件 | — |
| **bump commit** | 发版时由 `github-actions[bot]` 产生的自动提交，更新 VERSION 文件，message 格式 `chore(<skill>): release v<ver> [skip ci]` | — |
| **description** | skill 根 `.md` frontmatter 中的 `description` 字段，作为 Release 说明的 skill 用途简介 | — |
| **持久化 plan（plan-persist）** | 对“≥3 步骤或用户明示‘先规划/做大 plan’”的复杂任务，先落盘再开工的执行看板；以 `.agent/plans/NN-<slug>.md` 为载体，以进度表为唯一可信源 | planning / planning-plan / 计划文档（泛称） |
| **模块** | 一组强内聚的文件/职责簇（如一个 skill、一个子系统、一个文档域），是 plan 中拆分与验收的单位 | 组件/子任务（粒度不定） |
| **步骤** | 单个可验证的原子动作（改 N 个文件、跑一次验证、发一个 commit），是“≥3 步骤”阈值的计数单位 | task（易与 issue tracker 混） |
| **落盘** | 将 plan 按 5 段骨架写入 `.agent/plans/NN-<slug>.md` 并同步更新 `.agent/plans/index.md` | 保存/持久化（口语） |
| **续作** | 新会话自动扫描 `.agent/plans/index.md`，以进度表为准继续未完成模块，不重问已定事项 | 恢复/重启 |
| **进度表** | plan 内的状态矩阵：每行一模块，列含计划/状态/产出；状态采用五态机 | 进度清单 |
| **执行记录** | plan 末尾按时间追加的日志：日期 + 动作 + 备注，用于回溯 | 变更日志（易与 git log 混） |
| **五态机** | 模块/plan 状态：`待办 → 进行中 → 已完成 → 已归档 / 已废弃(→ archived/)` | 三态/两态（已废弃） |
| **软链兼容** | `.claude/plans → ../.agent/plans` 相对软链，使 Muse 原生路径与 `.agent` 主位互通 | 双写/绝对软链 |

## 边界与引用

- **落盘主位**：项目内 `.agent/plans/`（gitignore，不跟踪）；`.claude/plans` 仅作相对软链，不再是主位。
- **何时建 plan**：收紧为“≥3 步骤或用户明示‘先规划/做大 plan’”才建；单行问答/小编辑不建。
- **plan 内容**：沿用 5 段骨架 — Context（图纸/现状/分支）+ 模块归类表 + 大计划（目标/顺序/依赖/数据约定/约束）+ 各模块小计划（改动点+验收）+ 进度表 + 执行记录；每 plan 末尾加“验证”段。
- **文件名**：`NN-<slug>.md` 序号+slug，序号自增，agent 按序号一扫即得序；省 token 优先于人类一眼序。
- **并发**：允许多活跃 plan 并行；发现机制为 `.agent/plans/index.md` 极简列表（`NN - 标题 (状态)`），由模型在新建/改状态/废弃时同步维护。
- **归档/废弃**：已废弃移至 `.agent/plans/archived/`；存量 `~/.agent/plans/` 按需迁移。
- **引用**：plan 内写分支名 + 关联文件列表的轻量指针，不写全量 commit 区间。
- **衔接**：不依赖 `EnterPlanMode`；Muse 专属交互由 skill 内文字约定兜底。
- **触发**：模型检测到阈值满足时直接建（自动侧），用户亦可显式 `/plan-persist` 触发。

## 采纳

- 写新 plan 前读 `CONTEXT.md` 对齐本文术语；新增/改动术语需同步更新本表并在 ADR 中留痕。
