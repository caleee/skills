# ADR-0003: 根 agent 指令文件更名为 AGENTS.md

- 状态：已接受
- 日期：2026-09-29
- 前序：ADR-0002（持久化规划 Skill）

## 背景

仓库根级 agent 指令文件沿用自创名 `AGENT.md`，并以 `CLAUDE.md → AGENT.md` 相对软链覆盖 Claude Code。该命名带来两个问题：

1. **生态不识别**：`AGENTS.md` 是 Codex / opencode / Cursor / pi 等 agent 的事实标准发现名；`AGENT.md` 无工具原生发现，只能靠软链或人工指路。
2. **双份冲突注入**：仓库内潜伏一份 2026-09-16 的未跟踪副本 `AGENTS.md`（从未入版本库，内容已落后：缺 agent-doctor 行、写 "Codex" 而非 "Claude Code"、引用 `.Codex/plans`）。pi 会同时加载 `AGENTS.md` 与 `AGENT.md`，使每次会话注入两份互相矛盾的仓库约束。

## 决策

1. 根级指令文件更名为 `AGENTS.md`（内容取原 `AGENT.md` 的权威版本），删除那份落后副本。
2. `CLAUDE.md` 继续作为相对软链，目标改为 `AGENTS.md`（覆盖 Claude Code 的 `CLAUDE.md` 发现）。
3. 同步仓库内所有指向根文件的引用：`README.md`、`docs/adr/0002`、`obscura/AGENT.md`。
4. skill 目录内的 `<name>/AGENT.md`（skill 运行时指引）**本次不变**：它是 skill 包内文件，与根级文件层级和用途不同，且发布打包（`git archive`）与既有 skill 已按此名分发。

## 备选与否决

| 备选 | 否决理由 |
|------|----------|
| 保持 `AGENT.md`，仅删除孤儿 `AGENTS.md` | 放弃生态标准名的原生发现能力，继续依赖软链兜底 |
| `AGENTS.md` 作软链指向 `AGENT.md` | 让标准名成为二级指针；软链被识别依赖 `core.symlinks`，真源应持有标准名 |
| 一并把 `<name>/AGENT.md` 改为 `AGENTS.md` | 扩大本次变更面（4 个 skill + 发布产物命名），且非根级问题；留作后续独立决策 |

## 后果

- 根级 agent 指令以 `AGENTS.md` 为唯一权威：pi / Codex / opencode 原生发现，Claude Code 经 `CLAUDE.md` 软链发现。
- `docs/adr/0002` 中涉及根文件名的描述已就地修订并标注本 ADR。
- 仓库内同时存在根 `AGENTS.md` 与 `<name>/AGENT.md` 两种命名，属预期（层级不同）；若后续统一，另立 ADR。
