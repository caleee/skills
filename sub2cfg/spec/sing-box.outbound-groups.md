---
name: Sing-box 出站组（Selector/URLTest）格式定义
platform: sing-box
type: outbound-groups
---

# Sing-box 出站组配置格式

Sing-box 没有独立的 `proxy-groups` 概念，组（selector、urltest）与其他出站类型一样，并列在 `outbounds` 数组中。

## 参考文档

- Selector: https://sing-box.sagernet.org/configuration/outbound/selector/
- URLTest: https://sing-box.sagernet.org/configuration/outbound/urltest/
- 出站总览: https://sing-box.sagernet.org/configuration/outbound/

## selector 类型（手动选择）

```json
{
  "type": "selector",
  "tag": "select",
  "outbounds": [
    "proxy-a",
    "proxy-b",
    "proxy-c"
  ],
  "default": "proxy-c",
  "interrupt_exist_connections": false
}
```

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `type` | string | 是 | — | 固定为 `"selector"` |
| `tag` | string | 是 | — | 出站标识，用于路由规则引用 |
| `outbounds` | string[] | 是 | — | 可选出站标签列表 |
| `default` | string | 否 | 首个 outbound | 默认选中的出站标签 |
| `interrupt_exist_connections` | bool | 否 | `false` | 切换时中断现有连接 |

## urltest 类型（自动延迟测试）

```json
{
  "type": "urltest",
  "tag": "auto",
  "outbounds": [
    "proxy-a",
    "proxy-b",
    "proxy-c"
  ],
  "url": "https://www.gstatic.com/generate_204",
  "interval": "3m",
  "tolerance": 50,
  "idle_timeout": "30m",
  "interrupt_exist_connections": false
}
```

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `type` | string | 是 | — | 固定为 `"urltest"` |
| `tag` | string | 是 | — | 出站标识 |
| `outbounds` | string[] | 是 | — | 待测试出站标签列表 |
| `url` | string | 否 | `"https://www.gstatic.com/generate_204"` | 延迟测试 URL |
| `interval` | duration | 否 | `"3m"` | 测试间隔 |
| `tolerance` | int | 否 | `50` | 延迟容差（毫秒） |
| `idle_timeout` | duration | 否 | `"30m"` | 空闲超时 |
| `interrupt_exist_connections` | bool | 否 | `false` | 切换时中断现有连接 |

## 内置出站

Sing-box 需要显式定义 `direct` 出站才能在组中引用：

```json
{
  "type": "direct",
  "tag": "DIRECT"
}
```

## 与 Clash 的关键区别

| 维度 | Clash | Sing-box |
|------|-----------|----------|
| 位置 | 独立 `proxy-groups:` 段 | `outbounds[]` 数组，与其他出站并列 |
| 引用方式 | `proxies:` 字段 | `outbounds:` 字段（标签名） |
| 持续时间 | 秒（int） | 持续时间字符串（如 `"3m"`、`"30s"`） |
| 组标识 | `name` | `tag` |
| 内置直连 | `DIRECT`（关键字，无需定义） | `DIRECT`（需显式定义 `direct` 类型出站） |