---
name: nested-repos
description: 大仓内嵌多个独立小仓的双轨 Git 管理 — 双轨索引、初始化六步、常驻声明段、LF 换行符、提交/推送确认、Zed 单仓面板与故障排查
user-invocable: true
---

# nested-repos — 大仓/小仓双轨 Git 管理

一个主工作仓（**大仓**）内部，按目录内嵌多个各自独立的 Git 仓（**小仓**）。
两者共享同一份工作区文件，但各有 index 与 HEAD：大仓记录细碎开发态，小仓记录团队可见的里程碑。

> **一句话原则**：**判据来自本 skill，取值来自项目 `AGENTS.md` 的声明段**（[`TEMPLATE.md`](TEMPLATE.md)）。

---

## §0 何时必须加载本 skill

**先看这张表**——命中任一场景，加载本 skill 再动手；不要凭印象直接 `git add` / `git commit` / `git push`。

| 场景／用户说法 | 必须先做的事 |
|---|---|
| 「大仓」「小仓」「嵌套仓」「子仓」「内嵌仓库」「双轨」 | 读 §2 模型与 §5 提交规则 |
| 「提交小仓」「推送小仓」「合并小仓」「小仓发版」 | 读 §5；**提交/推送前弹选单确认** |
| 「把小仓改成独立仓」「新加一个小仓」 | 读 §3 初始化六步 |
| 「小仓没提交」「大仓里看到小仓的未提交」「两边状态不一致」 | 读 §9 故障排查 |
| 「Zed 的 Git 面板看到小仓」「Select a repository」「面板只显示一个仓」 | 读 §7 Zed 专章 |
| 「换行符」「CRLF」「Windows 同事」「文件全变了」 | 读 §4 换行符 |
| 在任何**含嵌套 `.git`** 的工作区做 git 操作 | 读 §2、§5，确认操作目标仓 |

**触发词**（agent 语义匹配用）：大仓、小仓、嵌套仓、子仓、内嵌仓库、双轨、仓库嵌套、subrepo、nested repo、小仓提交、小仓推送、Zed Git 面板、换行符 CRLF、`.gitmodules`。

> **为什么需要这一节**：skill 是条件加载的，agent 在跑 `git add` 时未必会主动想起本 skill。
> 因此项目必须在 `AGENTS.md` 写一段**常驻声明**（§10）指向本 skill——常驻的是指针，判据在这里。

---

## §1 定位与边界

- **管**：大仓/小仓的目录结构、双轨跟踪、初始化、忽略与换行符、提交/推送/合并的确认与分支、Zed 中的可见性、故障排查。
- **不管**：提交信息格式（→ `commit-message`）、任务编排（→ `agent-pipeline`）、计划落盘（→ `plan-persist`）、子模块语义（本 skill 刻意**不用** submodule）。
- **零项目路径**：正文只用 `big-repo/`、`services/<name>/`、`<user>` 等占位；具体取值走项目声明段。

---

## §2 模型：大仓与小仓

```text
big-repo/                    ← 大仓（个人／主工作仓，单 .git）
├── docs/                    ← 大仓自有内容
├── services/
│   ├── api/                 ← 小仓 A（目录内有独立 .git）
│   └── web/                 ← 小仓 B（目录内有独立 .git）
└── ...
```

| | 大仓（big repo） | 小仓（nested repo） |
|---|---|---|
| 定位 | 个人／主工作仓 | 团队交付仓或独立服务仓 |
| 远端 | 通常是私有仓 | 团队平台（如 codeup／GitLab） |
| 跟踪 | **逐文件**跟踪小仓目录下的源码与文档 | 只跟踪自己目录内的文件 |
| 提交粒度 | 小步、细碎，记录开发态 | 大步、里程碑，版本可用才提交 |
| 分支 | 固定在主分支 | 每人一个工作分支（`dev-<user>`） |
| 身份 | 大仓全局或 local identity | **小仓 local identity**（与团队一致） |

**双轨的事实**：两个仓共享同一份工作区文件，各自有 index/HEAD。git 允许这样——

- 大仓 `git add` 看到的是工作区文件，与小仓的提交互不影响；
- 小仓提交后，文件内容不变，大仓仍能看到「相对大仓上次提交的改动」；
- 大仓的 `.gitignore` 与小仓的 `.gitignore` 都会被读取（小仓目录下的 `.gitignore` 是普通文件，大仓也读）。

