# AGENT.md — plan-persist

## 何时建

- 预估 ≥3 步骤或用户说“先规划/做大 plan” → 直接建 `.agent/plans/NN-<slug>.md`；单行问答/小改不建。
- 显式调用 `/plan-persist` 时不论步骤数均建。

## 初始化（安装即建，幂等）

```bash
mkdir -p .agent/plans/archived
# .agent/plans/index.md 不存在时建极简列表（每行 "NN - 标题 (状态)"）
test -f .agent/plans/index.md || printf "# 计划索引\n\n" > .agent/plans/index.md
# Muse 兼容相对软链
mkdir -p .claude
test -L .claude/plans || ln -s ../.agent/plans .claude/plans
# 校验
ls -la .agent/plans/ && readlink .claude/plans && cat .agent/plans/index.md
```

> `.agent/` 已在根 `.gitignore`，plan 不入仓；下一序号取 `max(NN)+1`。

## 新建

1. 读 `CONTEXT.md` 对齐术语；读 `.agent/plans/index.md` 定下一 `NN`。
2. 按 `SKILL.md` 7 段（Context / 一源码与落位 / 二现状差距表 / 三协作关系 / 四大计划 / 五各模块小计划 / 六进度表 / 七执行记录 + 验证）写入 `NN-<slug>.md`。
3. 在 `index.md` 追加一行 `NN - 标题 (进行中)`。

## 执行中更新

- 每完成一模块：进度表该行改 `☑ 已完成 (YYYY-MM-DD)`，七、执行记录追加一行 `日期 | 动作 | 备注`，`index.md` 状态同步。
- 增删文件同步改“源码与落位”与“现状差距表”。
- 小改原位留痕；大范围变更另起新 `NN+1-*.md`，旧 plan 标“已废弃 → NN+1”并 `mv` 至 `archived/`。

## 中断续作

```bash
cat .agent/plans/index.md
# 选最新未完成（非已完成/已归档/已废弃），读其进度表
cat .agent/plans/NN-*.md
# 以进度表为准，确认后继续，不重问已定事项
```

## 归档与废弃

```bash
# 完成后
# plan 内进度表改"已归档"，index.md 同步
# 废弃
mv .agent/plans/NN-old.md .agent/plans/archived/
# index.md 该行改"已废弃"并可注"→ NN-new"
```

## 存量迁移（按需）

提到旧 `~/.agent/plans/xxx.md` 时再 `cp ~/.claude/plans/xxx.md .agent/plans/NN-xxx.md` 并补索引。

## 重要文件

- `plan-persist/SKILL.md` — 完整规范（触发/5段清单/状态机/发现/演进）
- `CONTEXT.md` — 共享词汇（模块/落盘/续作/五态机）
- `docs/adr/0002-plan-persist.md` — 35 决
- `.agent/plans/index.md` — 多 plan 发现入口（唯一可信索引）

## 注意事项

- 单行 `description` 校验：`python3 -c "import re; assert re.search(r'^description:\s*.+', open('plan-persist.md').read(), re.M)"`
- 不带独立模板文件与脚本，轻量文字清单即够。
