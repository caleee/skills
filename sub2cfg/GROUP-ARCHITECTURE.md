# 代理组架构设计（sub2cfg 落地参考）

> 基于 DAE、Clash、Sing-box 三平台统一架构设计
> 用于指导 sub2cfg 的 group 生成逻辑

---

## 1. 设计框架概述

### 1.1 核心目标

- 统一三平台（DAE、Clash、Sing-box）的分流逻辑
- 服务级别精细化分流：每个服务组独立测速选优
- 国内/国外流量区分：国内直连（`must_direct`/`DIRECT`），国外走代理
- 自建节点兜底：`self` 组作为最终保障
- 非常用国家节点归集：`others` 组手动选择

### 1.2 整体架构

```
用户流量 → 路由规则 → 服务组 → 区域组 → 节点
                 ↓
            国内直连 → 直接发出
```

**三层分流结构**：

```
第一层：路由规则（Rule）
  - 按域名/GeoIP/端口匹配
  - 国内 → Direct（直连）
  - 国外 → 对应服务组

第二层：服务组（Service Group）
  - 跨区域节点集合
  - 自动选最优区域组（urltest/fallback）
  - 各服务组独立测速地址

第三层：区域组（Regional Group）
  - 区域内节点集合
  - 自动选最优节点（urltest/url-test/min_moving_avg）
  - 统一测速地址
```

---

## 2. 节点分组策略

按国家/地区 **emoji 国旗** 自动分组：

| 区域 | 国旗 | 组名 | 类型 |
|------|------|------|------|
| 香港 | 🇭🇰 | hongkong | urltest |
| 澳门 | 🇲🇴 | macao | urltest |
| 台湾 | 🇨🇳 | taiwan | urltest |
| 日本 | 🇯🇵 | japan | urltest |
| 韩国 | 🇰🇷 | korea | urltest |
| 新加坡 | 🇸🇬 | singapore | urltest |
| 美国 | 🇺🇸 | america | urltest |
| 自建 | — | self | select（Clash/Sing-box）/ min_moving_avg（DAE） |
| 其他 | 其余国旗 | others | select |

**设计思路**：
- 7 个常用区域作为 `urltest`（自动测速选最优节点），覆盖日常使用的主要区域
- `self`（自建节点组）作为兜底，Clash/Sing-box 中 `select` 类型手动选择，DAE 中 `min_moving_avg` 自动选优
- `others` 收留非常用国家节点，`select` 类型手动选择（这些节点网络质量差异大，不适合自动选）。注：DAE 无 `others` 组

---

## 3. 基础组（区域组）设计

### 3.1 三平台对比

| 特性 | DAE | Clash | Sing-box |
|------|-----|-------|----------|
| 组类型 | `min_moving_avg` | `url-test` | `urltest` |
| 测速地址 | 全局默认 `cp.cloudflare.com,1.1.1.1` | `http://www.gstatic.com/generate_204` | `http://www.gstatic.com/generate_204` |
| 测速间隔 | 30s | 300s | 5m |
| 节点选择策略 | 移动平均延迟最低 | 延迟最低 | 延迟最低 |

### 3.2 DAE 的特殊性

DAE 的 group 机制与其他两平台有本质区别：

- DAE 的 group 通过 `filter` 从全局节点池筛选节点，**不支持 group 嵌套引用**
- Clash/Sing-box 的 group 可以引用其他 group 作为子项
- 因此 DAE 的服务组通过 `filter: subtag(a, b, c, ...)` 直接包含所有区域节点，而不是引用区域组

### 3.3 三平台映射关系

```yaml
# DAE
hongkong {
    filter: subtag(hongkong)
    policy: 'min_moving_avg'
}

# Clash
- name: hongkong
  type: url-test
  proxies: [节点列表]
  url: http://www.gstatic.com/generate_204
  interval: 300

# Sing-box
{
    "type": "urltest",
    "tag": "hongkong",
    "outbounds": [节点列表],
    "url": "http://www.gstatic.com/generate_204",
    "interval": "5m",
    "tolerance": 50
}
```

---

## 4. 服务组设计

### 4.1 服务组列表

| 组名 | 用途 | 是否可直连 | 测速地址 |
|------|------|-----------|----------|
| youtube | YouTube 视频 | ❌ 被墙 | `https://www.youtube.com/generate_204` |
| google | Google 搜索/Gmail/Play | ❌ 被墙 | `https://www.gstatic.com/generate_204` |
| github | GitHub 代码托管 | ✅ 可直连 | `https://github.com` |
| telegram | Telegram 通讯 | ❌ 被墙 | `https://telegram.org` |
| overseaai | OpenAI/Anthropic/AI | ❌ 被墙 | `https://chatgpt.com` |
| dns | 海外 DNS 解析 | ✅ 可直连 | `https://1.1.1.1` |
| cdn | 国外 CDN 资源 | ✅ 部分可直连 | `https://cp.cloudflare.com/generate_204` |
| apple | Apple 服务 | ✅ 国内有 CDN | `https://www.apple.com` |
| microsoft | Microsoft/OneDrive | ✅ 国内有业务 | `https://www.microsoft.com` |
| games | 海外游戏（DAE 无此组，直接路由到 hongkong） | ❌ 被墙 | `https://www.gstatic.com/generate_204` |
| final | 兜底组 | ✅ | `https://cp.cloudflare.com/generate_204` |

### 4.2 各平台组类型对比

| 服务组 | DAE | Clash | Sing-box | 说明 |
|--------|-----|-------|----------|------|
| youtube | min_moving_avg | **fallback** | urltest | Clash 有优先级，其余自动选优 |
| google | min_moving_avg | **fallback** | urltest | 同上 |
| github | min_moving_avg | **fallback + DIRECT** | urltest | 合法过墙，Clash 含 DIRECT 兜底 |
| 其余服务组（dns/cdn/apple/microsoft/final） | 合法过墙组含 DIRECT 兜底 | 同 github 模式 | 同 youtube 模式 | 合法过墙组含 DIRECT |

