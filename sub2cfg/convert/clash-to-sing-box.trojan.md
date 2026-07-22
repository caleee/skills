---
name: Clash → Sing-box Trojan 转换规则
source: clash
target: sing-box
protocol: trojan
---

# Clash (Mihomo) → Sing-box Trojan 转换规则

## 字段映射

Clash 的 Trojan 格式与 anytls 类似，都是平铺 YAML 字段 + TLS 相关字段，需要收拢为 Sing-box 的嵌套结构。

| Clash 字段 | Sing-box 字段 | 转换说明 |
|------------|---------------|----------|
| `name` | `tag` | 直接映射 |
| `server` | `server` | 直接映射 |
| `port` | `server_port` | 字段名不同 |
| `password` | `password` | 直接映射 |
| `sni` | `tls.server_name` | 从顶层字段放入 tls 对象 |
| `alpn` | `tls.alpn` | 数组直接映射 |
| `skip-cert-verify` | `tls.insecure` | 布尔值直接映射 |
| `client-fingerprint` | `tls.utls.enabled` + `tls.utls.fingerprint` | 展开为 utls 对象 |
| `udp` | 忽略 | Sing-box 由路由控制 |

## 默认值补充

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `type` | `"trojan"` | 固定值 |
| `tls.enabled` | `true` | 默认启用 |
| `tls.utls.enabled` | `true` | 有 fingerprint 时启用 |

## 转换规则

1. Clash 的平铺字段需要**收拢**为 Sing-box 的嵌套结构
2. `sni` 放入 `tls.server_name`
3. `skip-cert-verify` 放入 `tls.insecure`
4. `client-fingerprint` 展开为 `tls.utls.enabled: true` + `tls.utls.fingerprint`
5. `port` 改为 `server_port`

## 输入示例（Clash YAML）

```yaml
- name: "🇭🇰 香港 01"
  type: trojan
  server: hk-01.example.com
  port: 443
  password: "aB3dEfGhIjKlMnOpQrStUv"
  client-fingerprint: chrome
  alpn: [h2]
  sni: www.cloudflare.com
  skip-cert-verify: true
  udp: true
```

## 输出示例（Sing-box JSON）

```json
{
  "type": "trojan",
  "tag": "🇭🇰 香港 01",
  "server": "hk-01.example.com",
  "server_port": 443,
  "password": "aB3dEfGhIjKlMnOpQrStUv",
  "tls": {
    "enabled": true,
    "server_name": "www.cloudflare.com",
    "insecure": true,
    "alpn": ["h2"],
    "utls": {
      "enabled": true,
      "fingerprint": "chrome"
    }
  }
}
```