"""
DAE 完整配置生成器 — 用模板 + 动态内容组装完整配置。

DAE 的特殊性：
  - subscription 段由用户自己管理（每个区域一个订阅文件）
  - node 段为空（由 DAE 订阅机制填充）
  - group 段中区域组替换为生成的，服务组保留
  - routing 段为静态模板
  - DAE 不支持 others 组（非常用节点在 DAE 中通过 filter: subtag 全部加入节点池）
"""

import re


def _render_region_groups(region_names: list) -> str:
    """生成 DAE 格式的区域组文本，过滤掉 others。"""
    lines = []
    for r in region_names:
        if r == 'others':
            continue
        lines.append(f'    {r} {{')
        lines.append(f'        filter: subtag({r})')
        lines.append("        policy: 'min_moving_avg'")
        lines.append('    }')
    return '\n'.join(lines)


def generate(template_path: str, nodes: list,
             region_names: list, regions: dict) -> str:
    """读模板 → 替换动态部分 → 输出完整 DAE 配置。"""
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    match = re.search(
        r'# ====== MIXED: group ======\n(.*?)(?=\n# ====== |\n\Z)',
        template, re.DOTALL,
    )
    if not match:
        return template

    group_section = match.group(1)

    service_groups_text = []
    groups = re.findall(
        r'    \w+ \{[^}]*?\n    \}',
        group_section, re.DOTALL,
    )

    for g in groups:
        name_match = re.match(r'    (\w+) \{', g)
        if not name_match:
            service_groups_text.append(g)
            continue
        name = name_match.group(1)
        if name in region_names:
            continue  # 区域组由生成器替换
        service_groups_text.append(g)

    new_region_groups = _render_region_groups(region_names)

    merged_groups = 'group {\n'
    merged_groups += new_region_groups + '\n'
    for sg in service_groups_text:
        merged_groups += sg + '\n'
    merged_groups += '}'

    template = template[:match.start()] + '# ====== MIXED: group ======\n' + merged_groups + template[match.end():]

    return template