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

**字段含义**：这条声明段是给 **agent／人**读的**自然语言取值**；**CLI 本身不读** `AGENTS.md`（它只读 `.llm-wiki.toml` 与命令行参数）。未声明则走最小默认（`docs/` + `docs/raw/` + `docs/dist/`，预算 24，无门禁）。

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
orphans = true             # 孤儿页（`nav_mode=auto` 时自动替换为导航可达性检查）
nav_coverage = true        # 导航可达性：报出 `.pages` 空 nav 隐藏的页面（独立开关）
semantic = false           # 默认关（较慢）；`llmwiki lint --semantic` 可临时开
ignore = [".tmp", "archive", "node_modules", ".git"]
# `ignore` 有两类语义（命中即跳过）：
#   单段名（如 archive）      → 出现在路径任一层即跳过
#   子路径前缀（如 raw/asset） → 该前缀及其下全部跳过
# 用途：P1 只管「编译层的可读文档」；源层素材（原始导出／单据／截图集）不该计入预算。

[drift]
# 上游仓 → 我方分析篇（`llmwiki drift` 比对 git 落笔时差）
# [[drift.watch]]
# upstream = "ext-repos/pm/pm-contract-component"
# analysis = "docs/pm-code-analysis/components/pm-contract"

[export]
llms_txt = false           # 默认是否导出；true 时 `llmwiki export` 不传旗标也导出

[pdf]
# mermaid → PNG 中转时的主题映射；与内置默认**合并**，同名键以本配置为准
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
