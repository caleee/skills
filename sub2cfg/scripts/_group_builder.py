"""按区域分组 + 共享组构建骨架。"""

from _region import get_region


def group_by_region(nodes: list) -> tuple[dict[str, list[str]], list[str], list[str]]:
    """按区域分组，返回 (regions, region_names, all_node_names)。"""
    regions: dict[str, list[str]] = {}
    for node in nodes:
        r = get_region(node.get('name', ''))
        if r:
            regions.setdefault(r, []).append(node['name'])

    region_names = list(regions.keys())
    all_node_names = []
    for r in region_names:
        all_node_names.extend(regions[r])
    return regions, region_names, all_node_names


def build_base_groups(nodes: list, service_groups: list[str] | None = None) -> dict:
    """构建组骨架，返回包含 DIRECT、PROXIES、服务组、区域组、FINAL 的字典。"""
    regions, region_names, all_node_names = group_by_region(nodes)

    return {
        'direct': True,
        'proxies': all_node_names,
        'service_groups': service_groups or [],
        'regions': regions,
        'region_names': region_names,
    }
