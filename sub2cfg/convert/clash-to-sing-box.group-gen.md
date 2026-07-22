---
name: Clash → Sing-box 出站组生成规则
source: clash
target: sing-box
type: group-gen
---

# Clash → Sing-box 出站组生成规则

## 概述

从 Clash 格式的节点列表生成 Sing-box 的出站组配置（selector + urltest），与节点出站并列在 `outbounds` 数组中。

## 输入

Clash 格式的节点列表（YAML 数组），从订阅 YAML 的 `proxies:` 段提取。

## 节点过滤规则

1. 过滤掉非代理节点（name 不包含 emoji 国旗的节点，如 "当前流量"、"到期时间"）
2. 根据 name 中的 emoji 国旗前缀识别区域

## 区域映射

区域映射表见 `registry.md`。

## 关键词约定

Sing-box 中直连出站不是内置关键字，需显式定义。以下名称统一大写，与 Clash 保持一致：

| 名称 | 含义 | 出站类型 | 说明 |
|------|------|----------|------|
| `DIRECT` | 直连 | `direct` | 需在 `outbounds` 中显式定义 |
| `PROXIES` | 主选择组 | `selector` | 包含所有节点 |
| `FINAL` | 兜底组 | `selector` | 包含 PROXIES + 区域组 + DIRECT |

## 与 Clash 的区别

| 维度 | Clash | Sing-box |
|------|-----------|----------|
| 位置 | 独立 `proxy-groups:` 段 | 与节点并列在 `outbounds[]` |
| 引用方式 | `proxies:` 字段 | `outbounds:` 字段 |
| 组标识 | `name` 属性 | `tag` 属性 |
| 组类型 | `select` / `url-test` | `selector` / `urltest` |
| 持续时间 | 秒（int） | 持续时间字符串 |
| 内置直连 | `DIRECT`（关键字，无需定义） | `DIRECT`（需显式定义 `direct` 类型出站） |

## 生成的组结构

### 0. 内置出站

```json
{
  "type": "direct",
  "tag": "DIRECT"
}
```

### 1. 主选择组（PROXIES）

```json
{
  "type": "selector",
  "tag": "PROXIES",
  "outbounds": [
    "🇭🇰 HKG 香港 01",
    "🇭🇰 HKG 香港 02",
    ...
    "🇺🇸 USA 美国 01",
    ...
  ]
}
```

- `type: selector`
- 包含所有已转换的节点 tag
- 不含 `DIRECT`（直连通过 `FINAL` 组或路由规则引用）

### 2. 区域自动组（urltest）

每个区域生成一个 `urltest` 组，包含该区域所有节点。

```json
{
  "type": "urltest",
  "tag": "HK",
  "outbounds": [
    "🇭🇰 HKG 香港 01",
    "🇭🇰 HKG 香港 02",
    ...
  ],
  "url": "https://www.gstatic.com/generate_204",
  "interval": "5m",
  "tolerance": 50
}
```

- `type: urltest`
- `url` 默认值由 Sing-box 处理（`https://www.gstatic.com/generate_204`）
- `interval` 使用持续时间字符串格式

### 3. 兜底组（FINAL）

```json
{
  "type": "selector",
  "tag": "FINAL",
  "outbounds": [
    "PROXIES",
    "HK",
    "JP",
    "SG",
    "TW",
    "US",
    "DIRECT"
  ]
}
```

### 4. 完整输出示例

```json
{
  "outbounds": [
    {
      "type": "direct",
      "tag": "DIRECT"
    },
    {
      "type": "selector",
      "tag": "PROXIES",
      "outbounds": [
        "🇭🇰 HKG 香港 01",
        "🇭🇰 HKG 香港 02",
        ...
      ]
    },
    {
      "type": "selector",
      "tag": "FINAL",
      "outbounds": [
        "PROXIES",
        "HK",
        "JP",
        "SG",
        "TW",
        "US",
        "DIRECT"
      ]
    },
    {
      "type": "urltest",
      "tag": "HK",
      "outbounds": [
        "🇭🇰 HKG 香港 01",
        "🇭🇰 HKG 香港 02",
        ...
      ],
      "interval": "5m",
      "tolerance": 50
    },
    {
      "type": "urltest",
      "tag": "JP",
      "outbounds": [...],
      "interval": "5m",
      "tolerance": 50
    }
  ]
}
```

## 简化说明

Sing-box 的组生成比 Clash 简单，因为：
1. 不需要服务组（YouTube、Google 等），这些由路由规则控制
2. 只需要生成：DIRECT 出站 + PROXIES（selector）+ 区域组（urltest）+ FINAL（selector 兜底）
3. 节点名直接使用 tag 值，无需转换格式