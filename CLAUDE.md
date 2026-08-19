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

- **根目录 `.md` 文件**：skill 定义，供用户/Agent 发现 skill 存在
- **`{skill}/AGENT.md`**：skill 运行说明，含命令、架构、扩展指南
- **`{skill}/` 内其他文档**：仅放功能上依赖的文档（被代码引用、运行时需要）
- **`docs/{skill}/`**：开发者看的参考文档（架构设计、设计决策），skill 运行时不依赖
- **`CLAUDE.md`**：纯索引，不含任何 skill 的具体信息，避免污染上下文