# AGENT.md — sub2cfg

## 运行命令

需要在 `sub2cfg/scripts/` 目录下运行 Python 脚本。

```bash
# 验证（纯 Python，无需额外依赖）
cd sub2cfg && python3 verify.py
python3 verify.py --verbose

# 格式检测
cd sub2cfg/scripts && python3 detect.py < ../sample/clash-subscribe.yaml

# 订阅转换
cd sub2cfg/scripts
python3 sub2cfg.py ../sample/clash-subscribe.yaml -g
python3 sub2cfg.py ../sample/clash-subscribe.yaml -t sing-box -g -o /tmp/out.yaml
python3 sub2cfg.py ../sample/surge-subscribe.conf -f surge -t sing-box -g
python3 sub2cfg.py ../sample/shadowrocket-uri.txt -f shadowrocket -t clash

# 单元测试（需安装 pytest）
pip install pytest
cd sub2cfg && python3 -m pytest tests/ -v
```

## 架构

### 流水线

```
订阅源 (raw text)
  → detect.py 检测格式
  → extract/{format}.py 提取为统一 Clash 格式节点列表
  → convert/to_singbox.py 按协议转换 (anytls/ss/trojan)
  → [可选] group/{target}.py 生成策略组
  → yaml.dump 输出
```

### 统一中间格式

所有提取器输出 Clash 代理 dict：

```python
{
    "name": "🇭🇰 香港 01",  # emoji 国旗标识区域
    "type": "ss",           # ss / trojan / anytls
    "server": "...",
    "port": 443,
    "password": "...",
    "cipher": "chacha20-...",  # ss 专用
    "sni": "...",              # trojan/anytls 专用
    "skip-cert-verify": True,
    "client-fingerprint": "chrome",
}
```

### 提取器接口

所有 `extract/*.py` 导出 `extract(content: str, format: str | None = None) -> list[dict]`；`format` 由调用方（detect 已判定）传入，提取器按需使用（如 `surge.py` 区分 surge/loon），不用则忽略：

| 文件 | 解析格式 |
|------|----------|
| `clash.py` | YAML → `proxies:` 段 → emoji 过滤 |
| `surge.py` | `[Proxy]` 段落 → `name = protocol, server, port, kv...` |
| `shadowrocket.py` | `ss://` base64、`trojan://` 标准 URI |
| `base64.py` | base64 解码 → 递归分派到检测器 |
| `singbox.py` | JSON → `outbounds[]` → 反向映射到 Clash |

### 命名规范

- spec 文件: `{platform}.{protocol}.md` / `{platform}.{type}.md`
- convert 文件: `{src}-to-{dst}.{protocol}.md` / `{src}-to-{dst}.group-gen.md`
- Python 提取器: `extract/{format}.py`
- Python 转换器: `convert/to_{target}.py`

### 关键设计约定

- **惰性导入**：`sub2cfg.py` 在函数内部 import，避免路径问题和启动开销
- **跳过不支持的协议**：转换器返回 `None`，`sub2cfg.py` 统计跳过数量并给出警告
- **区域识别**：节点名中 emoji 国旗字符决定归属区域（`region.py` 统一维护国旗与区域映射）
- **协议注册表**：`protocol.py` 单一事实来源，提取器与转换器共享协议类型映射
- **验证独立**：`verify.py` 仅依赖 Python 标准库 + PyYAML，无需 shell 或 pytest

### 扩展指南

新增订阅格式：`extract/{fmt}.py` → `detect.py` 加检测 → `detect.py` EXTRACTOR_MODULES 注册 → spec 文档 → sample 示例

新增协议：`protocol.py` 注册类型映射 → `convert/to_singbox.py` 加 `convert_{protocol}()` 并加入 `_CONVERTERS` → spec 文档 → convert 文档

## 重要文件路径

- `sub2cfg.md` — skill 定义（交互流程）
- `scripts/sub2cfg.py` — 主入口（编排流水线）
- `scripts/detect.py` — 格式检测
- `scripts/extract/` — 提取器（5 个格式）
- `scripts/convert/to_singbox.py` — 转换器（3 个协议）
- `scripts/group/` — 策略组生成（2 个平台）
- `verify.py` — 验证脚本
- `ARCHITECTURE.md` — 详细架构设计文档
- `registry.md` — 模块清单