---
name: Clash 统一中间格式节点字段规范
platform: clash
type: proxy-format
---

# Clash 统一中间格式节点字段规范

本文档定义 sub2cfg 系统内部使用的统一 Clash 节点 dict 格式。所有提取器（extract/*.py）必须产出此格式，所有转换器（convert/*.py）消费此格式。

## 通用字段

以下字段适用于所有协议：

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `name` | string | 是 | 节点名称，含 emoji 国旗标识区域 |
| `type` | string | 是 | 协议类型，取值见下文 |
| `server` | string | 是 | 服务器地址（域名或 IP） |
| `port` | int | 是 | 服务器端口 |

## 各协议字段规范

### ss (Shadowsocks)

`type` 固定为 `"ss"`。

| 字段 | 类型 | 必填 | 说明 | 来源约束 |
|------|------|:----:|------|----------|
| `cipher` | string | 是 | 加密方法，如 `chacha20-ietf-poly1305`、`aes-256-gcm` | 所有提取器必须产生 |
| `password` | string | 是 | SS 密码 | 所有提取器必须产生 |
| `udp` | bool | 否 | 启用 UDP 支持 | 提取器有来源数据时设 `true`，无数据时省略；**不设 `false`** |
| `plugin` | string | 否 | 插件类型，如 `obfs`、`v2ray-plugin` | 仅 Clash 透传来源 |
| `plugin-opts` | dict | 否 | 插件选项 | 仅 Clash 透传来源 |

### trojan

`type` 固定为 `"trojan"`。

| 字段 | 类型 | 必填 | 说明 | 来源约束 |
|------|------|:----:|------|----------|
| `password` | string | 是 | Trojan 密码 | 所有提取器必须产生 |
| `sni` | string | 否 | TLS SNI | 有则设，无则省略 |
| `skip-cert-verify` | bool | 否 | 跳过 TLS 证书验证 | 仅在值为 `true` 时设置；**不设 `false`** |
| `alpn` | string[] | 否 | ALPN 协议列表，如 `["h2", "http/1.1"]` | 有则设，无则省略 |
| `client-fingerprint` | string | 否 | TLS 客户端指纹，如 `"chrome"`、`"firefox"` | 有则设，无则省略 |
| `udp` | bool | 否 | 启用 UDP 支持 | 提取器有来源数据时设 `true`，无数据时省略；**不设 `false`** |

### anytls

`type` 固定为 `"anytls"`。

| 字段 | 类型 | 必填 | 说明 | 来源约束 |
|------|------|:----:|------|----------|
| `password` | string | 是 | AnyTLS 密码 | 所有提取器必须产生 |
| `sni` | string | 否 | TLS SNI | 有则设，无则省略 |
| `skip-cert-verify` | bool | 否 | 跳过 TLS 证书验证 | 仅在值为 `true` 时设置；**不设 `false`** |
| `alpn` | string[] | 否 | ALPN 协议列表，如 `["h2"]` | 有则设，无则省略 |
| `client-fingerprint` | string | 否 | TLS 客户端指纹，如 `"chrome"`、`"firefox"` | 有则设，无则省略 |
| `udp` | bool | 否 | 启用 UDP 支持 | 提取器有来源数据时设 `true`，无数据时省略；**不设 `false`** |
| `idle-session-check-interval` | int | 否 | 空闲会话检查间隔（秒），默认 `30` | 有则设，无则省略 |
| `idle-session-timeout` | int | 否 | 空闲会话超时（秒），默认 `30` | 有则设，无则省略 |
| `min-idle-session` | int | 否 | 最少保持的空闲会话数，默认 `0` | 有则设，无则省略 |

### hysteria2

`type` 固定为 `"hysteria2"`。

| 字段 | 类型 | 必填 | 说明 | 来源约束 |
|------|------|:----:|------|----------|
| `password` | string | 是 | Hysteria2 密码 | 所有提取器必须产生 |
| `sni` | string | 否 | TLS SNI | 有则设，无则省略 |
| `skip-cert-verify` | bool | 否 | 跳过 TLS 证书验证 | 仅在值为 `true` 时设置；**不设 `false`** |
| `alpn` | string[] | 否 | ALPN 协议列表，如 `["h3"]` | 有则设，无则省略 |
| `client-fingerprint` | string | 否 | TLS 客户端指纹，如 `"chrome"` | 有则设，无则省略 |
| `obfs` | string | 否 | 混淆类型，如 `"salamander"` | 有则设，无则省略 |
| `obfs-password` | string | 否 | 混淆密码 | 有 `obfs` 时如有密码则设 |
| `up` | string | 否 | 上行带宽，格式如 `"30 Mbps"` | 有则设，无则省略 |
| `down` | string | 否 | 下行带宽，格式如 `"200 Mbps"` | 有则设，无则省略 |

## 通用规则

### 1. 字段命名

全部使用 **kebab-case**（连字符命名），与 Clash 官方格式一致：

- ✅ `skip-cert-verify`
- ✅ `client-fingerprint`
- ✅ `obfs-password`
- ✅ `idle-session-check-interval`
- ✅ `plugin-opts`

### 2. 布尔字段

- 值为 `true` 时才设置该字段
- 值为 `false` 或不确定时**省略该字段**，不显式设 `false`
- 例外：转换器消费时，`skip-cert-verify` 缺省视为 `false`（安全行为）

### 3. 可选字段

- 无数据来源时**省略字段**，不设空值或默认值
- 转换器消费时对缺省字段按安全默认值处理

### 4. 禁止字段

以下字段**不应出现在统一中间格式中**：

| 字段 | 原因 |
|------|------|

（当前无禁止字段。所有出现在 Clash 源数据中的合法字段均保留透传。）

### 5. 字段产生来源

| 提取器 | 字段来源说明 |
|--------|-------------|
| `clash.py` | 透传 `proxies:` 段中的所有字段，需确保符合本规范 |
| `surge.py` | 从 `name = protocol, server, port, k=v, ...` 解析；`encrypt-method` → `cipher`，`udp-relay` → `udp` |
| `shadowrocket.py` | 从 URI 解析；`peer` → `sni`，`allowInsecure` → `skip-cert-verify`，`fp` → `client-fingerprint` |
| `singbox.py` | 从 JSON outbound 反向映射；`server_name` → `sni`，`insecure` → `skip-cert-verify`，`fingerprint` → `client-fingerprint` |

## 字段顺序（输出 YAML 时）

按以下优先级排序输出，确保 YAML 可读性：

1. `name`
2. `type`
3. `server`
4. `port`
5. 各协议必填字段（`password`、`cipher`）
6. TLS 相关字段（`sni`、`skip-cert-verify`、`alpn`、`client-fingerprint`）
7. 协议特有字段（`obfs`、`obfs-password`、`up`、`down`、`plugin`、`plugin-opts`）
8. 功能开关（`udp`）
9. 高级参数（`idle-session-*`、`min-idle-session`）

## YAML 引号约定

PyYAML 自动处理引号：当值包含 YAML 特殊字符（`:`、`#`、`{}` 等）时自动加双引号，简单值不加引号。这是标准 YAML 行为，Clash 兼容。

### 示例输出

```yaml
proxies:
  - name: "🇭🇰 香港 01"
    type: ss
    server: example.com
    port: 443
    cipher: chacha20-ietf-poly1305
    password: "your-password"
    sni: "sni.example.com"
    skip-cert-verify: true
    client-fingerprint: chrome
    alpn:
      - h2
    udp: true
    idle-session-check-interval: 30
```