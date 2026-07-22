---
name: Sing-box Shadowsocks 格式定义
platform: sing-box
protocol: ss
---

# Sing-box Shadowsocks 出站配置格式

## 参考文档

- 官方文档: https://sing-box.sagernet.org/configuration/outbound/shadowsocks/

## 完整 JSON 结构

```json
{
  "type": "shadowsocks",
  "tag": "ss-out",
  "server": "127.0.0.1",
  "server_port": 1080,
  "method": "aes-256-gcm",
  "password": "8JCsPssfgS8tiRwiMlhARg==",
  "udp_over_tcp": false,
  "plugin": "",
  "plugin_opts": ""
}
```

## 字段说明

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `type` | string | 是 | — | 固定为 `"shadowsocks"` |
| `tag` | string | 否 | — | 路由标签 |
| `server` | string | 是 | — | 服务器地址 |
| `server_port` | int | 是 | — | 服务器端口 |
| `method` | string | 是 | — | 加密方法 |
| `password` | string | 是 | — | SS 密码 |
| `udp_over_tcp` | bool | 否 | `false` | UDP over TCP 代理 |
| `plugin` | string | 否 | — | 插件类型 |
| `plugin_opts` | string | 否 | — | 插件选项 |

## YAML 等效格式

```yaml
type: shadowsocks
tag: ss-out
server: 127.0.0.1
server_port: 1080
method: aes-256-gcm
password: "8JCsPssfgS8tiRwiMlhARg=="
udp_over_tcp: false
```

## 完整示例

```json
{
  "type": "shadowsocks",
  "tag": "🇭🇰 香港 01",
  "server": "hk-01.example.com",
  "server_port": 443,
  "method": "chacha20-ietf-poly1305",
  "password": "aB3dEfGhIjKlMnOpQrStUv"
}
```