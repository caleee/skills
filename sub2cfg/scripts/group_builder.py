"""按区域分组 + 共享组构建骨架。"""

import sys

from region import get_region


def group_by_region(nodes: list) -> tuple[dict[str, list[str]], list[str], list[str]]:
    """按区域分组，返回 (regions, region_names, all_node_names)。

    纯数据分区，不做 I/O。无法识别区域的节点收集到 others 组。
    """
    regions: dict[str, list[str]] = {}
    for node in nodes:
        name = node.get('name', '')
        r = get_region(name)
        if r:
            regions.setdefault(r, []).append(name)
        else:
            regions.setdefault('others', []).append(name)

    region_names = sorted(regions.keys())
    # PROXIES 中 others 放在最后
    all_node_names = []
    for r in region_names:
        if r == 'others':
            continue
        all_node_names.extend(regions[r])
    if 'others' in regions:
        all_node_names.extend(regions['others'])
    return regions, region_names, all_node_names


def build_base_groups(nodes: list, service_groups: list[str] | None = None) -> dict:
    """构建组骨架，返回包含 DIRECT、PROXIES、服务组、区域组、FINAL 的字典。"""
    regions, region_names, all_node_names = group_by_region(nodes)

    if 'others' in regions:
        others = regions['others']
        preview = ', '.join(others[:3])
        tail = '...' if len(others) > 3 else ''
        print(
            f'[sub2cfg] 提示: {len(others)} 个节点归入 others 组: {preview}{tail}',
            file=sys.stderr,
        )

    return {
        'direct': True,
        'proxies': all_node_names,
        'service_groups': service_groups or [],
        'regions': regions,
        'region_names': region_names,
    }