**不是 submodule**：不使用 `.gitmodules`、不记录 gitlink。原因是双轨需要大仓**逐文件**记录开发态，而 submodule 只记一个 commit 指针。

**已跟踪文件优先**：`.gitignore` 里写某文件，不会让已被跟踪的文件消失。若大仓已跟踪小仓的 `AGENTS.md`，小仓 `.gitignore` 写 `AGENTS.md` 只影响小仓。

---

## §3 初始化六步（新小仓接入）

> 前置：该目录**已有独立 `.git`**（`git init` 或 clone）。若没有，先决定它是小仓还是大仓普通目录。

### 第 1 步：确认仓与远端

```bash
git -C services/<name> remote -v
git -C services/<name> branch -a
git -C services/<name> log --oneline -3
```

### 第 2 步：设 local identity 与工作分支

```bash
git -C services/<name> config --local user.name  '<team-name>'
git -C services/<name> config --local user.email '<team-email>'
git -C services/<name> checkout -b dev-<user> <main-branch>
```

用 `--local`，**不要改 global**：只有这个小仓用团队身份，大仓与其他仓不受影响。

### 第 3 步：`.gitignore`（小仓不提交的文件）

至少包含：

```gitignore
# 大仓专属 agent 规范（如有）
AGENTS.md
CLAUDE.md

# 构建产物
target/
dist/
build/
node_modules/
coverage/
*.class
*.jar
*.log

# IDE / OS
.idea/
.vscode/*
!.vscode/extensions.json
**/.DS_Store
```

> 构建产物清单按实际技术栈裁剪。**已跟踪文件不受影响**；若发现产物已被跟踪，先 `git rm --cached` 再提交。

### 第 4 步：`.gitattributes`（换行符）

```gitattributes
* text=auto eol=lf
*.cmd text eol=crlf
```

`eol=lf` 的优先级**高于** Windows 本地的 `core.autocrlf`，队友克隆后得到 LF。`*.cmd` 保留 CRLF（`cmd.exe` 原生要求）。详见 §4。

### 第 5 步：`README.md`（团队可见）

小仓**不带** `AGENTS.md`（agent 规范留大仓），改由 `README.md` 承载团队需要的信息：

- 项目定位与技术栈
- 目录结构
- 本地构建与运行（含环境变量占位，**不写密钥**）
- 测试与门禁命令
- 工程约定与注意事项

README **不写**大仓路径、内部计划/决策编号、agent 协作口径。

### 第 6 步：构建门禁 → 基线提交

```bash
# 按技术栈选一个
./mvnw -B -DskipTests package
pnpm run build
# ...

git -C services/<name> add <明确路径...>
git -C services/<name> commit -m "<type>: 初始基线"
```

**提交前必须按 §5 弹选单确认**。首次基线默认**不 push**，推送另行确认。

### 初始化检查清单

- [ ] `.git` 独立、远端正确
- [ ] local identity 已设，global 未动
- [ ] 工作分支 `dev-<user>` 已建
- [ ] `.gitignore` 命中所有大仓专属文件与构建产物
- [ ] `.gitattributes` 为 LF（`*.cmd` 例外）
- [ ] `README.md` 无大仓路径/内部编号/密钥
- [ ] 构建通过
- [ ] 基线提交经确认，工作区干净

---

## §4 忽略规则与换行符

### 4.1 谁该被忽略

| 文件 | 小仓 | 大仓 |
|---|---|---|
| `AGENTS.md` / `CLAUDE.md` | **忽略**（团队仓不需要 agent 规范） | 正常跟踪（已被跟踪则不受忽略影响） |
| `target/` / `dist/` / `node_modules/` / `coverage/` | 忽略 | 忽略 |
| `.env.*.local` / 凭据 | 忽略 | 忽略 |
| `.env.development` / `.env.production`（无密钥） | 可提交（团队需要） | 可跟踪 |

验证：

```bash
git -C services/<name> check-ignore -v AGENTS.md CLAUDE.md target node_modules dist
```

### 4.2 强制 LF

```gitattributes
* text=auto eol=lf
*.cmd text eol=crlf
```

- `text=auto`：由 git 自动识别二进制，文本文件规范化。
- `eol=lf`：**checkout 时强制 LF**，覆盖队友本地的 `core.autocrlf`。
- `*.cmd`：Windows 批处理保留 CRLF。

