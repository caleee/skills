---
name: Clash (Mihomo) AnyTLS 格式定义
platform: clash
protocol: anytls
---

# Clash / Mihomo AnyTLS 代理格式

## 参考文档

- 官方文档: https://wiki.metacubex.one/config/proxies/anytls/

## 完整 YAML 结构

```yaml
proxies:
  - name: "节点名称"
    type: anytls
    server: example.com
    port: 443
    password: "your-password"
    udp: true
    sni: "example.com"
    alpn:
      - h2
      - http/1.1
    skip-cert-verify: true
    name-cert-verify: example.com
    client-fingerprint: firefox
    idle-session-check-interval: 30
    idle-session-timeout: 30
    min-idle-session: 0
```

## 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 节点名称 |
| `type` | string | 是 | 固定为 `anytls` |
| `server` | string | 是 | 服务器地址 |
| `port` | int | 是 | 服务器端口 |
| `password` | string | 是 | AnyTLS 密码 |
| `udp` | bool | 否 | 启用 UDP 支持 |
| `sni` | string | 否 | TLS SNI |
| `alpn` | string[] | 否 | ALPN 协议列表 |
| `skip-cert-verify` | bool | 否 | 跳过 TLS 证书验证 |
| `name-cert-verify` | string | 否 | 期望的证书名称 |
| `client-fingerprint` | string | 否 | TLS 客户端指纹（如 `firefox`） |
| `idle-session-check-interval` | int | 否 | 空闲会话检查间隔（秒），默认 `30` |
| `idle-session-timeout` | int | 否 | 空闲会话超时（秒），默认 `30` |
| `min-idle-session` | int | 否 | 最少保持的空闲会话数，默认 `0` |

## 完整示例

```yaml
proxies:
  - name: "🇭🇰 HKG 香港 01"
    type: anytls
    server: hk-01.fastnode.example.com
    port: 443
    password: "aB3dEfGhIjKlMnOpQrStUv"
    udp: true
    sni: "www.cloudflare.com"
    alpn:
      - h2
    skip-cert-verify: true
    client-fingerprint: firefox
```