"""
Clash 策略组生成 — 只生成区域组和自建组。

服务组、规则、DNS 等由用户提供的模板配置决定，sub2cfg 只负责
替换模板中的动态部分（节点列表 + 区域组）。
"""

from group_builder import build_base_groups


def build_groups(nodes: list, self_nodes: list | None = None) -> list:
    """生成 Clash proxy-groups — 仅区域组

    区域组：url-test 自动测速选最优节点
    自建组：select 手动选择
    others 组：select 手动选择
    """
    base = build_base_groups(nodes, self_nodes=self_nodes)

    groups = []

    for r in base['region_names']:
        if r in ('self', 'others'):
            groups.append({
                'name': r,
                'type': 'select',
                'proxies': base['regions'][r],
            })
        else:
            groups.append({
                'name': r,
                'type': 'url-test',
                'proxies': base['regions'][r],
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 300,
            })

    return groups