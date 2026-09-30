# ADR-0006：tzkit 通用能力 → skills 迁移（office-docs / mysql-cli / redis-cli / svc-ops / http-probe）

- 状态：已接受
- 日期：2026-09-30
- 前序：ADR-0005（llm-wiki——同模式先例）；ADR-0001（版本与发布策略）
- 源头：tenant 仓 `tools/tzkit`（约 10.5k 行、零第三方依赖的 Python CLI 工具集）

## 背景

tenant 的 `tz` CLI（`tzkit` 包）里沉淀了大量**与 tenant 业务无关的通用能力**——PPTX/XLSX 定点编辑、
MySQL/Redis 访问、进程与端口编排、HTTP 客户端、环境加载等。这些能力**每个工程都用得上**，
却锁死在 tenant 单仓：换项目就得重写一遍，修正也无法回流。

ADR-0005 已就**同一模式**做出先例：把 tenant 的文档站工具链抽成 `llm-wiki` skill，tenant 侧
`tz docs` 退化为 forwarder。本 ADR 把该模式**推广到 tz 的其余通用能力**。

需要裁决：抽成哪些 skill、粒度、安装方式、以及「工程改通用能力」如何回流。

## 决策

把 tz 的通用能力抽成**带 CLI 的独立发布 skill**，落到本仓，做到新工程「`ln` 即用」。

**产出一个 skill 的固定形态**（沿用 ADR-0005 / 仓 `AGENTS.md` 硬约束）：

```
<name>.md              # frontmatter name + 单行 description（Release 元数据）+ user-invocable
<name>/{SKILL.md, AGENT.md, TEMPLATE.md, VERSION, cli/<name>}
```

**本轮抽出的 5 个 skill**（＋既有 `llm-wiki`）：

| skill | 源模块（tenant `tzkit/`） | 命令面 | 声明段 / 配置文件 |
|---|---|---|---|
| `office-docs` | `report/{pptx,xlsx,__init__}.py` | `pptx …` / `xlsx …`（定点编辑 + md→xlsx） | `## 办公文档` / `.office-docs.toml` |
| `mysql-cli` | `sql.py`＋`dbimport.py`＋`mt/migrate.py` | `ping/query/script/tables/sample/backup/import/migrate-check` | `## 数据库` / `.mysql-cli.toml` |
| `redis-cli` | `redis_cli.py` | `ping/exec/keys` | `## 缓存` / `.redis-cli.toml` |
| `svc-ops` | `proc.py`＋`mt/svc.py`（通用部分）＋`envcmd.py` | `start/stop/restart/status/health`（服务表驱动） | `## 本地服务` / `.svc-ops.toml` |
| `http-probe` | `http.py` | `request/get/post`（＋任意方法） | `## 接口调试` / `.http-probe.toml` |

**四条贯穿原则**：

1. **判据与取值分离**（ADR-0004/0005 已确立）：`SKILL.md` **零项目路径**；项目取值走 `AGENTS.md`
   的 `## <域>` 声明段（自然语言，**CLI 不读**）＋ 项目根 `.x.toml`（机器可读，CLI 读）。
2. **CLI 单文件自包含 + stdlib-only**：`cli/<name>` 单文件；`git archive` 单 skill 打包即完整可复现。
   构建/网络类才调外部命令（`mysql`/`mysqldump`/`redis-cli`/`lsof`/`ps`）。
3. **`ln` 软链安装**（`install.sh`）：工程用 `.agents/skills.txt` 声明依赖，`install.sh` 批量软链；
   单一真源、改库即生效。
4. **回写回流**：通用能力的任何改动**都在本仓提交**（不落工程仓）；工程内编辑＝编辑库。

**关键取舍**：

