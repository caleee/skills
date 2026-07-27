"""
Sing-box 完整配置生成器 — 用模板 + 动态内容组装完整配置。
"""

import json

from region import REGION_TO_ISO


def _render_proxy_outbounds(nodes: list) -> list:
    """将节点列表转换为 Sing-box 出站格式。"""
    from convert.to_singbox import convert
    outbounds = []
    for node in nodes:
        try:
            ob = convert(node)
        except Exception:
            continue
        if ob:
            outbounds.append(ob)
    return outbounds


def _render_region_groups(region_names: list, regions: dict) -> list:
    """生成区域组出站列表。"""
    groups = []
    for r in region_names:
        if r == 'self':
            groups.append({
                'type': 'selector',
                'tag': 'self',
                'outbounds': regions[r],
            })
        else:
            groups.append({
                'type': 'urltest',
                'tag': r,
                'outbounds': regions[r],
                'url': 'http://www.gstatic.com/generate_204',
                'interval': '5m',
                'tolerance': 50,
            })
    return groups


def _render_geoip_rules(region_names: list) -> list:
    """生成 GEOIP 规则。"""
    rules = []
    for r in region_names:
        code = REGION_TO_ISO.get(r)
        if code:
            rules.append({'geoip': code, 'outbound': r})
    return rules


def generate(template_path: str, nodes: list,
             region_names: list, regions: dict) -> str:
    """读模板 → 替换动态部分 → 输出完整 Sing-box 配置。"""
    with open(template_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 1. 替换 outbounds：代理节点 + 区域组 + 保留的出站
    template_outbounds = config.get('outbounds', [])

    # 保留非区域组的出站（服务组、直连、DNS 等）
    kept_outbounds = [
        o for o in template_outbounds
        if o.get('tag') not in region_names
    ]

    # 生成代理节点出站
    proxy_outbounds = _render_proxy_outbounds(nodes)

    # 生成区域组
    new_region_groups = _render_region_groups(region_names, regions)

    # 合并：代理节点 + 区域组 + 保留的出站
    config['outbounds'] = proxy_outbounds + new_region_groups + kept_outbounds

    # 2. 替换 route.rules
    route = config.get('route', {})
    template_rules = route.get('rules', [])

    static_rules = [r for r in template_rules if 'geoip' not in r]
    geoip_rules = _render_geoip_rules(region_names)
    route['rules'] = geoip_rules + static_rules

    return json.dumps(config, ensure_ascii=False, indent=2)