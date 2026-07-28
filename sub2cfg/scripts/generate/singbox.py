"""
Sing-box 完整配置生成器 - 用模板 + 动态内容组装完整配置。
"""

import json
import sys

from region import REGION_TO_ISO

# 需要动态生成的区域组名
from group_builder import DYNAMIC_GROUPS
_DYNAMIC_GROUPS = DYNAMIC_GROUPS


def _render_proxy_outbounds(nodes: list) -> list:
    """将节点列表转换为 Sing-box 出站格式，统计跳过数量。"""
    from convert.to_singbox import convert
    outbounds = []
    skipped = 0
    for node in nodes:
        try:
            ob = convert(node)
        except Exception:
            skipped += 1
            continue
        if ob:
            outbounds.append(ob)
        else:
            skipped += 1
    if skipped:
        print(f'[sub2cfg] 模板路径跳过 {skipped} 个不支持的协议节点', file=sys.stderr)
    return outbounds


def _build_region_group(r: str, nodes: list) -> dict:
    """构建单个区域组。self/others 用 selector，其余用 urltest。"""
    if r in _DYNAMIC_GROUPS:
        return {'type': 'selector', 'tag': r, 'outbounds': nodes}
    return {
        'type': 'urltest',
        'tag': r,
        'outbounds': nodes,
        'url': 'http://www.gstatic.com/generate_204',
        'interval': '5m',
        'tolerance': 50,
    }


def _render_geoip_rules(region_names: list) -> list:
    """生成区域 GEOIP 规则（sing-box 用 rule_set 格式）。"""
    rules = []
    for r in region_names:
        code = REGION_TO_ISO.get(r)
        if code:
            rules.append({
                'rule_set': f'geoip-{code.lower()}',
                'action': 'route',
                'outbound': r,
            })
    return rules


def generate(template_path: str, nodes: list,
             region_names: list, regions: dict) -> str:
    """读模板 -> 替换动态部分 -> 输出完整 Sing-box 配置。"""
    with open(template_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 1. 替换 outbounds：代理节点 + 区域组 + 保留的出站
    template_outbounds = config.get('outbounds', [])
    region_set = set(region_names) | _DYNAMIC_GROUPS
    kept_outbounds = [
        o for o in template_outbounds
        if o.get('tag') not in region_set
    ]

    proxy_outbounds = _render_proxy_outbounds(nodes)
    new_region_groups = [_build_region_group(r, regions[r]) for r in region_names]

    config['outbounds'] = proxy_outbounds + new_region_groups + kept_outbounds

    # 2. 替换 route.rules
    route = config.get('route', {})
    template_rules = route.get('rules', [])

    region_outbounds = {r for r in region_names if r not in _DYNAMIC_GROUPS}

    static_rules = []
    for r in template_rules:
        if isinstance(r, dict) and 'rule_set' in r:
            rule_set = r.get('rule_set', '')
            outbound = r.get('outbound', '')
            if isinstance(rule_set, str) and rule_set.startswith('geoip-') \
               and outbound in region_outbounds:
                continue
        static_rules.append(r)

    geoip_rules = _render_geoip_rules(region_names)
    route['rules'] = geoip_rules + static_rules

    return json.dumps(config, ensure_ascii=False, indent=2)