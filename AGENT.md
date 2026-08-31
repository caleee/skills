# AGENT.md — for agents working in this repo

> 协作语言先读 [`CONTEXT.md`](CONTEXT.md)；发布机制详见 [`docs/adr/0001-version-and-release-strategy.md`](docs/adr/0001-version-and-release-strategy.md)。

## 仓库类型

Claude Code skill 集合仓库（人类入口见 [`README.md`](README.md)）。每个 skill 可独立发布：根 `<name>.md` + 同名目录 `<name>/`。

## Skill 清单

| Skill | 索引 | 实现目录 | 一句话 |
|-------|------|----------|--------|
| sub2cfg | `sub2cfg.md` | `sub2cfg/` | 订阅链接转 Clash/Sing-box/DAE 完整配置 |
| commit-message | `commit-message.md` | `commit-message/` | 按 Conventional Commits 生成提交信息 |
| plan-persist | `plan-persist.md` | `plan-persist/` | 复杂任务先落盘（`.agent/plans/NN-<slug>.md`）再开工，进度表驱动中断续作 |

## 文档层次（agent 视角）

- **根 `<name>.md`**：frontmatter `name` + 单行 `description`（Release 说明唯一来源，正则按行提取，多行截断）；正文仅一句指引，不重复 `SKILL.md`
- **`<name>/SKILL.md`**：Anthropic 标准 skill 入口，完整定义；`cc-switch` 从 ZIP 安装、Claude Code 识别均依赖它
- **`<name>/AGENT.md`**：skill 运行时指引（命令/架构/扩展）
- **`<name>/` 内其他文件**：仅放运行时依赖的文档/代码
- **根 `AGENT.md`（本文件）**：仓库级 agent 约束与清单
- **根 `CONTEXT.md`**：共享词汇与边界（`Skill`/`VERSION`/`plan-persist`/五态机等）
- **`docs/adr/`**：架构决策；`docs/{skill}/`：skill 参考文档（运行时不依赖）

## 结构硬约束（新增 skill 必满足，否则 `release-skill.yml` 校验失败）

- skill 名仅 `[a-zA-Z0-9_-]`（workflow 输入校验，防注入/路径遍历）
- 根 `<name>.md` 的 `description` 必须单行
- 目录内所有文件必须 `git add` 跟踪（发布用 `git archive` 仅打包 tracked 文件）
- 首次发布前必须手动创建 `<name>/VERSION`（`0.1.0`，无 `v` 前缀，单一事实源）

## VERSION 与发布

- `VERSION` 语义 `MAJOR.MINOR.PATCH`，每次发布 patch+1（不按 commit 类型分）
- Tag ` <skill>-v<version>` 打在 bump commit 上，bump 由 `github-actions[bot]` 提交 `chore(<skill>): release v<ver> [skip ci]`
- 修改仅影响发布机制时，同步更新 `docs/adr/0001` 与本文件

## Plan 约束

- 复杂任务（≥3 步骤或用户明示“先规划/做大 plan”）先落 `.agent/plans/NN-<slug>.md`（5 段骨架 + 进度表五态机 + 执行记录 + 验证段），并同步 `index.md`（极简列表）；`.claude/plans → ../.agent/plans` 仅作 Muse 兼容软链
- `.agent/` 已在 `.gitignore`，plan 不入仓；小改原位留痕、大改另起新 plan 旧的移 `archived/`

## 完成检查清单

1. `<name>.md` 含 `name` + 单行 `description`，正文仅一句指引
2. `<name>/` 含 `AGENT.md` + `SKILL.md` + `VERSION`（合法 semver）
3. 目录内文件已全部 `git add`
4. `AGENT.md`（本文件）与 `README.md` 索引已同步
5. `CONTEXT.md` 词汇已对齐新增术语
