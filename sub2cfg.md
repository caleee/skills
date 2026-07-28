---
name: sub2cfg
description: 订阅链接转代理配置 — 从订阅 URL 或节点信息生成 Clash/Sing-box/DAE 三平台完整配置
---

# sub2cfg — 订阅链接转代理配置

## 概述

从订阅 URL 或节点文件 → 提取节点 → 按区域分组 → 组装模板 → 输出完整可用的代理配置文件。

## 触发条件

用户提供以下任何一种输入时触发本 skill：
- 代理订阅链接（URL）
- 订阅文件（Clash YAML / Surge / Loon / Shadowrocket URI / Base64 / Sing-box JSON）
- 真实节点配置信息

## 流程

### 1. 确认输入

- 用户给了 URL → 用 `-u` 参数，sub2cfg 自动下载
- 用户给了本地文件 → 直接传入路径
- 用户给了自建节点（vless/hysteria2 等）→ 先用 `-s` 参数传入自建节点文件

### 2. 确认目标平台

- 默认 Clash
- 用户要 Sing-box 或 DAE → 加 `-t sing-box` 或 `-t dae`

### 3. 确认模板

- 默认 `clash.yaml`，自动在 `templates/` 目录查找
- 模板标记：`STATIC` 照抄 / `DYNAMIC` 替换 / `MIXED` 区域组替换 + 服务组保留
- 用户可提供自定义模板路径

### 4. 执行

```bash
cd sub2cfg/scripts

# 从 URL 生成 Clash 完整配置
python3 sub2cfg.py -u '<订阅URL>' -T clash.yaml -o /tmp/config.yaml

# 从本地文件生成 Sing-box 配置
python3 sub2cfg.py -t sing-box subscribe.txt -T sing-box.json -o /tmp/config.json

# 带自建节点
python3 sub2cfg.py subscribe.txt -s self-nodes.yaml -T clash.yaml -o /tmp/config.yaml

# 只输出节点和组（不组装模板）
python3 sub2cfg.py subscribe.txt -g
```

### 5. 验证

```bash
cd sub2cfg && python3 verify.py
```

- 全部通过 → 告知用户转换完成
- 有失败项 → 先修复再验证，无法修复的告知用户

## 参数

| 参数 | 说明 |
|------|------|
| `-u <URL>` | 从 URL 下载订阅（防 SSRF） |
| `-t clash/sing-box/dae` | 目标平台（默认 clash） |
| `-T <文件名>` | 模板文件，自动查找 `templates/` 目录 |
| `-s <文件>` | 自建节点文件，生成 self 兜底组 |
| `-g` | 生成策略组（无模板时） |
| `-f <格式>` | 强制指定输入格式 |
| `-o <文件>` | 输出到文件（默认 stdout） |

## 注意事项

- 模板中的代理段（`DYNAMIC: proxies`）由 sub2cfg 替换，占位符不影响输出
- 自建节点文件格式：Clash 用 `proxies:` 段，Sing-box 用 `outbounds:` 段
- 订阅链接 token 通常有时效，尽快使用