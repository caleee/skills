#!/usr/bin/env python3
"""
sub2cfg — 订阅链接转代理配置
主入口：检测格式 → 提取节点 → 转换格式 → 输出
"""
import sys
import argparse
import importlib


def load_content(path):
    """读取原始文件内容（不解析 YAML）。"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f'错误: 文件不存在 {path}', file=sys.stderr)
        sys.exit(1)


EXTRACTOR_MODULES = {
    'clash': 'extract.clash',
    'surge': 'extract.surge',
    'loon': 'extract.surge',
    'shadowrocket': 'extract.shadowrocket',
    'base64-uri': 'extract.base64',
    'sing-box': 'extract.singbox',
}


def main():
    import yaml
    parser = argparse.ArgumentParser(description='订阅链接转代理配置')
    parser.add_argument('input', help='订阅文件路径')
    parser.add_argument('-t', '--target', choices=['clash', 'sing-box'], default='clash',
                        help='目标平台 (默认: clash)')
    parser.add_argument('-g', '--gen-groups', action='store_true',
                        help='生成策略组')
    parser.add_argument('-f', '--format',
                        choices=['clash', 'sing-box', 'surge', 'loon', 'shadowrocket', 'base64-uri'],
                        help='强制指定输入格式 (默认: 自动检测)')
    parser.add_argument('-o', '--output', help='输出文件路径 (默认: stdout)')
    args = parser.parse_args()

    # 1. 加载原始内容
    content = load_content(args.input)

    # 2. 检测格式（或使用强制格式）
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
    module_path = EXTRACTOR_MODULES.get(fmt)
    if not module_path:
        print(f'错误: 不支持从 {fmt} 格式提取', file=sys.stderr)
        sys.exit(1)

    try:
        mod = importlib.import_module(module_path)
        nodes = mod.extract(content)
    except Exception as e:
        print(f'错误: 节点提取失败 {e}', file=sys.stderr)
        sys.exit(1)

    print(f'[sub2cfg] 提取到 {len(nodes)} 个有效节点', file=sys.stderr)
    if not nodes:
        print('错误: 未提取到任何有效节点', file=sys.stderr)
        sys.exit(1)

    # 4. 转换格式
    if args.target == 'sing-box':
        outbounds = []
        skipped = 0
        for node in nodes:
            try:
                from convert.to_singbox import convert
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
            groups = build_groups(nodes)
            outbounds = groups + outbounds

        result = {'outbounds': outbounds}
    else:
        # Clash 目标：直接输出节点
        result = {'proxies': nodes}

        if args.gen_groups:
            from group.clash import build_groups
            groups = build_groups(nodes)
            result['proxy-groups'] = groups

    # 5. 输出
    output = yaml.dump(result, allow_unicode=True, default_flow_style=False, sort_keys=False)
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f'[sub2cfg] 已写入 {args.output}', file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
