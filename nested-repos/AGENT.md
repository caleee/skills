# AGENT.md — nested-repos

> 完整判据见 [`SKILL.md`](SKILL.md)；项目声明模板见 [`TEMPLATE.md`](TEMPLATE.md)。

## 何时用本 skill

| 场景 | 动作 |
|---|---|
| 目录里同时有外层仓和内层 `.git` | 先读 `SKILL.md` §2、§5，确认操作目标仓 |
| 新小仓接入 | 按 `SKILL.md` §3 六步执行 |
| 小仓要提交/推送/合并 | **先弹选单确认**，再执行（§5） |
| 大仓里看到小仓的未提交 | 正常双轨现象（§2、§9） |
| Zed 面板显示小仓 | 面板切回大仓（§7） |
| 换行符大范围漂移 | 检查 `.gitattributes` 并 `--renormalize`（§4） |
| 大仓出现 `?? <小仓>/target/` | 小仓 `.gitignore` 缺产物（§9） |

## 快速开始（新小仓）

```bash
# 1) 确认仓与远端
git -C services/<name> remote -v

# 2) local identity + 工作分支
git -C services/<name> config --local user.name  '<team-name>'
git -C services/<name> config --local user.email '<team-email>'
git -C services/<name> checkout -b dev-<user> <main-branch>

# 3) .gitignore 补：AGENTS.md / CLAUDE.md / 构建产物
# 4) .gitattributes:
#      * text=auto eol=lf
#      *.cmd text eol=crlf
# 5) README.md 写团队可见信息（不含大仓路径/内部编号/密钥）

# 6) 构建门禁 + 基线提交（提交前弹选单确认）
```

## 提交前 checklist（小仓）

- [ ] 已弹选单并确认
- [ ] `status --short` 只含预期文件
- [ ] 无 `AGENTS.md`／`CLAUDE.md`／构建产物
- [ ] 构建通过
- [ ] 作者为团队 local identity
- [ ] 精确 `add`，未用 `git add -A`

## 诊断命令

```bash
# 两仓状态对照
git status --short
git -C services/<name> status --short

# 忽略规则
git -C services/<name> check-ignore -v AGENTS.md CLAUDE.md target

# 换行符
git -C services/<name> check-attr text eol -- <file>

# 身份/分支
git -C services/<name> config --get user.email
git -C services/<name> branch --show-current
```
