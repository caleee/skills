# AGENT.md — sub2cfg

## 运行命令

需要在 `sub2cfg/scripts/` 目录下运行 Python 脚本。

```bash
# 验证（纯 Python，无需额外依赖）
cd sub2cfg && python3 verify.py
python3 verify.py --verbose

# 格式检测
cd sub2cfg/scripts && python3 detect.py < ../sample/clash-subscribe.yaml

# 订阅转换（完整配置）
cd sub2cfg/scripts
python3 sub2cfg.py -u 'https://example.com/sub?token=xxx' -T clash.yaml -o /tmp/config.yaml
python3 sub2cfg.py -t sing-box subscribe.txt -T sing-box.json -o /tmp/config.json
python3 sub2cfg.py -t dae subscribe.txt -T config.dae -o /tmp/config.dae

# 只输出节点和组（不组装模板）
python3 sub2cfg.py subscribe.txt -g
python3 sub2cfg.py subscribe.txt -t sing-box -g

# 带自建节点
python3 sub2cfg.py subscribe.txt -s self-nodes.yaml -T clash.yaml -o /tmp/config.yaml

# 单元测试
python3 -m pytest tests/ -v
```

## 架构

### 流水线

```
订阅源 (raw text)
  → detect.py 检测格式
  → extract/{format}.py 提取为统一 Clash 格式节点列表
  → region.ensure_emoji_flag() 为无 emoji 节点推断并添加国旗
  → [可选] generate/{target}.py 读模板 → 替换动态部分 → 输出完整配置
  → 输出 (clash: YAML, sing-box: JSON, dae: HCL)
```

### 模板组装（generate/）

读取模板文件，替换标记段，输出完整配置：

| 标记 | 处理方式 |
|------|----------|
| `STATIC: *` | 照抄，不修改 |
| `DYNAMIC: proxies` | 替换为生成的节点列表 |
| `MIXED: proxy-groups` | 区域组替换为动态生成，服务组保留 |
| `DYNAMIC: rules` | 静态规则保留，GEOIP 规则按实际区域生成 |

三平台模板文件位于 `sub2cfg/templates/`。

### 提取器

所有 `extract/*.py` 导出 `extract(content: str, format: str | None = None) -> list[dict]`。

| 文件 | 解析格式 |
|------|----------|
| `clash.py` | YAML → `proxies:` 段 → 关键词排除信息条目 |
| `surge.py` | `[Proxy]` 段落 → `name = protocol, server, port, kv...` |
| `shadowrocket.py` | `ss://` base64、`trojan://` 标准 URI |
| `base64.py` | base64 解码 → 递归分派到检测器 |
| `singbox.py` | JSON → `outbounds[]` → 反向映射到 Clash |

### 参数

| 参数 | 说明 |
|------|------|
| `-u/--url` | 从 URL 下载订阅（防 SSRF） |
| `-T/--template` | 模板文件路径（自动查找 templates/ 目录） |
| `-t/--target` | 目标平台：clash / sing-box / dae |
| `-s/--self-nodes` | 自建节点文件，用于生成 self 兜底组 |
| `-g/--gen-groups` | 生成策略组（无模板时） |
| `-f/--format` | 强制指定输入格式 |

## 重要文件路径

- `sub2cfg/SKILL.md` — skill 定义（完整内容）
- `sub2cfg.md` — 根索引（frontmatter + 指引）
- `scripts/sub2cfg.py` — 主入口
- `scripts/detect.py` — 格式检测
- `scripts/extract/` — 提取器（5 个格式）
- `scripts/generate/` — 模板组装器（3 个平台）
- `scripts/group/` — 区域组生成（3 个平台）
- `scripts/group_builder.py` — 分组骨架
- `scripts/region.py` — 区域识别 + emoji 推断
- `scripts/proxy_format.py` — 节点字段顺序规范
- `templates/` — 配置模板（用户按需修改）
- `sample/` — 测试数据
- `verify.py` — 验证脚本
- `docs/sub2cfg/` — 设计文档（架构、分组、模块清单）

## 扩展指南

### 新增协议类型

1. `protocol.py` 注册类型映射
2. `convert/to_singbox.py` 加转换器
3. `proxy_format.py` 的 `_FIELD_ORDER` 加字段顺序
4. `spec/` 下加协议 spec 文档

### 新增订阅格式

1. `extract/{fmt}.py` 实现提取器
2. `detect.py` 加检测逻辑
3. `detect.py` 的 `EXTRACTOR_MODULES` 注册

### 新增目标平台

1. 模板文件放到 `templates/`
2. `group/{target}.py` 实现区域组生成
3. `generate/{target}.py` 实现模板组装器
4. `sub2cfg.py` 的 `-t` 参数加新选项