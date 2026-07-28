# sub2cfg 架构设计

> 订阅链接转代理配置 — 架构设计与模块说明

---

## 1. 整体架构

### 1.1 核心目标

- 从订阅链接或真实节点信息生成 Clash、Sing-box、DAE 三平台完整可用的内核配置文件
- **看样做菜**：用户提供配置模板，sub2cfg 只替换动态部分（节点列表 + 区域组）

### 1.2 数据流

```
订阅源 (raw text)
  → detect.py 检测格式
  → extract/{fmt}.py 提取为统一节点列表
  → ensure_emoji_flag() 推断添加 emoji 国旗
  → generate/{target}.py 读模板 → 替换标记
  → 输出完整配置
```

### 1.3 模板标记约定

| 标记 | 含义 | 处理方式 |
|------|------|----------|
| `STATIC: *` | 静态模板 | 照抄，不修改 |
| `DYNAMIC: proxies` | 动态节点列表 | 替换为生成的节点列表 |
| `MIXED: proxy-groups` | 混合 | 区域组替换，服务组保留 |
| `DYNAMIC: rules` | 动态规则 | 静态规则保留，GEOIP 按区域生成 |

---

## 2. 模块说明

### 检测层: `detect.py`

返回格式标识：`clash` / `surge` / `loon` / `shadowrocket` / `base64-uri` / `sing-box` / `unknown`

### 提取层: `extract/*.py`

统一接口：`extract(content, format) -> list[dict]`

| 文件 | 解析策略 |
|------|----------|
| `clash.py` | YAML → proxies: 段 → 关键词排除信息条目 |
| `shadowrocket.py` | URI 解析，支持 SIP002 两种变体 |
| `surge.py` | name = protocol, server, port, kv... |
| `singbox.py` | JSON → outbounds → 反向映射到 Clash |
| `base64.py` | 解码后递归分派 |

### 区域识别: `region.py`

- `REGION_MAP`：7 常用区域（emoji → 组名）
- `REGION_FLAGS`：92 已知 emoji 国旗
- `NAME_FLAG_MAP`：90+ 关键词 → 国旗
- `REGION_TO_ISO`：组名 → ISO 代码（GEOIP）

### 模板组装: `generate/*.py`

| 文件 | 模板格式 | 替换内容 |
|------|----------|----------|
| `clash.py` | YAML | proxies + proxy-groups + rules |
| `singbox.py` | JSON | outbounds + route.rules |
| `dae.py` | HCL | group 段 |

### 组生成: `group/*.py`

| 文件 | 组类型 | 特点 |
|------|--------|------|
| `clash.py` | url-test + select | 区域组 url-test，self/others select |
| `singbox.py` | urltest + selector | 区域组 urltest，self/others selector |

### 分组骨架: `group_builder.py`

`group_by_region(nodes, self_nodes)` → 按区域分组，自建节点归 self，非常用区域归 others

### 编排层: `sub2cfg.py`

参数：`-u` URL / `-T` 模板 / `-t` 平台 / `-s` 自建节点 / `-g` 组 / `-f` 格式 / `-o` 输出

---

## 3. 关键设计约定

1. **惰性导入**：sub2cfg.py 在函数内部 import
2. **统一中间格式**：Clash 代理 dict
3. **节点字段顺序**：`proxy_format.py` 的 `_FIELD_ORDER`
4. **跳过不支持的协议**：返回 None + 统计警告
5. **区域识别**：emoji 国旗 + NAME_FLAG_MAP 推断
6. **三平台模板**：templates/ 目录，用户按需修改

## 4. 安全设计

- URL 下载防 SSRF：仅 http/https，阻断内网地址
- 模板路径防穿越：拒绝绝对路径和 ../ 逃逸