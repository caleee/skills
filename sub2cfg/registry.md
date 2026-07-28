---
name: sub2cfg 模块清单
---

# sub2cfg 模块清单

## 订阅格式提取

当前支持从以下订阅格式中提取节点：

| 订阅格式 | 识别方法 | 提取方式 | 当前状态 |
|----------|----------|----------|----------|
| Clash YAML | 包含 `proxies:` 段 | 直接提取 `proxies:` 下的节点列表，按 INFO_KEYWORDS 过滤 | 已支持 |
| Surge | 包含 `[Proxy]` 段且有 `udp-relay` | 解析 `name = protocol, server, port, ...` 格式 | 已支持 |
| Loon | 包含 `[Proxy]` 段且无 `udp-relay` | 解析 `name = protocol, server, port, ...` 格式 | 已支持 |
| Shadowrocket | 行以 `ss://` 或 `trojan://` 开头 | 解析 URI 格式，支持 SIP002 两种变体 | 已支持 |
| Base64 编码 | 自动检测：base64 解码后内容为 URI 格式时返 `base64-uri` | base64 解码后递归检测 | 已支持 |
| Sing-box JSON | 包含 `"outbounds"` 段 | 解析 JSON outbounds 数组 | 已支持 |

## 目标平台

| 平台 | 组类型 | 模板格式 | 生成器 |
|------|--------|----------|--------|
| Clash (Mihomo) | url-test + select + fallback | YAML | `generate/clash.py` |
| Sing-box | urltest + selector | JSON | `generate/singbox.py` |
| DAE | min_moving_avg | HCL | `generate/dae.py` |

## 核心模块

| 模块 | 文件 | 说明 |
|------|------|------|
| 主入口 | `sub2cfg.py` | 编排流水线，参数解析 |
| 格式检测 | `detect.py` | 判断订阅格式类型 |
| 提取器 | `extract/{fmt}.py` | 5 个格式的节点提取 |
| 模板组装 | `generate/{target}.py` | 3 个平台的模板组装 |
| 区域组生成 | `group/{target}.py` | 3 个平台的区域组生成 |
| 分组骨架 | `group_builder.py` | 按区域分组 + self 注入 |
| 区域识别 | `region.py` | emoji 国旗 + 关键词推断 |
| 节点格式 | `proxy_format.py` | 字段顺序规范 |
| 协议注册 | `protocol.py` | 协议类型映射 |
| Sing-box 转换 | `convert/to_singbox.py` | Clash dict → Sing-box outbound |

## 区域映射表

7 个常用组各生成一个 url-test 策略组，非这 7 个区域的节点自动归入 `others` 组（DAE 无 `others`）。

| Emoji | 组名 | 节点名格式 |
|-------|------|-----------|
| 🇭🇰 | hongkong | `🇭🇰 香港 NN` |
| 🇲🇴 | macao | `🇲🇴 澳门 NN` |
| 🇨🇳 | taiwan | `🇨🇳 台湾 NN` |
| 🇯🇵 | japan | `🇯🇵 日本 NN` |
| 🇰🇷 | korea | `🇰🇷 韩国 NN` |
| 🇸🇬 | singapore | `🇸🇬 新加坡 NN` |
| 🇺🇸 | america | `🇺🇸 美国 NN` |
| 其他 | others | 自动归集 |

## 转换规则（convert）

| 文件 | 源平台 | 目标平台 | 说明 |
|------|--------|----------|------|
| `clash-to-sing-box.anytls.md` | Clash | Sing-box | anytls 协议转换规则 |
| `clash-to-sing-box.ss.md` | Clash | Sing-box | ss 协议转换规则 |
| `clash-to-sing-box.trojan.md` | Clash | Sing-box | trojan 协议转换规则 |
| `clash-to-sing-box.hysteria2.md` | Clash | Sing-box | hysteria2 协议转换规则 |
| `clash-to-clash.group-gen.md` | Clash | Clash | 区域组生成规则 |
| `clash-to-sing-box.group-gen.md` | Clash | Sing-box | 区域组生成规则 |