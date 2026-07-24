"""
Clash 策略组生成
"""

from group_builder import build_base_groups

# 默认服务策略组：这些是用户常用的特定服务分类，与按区域分组互补。
# 新增或移除服务时只需修改此处列表。
DEFAULT_SERVICE_GROUPS = [
    'DNS', 'OverseaAI', 'Bing', 'YouTube', 'Google',
    'GitHub', 'Telegram', 'Apple', 'OneDrive', 'Microsoft',
    'Games', 'Discord', 'Cloudflare',
]


def build_groups(nodes: list) -> list:
    """生成 Clash proxy-groups 列表"""
    base = build_base_groups(nodes, DEFAULT_SERVICE_GROUPS)

    groups = []

    # 1. PROXIES — 主选择组
    groups.append({
        'name': 'PROXIES',
        'type': 'select',
        'proxies': ['DIRECT'] + base['proxies'],
    })

    # 2. 服务策略组
    for sg in base['service_groups']:
        groups.append({
            'name': sg,
            'type': 'select',
            'proxies': ['DIRECT', 'PROXIES'] + base['region_names'] + ['FINAL'],
        })

    # 3. 区域 url-test 组
    for r in base['region_names']:
        groups.append({
            'name': r,
            'type': 'url-test',
            'proxies': base['regions'][r],
            'url': 'https://www.gstatic.com/generate_204',
            'interval': 300,
        })

    # 4. FINAL — 兜底组
    groups.append({
        'name': 'FINAL',
        'type': 'select',
        'proxies': ['DIRECT', 'PROXIES'] + base['region_names'],
    })

    return groups
