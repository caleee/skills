# AGENT.md — md-bundle

> 判据见 [`SKILL.md`](SKILL.md)；项目接入模板见 [`TEMPLATE.md`](TEMPLATE.md)。

## 何时用本 skill

| 场景 | 动作 |
|---|---|
| 把一个 md 目录发给外部 | `md-bundle pack <src> --out dist --name 交付稿_2026-11-05` |
| 对方不方便装任何东西，要双击就能看 | `md-bundle build <src> --out dist --suffix 离线页面` |
| 收到一个交付 zip，想验它有没有坏 | `md-bundle check <zip>` |
| 站点里有时序图 | 无需额外操作——`build` 自动预渲染成 SVG |
| 只想看产物有没有乱码 | `md-bundle check <zip>`（检查 UTF-8 标志） |

## 快速开始

```bash
# 1) 纯 md 包（零依赖）
md-bundle pack ./docs/delivery/multi-tenant --out ./docs/dist --name 设计文稿_2026-11-05

# 2) 离线站（需要项目内 vitepress ＋ PATH 上的 mmdc）
md-bundle build ./docs/delivery/multi-tenant --out ./docs/dist \
  --name 设计文稿_2026-11-05 --suffix 离线页面

# 3) 校验
md-bundle check ./docs/dist/设计文稿_2026-11-05.zip
md-bundle check ./docs/dist/设计文稿_2026-11-05_离线页面.zip
```

## 三个必须知道的约束

1. **`build` 的工作目录要在项目内**（默认 `<out>/.tmp/md-bundle`），因为 VitePress 依赖要从
   项目 `node_modules` 解析；`--work /tmp/...` 会找不到依赖。
2. **mermaid 没有 mmdc 就失败**，不会降级为客户端渲染——那不是「慢一点」，是 `file://` 下**根本看不见**。
3. **`check` 报「属性缺等号」= 后处理 bug**，不是内容问题；看 `relativize` 的注释。

## 与本 skill 无关的事

- 内容清洗（删内部编号、AI 字样、外链）——归**出口层治理** `llm-wiki clean`，本 skill 不读规则、不碰正文。
- 站点发布／部署——本 skill 只产本地目录与 zip。
