---
name: Clash 策略组生成规则
source: clash
target: clash
type: group-gen
---

# Clash 策略组生成规则

## 概述

从 Clash 格式的节点列表生成 `proxy-groups` 配置段。

## 输入

Clash 格式的节点列表（YAML 数组），从订阅 YAML 的 `proxies:` 段提取。

## 节点过滤规则

1. 过滤掉非代理节点（name 不包含 emoji 国旗的节点，如 "当前流量"、"到期时间"）
2. 根据 name 中的 emoji 国旗前缀识别区域

## 区域映射

区域映射表见 `registry.md`。

## 生成的组结构

### 1. 主选择组（PROXIES）

```yaml
- name: "PROXIES"
  type: select
  proxies:
    - DIRECT
    - 🇭🇰 HKG 香港 01
    - 🇭🇰 HKG 香港 02
    ...
    - 🇺🇸 USA 美国 01
    ...
```

- `type: select`
- 包含所有已转换的节点名 + `DIRECT`
- 节点按区域分组排列

### 2. 服务策略组（select）

标准服务组模板，每个包含：`DIRECT` + `PROXIES` + 各区域组名。

Standard service groups:
- `DNS` — 用于 DNS 解析的路由
- `OverseaAI` — 海外 AI 服务
- `Bing`
- `YouTube`
- `Google`
- `GitHub`
- `Telegram`
- `Apple`
- `OneDrive`
- `Microsoft`
- `Games`
- `Discord`
- `Cloudflare`

所有服务组格式：
```yaml
- name: "YouTube"
  type: select
  proxies:
    - DIRECT
    - PROXIES
    - HK
    - JP
    - SG
    - TW
    - US
    - FINAL
```

### 3. 区域自动组（url-test）

每个区域生成一个 `url-test` 组，包含该区域所有节点。

```yaml
- name: "HK"
  type: url-test
  proxies:
    - 🇭🇰 HKG 香港 01
    - 🇭🇰 HKG 香港 02
    ...
  url: https://www.gstatic.com/generate_204
  interval: 300
```

- `type: url-test`
- `url: https://www.gstatic.com/generate_204`
- `interval: 300`
- `proxies` 包含该区域内所有节点

### 4. 兜底组（FINAL）

```yaml
- name: "FINAL"
  type: select
  proxies:
    - DIRECT
    - PROXIES
    - HK
    - JP
    - SG
    - TW
    - US
```

## 完整输出示例

```yaml
proxy-groups:
  - name: "PROXIES"
    type: select
    proxies:
      - DIRECT
      - 🇭🇰 HKG 香港 01
      - 🇭🇰 HKG 香港 02
      ...
      - 🇺🇸 USA 美国 01
      ...

  - name: "DNS"
    type: select
    proxies:
      - DIRECT
      - PROXIES
      - HK
      - JP
      - SG
      - TW
      - US
      - FINAL

  ...（其他服务组类似）

  - name: "HK"
    type: url-test
    proxies:
      - 🇭🇰 HKG 香港 01
      - 🇭🇰 HKG 香港 02
      ...
    url: https://www.gstatic.com/generate_204
    interval: 300

  ...（其他区域组类似）

  - name: "FINAL"
    type: select
    proxies:
      - DIRECT
      - PROXIES
      - HK
      - JP
      - SG
      - TW
      - US
```