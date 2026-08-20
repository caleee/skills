# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## 仓库结构

本仓库是 Claude Code skill 集合。每个 skill 由一个根目录的 `.md` 文件（技能定义）和一个同名目录（实现文件 + `AGENT.md`）组成。

## Skill 列表

| Skill | 技能定义 | 详细说明 | 描述 |
|-------|----------|----------|------|
| sub2cfg | `sub2cfg.md` | `sub2cfg/AGENT.md` | 订阅链接转代理配置 |
| commit-message | `commit-message.md` | `commit-message/AGENT.md` | 按 Conventional Commits 规范生成提交信息 |

## 文档层次

- **根目录 `.md` 文件**：skill 索引（frontmatter + 指引），供用户/Agent 发现；完整定义在 `<name>/SKILL.md`，避免重复维护
- **`{skill}/SKILL.md`**：Anthropic 标准技能入口，完整 skill 定义（cc-switch 从 ZIP 安装、Claude Code 识别 skill 均依赖它）
- **`{skill}/AGENT.md`**：skill 运行说明，含命令、架构、扩展指南
- **`{skill}/` 内其他文档**：仅放功能上依赖的文档（被代码引用、运行时需要）
- **`docs/{skill}/`**：开发者看的参考文档（架构设计、设计决策），skill 运行时不依赖
- **`CLAUDE.md`**：纯索引，不含任何 skill 的具体信息，避免污染上下文

## 新增 Skill 通用注意事项

开发新 skill 时，除遵循上方结构外，还需满足发布机制（`.github/workflows/release-skill.yml` + `docs/adr/0001-version-and-release-strategy.md`）的要求：

### 结构要求

- 根目录 `<name>.md`：frontmatter 必须含 `name` 和**单行** `description`（workflow 用正则按行提取 description 作为 Release 说明，多行会截断），正文只放一句指引，不重复 SKILL.md 内容
- **`<name>/SKILL.md`**：完整 skill 定义（Anthropic 标准技能入口，cc-switch 从 ZIP 安装、Claude Code 识别 skill 均依赖它）
- skill 名只能用 `[a-zA-Z0-9_-]`（workflow 输入校验限制，命令注入防线）
- 目录内所有文件必须 `git add` 跟踪（打包用 `git archive`，只含 tracked 文件，未跟踪文件不会进 zip）

### VERSION 文件

- 每个 skill 目录必须有 `VERSION` 文件：内容为纯 semver（如 `0.1.0`），无 `v` 前缀
- 首次发布**手动创建**并写入初始版本（如 `0.1.0`），workflow 不负责首次创建，只负责 patch +1
- `VERSION` 是版本号单一事实来源，保持与实际发布一致

### 内容要求

- 根 `.md` 的 description 即 Release 说明的唯一来源，写清楚 skill 用途与触发条件
- 参考其他 skill 的既有约定：命名规范（`sub2cfg`）、触发条件段落、示例与模板
- 从其他仓库引入的文档按需适配（去掉源仓库特化内容，如路径、专用命令），并注明来源

### 完成检查清单

1. `<name>.md` 存在，frontmatter 含 `name` + 单行 `description`
2. `<name>/` 目录存在，含 `AGENT.md` 和 `SKILL.md`（完整定义）；根 `<name>.md` 只含 frontmatter + 指引
3. `<name>/VERSION` 存在且为合法 semver
4. 目录内文件已全部 `git add` 跟踪
5. `CLAUDE.md` Skill 列表与 `README.md` 已同步更新
