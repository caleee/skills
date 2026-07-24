---
name: sub2cfg
description: 订阅链接转代理配置 — 拉取订阅、提取节点、格式转换、策略组生成
---

# sub2cfg — 订阅链接转代理配置

## 概述

从订阅 URL 拉取 → 识别格式 → 提取节点 → 转换目标格式 → 生成策略组。

支持订阅格式：Clash YAML、Surge、Loon、Shadowrocket URI、Base64 编码、Sing-box JSON

支持协议：Shadowsocks (ss)、Trojan、AnyTLS

支持目标平台：Clash / Mihomo、Sing-box

## 交互流程

触发本 skill 后，我会依次问你几个问题：

### 0. 确认环境

> 你的设备上安装了 Python 3 吗？

如果没装，需要先安装 Python 3.10+。安装后把 `scripts/` 目录放到设备上。
验证方法：`python3 --version`

### 1. 提供订阅链接

> 把订阅 URL 发给我。

### 2. 确认订阅可获取

> 机场后台开启了订阅获取吗？有些有机防盗链，需要先去后台打开才能拉取（有效期一般 10 分钟）。

如果还没开启，先去后台操作，然后回来告诉我"已开启"。

### 3. 确认目标平台

> 要转换成什么平台的配置？(clash / sing-box)

如果不说，默认 Clash 格式（节点可直接用）。

### 4. 确认是否生成策略组

> 需要生成策略组吗？(proxy-groups / 不需要)

- Clash 生成 PROXIES + 服务组 + 区域 url-test + FINAL
- Sing-box 生成 PROXIES + 区域 urltest + FINAL + DIRECT

### 5. 执行

确认后执行：
1. `curl -sL "<订阅URL>"` 拉取订阅
2. `detect.py` 检测格式
3. 调用 `sub2cfg.py` 提取节点 + 转换 + 生成组
4. 输出结果
5. **验证**：运行 `python3 verify.py` 检查所有模块和流水线是否正常

### 6. 验证结果处理

- 如果验证**全部通过**（0 失败）：确认输出无误，告知用户转换完成
- 如果验证有**失败项**：先检查失败原因，能修复就立即修复并重新验证；无法修复的，把失败项告诉用户，由用户决定是否继续使用当前输出

## 变量说明

| 变量 | 来源 | 说明 |
|------|------|------|
| 订阅 URL | 用户提供 | curl 拉取的目标 |
| 订阅格式 | Python 自动检测 | clash / surge / loon / shadowrocket / base64-uri / sing-box / unknown |
| 目标平台 | 用户指定 | clash（默认）或 sing-box |
| 是否生成组 | 用户指定 | 是则调用 group 模块 |
| 节点协议 | 从节点数据读取 | ss, trojan, anytls 等 |

## 脚本用法

```bash
# 先拉取订阅
curl -sL "<订阅URL>" > subscribe.yaml

# 检测格式
python3 scripts/detect.py < subscribe.yaml

# 提取 + 转换 (Clash → Clash, 带组)
python3 scripts/sub2cfg.py subscribe.yaml -g

# 提取 + 转换 (Clash → Sing-box, 带组)
python3 scripts/sub2cfg.py subscribe.yaml -t sing-box -g

# 强制指定输入格式（自动检测失败时使用）
python3 scripts/sub2cfg.py surge.conf -f surge -t sing-box -g -o output.yaml

# 写入文件
python3 scripts/sub2cfg.py subscribe.yaml -t sing-box -g -o output.yaml
```

## 验证

转换完成后**必须**运行验证，确认结果可用。

```bash
# 运行所有测试
python3 verify.py

# 详细输出
python3 verify.py --verbose
```

验证失败时，检查输出中的 FAIL 项，按以下顺序排查：
1. 模块导入失败 → 检查 Python 环境和依赖（`pip install pyyaml`）
2. 格式检测失败 → 检查订阅文件是否已正确拉取
3. 提取器/转换器失败 → 检查节点数据是否有异常字段
4. 端到端失败 → 检查 sample 文件是否完整

## 参考文档

- Sing-box: https://sing-box.sagernet.org/configuration/outbound/
- Clash (Mihomo): https://wiki.metacubex.one/config/proxies/
- Shadowsocks (Clash): https://wiki.metacubex.one/config/proxies/ss/
- Trojan (Clash): https://wiki.metacubex.one/config/proxies/trojan/
- AnyTLS (Clash): https://wiki.metacubex.one/config/proxies/anytls/