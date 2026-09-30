# TEMPLATE — 项目声明段与配置

> 复制到项目 `AGENTS.md`（声明段）＋ 项目根 `.llm-wiki.toml`（可选配置）。

## 一、`AGENTS.md` 声明段

> **只写本 skill 独有取值**。落库分流的落点（决策台账／计划／设计稿／时间线／环境事实）
> **归 `agent-pipeline` 的 `## 工作流水线` 声明段**，本节**不重复**——两处都写＝双真源。

```markdown
## 知识库

> 判据见 `llm-wiki` skill；落库落点见「工作流水线」声明段。

- 知识库根：`docs/`
- 源层：`docs/raw/`（不可变素材）
- 出口层：`docs/dist/`（唯一对外面）
- 站点配置：`mkdocs.yml`；机器可读配置：`.llm-wiki.toml`
- 目录预算：24（P1；`0` = 关闭校验）
- 上锁文件：`mkdocs.yml`（其余上锁文件见「工作流水线」）
- 门禁：`tz docs --strict build`；体检：`tz docs lint`
```

**字段含义**：`llmwiki` 与各 agent 只认这些**声明值**；未声明则走最小默认（`docs/` + `docs/raw/` + `docs/dist/`，预算 24，无门禁）。

## 二、`.llm-wiki.toml`（项目根，可选）

```toml
[site]
root = "docs"              # 知识库根（MkDocs 的 docs_dir）
site_dir = "site"          # 构建产物
config = "mkdocs.yml"      # 站点配置
port = 8000                # 本地预览端口
nav_mode = "auto"          # auto=由目录生成 .pages(P4) | manual=用 mkdocs.yml 的 nav

[lint]
max_children = 24          # P1 目录预算；0 = 关闭
broken_links = true
orphans = true
semantic = false           # 默认关（较慢）；`llmwiki lint --semantic` 可临时开

[drift]
# 上游仓 → 我方分析篇（`llmwiki drift` 比对 git 落笔时差）
# [[drift.watch]]
# upstream = "ext-repos/pm/pm-contract-component"
# analysis = "docs/pm-code-analysis/components/pm-contract"

[export]
llms_txt = false           # `llmwiki export --llms-txt` 的默认开关

[pdf]
# mermaid → PNG 中转时使用的主题映射（深色纸面用 dark）
[pdf.theme_map]
"monokai-warm" = "dark"
"dracula-soft" = "dark"
```

## 三、最小可用步骤（新项目）

```bash
mkdir -p docs/raw docs/dist
llmwiki nav build          # 由目录生成 .pages（P4）
llmwiki lint               # 体检：目录预算 / 断链 / 孤儿
llmwiki check-deps         # 需要构建站点时再装 mkdocs
llmwiki serve start
```
