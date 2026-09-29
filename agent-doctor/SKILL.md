---
name: agent-doctor
description: 本机多 agent 能力自检 — 核验全局指令分发、扩展加载、MCP 连通、软链、hooks、明文密钥
user-invocable: true
---

# agent-doctor — 本机 agent 能力自检

把「装了，但不确定是否生效」变成一条命令。

**本 skill 只是入口；本体是零依赖的 [`scripts/doctor.sh`](scripts/doctor.sh)。**
自检的目的是发现「能力是否真的生效」，而 skill 本身也是一种能力 ——
若把自检挂在 skill 机制里，skill 失效时恰是最需要自检的时候，它也会一起消失。
故本体不依赖任何 agent 运行时，人、Claude Code、pi、Codex、opencode 都能直接跑。

## 触发条件

任一即跑：

- 用户说「自检 / 检查 agent 环境 / 为什么这个能力没生效 / doctor」
- 刚改过 agent 配置（`~/.agents/AGENTS.md`、`settings.json`、MCP 配置、hooks、skills 软链）
- 排查「装了但没反应」类问题 —— **先跑 doctor，再动手**
- 周期性体检（改动前后各一次，两份 `--json` 可对比）

## 执行

```bash
# 安装后（示例装在 ~/.agents/skills/；Claude Code 为 ~/.claude/skills/）
DOCTOR=~/.agents/skills/agent-doctor/scripts/doctor.sh

bash "$DOCTOR"            # 全量自检（人类可读）
bash "$DOCTOR" --json     # 机器可读（便于对比两次结果）
bash "$DOCTOR" --quiet    # 只看问题
bash "$DOCTOR" --online   # 额外探测 URL 型 MCP 连通性（联网；默认跳过）
```

零依赖：仅 `bash` + POSIX 工具；`jq` 可选（缺失时相关检查降级为 warn/info）。
**只诊断，不修复**（不改任何配置）。退出码：`0` 无 FAIL／`1` 有 FAIL／`2` 用法错误。

## 报告解读

| 符号 | 含义 | 该做什么 |
|------|------|----------|
| `✓` pass | 该项正常 | 无需动作 |
| `·` info | 未安装／已跳过 | 确认是否**应该**安装；不是问题 |
| `!` warn | 可疑，但可能是有意为之 | 人工判断 |
| `✗` fail | 明确失效 | 按下方映射修 |

末尾 `PASS/WARN/FAIL` 汇总；**只有 FAIL 影响退出码**。

## 常见 FAIL → 修复

| 报告 | 原因 | 修复 |
|------|------|------|
| `缺受管区块`（pi/Codex） | 真源没接入 | `bash ~/.agents/install.sh` |
| `instructions 未含真源`（opencode） | 同上，数组缺条目 | 同上（需 `jq`） |
| `残留整行 @ 引用（死文本）` | 曾误按 `@file` 类接入，而 pi 不解析 `@` | `bash ~/.agents/install.sh`（幂等清理） |
| `入口文件不存在` | 扩展「已安装 ≠ 已加载」（如 git 源未 build） | 进包目录 `pnpm install && pnpm build` → pi `/reload` |
| `未安装：npm:xxx` | settings 声明了但没装 | `pi install npm:xxx`，或从声明中移除 |
| `命令不在 PATH：xxx` | MCP 死条目 | 安装该命令，或从 MCP 配置移除该 server |
| `N 个断链` | skill 软链指向已删真源 | 重建软链，或删除失效链接 |
| `脚本不存在` / `存在但不可执行` | hook 目标丢失 | 恢复脚本／`chmod +x` |
| `含真实凭据且已被 git 跟踪` | 凭据进了版本历史 | `git rm --cached <file>` + 加入 `.gitignore` + **轮换该凭据** |
| `文件名暗示可分享，却含真实凭据` | 分享型模板未脱敏 | 换占位符后再分享 |

## 与相邻 skill 的分工

- **本 skill**：环境层 —— 配置是否正确、能力是否真的生效
- `diagnosing-bugs`：代码层 —— 逻辑为什么错
- `ctx-doctor`（context-mode 自带）：只管 context-mode 自身

## 边界

- 只读，不写任何配置（修复按上表手做）
- 默认不联网；`--online` 才做 URL 探测
- 不覆盖：agent 版本升级、依赖冲突、网络策略
