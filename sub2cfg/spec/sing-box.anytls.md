---
name: Sing-box AnyTLS 格式定义
platform: sing-box
protocol: anytls
---

# Sing-box AnyTLS 出站配置格式

## 参考文档

- 官方文档: https://sing-box.sagernet.org/configuration/outbound/anytls/
- TLS 配置: https://sing-box.sagernet.org/configuration/shared/tls/

## 完整 JSON 结构

```json
{
  "type": "anytls",
  "tag": "anytls-out",
  "server": "127.0.0.1",
  "server_port": 1080,
  "password": "8JCsPssfgS8tiRwiMlhARg==",
  "idle_session_check_interval": "30s",
  "idle_session_timeout": "30s",
  "min_idle_session": 5,
  "tls": {
    "enabled": true,
    "server_name": "example.com",
    "insecure": false,
    "alpn": ["h2"],
    "utls": {
      "enabled": true,
      "fingerprint": "firefox"
    }
  }
}
```

## 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 是 | 固定为 `"anytls"` |
| `tag` | string | 否 | 路由标签 |
| `server` | string | 是 | 服务器地址 |
| `server_port` | int | 是 | 服务器端口 |
| `password` | string | 是 | AnyTLS 密码 |
| `idle_session_check_interval` | duration | 否 | 空闲会话检查间隔，默认 `"30s"` |
| `idle_session_timeout` | duration | 否 | 空闲会话超时，默认 `"30s"` |
| `min_idle_session` | int | 否 | 最少保持的空闲会话数，默认 `0` |
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

## YAML 等效格式

```yaml
type: anytls
tag: anytls-out
server: 127.0.0.1
server_port: 1080
password: "8JCsPssfgS8tiRwiMlhARg=="
idle_session_check_interval: 30s
idle_session_timeout: 30s
min_idle_session: 5
tls:
  enabled: true
  server_name: example.com
  insecure: false
  alpn:
    - h2
  utls:
    enabled: true
    fingerprint: firefox
```

## 完整示例

```json
{
  "type": "anytls",
  "tag": "🇭🇰 HKG 香港 01",
  "server": "hk-01.fastnode.example.com",
  "server_port": 443,
  "password": "aB3dEfGhIjKlMnOpQrStUv",
  "tls": {
    "enabled": true,
    "server_name": "www.cloudflare.com",
    "insecure": true,
    "alpn": ["h2"]
  }
}
```