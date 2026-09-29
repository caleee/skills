# AGENT.md — agent-doctor

## 运行

```bash
# 安装后（示例装在 ~/.agents/skills/；Claude Code 为 ~/.claude/skills/）
bash ~/.agents/skills/agent-doctor/scripts/doctor.sh [--json|--quiet|--online|--help]

# 在本仓内开发时
bash agent-doctor/scripts/doctor.sh
```

- 零依赖：仅 `bash` + POSIX 工具（`find`/`grep`/`sed`/`tr`）；`jq` 可选（缺失时 JSON 相关检查降级为 warn/info）。
- 兼容 macOS 自带 **bash 3.2**。⚠️ 写本脚本时注意：**变量后紧跟全角字符必须写 `${var}`**，否则 3.2 会把多字节字符的首字节并入变量名（报 `pkg?: unbound variable`）。
- 只读，绝不修改任何配置。

## 架构

单文件、顺序执行 7 类检查；结果统一经 `rec(check, target, status, detail)` 收集，最后按 `--json` 与否渲染。

```
doctor.sh
  ├── check_instructions   [1] 全局指令分发（~/.agents/install.sh 产物核对）
  ├── check_pi_packages    [2] pi 扩展加载（已安装 ≠ 已加载）
  ├── check_pi_tools       [3] pi defaultTools 启用情况
  ├── check_mcp            [4] MCP server（stdio 命令存在性 / URL 可达性）
  ├── check_skills         [5] skills 软链断链
  ├── check_hooks          [6] hooks 脚本存在 + 可执行
  └── check_secrets        [7] 明文凭据（分享型文件 + git 跟踪状态）
```

渲染入口：`render_human`（默认）/ `render_json`（`--json`）。

## 检查项与判定标准

| # | 检查 | 判定 | 依据 |
|---|------|------|------|
| 1 | 全局指令分发 | cc 有 `@<真源>` 行或受管区块；pi/Codex 有受管区块；opencode `instructions` 含真源；C 类（pi/Codex）残留整行 `@` = **warn**（死文本） | `~/.agents/install.sh` 的三类接入契约 |
| 2 | pi 扩展加载 | `settings.packages[]` 每项在 `node_modules/<name>` 存在，且其 `pi.extensions`／`main` 入口文件存在 | pi 的「装了 ≠ 加载」模式 |
| 3 | pi defaultTools | 与平台期望集比对（非 Windows 不含 `powershell`） | 缺失 = warn（可能是有意精简） |
| 4 | MCP | stdio：`command -v` 或路径可执行；URL：仅 `--online` 时 curl 探测 | crg／cc-switch 死条目 |
| 5 | skills | `find -L <dir> -maxdepth 1 -type l` 非空 = 断链 | 软链指向已删真源 |
| 6 | hooks | cc `settings.hooks[*].hooks[*].command` 为文件路径时，存在且可执行 | — |
| 7 | 明文凭据 | ① 分享型文件名（`public`/`share`/`template`/`example`）含真实凭据 → fail；② 含凭据且被 `git ls-files` 跟踪 → fail；其余 → info | 以「文件名 + 跟踪状态」判定，不误报 `auth.json`／`config.toml` 这类预期凭据存储 |

## 重要文件

- `agent-doctor/scripts/doctor.sh` — 本体（唯一可执行文件）
- `agent-doctor/SKILL.md` — 触发条件／报告解读／故障→修复映射
- `agent-doctor.md` — 根索引
- `~/.agents/` — 真源与 `install.sh`（检查项 1 的契约来源；本 skill 不修改它）

## 扩展指南

### 新增一个 agent

1. 在 `check_instructions` 的 `for pair in ...` 列表加 `name:path`（C 类）/ 在 A、B 分支加分支。
2. 若该 agent 有独立的 MCP／skills／hooks 布局，在对应 `check_*` 里加循环分支。

### 新增一类检查

1. 在 `CHK_NAMES_KEYS` 数组登记 id，并在 `chk_name()` 加中文名。
2. 写 `check_xxx()`，内部用 `rec <id> <target> pass|warn|fail|info <detail>` 记录。
3. 在 `main()` 的检查序列中加入调用。
4. 同步更新本文件的检查项表（如 `SKILL.md` 有对应修复映射也一并补）。

### 自测（不改真实环境）

```bash
bash -n agent-doctor/scripts/doctor.sh          # 语法检查

# 假 HOME 造故障，验证判定逻辑
T=/tmp/doc-test; rm -rf "$T"; mkdir -p "$T/.pi/agent/skills"
ln -s /nonexistent "$T/.pi/agent/skills/broken"
HOME="$T" bash agent-doctor/scripts/doctor.sh   # 应报断链 FAIL
```

## 注意事项

- 分享型文件的判定只认文件名含 `public`/`share`/`template`/`example`，以免把 `auth.json` 这类**预期**凭据存储误报成问题。
- 新增检查项时，先在假 `HOME` 下造出「命中」与「不命中」两种样例，再上真实环境跑。
