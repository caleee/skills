---
name: Clash (Mihomo) Hysteria2 格式定义
platform: clash
protocol: hysteria2
---

# Clash / Mihomo Hysteria2 代理格式

## 参考文档

- 官方文档: https://wiki.metacubex.one/config/proxies/hysteria2/

## 完整 YAML 结构

```yaml
proxies:
  - name: "节点名称"
    type: hysteria2
    server: example.com
    port: 443
    password: "your-password"
    sni: "example.com"
    skip-cert-verify: true
    alpn:
      - h3
    obfs: salamander
    obfs-password: "your-obfs-password"
    up: "30 Mbps"
    down: "200 Mbps"
    client-fingerprint: chrome
```

## 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 节点名称 |
| `type` | string | 是 | 固定为 `hysteria2` |
| `server` | string | 是 | 服务器地址 |
| `port` | int | 是 | 服务器端口 |
| `password` | string | 是 | Hysteria2 密码 |
| `sni` | string | 否 | TLS SNI |
| `alpn` | string[] | 否 | ALPN 协议列表 |
| `skip-cert-verify` | bool | 否 | 跳过 TLS 证书验证 |
| `client-fingerprint` | string | 否 | TLS 客户端指纹（如 `chrome`） |
| `obfs` | string | 否 | 混淆类型（如 `salamander`） |
| `obfs-password` | string | 否 | 混淆密码 |
| `up` | string | 否 | 上行带宽（如 `"30 Mbps"`） |
| `down` | string | 否 | 下行带宽（如 `"200 Mbps"`） |

## 完整示例

```yaml
proxies:
  - name: "🇭🇰 香港 01"
    type: hysteria2
    server: hk-01.example.com
    port: 443
    password: "aB3dEfGh"
    sni: "www.cloudflare.com"
    alpn:
      - h3
    skip-cert-verify: true
    obfs: salamander
    obfs-password: "obfspass"
    up: "30 Mbps"
    down: "200 Mbps"
    client-fingerprint: chrome
```
