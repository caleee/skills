# TEMPLATE.md — nested-repos 项目声明模板

把下面这段粘进项目的 `AGENTS.md`（或等价常驻指令文件）。**这是常驻指针**：它保证 agent 每轮都能看到「这里有小仓」，从而在动手前加载 `nested-repos` skill。

> 只写**指针与取值**，不复制 skill 判据。

---

## 声明段模板

```markdown
## 大小仓（nested-repos 声明）

> 本仓为 nested-repos 结构。操作小仓前先加载 skill `nested-repos`。

- **大仓**：本仓根目录（个人工作仓；逐文件跟踪小仓源码，小步提交）
- **小仓**：
  - `<path/a>/`：团队仓，工作分支 `dev-<user>`，local identity `<team-email>`
  - `<path/b>/`：同上
- **小仓确认**：任何 commit／push／合并回主分支前，必须弹选单让用户确认
- **换行符**：小仓 `.gitattributes` 为 `* text=auto eol=lf`，`*.cmd` 例外 CRLF
- **IDE**：Zed Git 面板为单仓视图，固定选大仓（`Select a repository…`）
```

## 字段说明

| 字段 | 取值 |
|---|---|
| 大仓 | 外层仓根目录；说明其定位与提交节奏 |
| 小仓路径 | 每个内嵌独立仓的相对路径 |
| 主分支 | 远端主分支名（`main` 或 `master`，按团队平台） |
| 工作分支 | `dev-<user>`（每人一个，从主分支新建） |
| local identity | 团队要求的 `user.name` / `user.email` |
| 确认方式 | 默认 `AskUserQuestion` 选单；可写明选项偏好 |
| 门禁 | 小仓提交前的构建/测试命令 |
| IDE | 默认 Zed；写明面板固定选大仓 |

## 可选：项目级检查命令

若项目有统一脚本（`tz`／`make`／`pnpm`），可在声明段补一行：

```markdown
- **门禁**：小仓提交前运行 `<命令>`；换行符体检 `<命令>`
```
