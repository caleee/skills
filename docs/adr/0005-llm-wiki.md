# ADR-0005：llm-wiki skill（知识库体系 + 文档站工具链）

- 状态：已接受
- 日期：2026-09-30
- 前序：ADR-0004（agent-pipeline）；理论源头：Andrej Karpathy 的 **LLM Wiki pattern**

## 背景

tenant 仓积累了成熟的知识库治理实践（三层模型、落库分流、多写者纪律）与约 640 行文档站工具链（`tzkit/docs/`）。二者都与该仓强耦合，**无法复用到其他项目**——每换一个项目就要重新发明一遍目录规范与工具。

需要裁决：是否抽成 skill、抽哪些、边界在哪。

## 决策

**建立 `llm-wiki` skill**，三部分：

1. **判据层**（`SKILL.md`）：三层模型（源/编译/出口）· 目录四理念（P1–P4）· 落库分流（五类真源）· 三操作（ingest/query/lint）· 多写者治理。
2. **CLI**（`cli/llmwiki`）：`check-deps` / `build` / `deploy` / `serve` / `nav build` / `lint` / `drift` / `export` / `pdf`。
3. **模板**（`TEMPLATE.md`）：项目 `## 知识库` 声明段 ＋ `.llm-wiki.toml`。

**四个关键取舍**：

| 取舍 | 决定 | 理由 |
|---|---|---|
| CLI 放哪 | skill 内 `cli/`（自包含） | `git archive` 打包即完整可复现 |
| 是否迁移便携包（package 家族 ~200 行，含 Chromium runtime） | **不迁移**（废弃） | tenant 已定「不打包」；通用项目无此需求 |
| CLI 依赖 | 本体 stdlib-only；`build`/`serve`/`pdf` 调外部 `mkdocs`/`mmdc` | 判据类零依赖、可离线；构建类复用项目环境 |
| 配置载体 | 项目根 `.llm-wiki.toml` | 与 `mkdocs.yml` 解耦；自然语言的声明段归 agent 读 |

## 原因

1. **可转移性**：知识库治理是**跨项目**需求（每个项目都要目录规范与保鲜），留在单仓等于每个项目重新发明。
2. **单一真源**：判据（怎么组织）与取值（目录叫什么）分离——沿用 ADR-0004 已确立的模式。
3. **理论有源**：Karpathy 的 LLM Wiki pattern 提供第一性框架，使散落的治理决定（决策台账、一行式时间线、落库分流）获得**同一解释**，而非各自为政的手续。
4. **补真实缺口**：原体系只有**格式 lint**（`build --strict`）；**目录预算、孤儿页、漂移检测**是空白。P1 若无执行者，就只是文字。

## 备选与否决

| 备选 | 否决理由 |
|---|---|
| 留在 tenant，其他项目照抄 | 照抄即漂移；修正无法回流 |
| 只抽判据、不抽 CLI | 判据没有执行手段，落地成本仍高（P4 尤其依赖 `nav build`） |
| 连便携包一起迁 | 与「不打包」口径冲突；为无人使用的功能维护 Chromium 下载逻辑 |
| 做成 MCP 服务 | 判据类无需常驻进程；MCP 只在「跨项目查询索引」时才可能值得 |

## 后果

- **新项目接入成本**：一个 `## 知识库` 声明段 ＋ 一个 `.llm-wiki.toml`。
- **tenant 侧**：`tz docs` 退化为 forwarder（保「操作一律走 `tz`」铁律）；`package` 系列废弃。
- **`lint` 成为 P1 的执行者**——目录预算从理念变成可校验的门禁。
- **与 `agent-pipeline` 的边界**：本 skill 管**空间轴**（结构/保鲜/交付），agent-pipeline 管**时间轴**（何时做哪步），交叉点仅在流水线收尾环。
- 首次在 tenant 上运行 `lint` 即命中 3 处 P1 超预算（`raw/design/multi-tenant` 77 项等）——验证了判据的有效性。
