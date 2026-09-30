# TEMPLATE — 项目声明段与配置

> 复制到项目 `AGENTS.md`（声明段）＋ 项目根 `.office-docs.toml`（可选配置）。

## 一、`AGENTS.md` 声明段

> **只写本 skill 独有取值**。落库分流（决策台账／计划／设计稿／时间线／环境事实）**归
> `agent-pipeline` 的 `## 工作流水线` 声明段**，本节**不重复**——两处都写＝双真源。

```markdown
## 办公文档

> 判据见 `office-docs` skill。

- 只读模板基线：`docs/report/template/`（就地改写需 `--force`，`--out` 另存不受限）
- 机器可读配置：`.office-docs.toml`
- 门禁：`office-docs pptx check <产出.pptx>`
```

**字段含义**：这条声明段是给 **agent／人**读的**自然语言取值**；**CLI 本身不读** `AGENTS.md`（它只读 `.office-docs.toml` 与命令行参数）。未声明则走内置默认（基线 `docs/report/template`）。

## 二、`.office-docs.toml`（项目根，可选）

```toml
[baseline]
# 只读模板基线目录（相对项目根）；落在其内的文件就地改写需 --force。
# 设为 "-" 或空串表示本工程不设只读护栏。
dir = "docs/report/template"
```

## 三、最小可用步骤

```bash
office-docs pptx dump deck.pptx            # 看结构、拿 ref
office-docs pptx find deck.pptx "关键词"    # 按文本找 ref
office-docs pptx set deck.pptx --at slide1!sp[2] --text "改一下"
office-docs pptx check deck.pptx           # 自证
```
