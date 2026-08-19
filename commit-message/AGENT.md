# AGENT.md — commit-message

## 运行命令

```bash
# 查看暂存文件与变更
git status
git diff              # 未暂存变更
git diff --cached     # 已暂存变更

# 暂存（只加本逻辑变更涉及的文件）
git add <file>...

# 提交
git commit -m "<type>[scope]: <subject>"
git commit            # 打开编辑器写 full 风格（body + footer）

# 核对
git log -1 --stat
```

## 工作流要点

1. 无暂存文件时，只 `git add` 本次逻辑变更涉及的文件，禁止 `git add -A` 混入无关改动
2. 用 `git diff` 分析变更确定 type 与 scope；拿不准的 type 可参考 `AI-Agent提交规范.md` 的 type 表
3. 检测到混合类型 / 多模块 / 超大改动时，先建议拆分，不擅自合并提交
4. simple 风格（默认）：单行 `<type>[scope]: <subject>`；full 风格：body 写"为什么"，footer 放 BREAKING CHANGE / issue / 共同作者
5. 生成后先展示给用户确认再执行 `git commit`；提交后 `git log -1 --stat` 核对

## 重要文件路径

- `commit-message.md` — skill 定义（触发条件、规则、示例）
- `commit-message/AI-Agent提交规范.md` — 完整规范（body/footer 写作指南、拆分策略、最佳实践）

## 注意事项

- 规范源自 `brain/wiki/software/git/AI-Agent提交规范.md`，本仓库为适配副本（去掉了 brain 仓库特化的 pnpm 预检与全量 add 行为）
- 仓库原有提交历史可能含 emoji（如 ♻️），但本 skill 规范禁止 emoji，以本 skill 为准
- pre-commit 检查（lint/build）按目标仓库实际脚本执行，不存在则跳过