---
name: Loon 代理格式定义
platform: loon
type: proxy
---

# Loon 代理配置格式

## 参考文档

- 官方文档: https://manual.loon.com/

## 完整格式

Loon 的代理配置位于 `[Proxy]` 段落中，每行一个代理节点：

```ini
[Proxy]
🇭🇰 香港 01 = ss, example.com, 443, encrypt-method=chacha20-ietf-poly1305, password=xxx
🇭🇰 香港 02 = trojan, trojan.example.com, 443, password=xxx, sni=ts.example.com, skip-cert-verify=true
```

## 格式说明

```
name = protocol, server, port, key=value, key=value, ...
```

与 Surge 格式基本相同，但 Loon 不支持 `udp-relay` 参数；提取器会忽略该参数（即使出现也不解析为字段）。

## 通用参数

| 参数名 | 对应 Clash 字段 | 说明 |
|--------|-----------------|------|
| `encrypt-method` | `cipher` | 加密方法（SS 协议） |
| `password` | `password` | 密码 |
| `sni` | `sni` | TLS SNI |
| `skip-cert-verify` | `skip-cert-verify` | 跳过证书验证 |
| `client-fingerprint` | `client-fingerprint` | TLS 指纹 |