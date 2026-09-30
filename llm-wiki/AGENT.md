# AGENT.md — llm-wiki

> 判据见 [`SKILL.md`](SKILL.md)；项目声明模板见 [`TEMPLATE.md`](TEMPLATE.md)。

## 何时用本 skill

| 场景 | 动作 |
|---|---|
| 新建/重组知识库 | 先定三层（源/编译/出口），再按 P1–P4 排目录 |
| 目录"越用越乱" | `llmwiki lint` 看超预算目录 → 按 P2/P3 重新分组 |
| 收尾/定期体检 | `llmwiki lint --semantic` ＋ 交叉引用核对 |
| 交付成品 | 出口层材料化；**源层不得直转出口** |
| 上游代码变了 | `llmwiki drift` 找过期的分析篇 |

## 快速开始

```bash
# 1) 读项目声明（AGENTS.md 的 `## 知识库` 段）；无声明则用最小默认
# 2) 体检
llmwiki lint

# 3) 导航（P4：由目录生成，不手工维护 nav）
llmwiki nav build

# 4) 站点
llmwiki check-deps
llmwiki build --strict
llmwiki serve start          # 默认增量；增删页/改 nav 后用 --full
```

## 架构

```
llm-wiki/
├── SKILL.md      判据（零项目路径假设）
├── TEMPLATE.md   项目声明段 + .llm-wiki.toml 模板
├── AGENT.md      本文件（运行时指引）
├── VERSION       semver（发布用）
└── cli/llmwiki   CLI：stdlib-only 判据类 + 调用 mkdocs 的构建类
```

- **CLI 读配置的顺序**：命令行参数 → `.llm-wiki.toml` → `AGENTS.md` 声明段 → 最小默认。
- **CLI 不写项目文件**（除 `nav build` 生成的 `.pages` 与 `build` 产物）。

## 扩展点

- **新增 lint 规则**：在 `cli/llmwiki` 的 `cmd_lint` 内加检查函数，返回 `(级别, 说明)` 列表；规则须**机械可判**（有明确判据），语义类归 `--semantic`。
- **新增 nav 生成器**：`cmd_nav_build` 的 `render_pages(directory)`——默认产出 MkDocs `awesome-pages` 的 `.pages`。
- **新增站点后端**：目前仅 MkDocs；若换后端，替换 `build`/`serve` 的实现，判据层不动。

## 与其它 skill 的边界

| skill | 管什么 | 交叉点 |
|---|---|---|
| `agent-pipeline` | **时间轴**：何时做哪一步 | 其收尾环引用本 skill 的落库判据 |
| `plan-persist` | 执行期看板（`.agents/plans/`） | 本 skill 的「计划落点」声明指向它 |
| `domain-modeling` | 领域术语与 ADR | 术语表/ADR 归它；目录结构归本 skill |
| `writing-for-agents` | 怎么写给 agent 看的文档 | 本 skill 的文件本身按其规范写 |

## 注意事项

- **不要**在本 skill 里写任何具体项目的路径——那会立刻造成「判据 vs 取值」双真源（历史教训：路由行内联阈值）。
- 项目声明段只写**取值**，不写判据；判据永远只有一份（`SKILL.md`）。
