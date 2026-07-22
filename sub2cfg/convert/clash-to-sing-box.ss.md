---
name: Clash → Sing-box Shadowsocks 转换规则
source: clash
target: sing-box
protocol: ss
---

# Clash (Mihomo) → Sing-box Shadowsocks 转换规则

## 字段映射

| Clash 字段 | Sing-box 字段 | 转换说明 |
|------------|---------------|----------|
| `name` | `tag` | 直接映射 |
| `server` | `server` | 直接映射 |
| `port` | `server_port` | 字段名不同 |
| `cipher` | `method` | 字段名不同 |
| `password` | `password` | 直接映射 |
| `udp` | `udp_over_tcp` | 字段名不同 |
| `plugin` | `plugin` | 直接映射 |
| `plugin-opts` | `plugin_opts` | 连字符改为下划线 |

## 默认值补充

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `type` | `"shadowsocks"` | 固定值 |
| `method` | `"aes-256-gcm"` | 未指定时默认 |

## 转换说明

1. Clash 的 `cipher` 字段映射为 Sing-box 的 `method` 字段
2. Clash 的 `udp` 布尔值映射为 `udp_over_tcp`
3. `plugin-opts` 的连字符命名改为下划线命名

## 输入示例（Clash YAML）

```yaml
- name: "🇭🇰 香港 01"
  type: ss
  server: hk-01.example.com
  port: 443
  cipher: chacha20-ietf-poly1305
  password: "aB3dEfGhIjKlMnOpQrStUv"
  udp: true
```

## 输出示例（Sing-box JSON）

```json
{
  "type": "shadowsocks",
  "tag": "🇭🇰 香港 01",
  "server": "hk-01.example.com",
  "server_port": 443,
  "method": "chacha20-ietf-poly1305",
  "password": "aB3dEfGhIjKlMnOpQrStUv",
  "udp_over_tcp": true
}
```