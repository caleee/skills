"""
Sing-box 出站组生成 — 只生成区域组和自建组。

服务组、规则、DNS 等由用户提供的模板配置决定，sub2cfg 只负责
替换模板中的动态部分（节点列表 + 区域组）。
"""

from group_builder import build_base_groups


def build_groups(nodes: list, self_nodes: list | None = None) -> list:
    """生成 Sing-box 出站组 — 仅区域组

    区域组：urltest 自动测速选最优节点
    自建组：selector 手动选择
    others 组：selector 手动选择
    """
    base = build_base_groups(nodes, self_nodes=self_nodes)

    outbounds = []

    for r in base['region_names']:
        if r in ('self', 'others'):
            outbounds.append({
                'type': 'selector',
                'tag': r,
                'outbounds': base['regions'][r],
            })
        else:
            outbounds.append({
                'type': 'urltest',
                'tag': r,
                'outbounds': base['regions'][r],
                'url': 'http://www.gstatic.com/generate_204',
                'interval': '5m',
                'tolerance': 50,
            })

    return outbounds