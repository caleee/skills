# 代理组架构设计（sub2cfg 落地参考）

> 基于 DAE、Clash、Sing-box 三平台统一架构设计
> 用于指导 sub2cfg 的 group 生成逻辑

---

## 1. 设计框架概述

### 1.1 核心目标

- 统一三平台（DAE、Clash、Sing-box）的分流逻辑
- 服务级别精细化分流：每个服务组独立测速选优
- 国内/国外流量区分：国内直连，国外走代理
- 自建节点兜底：`self` 组作为最终保障
- 非常用国家节点归集：`others` 组手动选择

### 1.2 整体架构

```
用户流量 → 路由规则 → 服务组 → 区域组 → 节点
                 ↓
            国内直连 → 直接发出
```

**三层分流结构**：
1. 路由规则（Rule）→ 按域名/GeoIP 匹配
2. 服务组（Service Group）→ 跨区域集合，自动选优
3. 区域组（Regional Group）→ 区域内节点集合，自动选优

---

## 2. 节点分组策略

按国家/地区 **emoji 国旗** 自动分组：

| 区域 | 国旗 | 组名 | 类型 | 节点名格式 |
|------|------|------|------|-----------|
| 香港 | 🇭🇰 | hongkong | urltest | `🇭🇰 香港 NN` |
| 澳门 | 🇲🇴 | macao | urltest | `🇲🇴 澳门 NN` |
| 台湾 | 🇨🇳 | taiwan | urltest | `🇨🇳 台湾 NN` |
| 日本 | 🇯🇵 | japan | urltest | `🇯🇵 日本 NN` |
| 韩国 | 🇰🇷 | korea | urltest | `🇰🇷 韩国 NN` |
| 新加坡 | 🇸🇬 | singapore | urltest | `🇸🇬 新加坡 NN` |
| 美国 | 🇺🇸 | america | urltest | `🇺🇸 美国 NN` |
| 自建 | — | self | select（Clash）/ selector（Sing-box） | — |
| 其他 | 其余国旗 | others | select（DAE 无此组） | 自动归集 |

---

## 3. 区域组设计

| 特性 | DAE | Clash | Sing-box |
|------|-----|-------|----------|
| 组类型 | `min_moving_avg` | `url-test` | `urltest` |
| 测速地址 | 全局默认 | `gstatic.com/generate_204` | `gstatic.com/generate_204` |
| 测速间隔 | 30s | 300s | 5m |

DAE 特殊性：不支持 group 嵌套引用，通过 `filter: subtag()` 从节点池筛选。

---

## 4. 服务组设计

### 4.1 服务组列表

| 组名 | 用途 | 测速地址 |
|------|------|----------|
| youtube | YouTube 视频 | `https://www.youtube.com/generate_204` |
| google | Google 搜索 | `https://www.gstatic.com/generate_204` |
| github | GitHub 代码托管 | `https://github.com` |
| telegram | Telegram 通讯 | `https://telegram.org` |
| overseaai | OpenAI/Anthropic/AI | `https://chatgpt.com` |
| dns | 海外 DNS 解析 | `https://1.1.1.1` |
| cdn | 国外 CDN 资源 | `https://cp.cloudflare.com/generate_204` |
| apple | Apple 服务 | `https://www.apple.com` |
| microsoft | Microsoft/OneDrive | `https://www.microsoft.com` |
| games | 海外游戏 | `https://www.gstatic.com/generate_204` |
| final | 兜底组 | `https://cp.cloudflare.com/generate_204` |

### 4.2 各平台组类型

| 服务组 | DAE | Clash | Sing-box |
|--------|-----|-------|----------|
| 所有服务 | min_moving_avg | fallback | urltest |
| 可直连服务 | — | + DIRECT 兜底 | + DIRECT 兜底 |

### 4.3 服务组优先级顺序（Clash fallback）

| 服务 | 优先级顺序 |
|------|-----------|
| youtube/google | hongkong → macao → taiwan → japan → singapore → korea → america → self |
| github | japan → hongkong → macao → singapore → korea → america → taiwan → self |
| telegram | singapore → hongkong → macao → japan → korea → taiwan → america → self |
| overseaai | america → japan → singapore → korea → taiwan → hongkong → macao → self |
| dns/microsoft | japan → hongkong → macao → singapore → taiwan → korea → america → self |
| apple | hongkong → macao → taiwan → japan → singapore → korea → america → self |
| cdn | hongkong → macao → japan → singapore → taiwan → korea → america → self |
| games | japan → hongkong → macao → singapore → korea → taiwan → america → self |

---

## 5. 兜底策略（self 组）

- 自建节点作为所有服务组的最终兜底选项
- DAE：`[add_latency: +500ms]` 延迟惩罚
- Clash：`self` 放在每个 fallback 组的最后
- Sing-box：`self` 放在每个 urltest 组的出站列表末尾

---

## 6. 测速地址策略

- **服务相关性**：测速地址应代表该服务的目标网络
- **轻量性**：优先使用返回 204 的端点
- **两级测速**：服务组测各区域组延迟，区域组测各节点延迟