**已克隆的队友**需要一次重新规范化：

```bash
git add --renormalize .
git commit -m "chore: 统一换行符为 LF"
```

验证：

```bash
git check-attr text eol -- <file>
# 期望：<file>: text: auto / <file>: eol: lf
```

> **注意**：`.gitattributes` 也应当被两仓共享（同一份工作区文件），大仓同样受其约束。

---

## §5 提交 / 推送 / 合并（确认制）

### 5.1 默认节奏

| 仓 | 提交 | 推送 | 合并 |
|---|---|---|---|
| 大仓 | agent 可自主小步提交 | agent 可自主 push | 大仓自身分支策略 |
| 小仓 | **必须弹选单确认** | **必须弹选单确认** | **必须弹选单确认** |

**小仓确认（硬性）**：任何 `commit`／`push`／合并回主分支之前，agent 必须先调用交互式选单（如 `AskUserQuestion`）让用户确认；**未确认一律不执行**。

选单建议覆盖「执行到哪一步」：

1. 完整流程（提交 → 推送工作分支 → 合并主分支 → 推送主分支）
2. 仅提交并推工作分支
3. 仅本地提交
4. 暂不执行

### 5.2 精确提交

```bash
git -C services/<name> add <明确路径...>
git -C services/<name> commit -m "<type>: <描述>"

# 大仓：只提交指定路径
git commit --only <path...>
```

**禁止**裸 `git add -A` / 裸 `git commit`。原因：双仓共享工作区，误提交会跨仓污染。

### 5.3 合并主分支

主分支名以远端为准（`main` 或 `master`）：

```bash
git -C services/<name> checkout <main>
git -C services/<name> merge --ff-only dev-<user>
git -C services/<name> push origin <main>
git -C services/<name> checkout dev-<user>
```

`--ff-only` 失败说明工作分支落后或已分叉：先 `fetch`／rebase，再决定合并方式。

---

## §6 分支与身份

- **大仓**：固定在主分支（`main`），不额外开分支。
- **小仓**：每人一个 `dev-<user>` 工作分支，从主分支新建；版本确认后合并回主分支。
- **身份**：
  - 大仓沿用个人身份；
  - 每个小仓设 **local** identity，与团队提交邮箱一致。
  - `git config --local` 只影响当前仓，**不要改 global**。

验证：

```bash
git -C services/<name> config --get user.name
git -C services/<name> config --get user.email
git -C services/<name> branch --show-current
```

---

## §7 Zed 专章

> **版本事实（核查于 Zed 1.26.2，2026-11）**：上游行为可能随版本变化，升级后请复核本节。

### 7.1 当前行为

- Zed 的 Git 面板是**单仓库视图**：一次只显示一个 **active repository** 的未提交改动。
- 工作区内的嵌套 `.git` 会被**发现并注册**，但可通过面板的 **“Select a repository…”** 切换。
- 多仓聚合视图对应上游 PR `git_ui: Add multi-repository Git panel view`（opt-in `git_panel.show_all_repositories`），**当时未合并**。
- **没有**「隐藏某个嵌套仓」的稳定设置：`git.discover_nested_repositories` 对应上游 PR **当时仍未合并**。
- Zed 的扫描对 `.git` **目录与 `.git` 文件一视同仁**（按文件名 `.git` 判定）。因此把 gitdir 移到仓外（`--separate-git-dir`）**不能**规避发现。

### 7.2 操作建议

1. 用面板顶部的 **Select a repository…** 固定选中**大仓**。
2. 不要在 Zed 面板里判断「这是哪个仓的改动」——以 `git -C <仓> status` 为准。
3. 编辑小仓文件后，active repository 可能自动切到小仓；切回大仓即可。
4. `file_scan_depth` 可以让深层嵌套仓延迟激活，但**打开其中文件后仍会激活**，属于半可靠方案，不要依赖。

### 7.3 现象与处理

| 现象 | 原因 | 处理 |
|---|---|---|
| 面板里出现大量「未提交」，切到大仓后消失 | active repo 是小仓 | Select a repository… 选大仓 |
| 面板只显示一个仓 | 当前是单仓视图 | 正常；切换仓库，或等上游多仓视图 |
| 想永久隐藏小仓 | 无稳定设置 | 接受切换；或等 `discover_nested_repositories` 合并 |
| 打开小仓文件后面板跳到小仓 | 自动跟随活动文件 | 正常；切回大仓 |

