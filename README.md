# skills

Claude Code skill 集合仓库。每个 skill 由一个根目录的 `.md` 文件（技能定义）和一个同名目录（实现文件 + `AGENT.md`）组成。

## Skill 列表

| Skill | 技能定义 | 详细说明 | 描述 |
|-------|----------|----------|------|
| [sub2cfg](sub2cfg.md) | `sub2cfg.md` | `sub2cfg/AGENT.md` | 订阅链接转代理配置 |
| [commit-message](commit-message.md) | `commit-message.md` | `commit-message/AGENT.md` | 按 Conventional Commits 规范生成提交信息 |

## 文档层次

- **根目录 `.md` 文件**：skill 定义，供用户/Agent 发现 skill 存在
- **`{skill}/AGENT.md`**：skill 运行说明，含命令、架构、扩展指南
- **`{skill}/` 内其他文档**：仅放功能上依赖的文档（被代码引用、运行时需要）
- **`docs/{skill}/`**：开发者看的参考文档（架构设计、设计决策），skill 运行时不依赖
- **`CLAUDE.md`**：纯索引，不含任何 skill 的具体信息，避免污染上下文

## 安装方式

每个 skill 独立发版，通过 GitHub Actions 手动触发（`Actions → Release Skill → 输入 skill 名`）。发布流程自动完成 VERSION patch +1、打 tag（`<skill>-v<ver>`）、生成 zip 资产（内含 `<name>.md` + `<name>/` 目录）并创建 GitHub Release。

安装步骤：

1. 打开 [Releases](https://github.com/caleee/skills/releases)，选择目标 skill 的版本（如 `sub2cfg-v0.1.2`）
2. 下载 zip 资产（`<skill>-v<ver>.zip`）并解压，得到 `<name>.md` + `<name>/` 目录
3. 放入 skill 目录：Claude Code 用 `~/.claude/skills/`，opencode 用 `~/.config/opencode/skills/`

## 新增 Skill

1. 创建根目录 `{skill}.md`（含 `name` / 单行 `description` frontmatter）
2. 创建同名 `{skill}/` 目录，内含 `AGENT.md` 运行说明
3. 创建 `{skill}/VERSION`（初始如 `0.1.0`）
4. 更新 `CLAUDE.md` 与 `README.md` 的 Skill 列表
5. 需要发布时，在 Actions 触发 Release Skill
