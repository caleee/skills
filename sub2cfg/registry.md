---
name: sub2cfg 模块清单
---

# sub2cfg 模块清单

## 订阅格式提取

当前支持从以下订阅格式中提取节点：

| 订阅格式 | 识别方法 | 提取方式 | 当前状态 |
|----------|----------|----------|----------|
| Clash YAML | 包含 `proxies:` 段 | 直接提取 `proxies:` 下的节点列表 | 已支持 |
| Surge / Loon | 包含 `[Proxy]` 段 | 解析 `name = protocol, server, port, ...` 格式 | 已支持 |
| Shadowrocket | 行以 `ss://` 或 `trojan://` 开头 | 解析 URI 格式 | 已支持 |
| Base64 编码 | 需显式 `-f base64-uri`（自动检测时 base64 内容会被识别为 shadowrocket） | base64 解码后递归检测 | 已支持 |
| Sing-box JSON | 包含 `"outbounds"` 段 | 解析 JSON outbounds 数组 | 已支持 |

## 格式定义（spec）

### 节点格式

| 文件 | 平台 | 协议 | 参考文档 |
|------|------|------|----------|
| spec/clash.anytls.md | Clash (Mihomo) | anytls | https://wiki.metacubex.one/config/proxies/anytls/ |
| spec/clash.ss.md | Clash (Mihomo) | ss | https://wiki.metacubex.one/config/proxies/ss/ |
| spec/clash.trojan.md | Clash (Mihomo) | trojan | https://wiki.metacubex.one/config/proxies/trojan/ |
| spec/sing-box.anytls.md | Sing-box | anytls | https://sing-box.sagernet.org/configuration/outbound/anytls/ |
| spec/sing-box.ss.md | Sing-box | ss | https://sing-box.sagernet.org/configuration/outbound/shadowsocks/ |
| spec/sing-box.trojan.md | Sing-box | trojan | https://sing-box.sagernet.org/configuration/outbound/trojan/ |

### 订阅格式

| 文件 | 平台 | 说明 |
|------|------|------|
| spec/surge.proxy.md | Surge | Surge [Proxy] 段落格式定义 |
| spec/loon.proxy.md | Loon | Loon [Proxy] 段落格式定义 |
| spec/shadowrocket.md | Shadowrocket | Shadowrocket URI 格式定义 |

### 组格式

| 文件 | 平台 | 类型 | 参考文档 |
|------|------|------|----------|
| spec/clash.proxy-groups.md | Clash (Mihomo) | proxy-groups | https://wiki.metacubex.one/config/proxy-groups/ |
| spec/sing-box.outbound-groups.md | Sing-box | outbound-groups | https://sing-box.sagernet.org/configuration/outbound/selector/ |

## 转换规则（convert）

### 节点转换

| 文件 | 源平台 | 目标平台 | 协议 |
|------|--------|----------|------|
| convert/clash-to-sing-box.anytls.md | Clash | Sing-box | anytls |
| convert/clash-to-sing-box.ss.md | Clash | Sing-box | ss |
| convert/clash-to-sing-box.trojan.md | Clash | Sing-box | trojan |

### 组生成

| 文件 | 源平台 | 目标平台 | 说明 |
|------|--------|----------|------|
| convert/clash.group-gen.md | Clash | Clash | 从节点列表生成 proxy-groups |
| convert/clash-to-sing-box.group-gen.md | Clash | Sing-box | 从节点列表生成 outbound-groups |

## 区域映射表

所有组生成规则共享此区域映射，新增区域时只需更新此处。

| Emoji | 区域代码 | 组名 | 节点名格式 |
|-------|----------|------|-----------|
| 🇭🇰 | HK | 香港 | `🇭🇰 香港 NN` |
| 🇺🇸 | US | 美国 | `🇺🇸 美国 NN` |
| 🇯🇵 | JP | 日本 | `🇯🇵 日本 NN` |
| 🇸🇬 | SG | 狮城 | `🇸🇬 狮城 NN` |
| 🇨🇳 | TW | 台湾 | `🇨🇳 台湾 NN` |

## 添加新订阅格式的步骤

1. 识别订阅返回的格式特征（YAML 结构、URI 前缀、关键字等）
2. 提取节点列表，转成统一的 Clash 格式节点结构
3. 如果已有对应平台 spec，直接复用；否则新增 spec
4. 如需转其他格式，在 `convert/` 下添加转换规则

## 添加新协议的步骤

1. 在 `spec/` 下更新或创建平台协议定义
2. 在 `convert/` 下创建对应的转换规则
3. 更新本 `registry.md`

## 命名规范

- spec 节点文件: `{平台}.{协议}.md`
- spec 组文件: `{平台}.{type}.md`
- convert 节点文件: `{源平台}-to-{目标平台}.{协议}.md`
- convert 组文件: `{源平台}-to-{目标平台}.group-gen.md`