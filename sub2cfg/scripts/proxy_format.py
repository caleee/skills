"""Clash 代理节点格式工具：字段顺序规范与排序。"""

# Clash 节点字段输出顺序（按协议分组）
_FIELD_ORDER = {
    'ss': ['name', 'type', 'server', 'port', 'cipher', 'password',
           'plugin', 'plugin-opts', 'udp'],
    'trojan': ['name', 'type', 'server', 'port', 'password',
               'sni', 'skip-cert-verify', 'alpn', 'client-fingerprint', 'udp'],
    'anytls': ['name', 'type', 'server', 'port', 'password',
               'sni', 'skip-cert-verify', 'alpn', 'client-fingerprint',
               'udp',
               'idle-session-check-interval', 'idle-session-timeout', 'min-idle-session'],
    'hysteria2': ['name', 'type', 'server', 'port', 'password',
                  'sni', 'skip-cert-verify', 'alpn', 'client-fingerprint',
                  'obfs', 'obfs-password', 'up', 'down', 'udp'],
}


def reorder_node(node: dict) -> dict:
    """按规范顺序重排节点字段。"""
    node_type = str(node.get('type') or '')
    order = _FIELD_ORDER.get(node_type, [])
    seen = set(order)
    rest = [k for k in node if k not in seen]
    return {k: node[k] for k in order + rest if k in node}