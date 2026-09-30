# AGENTS.md — for agents working in this repo

> 协作语言先读 [`CONTEXT.md`](CONTEXT.md)；发布机制详见 [`docs/adr/0001-version-and-release-strategy.md`](docs/adr/0001-version-and-release-strategy.md)。

## 仓库类型

Claude Code skill 集合仓库（人类入口见 [`README.md`](README.md)）。每个 skill 可独立发布：根 `<name>.md` + 同名目录 `<name>/`。

## Skill 清单

| Skill | 索引 | 实现目录 | 一句话 |
|-------|------|----------|--------|
| sub2cfg | `sub2cfg.md` | `sub2cfg/` | 订阅链接转 Clash/Sing-box/DAE 完整配置 |
| commit-message | `commit-message.md` | `commit-message/` | 按 Conventional Commits 生成提交信息 |
| plan-persist | `plan-persist.md` | `plan-persist/` | 复杂任务先落盘（`.agents/plans/<业务>/NN-<slug>.md`）再开工，进度表驱动中断续作 |
| obscura | `obscura.md` | `obscura/` | 隐身无头浏览器 — JS 渲染抓取、截图对比、CDP/MCP 自动化 |
| agent-doctor | `agent-doctor.md` | `agent-doctor/` | 本机多 agent 能力自检 — 全局指令/扩展加载/MCP/软链/hooks/密钥 |
| agent-pipeline | `agent-pipeline.md` | `agent-pipeline/` | 跨 agent 工作流水线编排 — 七环闸门/中途接入/多计划串行与上下文卫生/无人值守托管 |
| llm-wiki | `llm-wiki.md` | `llm-wiki/` | 知识库体系与文档站工具链 — 三层模型/目录四理念/落库分流/lint·drift·nav CLI |
| office-docs | `office-docs.md` | `office-docs/` | 办公文档零依赖定点编辑 — PPTX 文字/形状/表格/连线/图片精确改 · XLSX 读取与 md→xlsx · 只读模板基线 |

## 文档层次（agent 视角）

- **根 `<name>.md`**：frontmatter `name` + 单行 `description`（Release 说明唯一来源，正则按行提取，多行截断）；正文仅一句指引，不重复 `SKILL.md`
- **`<name>/SKILL.md`**：Anthropic 标准 skill 入口，完整定义；`cc-switch` 从 ZIP 安装、Claude Code 识别均依赖它
- **`<name>/AGENT.md`**：skill 运行时指引（命令/架构/扩展）
- **`<name>/` 内其他文件**：仅放运行时依赖的文档/代码
- **根 `AGENTS.md`（本文件）**：仓库级 agent 约束与清单
- **根 `CONTEXT.md`**：共享词汇与边界（`Skill`/`VERSION`/`plan-persist`/五态机等）
- **`docs/adr/`**：架构决策；`docs/{skill}/`：skill 参考文档（运行时不依赖）

## 结构硬约束（新增 skill 必满足，否则 `release-skill.yml` 校验失败）

- skill 名仅 `[a-zA-Z0-9_-]`（workflow 输入校验，防注入/路径遍历）
- 根 `<name>.md` 的 `description` 必须单行
- 目录内所有文件必须 `git add` 跟踪（发布用 `git archive` 仅打包 tracked 文件）
- 首次发布前必须手动创建 `<name>/VERSION`（`0.1.0`，无 `v` 前缀，单一事实源）

## 清单与安装

- **`skills.json`**（仓根）：机器可读 skill 清单，由 `scripts/gen_skills_json.py` 从各 `<name>.md` frontmatter ＋ `<name>/VERSION` **派生**——新增/改 skill 后重跑；`--check` 拦漂移（`tests/test_skills_manifest.py` 已锁）。**不要手改**。
- **`install.sh`**：把 skill **软链**进工程——`<工程>/.agents/skills/<skill>` → 本仓，`<工程>/.claude/skills/<skill>` → 兼容链；工程声明清单 `<工程>/.agents/skills.txt`，快照写 `.agents/skills.lock`。软链＝单一真源、改库即生效；代价是工程 clone 不自举（重跑 `install.sh` 补偿）。

## VERSION 与发布

- `VERSION` 语义 `MAJOR.MINOR.PATCH`，每次发布 patch+1（不按 commit 类型分）
- Tag ` <skill>-v<version>` 打在 bump commit 上，bump 由 `github-actions[bot]` 提交 `chore(<skill>): release v<ver> [skip ci]`
- 修改仅影响发布机制时，同步更新 `docs/adr/0001` 与本文件

## 回归网

- `tests/` 是仓级冒烟测试（stdlib `unittest`）：`python3 -m unittest discover -s tests`；CI 见 `.github/workflows/ci.yml`（push/PR 触发，显式钉 Python 3.11）
- 测试**不进发布包**（`git archive` 只打包 `<name>.md` + `<name>/`），故不受「skill 目录内仅放运行时依赖」约束
- 改 CLI 实现时同步加测试——CI 用来拦 P0 级回归（历史教训：`deploy` 的 `NameError` 随着 3 个 Release 发出去而无人发现）

## 工作流水线

> 判据见 `agent-pipeline` skill；**本段只写取值**。未列出的字段走该 skill 的最小默认（字段定义真源：`agent-pipeline/TEMPLATE.md`）。

- **计划落点**：`.agents/plans/`，索引 `.agents/plans/index.md`（`.agents/` 已 gitignore，**计划不入仓**；`.claude/plans → ../.agents/plans` 仅作 Muse / Claude Code 兼容软链）
- **决策台账**：无（本仓决策落 `docs/adr/`，非 append-only 台账）
- **设计稿落点**：`docs/adr/`（架构决策）；`docs/<skill>/`（skill 参考文档）
- **时间线**：无
- **环境事实落点**：本文件
- **门禁命令**：测试 `python3 -m unittest discover -s tests`；构建 无；文档 无
- **质量轮触发**：按需
- **审查基准**：该 skill 的最新 Release tag `<skill>-v<ver>`（＝上次对外发布的版本）
- **报告落点**：`.agents/reviews/`（同样不入仓）
- **红线**（托管模式同样不做）：
  - **不手改 `<name>/VERSION`**——版本号由 `release-skill.yml` bump，手改会让文件与 tag 对不上
  - **不 push、不打 tag、不 `workflow_dispatch` 发布**——发布是人的动作（Release body 常需人工补行为变更）

## 完成检查清单

1. `<name>.md` 含 `name` + 单行 `description`，正文仅一句指引
2. `<name>/` 含 `AGENT.md` + `SKILL.md` + `VERSION`（合法 semver）
3. 目录内文件已全部 `git add`
4. `AGENTS.md`（本文件）与 `README.md` 索引已同步
5. `CONTEXT.md` 词汇已对齐新增术语
6. `python3 -m unittest discover -s tests` 全绿（本批改动含 CLI 时）
7. `python3 scripts/gen_skills_json.py --check` 绿（新增/改 skill 后已重生成 `skills.json`）
