# AGENT.md — office-docs

> 判据见 [`SKILL.md`](SKILL.md)；项目声明模板见 [`TEMPLATE.md`](TEMPLATE.md)。

## 何时用本 skill

| 场景 | 动作 |
|---|---|
| 改汇报 pptx 的文字 | `dump`/`find` 拿 ref → `set --at <ref> --text …` |
| 表格加/删行、批量填表 | `add-row`/`del-row`/`fill-table` |
| 画架构图（方框＋连线） | `add-shape`/`add-connector`；容器框标题用 `--anchor t --align l` |
| 拼图（克隆/移动/改尺寸/层级） | `copy-shape`/`move-shape`/`resize`/`reorder` |
| 换模板里的图 | `media` 找 imageN → `put-image`（同名同扩展名） |
| 把 xlsx 区域搬进 pptx | `xlsx dump` 看结构 → `pptx add-table --from <xlsx> --range <区域>` |
| md 表格 → xlsx | `xlsx from-md <md> --out <xlsx>` |
| 收尾自证 | `pptx check [--render]`；差异 `pptx diff` 回填 md |

## 快速开始

```bash
# 1) 看结构、拿 ref
office-docs pptx dump deck.pptx
office-docs pptx find deck.pptx "低阈值预算"

# 2) 定点改（默认就地＋备份；--out 另存）
office-docs pptx set deck.pptx --at slide2!tbl0.r1.c2 --text "新描述"

# 3) 自证 + 回填
office-docs pptx check deck.pptx
office-docs pptx diff deck.pptx.bak.pptx deck.pptx
```

## 架构

```
office-docs/
├── SKILL.md      判据（零项目路径假设）
├── TEMPLATE.md   项目声明段 + .office-docs.toml 模板
├── AGENT.md      本文件（运行时指引）
├── VERSION       semver（发布用）
└── cli/office-docs   CLI：单文件 stdlib-only（pptx 定点编辑 + xlsx 读取/导入）
```

- **单文件自包含**：`cli/office-docs` 由 tenant `tzkit.report`（pptx／xlsx／分派）合并而成，`git archive` 单 skill 打包即完整可复现。
- **配置双路径**：CLI（机器值）读 `--root`／`--baseline-dir`／`OFFICE_DOCS_BASELINE`／`.office-docs.toml`；`AGENTS.md` 声明段**只给 agent／人读**，CLI 不读。
- **CLI 写文件的命令**：`set`／`add-*`／`del-*`／`move-shape`／`copy-shape`／`resize`／`reorder`／`fill-table`／`row-height`／`font-size`／`put-image`／`xlsx from-md`；其余只读。就地写回一律先备份。

## 扩展点

- **新增 pptx 子命令**：在 `cli/office-docs` 的 `pptx_main` 加分支（参数用 `_opt`／`_flag` 解析），实现放 pptx 段；落盘必须 `ET.fromstring` 写前自检 ＋ 走 `_write_verified`。
- **新增 xlsx 输出**：在 xlsx 段加 `write_*`（零依赖手写部件），沿用 `write_table` 的「目标已存在默认拒绝、`--force` 覆盖」约定。
- **改基线判定**：`_is_readonly_baseline` 读 `CFG["baseline"]`（已配置化，不再硬编码路径）。

## 注意事项

- **不要**在本 skill 里写任何具体项目路径——那会立刻造成「判据 vs 取值」双真源。
- 改**表格**后必跑 `check --render`；`dump`／`diff`／`ET` **都查不出**静默丢行与超页被裁。
- 多 run 段落（一段被拆成多段格式）默认拒绝改写，须 `--run N` 或 `--merge`。