| 取舍 | 决定 | 理由 |
|---|---|---|
| 安装：软链 vs 复制入仓 | **软链**（`install.sh`） | 单一真源 + 即时生效；**回写回流只能软链实现**（复制需手动同步）；代价＝工程 clone 不自举，用重链补偿 |
| `office-docs` 粒度 | pptx + xlsx **合并** | agent 视角同属「办公文档」一域，`description` 能说清 |
| `mysql-cli` / `redis-cli` | **分开** | 用途不同（关系库 vs KV），合并会让 `description` 失焦 |
| 底座模块（`output`/`common`/`env`/`cli`） | **内联**进各 CLI | 契合「单文件自包含 + `git archive` 即完整」；跨 skill 共享会打破单 skill 打包 |
| 配置文件命名 | **每 skill 各自** `.x.toml` | 沿用 `.llm-wiki.toml` 先例，边界清晰 |
| 机器可读清单 | **`skills.json`**（`gen_skills_json.py` 派生）＋ `install.sh` | 单一行式、`--check` 拦漂移 |
| `svc-ops` 抽不抽 | **抽**（服务表驱动） | 服务编排是普遍需求；`build`/`test`/`sso`/`account` 与工程栈强绑定，**留 tenant** |

## 原因

1. **可转移性**：这些能力是跨项目需求，留在单仓等于每项目重造。
2. **单一真源**：判据（怎么用）与取值（连哪个库/起哪些服务）分离，消除「判据与取值双写」的历史漂移。
3. **工程侧回写**：约定「所有工程都可更新本库的通用能力」——工程内发现 bug／需增强，直接改库并回流（软链使「工程内编辑＝改库」天然成立）。
4. **可发现性**：封装成 skill 才能被 agent **发现**（`description` 进 system prompt）与调用——这是相对「只发 pip 包」的核心优势。

## 备选与否决

| 备选 | 否决理由 |
|---|---|
| 复制入仓（tenant 旧法 MT-152） | 每工程一份，易漂移；回写回流做不到 |
| 只发 pip 包、不做 skill | agent 不可发现、不可调用（`description` 无入口） |
| 建 `cli-base` 共享底座 skill | `git archive` 单 skill 打包不含它，需另行分发，复杂 |
| 连 `build`/`test`/`sso`/`account` 一起抽 | 与工程栈强绑定（maven/pnpm/PM 字段、IdP 端点），通用化收益低、耦合高 |
| 引入版本 pin（工程锁定 skill 版本） | 与「单一真源 + 即时生效」冲突；YAGNI，真需要时再评估 ln 到 release tag |

## 后果

- **新工程接入成本**：一个 `.agents/skills.txt` ＋ 一次 `install.sh`。
- **tenant 侧**：`tz` 的通用域将退化为 **forwarder**（`tz office …` ≡ 调 `cli/office-docs`，与 `tz docs` 同形），
  「操作一律走 `tz`」铁律不破；tzkit 从约 10.5k 行瘦身。
- **风险（须写入各 `SKILL.md`/`AGENT.md` 告知）**：一个工程改了通用能力，**立即影响所有已 ln 的工程**
  （无版本隔离）。本轮明确取「单一真源＋即时生效」，**不引入版本 pin**。
- **与既有 skill 的边界**：`office-docs` 管文档内容轴、`llm-wiki` 管知识资产空间轴、`svc-ops`/`http-probe`
  管本地服务与接口、`mysql-cli`/`redis-cli` 管数据访问。

## 后续注记（不回改上方决议，只加注记）

- **2026-09-30：S1–S5 落地。** S1 `office-docs`（pptx+xlsx 合并，修 tenant 侧 `resize` 死代码）；
  S2 安装机制（`skills.json`＋`gen_skills_json.py`＋`install.sh`）；S3 数据类（`mysql-cli`＋`redis-cli`）；
  S4 编排类（`svc-ops`＋`http-probe`）；S5 第二工程实测「ln 即用 ＋ 回写回流」通过。
  各 skill 带 `unittest`（全 mock，不连真库/真进程/真网络）；本仓回归网 `python3 -m unittest discover -s tests`。
  迁移计划见 `.agents/plans/self/08-tzkit-generic-skills.md`（不入仓）。
