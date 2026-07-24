"""按区域分组 + 共享组构建骨架。"""

import sys

from region import get_region


def group_by_region(nodes: list) -> tuple[dict[str, list[str]], list[str], list[str], list[str]]:
    """按区域分组，返回 (regions, region_names, all_node_names, ungrouped)。

    纯数据分区，不做 I/O。无法识别区域的节点收集到 ungrouped，
    仍加入 all_node_names（出现在 PROXIES 中）但不归属任何区域组。
    """
    regions: dict[str, list[str]] = {}
    ungrouped = []
    for node in nodes:
        name = node.get('name', '')
        r = get_region(name)
        if r:
            regions.setdefault(r, []).append(name)
        else:
            ungrouped.append(name)

    region_names = list(regions.keys())
    all_node_names = []
    for r in region_names:
        all_node_names.extend(regions[r])
    all_node_names.extend(ungrouped)
    return regions, region_names, all_node_names, ungrouped


def build_base_groups(nodes: list, service_groups: list[str] | None = None) -> dict:
    """构建组骨架，返回包含 DIRECT、PROXIES、服务组、区域组、FINAL 的字典。"""
    regions, region_names, all_node_names, ungrouped = group_by_region(nodes)

    if ungrouped:
        preview = ', '.join(ungrouped[:3])
        tail = '...' if len(ungrouped) > 3 else ''
        print(
            f'[sub2cfg] 警告: {len(ungrouped)} 个节点无法识别区域，'
            f'已加入 PROXIES 但未归入区域组: {preview}{tail}',
            file=sys.stderr,
        )

    return {
        'direct': True,
        'proxies': all_node_names,
        'service_groups': service_groups or [],
        'regions': regions,
        'region_names': region_names,
    }
