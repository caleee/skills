---
name: Clash -> Sing-box Hysteria2 转换规则
source: clash
target: sing-box
protocol: hysteria2
---

# Clash (Mihomo) -> Sing-box Hysteria2 转换规则

## 字段映射

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
| `obfs` | `obfs.type` | 放入 obfs 对象 |
| `obfs-password` | `obfs.password` | 放入 obfs 对象 |
| `up` | `up_mbps` | 字符串 `"30 Mbps"` -> int `30` |
| `down` | `down_mbps` | 字符串 `"200 Mbps"` -> int `200` |

## 默认值补充

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `type` | `"hysteria2"` | 固定值 |
| `tls.enabled` | `true` | 默认启用 |
| `tls.utls.enabled` | `true` | 有 fingerprint 时启用 |

## 转换规则

1. Clash 的平铺字段收拢为 Sing-box 的嵌套结构
2. `sni` 放入 `tls.server_name`，`skip-cert-verify` 放入 `tls.insecure`
3. `client-fingerprint` 展开为 `tls.utls` 对象
4. `obfs` + `obfs-password` 合并为 `obfs` 对象（`type` + `password`）
5. `up`/`down` 带宽字符串提取数字转为 `up_mbps`/`down_mbps`（int）
6. `port` 改为 `server_port`

## 输入示例（Clash YAML）

```yaml
- name: "🇭🇰 香港 01"
  type: hysteria2
  server: hk-01.example.com
  port: 443
  password: "aB3dEfGh"
  sni: www.cloudflare.com
  alpn: [h3]
  skip-cert-verify: true
  obfs: salamander
  obfs-password: obfspass
  up: "30 Mbps"
  down: "200 Mbps"
  client-fingerprint: chrome
```

## 输出示例（Sing-box JSON）

```json
{
  "type": "hysteria2",
  "tag": "🇭🇰 香港 01",
  "server": "hk-01.example.com",
  "server_port": 443,
  "password": "aB3dEfGh",
  "obfs": {
    "type": "salamander",
    "password": "obfspass"
  },
  "up_mbps": 30,
  "down_mbps": 200,
  "tls": {
    "enabled": true,
    "server_name": "www.cloudflare.com",
    "insecure": true,
    "alpn": ["h3"],
    "utls": {
      "enabled": true,
      "fingerprint": "chrome"
    }
  }
}
```
