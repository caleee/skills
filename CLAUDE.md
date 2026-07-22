# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 仓库结构

本仓库是 Claude Code skill 集合。每个 skill 由一个根目录的 `.md` 文件（技能定义，用于 Claude 交互）和一个同名目录（实现文件 + `AGENT.md` 详细说明）组成。

## Skill 列表

| Skill | 技能定义 | 详细说明 | 描述 |
|-------|----------|----------|------|
| sub2cfg | `sub2cfg.md` | `sub2cfg/AGENT.md` | 订阅链接转代理配置 |

## 通用约定

- 根目录下不放置实现代码，只放 skill 定义文件（`.md`）和项目级配置
- 每个 skill 目录下需包含 `AGENT.md`，描述该 skill 的架构、命令、扩展指南
- 新增 skill 时，在本表添加一行，并在对应目录下创建 `AGENT.md`