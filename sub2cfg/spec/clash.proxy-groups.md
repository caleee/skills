---
name: Clash (Mihomo) Proxy-Groups 格式定义
platform: clash
type: proxy-groups
---

# Clash / Mihomo Proxy-Groups 配置格式

## 参考文档

- 官方文档: https://wiki.metacubex.one/config/proxy-groups/
- Select 类型: https://wiki.metacubex.one/config/proxy-groups/select/
- URL-Test 类型: https://wiki.metacubex.one/config/proxy-groups/url-test/

## 通用结构

```yaml
proxy-groups:
  - name: "组名"
    type: select        # 或 url-test, fallback, load-balance, relay
    proxies:
      - DIRECT
      - 节点名或子组名
    url: 'https://www.gstatic.com/generate_204'  # url-test 用
    interval: 300                                 # url-test 用
```

## 公共字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 策略组名称 |
| `type` | string | 是 | 组类型：`select` / `url-test` / `fallback` / `load-balance` / `relay` |
| `proxies` | string[] | 否 | 引用出站代理或其他策略组 |
| `use` | string[] | 否 | 引用 proxy-provider |
| `url` | string | 否 | 延迟测试 URL，默认 `https://www.gstatic.com/generate_204` |
| `interval` | int | 否 | 延迟测试间隔（秒），`0` 为禁用 |
| `lazy` | bool | 否 | 未使用时跳过测试，默认 `true` |
| `timeout` | int | 否 | 延迟测试超时（毫秒），默认 `5000` |
| `tolerance` | int | 否 | 延迟切换容差（毫秒），仅 url-test 使用 |
| `max-failed-times` | int | 否 | 最大失败次数后强制测试 |
| `disable-udp` | bool | 否 | 禁用 UDP |
| `expected-status` | string | 否 | 期望 HTTP 状态码，默认 `*`（任意） |
| `hidden` | bool | 否 | 在 API 中隐藏该组 |

## select 类型

手动选择，用户从列表中选择要使用的节点或子组。

```yaml
- name: "Proxy"
  type: select
  proxies:
    - ss
    - vmess
    - auto
```

| 特有字段 | 说明 |
|----------|------|
| `default-selected` | 可选，默认选中的节点 |

## url-test 类型

自动选择延迟最低的节点。

```yaml
- name: "自动选择"
  type: url-test
  proxies:
    - ss
    - vmess
  url: 'https://www.gstatic.com/generate_204'
  interval: 300
  tolerance: 50
  lazy: true
```

| 特有字段 | 说明 |
|----------|------|
| `tolerance` | 延迟容差（毫秒），避免频繁切换 |
| `lazy` | 延迟首次测试直到有实际连接 |