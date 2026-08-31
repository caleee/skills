# skills

Claude Code skill 集合 — 按需取用的可独立发布技能。

每个 skill 可单独下载安装：根目录 `<name>.md` + 同名目录 `<name>/`，开箱即用。

## Skills

| Skill | 一句话 | 适合谁 |
|-------|--------|--------|
| [sub2cfg](sub2cfg.md) | 订阅链接转 Clash/Sing-box/DAE 完整配置 | 有代理订阅需转配置 |
| [commit-message](commit-message.md) | 按 Conventional Commits 生成提交信息 | 写提交时想规范化 |
| [plan-persist](plan-persist.md) | 复杂任务先落盘再开工，进度可中断续作 | ≥3 步骤或需跨会话执行的任务 |

更多能力见各 `SKILL.md`。

## 安装

1. 打开 [Releases](https://github.com/caleee/skills/releases)，选目标 skill 的版本（`{skill}-v{ver}`）
2. 下载 `*.zip` 并解压，得 `<name>.md` + `<name>/`
3. 放到本地 skill 目录：
   - Claude Code：`~/.claude/skills/`
   - Codex / 通用：`~/.agents/skills/` 或 `~/.config/opencode/skills/`

## 给维护者

新增 skill 需同时满足仓库规范与发布机制，详见 [AGENT.md](AGENT.md) 与 `docs/adr/0001-version-and-release-strategy.md`。

简要步骤：建 `<name>.md`（单行 description）+ `<name>/SKILL.md`/`AGENT.md`/`VERSION`（`0.1.0`）→ `git add` 全部跟踪 → 更新 `AGENT.md`/`README.md` 索引 → Actions `Release Skill` 填 skill 名发布。

## 词汇

- 协作语言见 [CONTEXT.md](CONTEXT.md)
- 发布机制 ADR 见 [docs/adr/](docs/adr/)

## 许可

[LICENSE](LICENSE)
