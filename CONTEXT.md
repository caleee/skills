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
| **持久化 plan（plan-persist）** | 复杂任务的执行看板：先落盘再开工（载体 `.agents/plans/`；触发条件与骨架见 `plan-persist` skill） | planning / planning-plan / 计划文档（泛称） |
| **业务类型目录（biz dir）** | `.agents/plans/` 下的第一层分组（自由命名，如 `mt`/`fp`/`infra`）；`NN` 在组内自增（何时可省略见 skill） | 分类/子目录（泛称） |
| **Doctor（自检）** | 对 agent 环境做**只读**健康检查的机制；**本体是零 agent 依赖的脚本**、skill 仅作入口（skill 机制失效时仍可运行）。只诊断不修复 | health check / 体检（泛称） |
| **流水线（agent-pipeline）** | 跨 agent、跨项目的**工作编排**机制：七环顺序与闸门、接入判定、外层循环、上下文卫生、托管边界。**判据来自 skill，命令与落点来自项目声明**（`## 工作流水线` 段） | workflow / 流程 / SOP（泛称） |
| **位置探针** | 判定“当前在第几环”的依据：每环一个**可机械验证的痕迹位**（计划头字段／进度表绿行／执行记录行…）；证据不足时退到能确证的最早环 | 进度检查（易与进度表混） |
| **托管（无人值守）** | 无人复核时 agent 的接管机制：三档边界（可逆自决／不可逆阻塞／红线永不做）＋ 三层开关（触发词／标记文件／项目默认） | 全自动 / 无人模式（口语） |
| **外层循环** | 流水线在**计划之上**的一层：多计划串行、依赖拓扑序、计划间上下文卫生（compact/new/handoff） | 批处理（易混） |
| **模块** | 一组强内聚的文件/职责簇（如一个 skill、一个子系统、一个文档域），是 plan 中拆分与验收的单位 | 组件/子任务（粒度不定） |
| **步骤** | 单个可验证的原子动作（改 N 个文件、跑一次验证、发一个 commit）——plan 拆分与验收的计数单位 | task（易与 issue tracker 混） |
| **落盘** | 将 plan 写入 `.agents/plans/` 并同步 `index.md`（骨架见 skill） | 保存/持久化（口语） |
| **续作** | 新会话接着做未完成的 plan，不重问已定事项（发现机制见 skill） | 恢复/重启 |
| **进度表** | plan 内的状态矩阵：每行一模块，列含计划/状态/产出；状态采用五态机 | 进度清单 |
| **执行记录** | plan 末尾按时间追加的日志：日期 + 动作 + 备注，用于回溯 | 变更日志（易与 git log 混） |
| **五态机** | 模块/plan 状态：`待办 → 进行中 → 已完成 → 已归档 / 已废弃(→ archived/)` | 三态/两态（已废弃） |
| **软链兼容** | `.claude/plans → ../.agents/plans` 相对软链，使 Muse / Claude Code 的原生路径能找到 `.agents/plans/` | 双写/绝对软链 |
| **llm-wiki（知识库体系）** | 管知识资产**空间轴**的 skill：三层模型 / 目录四理念 / 落库分流 / 三操作。**判据来自 skill，取值来自项目 `## 知识库` 声明段** | 文档规范（泛称） |
| **三层模型** | 源层（不可变素材，人策展）／编译层（LLM 维护的结论）／出口层（对外成品，人签发）；**跨层不直连** | 三段式（泛称） |
| **目录四理念（P1–P4）** | P1 目录预算 ≤24 · P2 增长轴被有界轴包夹 · P3 分组轴真实语义化 · P4 结构即导航 | — |
| **落库分流** | 五类性质各归唯一落点：决策／范围／机制／时间线／环境事实，禁重复记 | 分类存储（泛称） |
| **`.llm-wiki.toml`** | 项目根的**机器可读**配置（端口/目录/预算/drift watch）；与 `AGENTS.md` 的 `## 知识库`（自然语言）声明段配套 | — |
| **office-docs（办公文档）** | 管办公文档**内容轴**的 skill：PPTX 零依赖定点编辑（只改目标字节、可 diff 回填）／XLSX 读取与 md→xlsx。**判据来自 skill，基线取值来自项目 `## 办公文档` 声明段 ＋ `.office-docs.toml`** | 汇报材料编辑（泛称） |
| **ref（office-docs 寻址）** | PPTX 内定位单元的坐标语法（`slide2!sp[3]`／`slide2!tbl0.r1.c2`／`.p0`）；序号与 `dump` 一致，坐标一律 pt | 位置引用（易与行号混） |
| **`.office-docs.toml`** | 项目根的**机器可读**配置（只读模板基线目录）；与 `AGENTS.md` 的 `## 办公文档`（自然语言）声明段配套 | — |
| **skills.json** | 仓根的**机器可读** skill 清单（name/description/version/path）；由 `scripts/gen_skills_json.py` 从 `<name>.md` ＋ `<name>/VERSION` **派生**，`--check` 拦漂移 | — |
| **软链安装（`install.sh`）** | 把本仓 skill 软链进工程（`.agents/skills/`＋`.claude/skills/`）的机制：**单一真源、改库即生效**；工程声明清单 `.agents/skills.txt`，快照 `.agents/skills.lock`。代价＝工程 clone 不自举（重跑补偿） | 复制入仓（旧法） |

## 边界与引用

- **正文归属**：判据只在各 skill 的 `SKILL.md`（单一真源）；本仓文档**不复述判据**，只写取值与指针。历史两次踩坑都是复述：全局路由行内联阈值（`MT-145`）、本仓 `## Plan 约束` 内联 plan-persist 的阈值与骨架（2026-09-30 已收拢为指针）。
- **声明段**：项目 `AGENTS.md` 只写声明段——`## 工作流水线`（agent-pipeline：落点/命令/红线，模板见 `agent-pipeline/TEMPLATE.md`）与 `## 知识库`（llm-wiki：知识库取值，模板见 `llm-wiki/TEMPLATE.md`）、`## 办公文档`（office-docs：基线取值，模板见 `office-docs/TEMPLATE.md`）；机器可读值写 `.llm-wiki.toml`／`.office-docs.toml`。
- **本仓取值**：见根 `AGENTS.md` 的 `## 工作流水线` 段。

## 采纳

- 本表是**术语与别名的单一真源**：新增/改动术语须同步更新本表，并在 ADR 留痕。
