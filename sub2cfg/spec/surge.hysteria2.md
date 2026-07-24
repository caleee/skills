---
name: Surge Hysteria2 代理格式定义
platform: surge
protocol: hysteria2
---

# Surge Hysteria2 代理配置格式

## 参考文档

- Surge hysteria2: https://manual.nssurge.com/policy/hysteria2.html

## 完整格式

Surge 的 hysteria2 代理位于 `[Proxy]` 段落，格式与通用 Surge 代理一致：

```ini
[Proxy]
🇭🇰 香港 01 = hysteria2, example.com, 443, password=your-password, sni=example.com, obfs=salamander, obfs-password=obfspass, up=30, down=200, skip-cert-verify=true, client-fingerprint=chrome
```

## 格式说明

```
name = hysteria2, server, port, key=value, key=value, ...
```

## 通用参数

| 参数名 | 对应 Clash 字段 | 说明 |
|--------|-----------------|------|
| `password` | `password` | Hysteria2 密码 |
| `sni` | `sni` | TLS SNI |
| `skip-cert-verify` | `skip-cert-verify` | 跳过证书验证（true/false） |
| `client-fingerprint` | `client-fingerprint` | TLS 指纹 |
| `alpn` | `alpn` | ALPN 协议（如 h3） |
| `obfs` | `obfs` | 混淆类型（如 salamander） |
| `obfs-password` | `obfs-password` | 混淆密码 |
| `up` | `up` | 上行带宽（Mbps） |
| `down` | `down` | 下行带宽（Mbps） |

## 备注

Surge hysteria2 的字段名与 Clash 一致，提取器通过 `_parse_kv_pairs` 透传。`up`/`down` 在 Surge 中为数字（Mbps），与 Clash 的 `"30 Mbps"` 字符串格式不同；转换为 sing-box 时由 `_parse_bandwidth` 提取数字。
