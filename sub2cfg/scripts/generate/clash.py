"""
Clash 完整配置生成器 - 用模板 + 动态内容组装完整配置。
"""

import re
import yaml
from region import REGION_TO_ISO

# 需要动态生成的区域组名（self/others 由生成器产出，不从模板保留）
from group_builder import DYNAMIC_GROUPS
_DYNAMIC_GROUPS = DYNAMIC_GROUPS


def _render_proxies(nodes: list) -> str:
    """将节点列表渲染为 YAML 格式的 proxies 段，使用规范字段顺序。"""
    from proxy_format import reorder_node
    lines = ['proxies:']
    for node in nodes:
        ordered = reorder_node(node)
        items = []
        for k, v in ordered.items():
            if isinstance(v, list):
                v_str = '[' + ', '.join(
                    repr(x) if isinstance(x, str) else str(x) for x in v
                ) + ']'
            elif isinstance(v, bool):
                if v:
                    v_str = 'true'
                else:
                    continue
            elif isinstance(v, str):
                if any(c in v for c in ':{}[]&*!|>"%#@') or v.startswith(' ') or v.endswith(' '):
                    v_str = repr(v)
                else:
                    v_str = v
            else:
                v_str = str(v)
            items.append(f'{k}: {v_str}')
        lines.append('  - {' + ', '.join(items) + '}')
    return '\n'.join(lines)


def _build_region_group(r: str, nodes: list) -> dict:
    """构建单个区域组。self/others 用 select，其余用 url-test。"""
    if r in _DYNAMIC_GROUPS:
        return {'name': r, 'type': 'select', 'proxies': nodes}
    return {
        'name': r,
        'type': 'url-test',
        'proxies': nodes,
        'url': 'http://www.gstatic.com/generate_204',
        'interval': 300,
    }


def _render_geoip_rules(region_names: list) -> list:
    """生成区域 GEOIP 规则（仅 region_names 中的区域）。"""
    rules = []
    for r in region_names:
        code = REGION_TO_ISO.get(r)
        if code:
            rules.append(f'GEOIP,{code},{r},no-resolve')
    return rules


def generate(template_path: str, nodes: list,
             region_names: list, regions: dict) -> str:
    """读模板 -> 替换动态部分 -> 输出完整 Clash 配置。"""
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # 1. 替换 DYNAMIC: proxies
    proxies_yaml = _render_proxies(nodes)
    template = re.sub(
        r'# ====== DYNAMIC: proxies ======.*?(?=\n# ====== |\n\Z)',
        '# ====== DYNAMIC: proxies ======\n' + proxies_yaml,
        template, count=1, flags=re.DOTALL,
    )

    # 2. 替换 MIXED: proxy-groups
    try:
        template_data = yaml.safe_load(template)
        template_groups = template_data.get('proxy-groups', [])
    except Exception:
        template_groups = []

    # 保留服务组，区域组（含 self/others）由生成器产出
    region_set = set(region_names) | _DYNAMIC_GROUPS
    kept_groups = [
        g for g in template_groups
        if g.get('name') not in region_set
    ]

    new_region_groups = [_build_region_group(r, regions[r]) for r in region_names]

    merged_groups = new_region_groups + kept_groups
    groups_yaml = yaml.dump({'proxy-groups': merged_groups},
                            allow_unicode=True, default_flow_style=False,
                            sort_keys=False)

    template = re.sub(
        r'# ====== MIXED: proxy-groups ======.*?(?=\n# ====== |\n\Z)',
        '# ====== MIXED: proxy-groups ======\n' + groups_yaml,
        template, count=1, flags=re.DOTALL,
    )

    # 3. 替换 DYNAMIC: rules
    # 只替换区域 GEOIP 规则，保留 CN/DIRECT 等其他 GEOIP 规则
    match = re.search(
        r'# ====== DYNAMIC: rules ======\n(.+?)(?=\n# ====== |\n\Z)',
        template, re.DOTALL,
    )
    if match:
        try:
            template_data = yaml.safe_load(template)
            template_rules = template_data.get('rules', [])
        except Exception:
            template_rules = []

        # 区域出站名集合，用于识别要替换的 GEOIP 规则
        region_outbounds = {r for r in region_names if r not in _DYNAMIC_GROUPS}

        # 保留非区域 GEOIP 规则（如 GEOIP,CN,DIRECT）和所有非 GEOIP 规则
        static_rules = []
        for r in template_rules:
            if isinstance(r, str) and r.startswith('GEOIP,'):
                # GEOIP,code,outbound,... - 检查 outbound 是否为区域组
                parts = r.split(',')
                if len(parts) >= 3 and parts[2] in region_outbounds:
                    continue  # 区域 GEOIP 规则，由生成器重建
            static_rules.append(r)

        geoip_rules = _render_geoip_rules(region_names)
        all_rules = static_rules + geoip_rules

        rules_lines = ['rules:']
        for r in all_rules:
            if isinstance(r, str):
                rules_lines.append(f'  - {r}')
            else:
                rules_lines.append(f'  - {yaml.dump(r).strip()}')
        rules_yaml = '\n'.join(rules_lines)

        template = template[:match.start()] + rules_yaml + template[match.end():]

    return template