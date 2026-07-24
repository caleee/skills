---
name: Sing-box Hysteria2 格式定义
platform: sing-box
protocol: hysteria2
---

# Sing-box Hysteria2 出站配置格式

## 参考文档

- 官方文档: https://sing-box.sagernet.org/configuration/outbound/hysteria2/
- TLS 配置: https://sing-box.sagernet.org/configuration/shared/tls/

## 完整 JSON 结构

```json
{
  "type": "hysteria2",
  "tag": "hysteria2-out",
  "server": "127.0.0.1",
  "server_port": 1080,
  "password": "8JCsPssfgS8tiRwiMlhARg==",
  "obfs": {
    "type": "salamander",
    "password": "8JCsPssfgS8tiRwiMlhARg=="
  },
  "up_mbps": 30,
  "down_mbps": 200,
  "tls": {
    "enabled": true,
    "server_name": "example.com",
    "insecure": false,
    "alpn": ["h3"],
    "utls": {
      "enabled": true,
      "fingerprint": "chrome"
    }
  }
}
```

## 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 是 | 固定为 `"hysteria2"` |
| `tag` | string | 否 | 路由标签 |
| `server` | string | 是 | 服务器地址 |
| `server_port` | int | 是 | 服务器端口 |
| `password` | string | 是 | Hysteria2 密码 |
| `obfs` | object | 否 | 混淆配置 |
| `obfs.type` | string | 否 | 混淆类型（如 `salamander`） |
| `obfs.password` | string | 否 | 混淆密码 |
| `up_mbps` | int | 否 | 上行带宽（Mbps） |
| `down_mbps` | int | 否 | 下行带宽（Mbps） |
| `tls` | object | 是 | TLS 配置（见下方） |

### tls 字段（出站）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `enabled` | bool | 否 | 是否启用 TLS，默认 `true` |
| `server_name` | string | 否 | TLS SNI，用于证书验证 |
| `insecure` | bool | 否 | 是否跳过证书验证，默认 `false` |
| `alpn` | string[] | 否 | ALPN 协议列表 |
| `utls` | object | 否 | uTLS 指纹配置 |
| `utls.enabled` | bool | 否 | 是否启用 uTLS |
| `utls.fingerprint` | string | 否 | 指纹类型：`firefox`, `chrome`, `edge`, `safari`, `ios`, `android`, `random` 等 |

## 完整示例

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
