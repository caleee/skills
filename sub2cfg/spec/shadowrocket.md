---
name: Shadowrocket URI 格式定义
platform: shadowrocket
type: uri
---

# Shadowrocket URI 订阅格式

## 参考文档

- Shadowrocket: https://apps.apple.com/app/shadowrocket/id932747118
- SIP002 URI 规范: https://shadowsocks.org/guide/sip002.html

## 完整格式

Shadowrocket 使用标准 URI 格式表示代理节点，每行一个 URI：

```
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpzc3Bhc3MxMjNAZXhhbXBsZS5jb206NDQz#🇭🇰香港01
trojan://password@example.com:443?peer=example.com&allowInsecure=1#🇭🇰香港02
```

## ss:// 格式

```
ss://base64(method:password@server:port)#fragment
```

- `method:password@server:port` 整体进行 base64 编码
- `#fragment` 为节点名称（URL 编码）

## trojan:// 格式

```
trojan://password@server:port?params#fragment
```

- `password` 为 Trojan 密码
- `params` 为查询参数
- `#fragment` 为节点名称（URL 编码）

### 查询参数

| 参数 | 说明 | 对应 Clash 字段 |
|------|------|-----------------|
| `peer` | TLS SNI | `sni` |
| `allowInsecure` | 允许不安全证书 | `skip-cert-verify` |
| `fp` | TLS 指纹 | `client-fingerprint` |