"""
从 Clash YAML proxies 段提取并过滤节点
"""

# 用于识别区域节点的 emoji 国旗
FLAG_EMOJIS = set('🇭🇰🇺🇸🇯🇵🇸🇬🇨🇳🇬🇧🇩🇪🇫🇷🇰🇷🇮🇳🇨🇦🇦🇺🇷🇺🇧🇷🇳🇱🇸🇪🇳🇴🇫🇮🇩🇰🇵🇱🇨🇿🇭🇺🇷🇴🇹🇷🇮🇱🇦🇪🇿🇦🇲🇽🇦🇷🇨🇱🇵🇪🇵🇭')


def is_proxy_node(node) -> bool:
    """判断是否为真实代理节点（过滤信息条目）"""
    name = node.get('name', '')
    if not name:
        return False
    if '当前流量' in name or '到期时间' in name or '剩余流量' in name:
        return False
    for ch in name:
        if ch in FLAG_EMOJIS:
            return True
    return False


def filter_proxies(proxies: list) -> list:
    """过滤非代理节点"""
    return [p for p in proxies if is_proxy_node(p)]


def extract(content: str) -> list:
    """从原始 YAML 文本中提取 Clash 代理节点。"""
    import yaml
    try:
        data = yaml.safe_load(content)
    except Exception:
        return []
    if not data or 'proxies' not in data:
        return []
    return filter_proxies(data['proxies'])