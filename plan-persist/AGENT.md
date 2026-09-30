# AGENT.md — plan-persist

## 何时建

- 预估 ≥3 步骤或用户说“先规划/做大 plan” → 直接建 `.agents/plans/<业务>/NN-<slug>.md`；单行问答/小改不建。
- 显式调用 `/plan-persist` 时不论步骤数均建。

## 初始化（安装即建，幂等）

```bash
# 业务目录名自定义（示例 mt）；单业务小项目（plan 总数 <24）可省略该层
BIZ=mt
mkdir -p ".agents/plans/$BIZ" ".agents/plans/archived/$BIZ"
# index.md 不存在时建极简列表（按业务分节）
test -f .agents/plans/index.md || printf "# 计划索引\n\n" > .agents/plans/index.md
grep -qxF "## $BIZ" .agents/plans/index.md || printf '## %s\n\n' "$BIZ" >> .agents/plans/index.md
# Muse / Claude Code 兼容相对软链
mkdir -p .claude
test -L .claude/plans || ln -s ../.agents/plans .claude/plans
# 校验
ls -la ".agents/plans/$BIZ" && readlink .claude/plans && cat .agents/plans/index.md
```

> `.agents/` 已在根 `.gitignore`，plan 不入仓；**该业务目录**的下一序号取 `max(NN)+1`。

## 新建

1. 读 `CONTEXT.md` 对齐术语；读 `.agents/plans/index.md` 定目标业务的下一 `NN`。
2. 按 `SKILL.md` 5 段+验证（Context / 模块归类表[可展开为源码与落位/现状差距/协作关系三表] / 大计划 / 各模块小计划 / 进度表+执行记录 / 验证）写入 `.agents/plans/<业务>/NN-<slug>.md`。
3. 在 `index.md` 该业务节下追加一行 `NN - 标题 (进行中)`。

## 执行中更新

- 每完成一模块：进度表该行改 `☑ 已完成 (YYYY-MM-DD)`，执行记录追加一行 `日期 | 动作 | 备注`，`index.md` 状态同步。
- 增删文件同步改“源码与落位”与“现状差距表”。
- 小改原位留痕；大范围变更另起新 `NN+1-*.md`，旧 plan 标“已废弃 → NN+1”并 `mv` 至 `archived/<业务>/`。

## 中断续作

```bash
cat .agents/plans/index.md
# 按业务节选最新未完成（非已完成/已归档/已废弃），读其进度表
cat .agents/plans/<业务>/NN-*.md
# 以进度表为准，确认后继续，不重问已定事项
```

## 归档与废弃

```bash
# 完成后
# plan 内进度表改"已归档"，index.md 同步
# 废弃
mv .agents/plans/<业务>/NN-old.md .agents/plans/archived/<业务>/
# index.md 该行改"已废弃"并可注"→ NN-new"
```

## 存量迁移（按需）

提到旧 `.agent/plans/xxx.md`（或 `~/.claude/plans/xxx.md`）时再 `cp` 到 `.agents/plans/<业务>/NN-xxx.md` 并补索引；`.agent`（单数）为旧目录名，一律并入 `.agents`。

## 目录预算（硬性）

- 任一目录**直接子项 ≤24**；超限先分组（新增业务目录或再分层）。
- 业务目录名自由命名（`[a-z0-9_-]+`），一经采用勿随意改名（改名会切断续作线索）。

## 重要文件

- `plan-persist/SKILL.md` — 完整规范（触发/5段清单/状态机/发现/演进）
- `CONTEXT.md` — 共享词汇（模块/落盘/续作/五态机/业务类型目录）
- `docs/adr/0002-plan-persist.md` — 35 决
- `.agents/plans/index.md` — 多 plan 发现入口（唯一可信索引）

## 注意事项

- 单行 `description` 校验：`python3 -c "import re; assert re.search(r'^description:\s*.+', open('plan-persist.md').read(), re.M)"`
- 不带独立模板文件与脚本，轻量文字清单即够。
