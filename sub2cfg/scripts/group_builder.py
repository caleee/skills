"""按区域分组 + 共享组构建骨架。"""

import sys

from region import get_region

# 需要动态生成的区域组名（self/others 由生成器产出，不从模板保留）
DYNAMIC_GROUPS = {'self', 'others'}


def group_by_region(nodes: list, self_nodes: list | None = None) -> tuple[dict[str, list[str]], list[str], list[str]]:
    """按区域分组，返回 (regions, region_names, all_node_names)。

    自建节点归入 self 组，非常用区域节点归入 others 组。
    """
    regions: dict[str, list[str]] = {}

    # 自建节点
    if self_nodes:
        self_names = [n.get('name', '') for n in self_nodes if n.get('name')]
        if self_names:
            regions['self'] = self_names

    # 机场节点按区域分组
    for node in nodes:
        name = node.get('name', '')
        if not name:
            continue
        r = get_region(name)
        if r:
            regions.setdefault(r, []).append(name)
        else:
            regions.setdefault('others', []).append(name)

    # 按模板定义的顺序排列区域组（匹配 GROUP-ARCHITECTURE.md）
    _TEMPLATE_ORDER = ['hongkong', 'macao', 'taiwan', 'japan', 'korea', 'singapore', 'america']
    region_names = []
    for r in _TEMPLATE_ORDER:
        if r in regions:
            region_names.append(r)
    # 模板外的新区域按字母序追加
    for r in sorted(regions):
        if r not in _TEMPLATE_ORDER and r != 'self' and r != 'others':
            region_names.append(r)
    if 'self' in regions:
        region_names.append('self')
    if 'others' in regions:
        region_names.append('others')

    # PROXIES 顺序：7 区域 → self → others
    all_node_names = []
    for r in region_names:
        if r in ('self', 'others'):
            continue
        all_node_names.extend(regions[r])
    if 'self' in regions:
        all_node_names.extend(regions['self'])
    if 'others' in regions:
        all_node_names.extend(regions['others'])

    return regions, region_names, all_node_names


def build_base_groups(nodes: list, self_nodes: list | None = None) -> dict:
    """构建组骨架，返回包含 DIRECT、PROXIES、区域组、FINAL 的字典。"""
    regions, region_names, all_node_names = group_by_region(nodes, self_nodes)

    if 'others' in regions:
        print(
            f'[sub2cfg] 提示: {len(regions["others"])} 个节点归入 others 组',
            file=sys.stderr,
        )

    return {
        'direct': True,
        'proxies': all_node_names,
        'regions': regions,
        'region_names': region_names,
    }