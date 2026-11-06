---
name: md-site
description: Markdown 交付包工具链 — md 目录打包为 UTF-8 文件名 zip、转换为可 file:// 直读的离线 VitePress 站点（相对路径、mermaid 构建期预渲染、宽屏）、产物校验（编码标志/属性/断链）
user-invocable: true
---

# md-site — Markdown 交付包工具链

把一棵 **md 目录树**变成可外发的交付物：要么是纯 md 的 zip，要么是双击就能看的离线站点。

> **一句话原则**：**离线站必须能 `file://` 直读**——一切资源走相对路径，mermaid 在构建期就渲染成 SVG，
> 不依赖任何运行时脚本。

## 定位与边界

- **管「md 树 → 交付产物」**：打包、静态站构建、产物校验。
- **不管「内容清洗」**：哪些词不该出现、哪些编号要拆，属项目口径，由调用方（如 `tz delivery scan`）负责。
- **不管「站点部署」**：产出的是本地目录／zip，不发布。
- **不假设项目结构**：`--root` 定位项目根（找 `node_modules`），其余全部显式参数。

---

## §1 命令面（`cli/md-site`）

| 命令 | 作用 |
|---|---|
| `pack <src>` | md 目录 → zip（顶层同名目录、UTF-8 文件名标志 0x800） |
| `build <src>` | md 目录 → 离线 VitePress 站 → zip（相对路径、mermaid 预渲染、宽屏） |
| `check <zip>` | 产物校验：文件名编码标志、HTML 属性合法性、站内断链 |

**公共旗标**：`--root DIR`（项目根，用于定位 `node_modules`；默认向上找 `.git`）／`--json`。

`pack`：
```
md-site pack <src> --out <dir> [--name N] [--top DIR]
```

`build`：
```
md-site build <src> --out <dir> [--name N] [--title T] [--date D]
                   [--suffix 离线页面] [--work DIR] [--keep]
```
- `--name` 缺省 `<title>_<date>`；`--title` 缺省取首个 md 的 H1；`--date` 缺省今天。
- 产物：`<out>/<name>.zip`（pack）／`<out>/<name>_<suffix>.zip`（build）。

> **旗标以 `md-site --help` 为准**；本表只给命令面与作用。

---

## §2 离线站的四条硬规则（都是踩出来的）

1. **相对路径，且必须保留属性等号**。
   VitePress 产物里是 `/assets/x.js`，`file://` 下会指向磁盘根。后处理按
   `(href|src)=(["'])(path)\2` **整段重写**成 `<../×depth>path`。
   ⚠️ 曾用子串替换 `"./assets/` → `"../assets/`，把 `=` 吃掉生成 `href"../assets/x`，
   浏览器静默忽略样式与脚本 —— 页面「没样式」但无报错。`check` 会断言此类畸形属性为 0。

2. **mermaid 必须构建期渲染成 SVG**。
   `file://` 下客户端渲染拿不到模块、图永远空白。`build` 调 `mmdc` 逐块出 SVG，
   md 引用改成相对路径；`mmdc` 缺失**直接报错**，不静默降级。

3. **宽屏**。VitePress 默认内容区约 688px，交付文档要全宽（内置 CSS）。

4. **中文 URL**。侧栏链接被编码成 `%E5…`，后处理只匹配前缀、不解码。

---

## §3 依赖

| 依赖 | 用于 | 缺失时 |
|---|---|---|
| `vitepress`（项目 `node_modules` 或 npx） | `build` | 报错并给安装命令 |
| `mmdc`（mermaid-cli） | `build`（渲染图） | 报错并给安装命令 |
| 标准库 | 全部 | — |

`pack` / `check` **零依赖**，不需要 node。

---

## §4 退出码

`0` 成功；`1` 校验发现缺陷或构建失败；`2` 用法错误。
`check` 的问题清单打到 stdout（`--json` 为结构化数组），退出码只看有无问题。

---

## §5 项目侧接入

项目在自己的 `AGENTS.md` 声明段写清「交付区在哪、产物放哪、命名口径」，CLI 用薄转发壳调用本 skill
（模板见 [`TEMPLATE.md`](TEMPLATE.md)）。**内容清洗规则不进本 skill**。
