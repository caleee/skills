---
name: Clash → Sing-box AnyTLS 转换规则
source: clash
target: sing-box
protocol: anytls
---

# Clash (Mihomo) → Sing-box AnyTLS 转换规则

## 字段映射

Clash 的 anytls 格式是平铺的 YAML 字段，Sing-box 使用嵌套 JSON 结构。

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
| `tfo` | 忽略 | Sing-box 由 dial 字段控制 |
| `name-cert-verify` | 忽略 | Sing-box 无对应字段 |
| `idle-session-check-interval` | `idle_session_check_interval` | 字段名变为下划线，值单位不变 |
| `idle-session-timeout` | `idle_session_timeout` | 同上 |
| `min-idle-session` | `min_idle_session` | 同上 |

## 默认值补充

转换时补充以下 Sing-box 默认值：

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `type` | `"anytls"` | 固定值 |
| `tls.enabled` | `true` | 默认启用 |
| `tls.utls.enabled` | `true` | 有 fingerprint 时启用 |

## 转换规则

1. Clash 的平铺字段需要**收拢**为 Sing-box 的嵌套结构
2. `sni` 放入 `tls.server_name`
3. `skip-cert-verify` 放入 `tls.insecure`
4. `client-fingerprint` 展开为 `tls.utls.enabled: true` + `tls.utls.fingerprint`
5. `port` 改为 `server_port`
6. Clash 特有的 `udp`、`tfo` 等字段忽略
7. 连字符字段名改为下划线命名

## 转换说明

Clash 的 TLS 字段是平铺的（`sni`、`skip-cert-verify`、`client-fingerprint`），需要收拢到 Sing-box 的嵌套 `tls` 对象中，这是转换中最需要关注的部分。

## 输入示例（Clash YAML）

```yaml
- name: "🇭🇰 香港 01"
  type: anytls
  server: hk-01.fastnode.example.com
  port: 443
  password: "aB3dEfGhIjKlMnOpQrStUv"
  client-fingerprint: firefox
  alpn: [h2]
  sni: www.cloudflare.com
  skip-cert-verify: true
  udp: true
```

## 输出示例（Sing-box JSON）

```json
{
  "type": "anytls",
  "tag": "🇭🇰 香港 01",
  "server": "hk-01.fastnode.example.com",
  "server_port": 443,
  "password": "aB3dEfGhIjKlMnOpQrStUv",
  "tls": {
    "enabled": true,
    "server_name": "www.cloudflare.com",
    "insecure": true,
    "alpn": ["h2"],
    "utls": {
      "enabled": true,
      "fingerprint": "firefox"
    }
  }
}
```