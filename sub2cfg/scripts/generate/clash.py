"""
Clash 完整配置生成器 — 用模板 + 动态内容组装完整配置。
"""

import re
import yaml
from region import REGION_TO_ISO


def _render_proxies(nodes: list) -> str:
    """将节点列表渲染为 YAML 格式的 proxies 段，使用规范字段顺序。"""
    from sub2cfg import _reorder_node
    lines = ['proxies:']
    for node in nodes:
        ordered = _reorder_node(node)
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


def _render_region_groups(region_names: list, regions: dict) -> str:
    """渲染区域组（url-test）。"""
    lines = []
    for r in region_names:
        if r == 'self':
            lines.append(f'- name: self')
            lines.append('  type: select')
            lines.append('  proxies:')
            for name in regions[r]:
                lines.append(f'  - {name}')
        else:
            lines.append(f'- name: {r}')
            lines.append('  type: url-test')
            lines.append('  proxies:')
            for name in regions[r]:
                lines.append(f'  - {name}')
            lines.append("  url: http://www.gstatic.com/generate_204")
            lines.append('  interval: 300')
    return '\n'.join(lines)


def _render_geoip_rules(region_names: list) -> list:
    """生成 GEOIP 规则（按实际存在的区域）。"""
    rules = []
    for r in region_names:
        code = REGION_TO_ISO.get(r)
        if code:
            rules.append(f'GEOIP,{code},{r},no-resolve')
    return rules


def generate(template_path: str, nodes: list,
             region_names: list, regions: dict) -> str:
    """读模板 → 替换动态部分 → 输出完整 Clash 配置。"""
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

    kept_groups = [g for g in template_groups
                   if g.get('type') != 'url-test']

    new_region_groups = []
    for r in region_names:
        if r == 'self':
            new_region_groups.append({
                'name': 'self',
                'type': 'select',
                'proxies': regions[r],
            })
        else:
            new_region_groups.append({
                'name': r,
                'type': 'url-test',
                'proxies': regions[r],
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 300,
            })

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

        static_rules = [r for r in template_rules
                        if not isinstance(r, str) or not r.startswith('GEOIP,')]
        geoip_rules = _render_geoip_rules(region_names)

        all_rules = static_rules + geoip_rules

        rules_lines = ['rules:']
        for r in all_rules:
            if isinstance(r, str):
                rules_lines.append(f'  - {r}')
            else:
                rules_lines.append(f'  - {yaml.dump(r, line_break=True).strip()}')
        rules_yaml = '\n'.join(rules_lines)

        template = template[:match.start()] + rules_yaml + template[match.end():]

    return template