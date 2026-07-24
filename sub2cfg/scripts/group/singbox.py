"""
Sing-box 出站组生成
"""

from group_builder import build_base_groups


def build_groups(nodes: list) -> list:
    """生成 Sing-box 出站组 (selector + urltest + direct)"""
    base = build_base_groups(nodes)

    outbounds = []

    # 0. DIRECT 出站
    outbounds.append({
        'type': 'direct',
        'tag': 'DIRECT',
    })

    # 1. PROXIES - 主选择组
    outbounds.append({
        'type': 'selector',
        'tag': 'PROXIES',
        'outbounds': base['proxies'],
    })

    # 2. 区域 urltest 组
    for r in base['region_names']:
        outbounds.append({
            'type': 'urltest',
            'tag': r,
            'outbounds': base['regions'][r],
            'url': 'https://www.gstatic.com/generate_204',
            'interval': '5m',
            'tolerance': 50,
        })

    # 3. FINAL - 兜底组
    outbounds.append({
        'type': 'selector',
        'tag': 'FINAL',
        'outbounds': ['PROXIES'] + base['region_names'] + ['DIRECT'],
    })

    return outbounds
