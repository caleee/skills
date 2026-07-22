---
name: Clash (Mihomo) Trojan 格式定义
platform: clash
protocol: trojan
---

# Clash / Mihomo Trojan 代理格式

## 参考文档

- 官方文档: https://wiki.metacubex.one/config/proxies/trojan/

## 完整 YAML 结构

```yaml
proxies:
  - name: "节点名称"
    type: trojan
    server: example.com
    port: 443
    password: "your-password"
    udp: true
    sni: example.com
    alpn:
      - h2
      - http/1.1
    skip-cert-verify: true
    client-fingerprint: chrome
```

## 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 节点名称 |
| `type` | string | 是 | 固定为 `trojan` |
| `server` | string | 是 | 服务器地址 |
| `port` | int | 是 | 服务器端口 |
| `password` | string | 是 | Trojan 密码 |
| `udp` | bool | 否 | 启用 UDP 支持 |
| `sni` | string | 否 | TLS SNI |
| `alpn` | string[] | 否 | ALPN 协议列表 |
| `skip-cert-verify` | bool | 否 | 跳过 TLS 证书验证 |
| `client-fingerprint` | string | 否 | TLS 客户端指纹（如 `chrome`、`firefox`） |

## 完整示例

```yaml
proxies:
  - name: "🇭🇰 香港 01"
    type: trojan
    server: hk-01.example.com
    port: 443
    password: "aB3dEfGhIjKlMnOpQrStUv"
    udp: true
    sni: www.cloudflare.com
    alpn:
      - h2
    skip-cert-verify: true
    client-fingerprint: chrome
```