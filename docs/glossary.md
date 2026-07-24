# 词汇表

skill 打包发布机制的领域术语。

| 概念 | 定义 |
|------|------|
| **Skill** | 仓库中一个可独立发布的单元 = 根目录 `<name>.md`（skill 定义）+ 同名目录 `<name>/`（实现文件） |
| **VERSION 文件** | skill 目录下的纯文本文件，内容为该 skill 的 semver（如 `0.1.0`），是版本号的单一事实来源。首次由作者手动创建 |
| **版本号** | semver 格式 `MAJOR.MINOR.PATCH`，无 `v` 前缀；每次发布 PATCH +1 |
| **Tag** | git tag，格式 `<skill>-v<version>`（如 `sub2cfg-v0.1.1`），标识某 skill 的一次发布 |
| **Release** | GitHub Release，附 zip 资产 + skill 用途简介（来自根 `.md` frontmatter 的 `description`） |
| **包（zip）** | Release 的资产，用 `git archive` 生成，含 `<name>.md` + `<name>/` 的所有 git tracked 文件 |
| **bump commit** | 发版时由 `github-actions[bot]` 产生的自动提交，更新 VERSION 文件，message 格式 `chore(<skill>): release v<ver> [skip ci]` |
| **description** | skill 根 `.md` frontmatter 中的 `description` 字段，作为 Release 说明的 skill 用途简介 |
