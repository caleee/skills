# ADR-0001: Skill 版本与发布策略

- 状态：已接受
- 日期：2026-07-24

## 背景

本仓库（`caleee/skills`）是个人公开的 Claude Code skill 集合。每个 skill 是一个可独立发布的单元：根目录 `<name>.md`（skill 定义）+ 同名目录 `<name>/`（实现文件）。skill 数量会持续增长，首个完成的是 sub2cfg。

需要一个 GitHub Actions workflow 实现：每个 skill 单独打包、独立版本号、手动选择某个 skill 进行 tag 与 release。

## 决策

### 1. 版本号管理

- 每个 skill 目录下维护 `VERSION` 文件，内容为纯 semver（如 `0.1.0`），无 `v` 前缀。
- `VERSION` 是版本号的**单一事实来源**。
- 首次发布由作者**手动创建** `VERSION` 文件并写入初始版本（如 `0.1.0`），workflow 不负责首次创建。
- 每次发布自动 patch +1（`0.1.0 -> 0.1.1`），不按 commit 类型区分。

### 2. Tag 命名

- 格式：`<skill>-v<version>`，如 `sub2cfg-v0.1.1`。
- Tag 打在 VERSION bump 产生的 commit 上（确保 zip 内容、VERSION 文件、tag 三者一致）。

### 3. 发布流程

1. `workflow_dispatch` 手动触发，文本输入 skill 名。
2. workflow 校验 `<name>.md` + `<name>/` + `<name>/VERSION` 三者存在，且 VERSION 内容是合法 semver。
3. 读取 VERSION，patch +1，写回文件。
4. `github-actions[bot]` 提交 bump（`chore(<skill>): release v<ver> [skip ci]`）并 push。
5. 在新 commit 上打 tag `<skill>-v<ver>` 并 push。
6. 用 `git archive` 打 zip 包（仅 git tracked 文件，含 `<name>.md` + `<name>/`）。
7. 从 `<name>.md` frontmatter 提取 `description` 作为 Release 说明（skill 用途简介）。
8. 创建 GitHub Release，附 zip 资产。

### 4. 权限与副作用

- workflow 需要 `permissions: contents: write`（commit、push tag、创建 Release）。
- bump commit 加 `[skip ci]` 避免触发其他 CI。

## 备选方案与否决理由

| 方案 | 否决理由 |
|------|----------|
| 版本号来源用 tag 而非 VERSION 文件 | 仓库内无法直接看到每个 skill 当前版本 |
| 按 commit 类型递进（feat=minor / fix=patch / breaking=major） | 实现复杂（需按 path 过滤 commit），patch +1 已足够 |
| tag 打在触发时 commit 上，不产生 bump commit | VERSION 文件会落后 tag 一个版本，破坏"单一事实来源" |
| `workflow_dispatch` 用 choice 下拉选 skill | GitHub choice 选项静态写死在 yaml，新增 skill 要改 workflow；改用文本输入 + 校验 |
| Release 附安装指引 | 不同 skill 安装步骤差异大（sub2cfg 需 Python，纯 md skill 不需要），统一模板不准确；改为只放 skill 用途简介，安装由用户自行处理 |

## 后果

- 每次发版产生一个 `github-actions[bot]` 自动 commit。
- 新增 skill 只需创建 `<name>.md` + `<name>/` + `<name>/VERSION`，**无需改 workflow**。
- Release 说明只有 skill 用途简介 + 版本号，无安装指引；作者如需可手动编辑 Release body 补充。
- zip 包用 `git archive` 生成，自动排除 `__pycache__` / `.pytest_cache` / `.DS_Store` 等未跟踪文件。
