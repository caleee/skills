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
- 站点后端：`vitepress`（默认 `mkdocs`；`build`/`serve`/`deploy` 走对应官方 CLI）
- 目录预算：24（P1；`0` = 关闭校验）
- 上锁文件：`mkdocs.yml`（其余上锁文件见「工作流水线」）
- 门禁：`tz docs --strict build`；体检：`tz docs lint`
```

**字段含义**：这条声明段是给 **agent／人**读的**自然语言取值**；**CLI 本身不读** `AGENTS.md`（它只读 `.llm-wiki.toml` 与命令行参数）。未声明则走最小默认（`docs/` + `docs/raw/` + `docs/dist/`，预算 24，无门禁）。

## 二、`.llm-wiki.toml`（项目根，可选）

```toml
[site]
root = "docs"              # 知识库根（MkDocs 的 docs_dir）
site_dir = "site"          # 构建产物（mkdocs 语义）。vitepress 下默认即 `<docs>/.vitepress/dist`
                           # （官方 outDir），留默认即可；显式改则须与 `config.mts` 的 outDir 一致
config = "mkdocs.yml"      # 站点配置（mkdocs 用；vitepress 用 `docs/.vitepress/config.mts`）
backend = "mkdocs"           # 站点后端：mkdocs（默认）| vitepress
                           # vitepress 侧只认项目本地安装（仓根 `node_modules/.bin/vitepress`，
                           # 另起 `docs/package.json` 装完也找不到），包管理默认 pnpm
                           # vitepress 侧首次 `nav build` 会脚手架最小 `config.mts`（已存在永不动）
port = 8000                # 本地预览端口
nav_mode = "auto"          # auto=由目录生成 .pages(P4) | manual=用 mkdocs.yml 的 nav
                           # （vitepress 下 auto=生成 `sidebar.auto.mts`，分组同名去重已内建）

[lint]
max_children = 24          # P1 目录预算；0 = 关闭
broken_links = true
orphans = true             # 孤儿页：manual 模式下「无人链接且不在 nav」的页面
nav_coverage = true        # 导航可达性：`.pages` 空 nav 隐藏的页面（仅 nav_mode=auto）
semantic = false           # 待确认/过期标记密度（默认关：较慢）
# orphans 与 nav_coverage **按 nav_mode 二选一**（两种模式下总有一条在守导航可达性）：
#   auto   → 目录即导航，「孤儿」判据不适用 ⇒ 由 nav_coverage 替代
#   manual → mkdocs.yml 的 nav 才是真源 ⇒ 由 orphans 守
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
# paths = ["src", "docs"]       # 可选：只看上游这若干子路径的最后 commit，避开整仓噪声

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

## 四、vitepress 落位（`.gitignore` 必备）

> 根 `.gitignore` 若有 `**/.*`（默认忽略一切点目录），`docs/.vitepress/` 会被静默忽略——
> 站点工程建了却不入仓，clone 后“配置丢了”且 `git status` 无提示。按下式**先加白、再排除产物**：

```gitignore
!docs/.vitepress/
!docs/.vitepress/**
docs/.vitepress/dist
docs/.vitepress/cache
docs/.vitepress/.temp
```
