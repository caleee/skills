# sub2cfg 架构设计

## 概述

sub2cfg 是一个订阅链接转代理配置工具，核心功能是从不同格式的订阅源中提取代理节点，转换到目标平台格式，并可选生成策略组。

```
订阅源 → 格式检测 → 节点提取 → 格式转换 → 策略组生成 → 输出
```

---

## 架构分层

### 数据流

```
                        ┌───────────────────────┐
                        │   订阅源 (用户提供)     │
                        │  Clash YAML / Surge /  │
                        │  Loon / Shadowrocket / │
                        │  Base64 / Sing-box     │
                        └──────────┬────────────┘
                                   │ raw text
                                   ▼
                        ┌───────────────────────┐
                        │   detect.py           │ ← 格式检测层
                        │   返回格式标识         │
                        │   clash / surge / ...  │
                        └──────────┬────────────┘
                                   │ format string
                                   ▼
                        ┌───────────────────────┐
                        │   extract/{fmt}.py    │ ← 提取层
                        │   解析原始内容         │
                        │   输出统一节点列表      │
                        └──────────┬────────────┘
                                   │ list[Clash-proxy-dict]
                                   ▼
                        ┌───────────────────────┐
                        │   convert/            │ ← 转换层
                        │   按协议分派转换器      │
                        │   anytls → convert_anytls │
                        │   ss → convert_ss     │
                        │   trojan → convert_trojan │
                        └──────────┬────────────┘
                                   │ list[target-format-dict]
                                   ▼
                        ┌───────────────────────┐
                        │   group/              │ ← 组生成层 (可选)
                        │   build_groups(nodes) │
                        │   Clash: proxy-groups │
                        │   Sing-box: outbounds │
                        └──────────┬────────────┘
                                   │
                                   ▼
                        ┌───────────────────────┐
                        │   yaml.dump → 输出     │ ← 输出层
                        │   stdout 或文件        │
                        └───────────────────────┘
```

### 统一中间格式

所有提取器输出同一格式：**Clash 代理节点 dict**。这是整个系统的核心约定。

```python
{
    "name": "🇭🇰 香港 01",     # 节点名称（含 emoji 区域标识）
    "type": "ss",              # 协议类型: ss / trojan / anytls
    "server": "example.com",   # 服务器地址
    "port": 443,               # 服务器端口
    "password": "xxx",         # 密码
    # 协议特有字段:
    "cipher": "chacha20-ietf-poly1305",  # SS 加密方法
    "sni": "sni.example.com",            # TLS SNI (trojan/anytls)
    "skip-cert-verify": True,            # 跳过证书验证
    "udp": True,                         # UDP 支持
    "client-fingerprint": "chrome",      # TLS 指纹
    "alpn": ["h2", "http/1.1"],         # ALPN 列表
}
```

---

## 模块职责

### 检测层: `detect.py`

单一职责：判断订阅内容的格式类型。

| 输入 | 输出 | 判断依据 |
|------|------|----------|
| 原始文本 | 格式标识字符串 | 关键字匹配、正则、base64 解码 |

返回的格式标识决定了后续使用哪个提取器。格式标识列表：

