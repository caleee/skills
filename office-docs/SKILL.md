---
name: office-docs
description: 办公文档零依赖定点编辑 — PPTX 文字/形状/表格/连线/图片精确改（只改目标条目、可 diff 回填），XLSX 读取与 md→xlsx，含只读模板基线护栏
user-invocable: true
---

# office-docs — 办公文档定点编辑与转换

用**零依赖**的方式精确修改 PPTX／读取 XLSX，让 agent 能改汇报材料的内容而不破坏版式。

> **一句话原则**：只改**目标字节**，其余原样保留——改动可 diff、可回填返源。判据来自本 skill；模板基线与配置**来自项目声明段**（模板见 [`TEMPLATE.md`](TEMPLATE.md)）。

## 定位与边界

- **管「改内容」**：PPTX 的文字／形状／表格／连线／图片、增删页与行列、z-order；XLSX 的读取与 md 表格导入。
- **不管「做版式」**：字号／配色／布局的**设计**归人（WPS／PowerPoint）；本 skill 只做可控的定点编辑。
- **零依赖**：PPTX 直接操作 OOXML zip 条目；XLSX 直接解析部件。**不引** `python-pptx`／`openpyxl`。仅 `check --render` 可选调用本机 PowerPoint 做自证。
- **零项目路径假设**：本文件不出现任何具体项目路径；项目取值走 `AGENTS.md` 声明段 ＋ 项目根 `.office-docs.toml`。

---

## §1 核心原则（保真定点编辑）

1. **只改目标，其余逐字保留**——PPTX 修改只动目标 `<a:t>`／`<a:off>`／`<a:ext>` 等字节，其余 zip 条目**逐字不变**。（实现约束：重打包**必须新建 `ZipInfo`**，复用原对象会把中央目录偏移写坏。）
2. **写前自检、失败回滚**——每次改完立即校验（条目名唯一／zip 可解／XML/rels 良构），不合格**就地回滚**（从备份恢复或删输出），绝不留下坏文件。
3. **默认就地写回并备份** `<名>.bak.pptx`；`--out` 另存不改原文件。
4. **多 run 段落默认拒绝**——一个段落被拆成多 run（局部格式）时默认不合并（会丢其余 run 的格式），须显式 `--run N` 或 `--merge`。

> ⚠️ **渲染是最终判据**：`ET` 良构、`dump`、`diff` **都查不出**「PowerPoint 静默丢行／超页被裁」这类问题。改表格后应 `check --render` ＋ 读回渲染结果核对。

---

## §2 ref 寻址模型（PPTX）

| ref 形态 | 指 |
|---|---|
| `slide2!sp[3]` | 第 2 页第 3 个形状（`sp[i]` 形状；`pic[i]` 图片／`gf[i]` 表格框／`cx[i]` 连线） |
| `slide2!tbl0.r1.c2` | 第 2 页第 0 个表格的第 1 行第 2 列单元格 |
| `slide1!sp[2].p0` | 形状内第 0 个段落 |

- 序号与 `dump` 列出的**一致**——先 `dump`／`find` 拿 ref，再改。
- 坐标一律 **pt**（`1pt = 12700 EMU`）；`dump` 输出的 `at:{x,y,w,h}` 可直接回填 `--at/--size/--to`。

---

## §3 命令面（`cli/office-docs`）

本体 **stdlib-only**，分 `pptx` / `xlsx` 两域。

| 命令 | 作用 |
|---|---|
| `pptx dump <f>` | 结构清单（带文字的形状＋表格单元格＋坐标＋连线） |
| `pptx find <f> <文本>` | 按文本找 ref |
| `pptx set <f> --at <ref> --text <t>` | 定点替换文字；`--run N`／`--merge` 处理多 run |
| `pptx diff <旧> <新>` | 文字级差异（回填 md 用） |
| `pptx del-shape/move-shape/copy-shape/resize/reorder` | 形状／表格的删、移、克隆（可跨页）、改尺寸、调 z-order |
| `pptx add-shape/add-connector` | 从零画方框与连线（`straight/elbow/curve`、可带箭头） |
| `pptx add-slide/del-slide` | 增删页（同步维护 `sldIdLst`／分节／rels／Content_Types） |
| `pptx add-table` | 把 xlsx 区域搬成**原生表格**（逐格样式） |
| `pptx add-row/del-row/fill-table/row-height/font-size` | 表格结构编辑（批量填表、裁行、压回页内） |
| `pptx media/put-image` | 媒体清单／换图（同名同扩展名换字节） |
| `pptx check [--render]` | 结构自检；`--render` 用本机 PowerPoint 导出 PDF 做**Office 自证** |
| `xlsx dump <f>` | 工作表结构（值＋样式摘要＋合并＋行列尺寸） |
| `xlsx from-md <md> --out <xlsx>` | md 管道表格 → xlsx（表头加粗＋冻结首行） |

> **旗标以 `office-docs <域> --help` 为准**——本表只给命令面与作用，**不复述旗标**（逐条罗列必与实现漂移）。

**全局旗标**：`--json`（机器可读输出）／`--dry-run`（写操作只预演）／`--root`（钉项目根）／`--baseline-dir`（覆盖只读基线）。

---

## §4 配置（判据 vs 取值分离）

- **判据**只在本 skill（本文件）。
- **取值**：项目 `AGENTS.md` 的 `## 办公文档` 声明段（自然语言；**CLI 不读**）＋ 项目根 `.office-docs.toml`（**机器可读**；CLI 读）。

```toml
[baseline]
dir = "docs/report/template"   # 只读模板基线目录（相对项目根）；"-" 或空串 = 不设护栏
```

项目根定位：`--root` → `OFFICE_DOCS_ROOT` 环境变量 → 向上查找 `.office-docs.toml` → `.git`。

---

## §5 只读基线护栏

汇报模板（来料基线）**默认只读**：落在基线目录内的文件**就地改写**需 `--force`；`--out` 另存不受限。

> 护栏在**工具里**，不只靠人记纪律：起因是 `--dry-run` 曾写在子命令末尾被当成 `set` 的参数，**真的就地改写了模板**。

---

## §6 边界与落地检查

| skill | 管什么 | 交叉点 |
|---|---|---|
| `llm-wiki` | 文档知识库（空间轴／出口层） | 汇报材料属「出口层」；本 skill 只改其**内容** |
| `find-docs` | 第三方库文档 | 无 |

落地检查：

1. 本 skill 无任何项目路径（取值全在声明段／`.toml`）。
2. 改完 pptx 跑 `check`；**改表格**还要 `check --render` ＋ 读回核对。
3. 报告材料改动用 `diff` 回填 md，保持「md 为真源」。
