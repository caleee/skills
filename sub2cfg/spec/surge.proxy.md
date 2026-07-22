---
name: Surge 代理格式定义
platform: surge
type: proxy
---

# Surge 代理配置格式

## 参考文档

- 官方文档: https://manual.nssurge.com/

## 完整格式

Surge 的代理配置位于 `[Proxy]` 段落中，每行一个代理节点：

```ini
[Proxy]
🇭🇰 香港 01 = ss, example.com, 443, encrypt-method=chacha20-ietf-poly1305, password=xxx, udp-relay=true
🇭🇰 香港 02 = trojan, trojan.example.com, 443, password=xxx, sni=ts.example.com, skip-cert-verify=true
🇭🇰 香港 03 = anytls, anytls.example.com, 443, password=xxx, sni=any.example.com, skip-cert-verify=true, client-fingerprint=firefox
```

## 格式说明

```
name = protocol, server, port, key=value, key=value, ...
```

- `name`: 节点名称
- `protocol`: 代理协议（`ss`、`trojan`、`anytls`、`http`、`socks5`、`vmess`）
- `server`: 服务器地址
- `port`: 服务器端口
- `key=value`: 协议参数，逗号分隔

## 通用参数

| 参数名 | 对应 Clash 字段 | 说明 |
|--------|-----------------|------|
| `encrypt-method` | `cipher` | 加密方法（SS 协议） |
| `password` | `password` | 密码 |
| `sni` | `sni` | TLS SNI |
| `skip-cert-verify` | `skip-cert-verify` | 跳过证书验证 |
| `udp-relay` | `udp` | UDP 中继 |
| `client-fingerprint` | `client-fingerprint` | TLS 指纹 |
| `tfo` | `tfo` | TCP Fast Open |