| 标识 | 对应格式 |
|------|----------|
| `clash` | Clash / Mihomo YAML |
| `surge` | Surge [Proxy] 段落 |
| `loon` | Loon [Proxy] 段落（无 udp-relay） |
| `shadowrocket` | Shadowrocket URI (ss:// trojan://) |
| `base64-uri` | Base64 编码内容 |
| `sing-box` | Sing-box JSON |
| `unknown` | 无法识别 |

### 提取层: `extract/*.py`

每个文件对应一种订阅格式，统一导出 `extract(content: str, format: str | None = None) -> list[dict]`。`format` 由调用方（`detect.py` 已判定）传入，避免提取器重复嗅探。

| 文件 | 输入格式 | 解析策略 |
|------|----------|----------|
| `clash.py` | YAML 文本 | `yaml.safe_load` → 取 `proxies:` 段 → 按 emoji 国旗过滤 |
| `surge.py` | 行文本 | 按 `name = protocol, server, port, kv...` 格式解析 |
| `shadowrocket.py` | URI 文本 | 解析 `ss://` base64 编码或 `trojan://` 标准 URI |
| `base64.py` | base64 文本 | 解码后递归调用 `detect()` 分派到对应提取器 |
| `singbox.py` | JSON 文本 | `json.loads` → 取 `outbounds[]` → 反向映射到 Clash 格式 |

### 转换层: `convert/to_singbox.py`

按协议类型将 Clash 格式节点转换为目标平台格式。

```python
convert_anytls(clash_node) -> singbox_outbound | None  # s
convert_ss(clash_node) -> singbox_outbound | None       # ss
convert_trojan(clash_node) -> singbox_outbound | None   # trojan
```

`convert/to_singbox.py` 中的 `convert()` 通过 `_CONVERTERS` 字典按 `node["type"]` 分派到对应的转换器。

### 组生成层: `group/*.py`

从节点列表中按区域分组（通过 emoji 国旗识别区域），生成策略组。

| 文件 | 目标平台 | 组结构 |
|------|----------|--------|
| `clash.py` | Clash | PROXIES + 13 个服务组 + 区域 url-test 组 + FINAL |
| `singbox.py` | Sing-box | DIRECT + PROXIES + 区域 urltest 组 + FINAL |

### 编排层: `sub2cfg.py`

主入口，编排整个流水线。

```
load_content() → detect() → EXTRACTOR_MODULES[fmt].extract() → convert() → [build_groups()] → yaml.dump()
```

---

## 关键设计决策

### 1. 统一中间格式为 Clash 格式

所有订阅格式的节点都转为 Clash 代理 dict，再按目标平台转换。这样新增格式只需写提取器，新增协议只需写转换器，互不耦合。

### 2. 惰性导入

`sub2cfg.py` 在函数内部使用 `from extract.clash import extract` 而非文件顶部导入。原因是：
- 避免启动时加载所有模块
- 路径依赖：`PYTHONPATH` 可能不含 `scripts/` 目录
- 保持 CLI 响应速度

### 3. 提取器与转换器分离

提取器只关心"怎么从订阅文本中解析出节点"，转换器只关心"怎么把节点转成目标格式"。

```
新增格式 → 写 extract/{format}.py
新增协议 → 写 convert/to_{target}.py 中的函数
新增目标平台 → 新建 convert/to_{target}.py + group/{target}.py
```

### 4. 跳过不支持的协议

转换器对不支持的协议返回 `None`，`sub2cfg.py` 统计跳过数量并输出警告，而不是直接报错退出。这样可以处理混合协议订阅。

### 5. 区域识别依赖 emoji 国旗

节点名中包含 emoji 国旗字符即视为该区域节点。这是一个启发式策略，覆盖了大多数机场的命名规范。

---

## 扩展指南

### 新增订阅格式

1. 在 `extract/` 下创建 `{format}.py`，实现 `extract(content: str) -> list[dict]`
2. 在 `detect.py` 的 `detect()` 函数中增加格式检测逻辑
3. 在 `detect.py` 的 `EXTRACTOR_MODULES` 字典中注册
4. 在 `spec/` 下创建格式定义文档
5. 在 `sample/` 下创建示例文件
6. 更新 `registry.md` 的订阅格式提取表

### 新增协议

1. 在 `convert/to_singbox.py` 中新增 `convert_{protocol}()` 函数
2. 在 `protocol.py` 注册类型映射，在 `convert/to_singbox.py` 的 `_CONVERTERS` 中增加分派
3. 在 `spec/` 下创建各平台的协议格式定义
4. 在 `convert/` 下创建协议转换规则文档
5. 更新 `registry.md` 的格式定义表和转换规则表

### 新增目标平台

1. 创建 `convert/to_{target}.py`，实现各协议的转换函数
2. 创建 `group/{target}.py`，实现 `build_groups()` 函数
3. 在 `sub2cfg.py` 的 `argparse` 中增加 `-t` 选项值
4. 在 `spec/` 下创建目标平台的格式定义
5. 更新 `registry.md`

---

## 目录结构

```
sub2cfg/
├── verify.py                  # 验证脚本（纯 Python）
├── registry.md                # 模块清单（所有格式、协议、转换规则的索引）
├── scripts/
│   ├── sub2cfg.py             # 主入口，编排流水线
│   ├── detect.py              # 格式检测
│   ├── requirements.txt       # 依赖：PyYAML + pytest（可选）
│   ├── extract/
│   │   ├── clash.py           # Clash YAML 提取
│   │   ├── surge.py           # Surge / Loon 提取
│   │   ├── shadowrocket.py    # Shadowrocket URI 提取
│   │   ├── base64.py          # Base64 解码提取
│   │   └── singbox.py         # Sing-box JSON 提取
│   ├── convert/
│   │   └── to_singbox.py      # Clash → Sing-box 转换（含 anytls/ss/trojan）
│   └── group/
│       ├── clash.py           # Clash 策略组生成
│       └── singbox.py         # Sing-box 出站组生成
├── spec/                      # 格式定义文档
│   ├── clash.anytls.md
│   ├── clash.ss.md
│   ├── clash.trojan.md
│   ├── clash.proxy-groups.md
│   ├── sing-box.anytls.md
│   ├── sing-box.ss.md
│   ├── sing-box.trojan.md
│   ├── sing-box.outbound-groups.md
│   ├── surge.proxy.md
│   ├── loon.proxy.md
│   └── shadowrocket.uri.md
├── convert/                   # 转换规则文档
│   ├── clash-to-sing-box.anytls.md
│   ├── clash-to-sing-box.ss.md
│   ├── clash-to-sing-box.trojan.md
│   ├── clash-to-sing-box.group-gen.md
│   └── clash-to-clash.group-gen.md
├── sample/                    # 示例数据
│   ├── clash-subscribe.yaml
│   ├── surge-subscribe.conf
│   ├── shadowrocket-uri.txt
│   ├── loon-subscribe.conf
│   ├── base64-uri.txt
│   └── sing-box-subscribe.json
└── tests/                     # 单元测试
    ├── test_detect.py
    ├── test_extract.py
    ├── test_convert.py
    └── test_pipeline.py
```

---

## 依赖

| 依赖 | 用途 | 内置 |
|------|------|------|
| `PyYAML` | YAML 解析和输出 | 否 |
| `json` | Sing-box JSON 解析 | 是 |
| `base64` | Base64 解码 | 是 |
| `re` | 正则匹配 | 是 |
| `argparse` | CLI 参数解析 | 是 |
| `unittest` / `pytest` | 测试（可选） | 是（unittest） |