---

## §8 日常操作手册

```bash
# 看两仓各自状态
git status --short
git -C services/<name> status --short

# 大仓小步提交（精确路径）
git commit --only docs/foo.md

# 小仓里程碑提交（先确认！）
git -C services/<name> add <路径...>
git -C services/<name> commit -m "feat: ..."

# 小仓推工作分支（先确认！）
git -C services/<name> push -u origin dev-<user>

# 撤回小仓最近一次提交，保留工作区改动
git -C services/<name> log --oneline -3          # 先核对
git -C services/<name> reset --mixed HEAD~1

# 从大仓视角看小仓目录改动
git status --short -- services/<name>
```

---

## §9 故障排查

| 现象 | 根因 | 处理 |
|---|---|---|
| 小仓 `status` 全是 `??` | 小仓尚无基线提交（空仓或刚 `init`） | 按 §3 完成基线提交 |
| 大仓出现 `?? services/<name>/target/` | 小仓 `.gitignore` 缺构建产物 | 补 `.gitignore`；已跟踪则 `git rm --cached` |
| 大仓 `status` 显示小仓文件改动 | 双轨的正常现象 | 正常；大仓按自己的节奏提交 |
| 换行符把整文件标成改动 | `core.autocrlf`／缺 `.gitattributes` | 按 §4 加规则并 `--renormalize` |
| 文件没改却显示 `M`，`git diff` 为空 | index stat 缓存过期 | `git update-index --refresh -- <path>` |
| 小仓 `.gitignore` 写了 `AGENTS.md`，大仓仍跟踪 | 已跟踪文件不受忽略规则影响 | 正常；若大仓也要忽略，需 `git rm --cached`（谨慎） |
| 小仓 push 被拒、远端无工作分支 | 首次推送未 `-u` 或分支未建 | `git push -u origin dev-<user>` |
| 小仓提交作者错了 | 未设 local identity | `git config --local user.email <team-email>`；必要时 amend |
| Zed 面板显示小仓 | active repository 是小仓 | 见 §7.2 |

---

## §10 项目接入：常驻声明段（关键）

skill 只在被加载时生效。为了让它「像写在 `AGENTS.md` 里一样必然被看到」，**每个使用本 skill 的项目**都要在 `AGENTS.md`（或等价常驻指令文件）写一段**短声明**：

```markdown
## 大小仓（nested-repos 声明）

> 本仓为 nested-repos 结构。操作小仓前先加载 skill `nested-repos`。

- 大仓：本仓根目录（个人工作仓，逐文件跟踪、小步提交）
- 小仓：
  - `services/api/`（团队仓，分支 `dev-<user>`，local identity `<team-email>`）
  - `services/web/`（同上）
- 小仓确认：任何 commit／push／合并前必须弹选单确认
- 换行符：小仓 `.gitattributes` 强制 LF（`*.cmd` 例外 CRLF）
- IDE：Zed Git 面板固定选大仓
```

> **为什么这行必须有**：它每轮注入，agent 即使没触发 skill，也会看到「这里有小仓，操作前先加载」。
> 声明段只放**指针与取值**，完整判据留在本 skill——既不膨胀 AGENTS.md，也不丢可见性。

---

## §11 检查清单

### 提交前（小仓）

- [ ] 已弹选单并得到确认
- [ ] `git -C <仓> status --short` 只含预期文件
- [ ] 无大仓专属文件（`AGENTS.md`／`CLAUDE.md`）与构建产物
- [ ] 构建/门禁通过
- [ ] 作者身份为团队 local identity
- [ ] 提交信息符合项目规范

### 初始化后（新小仓）

- [ ] 六步全部完成
- [ ] `check-ignore` 命中大仓专属文件与产物
- [ ] `check-attr eol` 为 `lf`
- [ ] 工作区干净、远端分支已建（按需）

---

## §12 关联

| skill | 关系 |
|---|---|
| `commit-message` | 提交信息格式 |
| `agent-pipeline` | 任务编排；本 skill 可作为其声明段中的域规则 |
| `plan-persist` | 多步任务先落盘 |

## 变更记录

- 2026-11-03：v0.1.0 首版。双轨模型、初始化六步、LF 换行符、确认制提交、Zed 单仓面板与故障排查；明确「常驻声明段 + 按需 skill」双层布点。
