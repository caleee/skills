---
name: commit-message
description: 按 Conventional Commits 规范生成 git commit message。用户说"提交"、"commit"、"生成 commit message"、"写提交信息"时使用。Type 保持英文，描述用中文，禁止 emoji。
user-invocable: true
---

# commit-message — 提交规范

按 Conventional Commits 规范生成提交信息。依据 brain 仓库 git 提交规范 wiki 文档改编。

## 触发条件

用户要求提交 / 生成 commit message / 写提交信息时触发：
- 说"提交"、"commit"、"生成 commit message"、"写提交信息"
- 或提交前需要按规范格式化提交信息

## 核心规则

- **Type 英文**，subject/body 中文，**禁止 emoji**
- 格式：`<type>[optional scope]: <subject>`
- subject：祈使句、≤50 字（硬上限 72）、无句号；描述效果而非实现细节
- body：写"为什么"不写"改了什么"；**禁止编造动机**，不确定就问
- 一个逻辑变更一个 commit，不相关改动先拆分

## 流程

0. 提交前检查（如仓库配置了 lint/build 脚本，先探测包管理器与实际脚本，存在才执行；不存在或失败则停下询问）
1. `git status` 查看暂存文件；无暂存则 `git add` 相关文件（只加本逻辑变更涉及的）
2. `git diff`（或 `git diff --cached`）分析变更，确定 type 与 scope
3. 检测是否需要拆分，符合以下任一场景时先拆分（不擅自合并提交）：
   - 混合类型（feat + fix 同仓）
   - 多模块无关改动
   - 源码 / 测试 / 文档混杂
   - 依赖更新混入功能改动
4. 生成 message（simple 单行 / full 带 body+footer），展示后执行 `git commit`
5. 提交后 `git log -1 --stat` 核对文件列表

## body/footer 写作要点（full 风格）

- 默认 simple（单行）；以下场景改用 full：破坏性变更、复杂功能、需解释的修复、跨多系统的改动
- body 写 **what + why**（不写 how）：改了什么、为什么改、对比改动前后行为、引用关联 issue/决策
- 多条改动用 bullet；每行 ≤72 字符
- footer：`BREAKING CHANGE:` 破坏性变更；`Fixes:` / `Closes:` / `Refs:` 关联 issue；`Co-authored-by: 名 <邮箱>` 共同作者；`Reviewed-by:` / `Approved-by:` 评审

## Type 类型

| type | 场景 |
| --- | --- |
| `feat` | 新功能 |
| `fix` | 修 bug |
| `refactor` | 重构（行为不变） |
| `docs` | 仅文档 |
| `style` | 格式化，无逻辑变更 |
| `test` | 测试 |
| `perf` | 性能优化 |
| `build` | 构建/依赖 |
| `ci` | CI/CD |
| `chore` | 杂务 |
| `revert` | 回退 |
| `security` | 安全漏洞 |

## Scope

- 业务域中文（`用户`、`订单`），≤15 字符；跨模块留空
- 常见英文 scope：`api`、`auth`、`ui`、`db`、`config`、`deps`、组件名（`button`、`modal`）、模块名（`parser`、`validator`）

## Footer

- `BREAKING CHANGE: <说明>` 破坏性变更（或在 type 后加 `!`）
- issue 引用：`Fixes #123`、`Closes: #456`
- `Co-authored-by: Name <email>` 共同作者

## 硬性禁止

- ❌ emoji
- ❌ 编造动机（"为什么"拿不准必须问用户）
- ❌ secret / `.env` / 凭证
- ❌ 混合多个逻辑变更
- ❌ 提交 `main`、强推（force push）、amend 已 push 的 commit
- ❌ 过去时、句号结尾、超长 subject（>72）

## 示例

```
feat(购物车): 支持批量删除商品
fix(订单): 修复并发下单库存超卖
refactor(支付): 统一微信和支付宝回调处理
docs: 添加部署说明
```

```
feat(api)!: 订单 id 由整数改为 UUID

BREAKING CHANGE: 以整数解析订单 id 的客户端需在升级前更新
```

## 模板

```
type(scope): 祈使句摘要 ≤50 字（硬上限 72）

- 改了什么（1-3 条 bullet）
- 为什么（ticket 链接或理由）
- 验证方式（测试等）
```