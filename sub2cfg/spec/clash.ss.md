---
name: Clash (Mihomo) Shadowsocks 格式定义
platform: clash
protocol: ss
---

# Clash / Mihomo Shadowsocks 代理格式

## 参考文档

- 官方文档: https://wiki.metacubex.one/config/proxies/ss/

## 完整 YAML 结构

```yaml
proxies:
  - name: "节点名称"
    type: ss
    server: example.com
    port: 443
    cipher: chacha20-ietf-poly1305
    password: "your-password"
    udp: true
    plugin: obfs
    plugin-opts:
      mode: tls
      host: example.com
```

## 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 节点名称 |
| `type` | string | 是 | 固定为 `ss` |
| `server` | string | 是 | 服务器地址 |
| `port` | int | 是 | 服务器端口 |
| `cipher` | string | 是 | 加密方法，如 `chacha20-ietf-poly1305`、`aes-256-gcm`、`aes-128-gcm` |
| `password` | string | 是 | SS 密码 |
| `udp` | bool | 否 | 启用 UDP 支持 |
| `plugin` | string | 否 | 插件类型，如 `obfs`、`v2ray-plugin` |
| `plugin-opts` | dict | 否 | 插件选项 |

## 常用加密方法

- `aes-256-gcm`（推荐）
- `aes-128-gcm`
- `chacha20-ietf-poly1305`（推荐）
- `xchacha20-ietf-poly1305`
- `none`（不加密，不推荐）

## 完整示例

```yaml
proxies:
  - name: "🇭🇰 香港 01"
    type: ss
    server: hk-01.example.com
    port: 443
    cipher: chacha20-ietf-poly1305
    password: "aB3dEfGhIjKlMnOpQrStUv"
    udp: true
```