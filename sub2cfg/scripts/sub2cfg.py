#!/usr/bin/env python3
"""
sub2cfg — 订阅链接转代理配置
主入口：检测格式 → 提取节点 → 转换格式 → 输出
"""
import sys
import argparse
import importlib
import os
import urllib.request
import urllib.error
import urllib.parse
from proxy_format import reorder_node

# 脚本所在目录（用于解析模板路径等）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(SCRIPT_DIR, '..', 'templates')




def load_content(path):
    """读取原始文件内容（不解析 YAML）。"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f'错误: 文件不存在 {path}', file=sys.stderr)
        sys.exit(1)


def fetch_url(url):
    """从 URL 下载订阅内容，仅允许 http/https 协议，阻断内网地址。"""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        print(f'错误: 不支持的协议 {parsed.scheme}，仅支持 http/https', file=sys.stderr)
        sys.exit(1)

    import socket
    try:
        ip = socket.gethostbyname(parsed.hostname)
        parts = ip.split('.')
        if parts[0] == '10' or \
           (parts[0] == '172' and 16 <= int(parts[1]) <= 31) or \
           (parts[0] == '192' and parts[1] == '168') or \
           parts[0] == '127' or parts[0] == '0' or \
           ip.startswith('169.254.'):
            print(f'错误: 拒绝访问内网地址 {ip}', file=sys.stderr)
            sys.exit(1)
    except socket.gaierror:
        print(f'错误: 无法解析域名 {parsed.hostname}', file=sys.stderr)
        sys.exit(1)

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'sub2cfg/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode('utf-8')
    except Exception as e:
        print(f'错误: 下载失败 {e}', file=sys.stderr)
        sys.exit(1)


def resolve_template_path(path):
    """解析模板路径。

    只允许两种路径：
    1. 纯文件名 → 在 templates/ 目录下查找
    2. 相对路径 → 在当前工作目录下查找
    拒绝绝对路径和 ../ 逃逸。
    """
    if os.path.isabs(path):
        print(f'错误: 模板路径不支持绝对路径 {path}，请使用文件名', file=sys.stderr)
        print('可用模板: clash.yaml, config.dae, sing-box.json', file=sys.stderr)
        sys.exit(1)

    normalized = os.path.normpath(path)
    if normalized.startswith('..') or '/../' in normalized or normalized == '..':
        print(f'错误: 模板路径不允许越级 {path}', file=sys.stderr)
        sys.exit(1)

    candidate = os.path.join(TEMPLATE_DIR, normalized)
    if os.path.exists(candidate):
        return os.path.realpath(candidate)

    cwd_candidate = os.path.join(os.getcwd(), normalized)
    if os.path.exists(cwd_candidate):
        return os.path.realpath(cwd_candidate)

    print(f'错误: 找不到模板文件 {path}，请在 templates/ 目录下查找', file=sys.stderr)
    print('可用模板: clash.yaml, config.dae, sing-box.json', file=sys.stderr)
    sys.exit(1)


def main():
    import yaml
    parser = argparse.ArgumentParser(description='订阅链接转代理配置')
    parser.add_argument('input', nargs='?', help='订阅文件路径')
    parser.add_argument('-u', '--url', help='订阅链接 URL（与 input 二选一）')
    parser.add_argument('-t', '--target', choices=['clash', 'sing-box', 'dae'], default='clash',
                        help='目标平台 (默认: clash)')
    parser.add_argument('-g', '--gen-groups', action='store_true',
                        help='生成策略组')
    parser.add_argument('-f', '--format',
                        choices=['clash', 'sing-box', 'surge', 'loon', 'shadowrocket', 'base64-uri'],
                        help='强制指定输入格式 (默认: 自动检测)')
    parser.add_argument('-o', '--output', help='输出文件路径 (默认: stdout)')
    parser.add_argument('-s', '--self-nodes', help='自建节点文件路径，用于生成 self 兜底组')
    parser.add_argument('-T', '--template', help='模板文件名（如 clash.yaml），自动查找 templates/ 目录')
    args = parser.parse_args()

    # 检查输入来源
    if not args.input and not args.url:
        print('错误: 请指定订阅文件路径或使用 -u 指定订阅链接', file=sys.stderr)
        sys.exit(1)

    # 0. 加载自建节点（如有）
    self_nodes = []
    if args.self_nodes:
        import yaml
        with open(args.self_nodes) as f:
            self_data = yaml.safe_load(f)
        self_nodes = self_data.get('proxies', [])
        print(f'[sub2cfg] 加载 {len(self_nodes)} 个自建节点', file=sys.stderr)

    # 1. 加载原始内容（从 URL 或文件）
    if args.url:
        content = fetch_url(args.url)
        print(f'[sub2cfg] 从 URL 下载 {len(content)} 字节', file=sys.stderr)
    else:
        content = load_content(args.input)

    # 2. 检测格式
    if args.format:
        fmt = args.format
    else:
        from detect import detect
        fmt = detect(content)
        if fmt == 'unknown':
            print('错误: 无法识别订阅格式，请使用 -f 手动指定', file=sys.stderr)
            sys.exit(1)
    print(f'[sub2cfg] 检测到格式: {fmt}', file=sys.stderr)

    # 3. 提取节点
    from detect import EXTRACTOR_MODULES
    module_path = EXTRACTOR_MODULES.get(fmt)
    if not module_path:
        print(f'错误: 不支持从 {fmt} 格式提取', file=sys.stderr)
        sys.exit(1)

    try:
        mod = importlib.import_module(module_path)
        nodes = mod.extract(content, fmt)
    except Exception as e:
        print(f'错误: 节点提取失败 {e}', file=sys.stderr)
        sys.exit(1)

    print(f'[sub2cfg] 提取到 {len(nodes)} 个有效节点', file=sys.stderr)
    if not nodes:
        print('错误: 未提取到任何有效节点', file=sys.stderr)
        sys.exit(1)

    # 4. 为无 emoji 国旗的节点名推断并添加国旗
    from region import ensure_emoji_flag
    inferred = 0
    for node in nodes:
        old = node.get('name', '')
        new = ensure_emoji_flag(old)
        if old != new:
            node['name'] = new
            inferred += 1
    if inferred:
        print(f'[sub2cfg] 为 {inferred} 个节点添加了 emoji 国旗', file=sys.stderr)

    # 5. 模板组装（如有模板）
    output = ''
    if args.template:
        template_path = resolve_template_path(args.template)
        from group_builder import group_by_region
        regions, region_names, _ = group_by_region(nodes, self_nodes)

        if args.target == 'clash':
            from generate.clash import generate
            output = generate(template_path, nodes, region_names, regions)
        elif args.target == 'sing-box':
            from generate.singbox import generate
            output = generate(template_path, nodes, region_names, regions)
        elif args.target == 'dae':
            from generate.dae import generate
            output = generate(template_path, region_names)
    else:
        # 无模板：只输出节点和组
        if args.target == 'sing-box':
            from convert.to_singbox import convert
            outbounds = []
            skipped = 0
            for node in nodes:
                try:
                    outbound = convert(node)
                except Exception as e:
                    name = node.get('name', '?')
                    print(f'警告: 节点 "{name}" 转换失败: {e}', file=sys.stderr)
                    continue
                if outbound:
                    outbounds.append(outbound)
                else:
                    skipped += 1
            if skipped:
                print(f'[sub2cfg] 跳过 {skipped} 个不支持的协议节点', file=sys.stderr)
            if args.gen_groups:
                from group.singbox import build_groups
                groups = build_groups(nodes, self_nodes=self_nodes)
                outbounds = groups + outbounds
            result = {'outbounds': outbounds}
            import json
            output = json.dumps(result, ensure_ascii=False, indent=2)
        else:
            result = {'proxies': [reorder_node(n) for n in nodes]}
            if args.gen_groups:
                from group.clash import build_groups
                groups = build_groups(nodes, self_nodes=self_nodes)
                result['proxy-groups'] = groups
            output = yaml.dump(result, allow_unicode=True, default_flow_style=False, sort_keys=False)

    # 输出
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f'[sub2cfg] 已写入 {args.output}', file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()