**关键差异**：
- **DAE**：`min_moving_avg` 自动选延迟最低节点，不能手动切换
- **Clash**：`fallback` 按优先级顺序尝试，第一个可用即走；可手动切区域组
- **Sing-box**：`urltest` 测所有出站选延迟最低，顺序无关；可手动切区域组

### 4.3 服务组优先级顺序

各服务组的区域优先级（仅 Clash fallback 按此顺序，DAE/Sing-box 自动选优不受顺序影响）：

| 服务 | 优先级顺序（公共尾部：`→ self`） |
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

## 5. 兜底策略（self 自建组）

### 5.1 self 节点

- 自建节点（vless+reality、hysteria2 等）
- 作为所有服务组的最终兜底选项

### 5.2 DAE 的 add_latency 机制

DAE 通过 `[add_latency: +500ms]` 实现兜底优先级：

```
filter: subtag(america, hongkong, japan, korea, macao, taiwan, singapore)
filter: subtag(self) [add_latency: +500ms]    ← 延迟加 500ms，只有其他区域都故障才选 self
```

### 5.3 Clash/Sing-box 的兜底

- Clash：`self` 放在每个 fallback 组的最后，优先级最低
- Sing-box：`self` 放在每个 urltest 组的出站列表末尾

---

## 6. 测速地址策略

### 6.1 设计原则

1. **服务相关性**：测速地址应代表该服务的目标网络，测出的延迟能反映节点访问该服务的质量
2. **轻量性**：优先使用返回 204 的端点（无 body，纯测连接+响应时间）
3. **稳定性**：端点需长期稳定可用

### 6.2 测速地址参考

| 测速地址 | 响应 | 评价 |
|----------|------|------|
| `https://cp.cloudflare.com/generate_204` | 204 | 🥇 最优，Cloudflare 官方 204 端点 |
| `https://www.apple.com` | 200 | ✅ 快，但非 204 |
| `https://www.youtube.com/generate_204` | 204 | 🥇 最优，YouTube 官方 204 |
| `https://github.com` | 200 | ✅ 稳定 |
| `https://www.gstatic.com/generate_204` | 204 | 🥇 最优，Google 官方 204 |
| `https://1.1.1.1` | — | ✅ Cloudflare DNS |
| `https://www.microsoft.com` | 200 | ⚠️ 有抖动 |
| `https://chatgpt.com` | 403 | ⚠️ 403 但稳定，能反映 AI 可达性 |
| `https://telegram.org` | 200 | ⚠️ 较慢但稳定 |

### 6.3 两级测速链路

```
服务组 (urltest/fallback)
  → 专属测速地址（如 chatgpt.com）
  → 测各区域组到该地址的延迟
  → 选最优区域组
      ↓
区域组 (urltest/url-test)
  → 统一测速地址（gstatic.com/generate_204）
  → 测区域内各节点到该地址的延迟
  → 选最优节点
```

---

## 7. 三平台差异总结

### 7.1 架构差异

| 维度 | DAE | Clash | Sing-box |
|------|-----|-------|----------|
| **内核机制** | eBPF + tproxy | 用户态代理 | 用户态代理 |
| **组嵌套** | ❌ 不支持 | ✅ 支持 | ✅ 支持 |
| **组类型** | `min_moving_avg`（唯一自动策略） | `url-test` `select` `fallback` | `urltest` `selector` |
| **手动选组** | ❌ 不能 | ✅ 可 UI 手动切 | ✅ 可 UI 手动切 |

### 7.2 组类型映射

| DAE | Clash | Sing-box | 行为 |
|-----|-------|----------|------|
| `min_moving_avg` | `url-test`/`fallback` | `urltest` | 自动选节点 |
| — | `select` | `selector` | 手动选择 |
| `must_direct` | `DIRECT` | `Direct` | 直连 |

---

## 8. 设计决策记录

### 8.1 为什么用 `must_direct` 而非 `direct`（DAE）

- `must_direct`：dae 内核 bypass，不经过 DNS 劫持，直接 eBPF 发出
- `direct`：经过 tproxy 劫持 → dae DNS 处理 → 再直连
- 国内域名走 `must_direct` 更高效，且兼容系统 DNS

### 8.2 为什么服务组用 `urltest` 而非 `selector`（Sing-box）

- 用户希望自动故障转移（当区域组故障时自动切到其他区域）
- `urltest` 自动测速选最优，实现故障转移

### 8.3 为什么 Clash 用 `fallback` 而非 `url-test`

- `fallback` 按优先级顺序尝试，第一个可用即走
- 适合控制"首选香港，香港挂了走台湾"的优先级
- `url-test` 测所有节点选延迟最低，无法控制优先级

### 8.4 为什么 `self` 放在最后兜底

- 自建节点带宽有限，用作主力不合适
- 作为机场节点全挂时的最后保障
- DAE 通过 `add_latency: +500ms` 实现，Clash/Sing-box 通过出站列表顺序实现

### 8.5 为什么区分 `others` 组

- 非常用国家节点网络质量差异大
- 不适合自动选优（可能选到延迟低但带宽小的节点）
- 手动选择让用户根据实际需求挑选

### 8.6 为什么香港和澳门在 overseaai 中排在最后

- 香港/澳门对海外 AI 服务（OpenAI、Anthropic）支持差
- 政治因素导致机场转发到其他地区
- 所以 overseaai 的优先级：america → japan → singapore → korea → taiwan → hongkong → macao