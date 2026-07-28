"""
DAE 完整配置生成器 - 用模板 + 动态内容组装完整配置。

DAE 的特殊性：
  - subscription 段由用户自己管理（每个区域一个订阅文件）
  - node 段为空（由 DAE 订阅机制填充）
  - group 段中区域组替换为生成的，服务组保留
  - routing 段为静态模板
  - DAE 不支持 others 组
  - self 组仅在存在自建节点时生成
"""

import re

_SKIP_GROUPS = {'others'}


def _render_region_groups(region_names: list) -> str:
    """生成 DAE 格式的区域组文本，跳过 others。"""
    lines = []
    for r in region_names:
        if r in _SKIP_GROUPS:
            continue
        lines.append(f'    {r} {{')
        lines.append(f'        filter: subtag({r})')
        lines.append("        policy: 'min_moving_avg'")
        lines.append('    }')
    return '\n'.join(lines)


def generate(template_path: str, region_names: list) -> str:
    """读模板 -> 替换 group 段 -> 输出完整 DAE 配置。"""
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # 定位 MIXED: group 标记
    marker = '# ====== MIXED: group ======'
    marker_pos = template.find(marker)
    if marker_pos == -1:
        return template

    # 找下一个标记或文件末尾
    next_marker = template.find('\n# ======', marker_pos + len(marker))
    if next_marker == -1:
        group_section = template[marker_pos + len(marker):]
    else:
        group_section = template[marker_pos + len(marker):next_marker]

    # 按行解析，按缩进级别拆分区域组和服务组
    region_set = set(region_names) - _SKIP_GROUPS
    service_lines = []
    in_group = False
    group_name = ''
    group_lines = []
    brace_count = 0

    for line in group_section.split('\n'):
        if not in_group:
            # 找组定义行
            m = re.match(r'    (\w+) \{', line)
            if m:
                in_group = True
                group_name = m.group(1)
                group_lines = [line]
                brace_count = line.count('{') - line.count('}')
            else:
                service_lines.append(line)
        else:
            group_lines.append(line)
            brace_count += line.count('{') - line.count('}')
            if brace_count <= 0:
                # 组结束
                if group_name in region_set:
                    pass  # 区域组，丢弃
                else:
                    service_lines.extend(group_lines)
                in_group = False

    # 生成新区域组
    new_region_groups = _render_region_groups(region_names)

    # 合并
    merged = 'group {\n'
    merged += new_region_groups + '\n'
    for line in service_lines:
        merged += line + '\n'
    merged += '}'

    template = template[:marker_pos] + marker + '\n' + merged + template[next_marker:]

    return template