"""
从 Clash YAML proxies 段提取并过滤节点

过滤策略：按关键词排除信息条目（如"当前流量"、"到期时间"），
其余节点均视为有效代理节点。emoji 国旗推断在后续步骤中自动添加。
"""

# 用于过滤非代理节点的关键词（名称含这些关键词的条目会被跳过）
INFO_KEYWORDS = ['当前流量', '到期时间', '剩余流量', '已用流量', '套餐', '订阅']


def is_proxy_node(node) -> bool:
    """判断是否为真实代理节点（过滤信息条目）"""
    name = node.get('name', '')
    if not name:
        return False
    for kw in INFO_KEYWORDS:
        if kw in name:
            return False
    return True


def filter_proxies(proxies: list) -> list:
    """过滤非代理节点"""
    return [p for p in proxies if is_proxy_node(p)]


def extract(content: str, format: str | None = None) -> list:
    """从原始 YAML 文本中提取 Clash 代理节点。"""
    import yaml
    try:
        data = yaml.safe_load(content)
    except Exception:
        return []
    if not data or 'proxies' not in data:
        return []
    return filter_proxies(data['proxies'])