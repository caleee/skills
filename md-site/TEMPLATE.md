# TEMPLATE — 项目声明段与接入

> 复制到项目 `AGENTS.md`（声明段）。本 skill **无配置文件**——所有取值走命令行，
> 项目侧通常再包一层薄转发壳（如 `tz delivery`）。

## 一、`AGENTS.md` 声明段

> **只写本 skill 独有取值**。落库分流归项目的 `agent-pipeline` 声明段，本节不重复。

```markdown
## 交付包（md-site 声明）

> 判据见 `md-site` skill。

- 交付区：`docs/delivery/<板块>/`（对外稿，不含内部编号与 AI 字样）
- 产物落点：`docs/dist/`
- 命名：`<标题>_<交付日期>.zip`；离线包 `<标题>_<交付日期>_离线页面.zip`
- 生成：`tz delivery build`（薄转发：scan → md → site → check）
- 门禁：`tz delivery scan`（零命中）＋ `tz delivery check`（两个包）
```

**字段含义**：给 **agent／人**读的自然语言取值；**CLI 不读 `AGENTS.md`**。

## 二、最小接入

```bash
# 脚本化：先清洗门禁，再出两个包，最后各自校验
md-site pack  <src> --out dist --name <标题>_<日期>
md-site build <src> --out dist --name <标题>_<日期> --suffix 离线页面
md-site check dist/<标题>_<日期>.zip
md-site check dist/<标题>_<日期>_离线页面.zip
```

## 三、目录约定（推荐）

```
<src>/
├── 00-交付说明.md          ← 首页（build 会复制为 index.md）
├── 01-设计文稿/
├── 02-数据库设计/
└── 03-接口文档/
```

- 侧栏由**目录结构**自动生成，无需配置。
- `00-交付说明.md` 建议写「交付日期：YYYY-MM-DD」——`pack`/`build` 的默认日期从这里取。
- 图片与正文同目录或用相对路径引用；不要写绝对路径。
