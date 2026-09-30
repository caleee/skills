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
| **持久化 plan（plan-persist）** | 对“≥3 步骤或用户明示‘先规划/做大 plan’”的复杂任务，先落盘再开工的执行看板；以 `.agents/plans/<业务>/NN-<slug>.md` 为载体，以进度表为唯一可信源 | planning / planning-plan / 计划文档（泛称） |
| **业务类型目录（biz dir）** | `.agents/plans/` 下的第一层分组（自由命名，如 `mt`/`fp`/`infra`）；`NN` 在组内自增；单业务小项目（直接子项 ≤24）可省略 | 分类/子目录（泛称） |
| **Doctor（自检）** | 对 agent 环境做**只读**健康检查的机制；**本体是零 agent 依赖的脚本**、skill 仅作入口（skill 机制失效时仍可运行）。只诊断不修复 | health check / 体检（泛称） |
| **流水线（agent-pipeline）** | 跨 agent、跨项目的**工作编排**机制：七环顺序与闸门、接入判定、外层循环、上下文卫生、托管边界。**判据来自 skill，命令与落点来自项目声明**（`## 工作流水线` 段） | workflow / 流程 / SOP（泛称） |
| **位置探针** | 判定“当前在第几环”的依据：每环一个**可机械验证的痕迹位**（计划头字段／进度表绿行／执行记录行…）；证据不足时退到能确证的最早环 | 进度检查（易与进度表混） |
| **托管（无人值守）** | 无人复核时 agent 的接管机制：三档边界（可逆自决／不可逆阻塞／红线永不做）＋ 三层开关（触发词／标记文件／项目默认） | 全自动 / 无人模式（口语） |
| **外层循环** | 流水线在**计划之上**的一层：多计划串行、依赖拓扑序、计划间上下文卫生（compact/new/handoff） | 批处理（易混） |
| **模块** | 一组强内聚的文件/职责簇（如一个 skill、一个子系统、一个文档域），是 plan 中拆分与验收的单位 | 组件/子任务（粒度不定） |
| **步骤** | 单个可验证的原子动作（改 N 个文件、跑一次验证、发一个 commit），是“≥3 步骤”阈值的计数单位 | task（易与 issue tracker 混） |
| **落盘** | 将 plan 按 5 段骨架写入 `.agents/plans/<业务>/NN-<slug>.md` 并同步更新 `.agents/plans/index.md` | 保存/持久化（口语） |
| **续作** | 新会话自动扫描 `.agents/plans/index.md`，以进度表为准继续未完成模块，不重问已定事项 | 恢复/重启 |
| **进度表** | plan 内的状态矩阵：每行一模块，列含计划/状态/产出；状态采用五态机 | 进度清单 |
| **执行记录** | plan 末尾按时间追加的日志：日期 + 动作 + 备注，用于回溯 | 变更日志（易与 git log 混） |
| **五态机** | 模块/plan 状态：`待办 → 进行中 → 已完成 → 已归档 / 已废弃(→ archived/)` | 三态/两态（已废弃） |
| **软链兼容** | `.claude/plans → ../.agents/plans` 相对软链，使 Muse / Claude Code 原生路径与 `.agents` 主位互通 | 双写/绝对软链 |
| **llm-wiki（知识库体系）** | 管知识资产**空间轴**的 skill：三层模型 / 目录四理念 / 落库分流 / 三操作。**判据来自 skill，取值来自项目 `## 知识库` 声明段** | 文档规范（泛称） |
| **三层模型** | 源层（不可变素材，人策展）／编译层（LLM 维护的结论）／出口层（对外成品，人签发）；**跨层不直连** | 三段式（泛称） |
| **目录四理念（P1–P4）** | P1 目录预算 ≤24 · P2 增长轴被有界轴包夹 · P3 分组轴真实语义化 · P4 结构即导航 | — |
| **落库分流** | 五类性质各归唯一落点：决策／范围／机制／时间线／环境事实，禁重复记 | 分类存储（泛称） |
| **`.llm-wiki.toml`** | 项目根的**机器可读**配置（端口/目录/预算/drift watch）；与 `AGENTS.md` 的 `## 知识库`（自然语言）声明段配套 | — |

## 边界与引用

- **落盘主位**：项目根 `.agents/plans/`（gitignore，不跟踪）；`.claude/plans` 仅作相对软链，不再是主位。目录名取**复数** `.agents`（与 `AGENTS.md` 同源；社区约定见 dotagentsprotocol.com / getsentry/dotagents）。
- **何时建 plan**：收紧为“≥3 步骤或用户明示‘先规划/做大 plan’”才建；单行问答/小编辑不建。
- **plan 内容**：沿用 5 段骨架 — Context（图纸/现状/分支）+ 模块归类表 + 大计划（目标/顺序/依赖/数据约定/约束）+ 各模块小计划（改动点+验收）+ 进度表 + 执行记录；每 plan 末尾加“验证”段。
- **文件名**：`NN-<slug>.md` 序号+slug，序号自增，agent 按序号一扫即得序；省 token 优先于人类一眼序。
- **并发**：允许多活跃 plan 并行；发现机制为 `.agents/plans/index.md` 极简列表，**按业务分节**（`## <业务>` 下每行 `NN - 标题 (状态)`），由模型在新建/改状态/废弃时同步维护。
- **归档/废弃**：已废弃移至 `.agents/plans/archived/<业务>/`；存量 `.agent/plans/`、`~/.claude/plans/` 按需迁移。
- **引用**：plan 内写分支名 + 关联文件列表的轻量指针，不写全量 commit 区间。
- **衔接**：不依赖 `EnterPlanMode`；Muse 专属交互由 skill 内文字约定兜底。
- **触发**：模型检测到阈值满足时直接建（自动侧），用户亦可显式 `/plan-persist` 触发。
- **流水线正文归属**：`agent-pipeline` skill 为单一真源；全局 `~/.agents/AGENTS.md` 只留 grilling 口径与 `ok` 约定等**元约定**；项目 `AGENTS.md` 只写 `## 工作流水线` **声明段**（模板见 `agent-pipeline/TEMPLATE.md`）。
- **知识库正文归属**：`llm-wiki` skill 为单一真源（三层模型/目录四理念/落库分流）；项目 `AGENTS.md` 只写 `## 知识库` **声明段**（模板见 `llm-wiki/TEMPLATE.md`），机器可读取值写 `.llm-wiki.toml`。

## 采纳

- 写新 plan 前读 `CONTEXT.md` 对齐本文术语；新增/改动术语需同步更新本表并在 ADR 中留痕。
