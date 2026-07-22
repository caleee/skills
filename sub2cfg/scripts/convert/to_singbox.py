"""
Clash → Sing-box 节点转换
"""

from _idle_session_fields import CLASH_TO_SINGBOX_IDLE_FIELDS


_CONVERTERS = {
    'anytls': 'convert_anytls',
    'ss': 'convert_ss',
    'trojan': 'convert_trojan',
}


def _build_tls(clash_node: dict) -> dict:
    """从 Clash 节点提取 TLS 字段，构造 Sing-box tls 对象。"""
    tls = {'enabled': True}
    if clash_node.get('sni'):
        tls['server_name'] = clash_node['sni']
    if clash_node.get('skip-cert-verify'):
        tls['insecure'] = True
    if clash_node.get('alpn'):
        tls['alpn'] = clash_node['alpn']
    fp = clash_node.get('client-fingerprint')
    if fp:
        tls['utls'] = {'enabled': True, 'fingerprint': fp}
    return tls


def convert_anytls(clash_node: dict) -> dict | None:
    """将单个 Clash anytls 节点转为 Sing-box 出站格式"""
    if clash_node.get('type') != 'anytls':
        return None

    outbound = {
        'type': 'anytls',
        'tag': clash_node.get('name', ''),
        'server': clash_node.get('server', ''),
        'server_port': clash_node.get('port', 443),
        'password': clash_node.get('password', ''),
        'tls': _build_tls(clash_node),
    }

    # 空闲会话字段: Clash 连字符命名 → Sing-box 下划线命名
    for clash_key, sb_key in CLASH_TO_SINGBOX_IDLE_FIELDS:
        if clash_key in clash_node:
            outbound[sb_key] = clash_node[clash_key]

    return outbound


def convert_ss(clash_node: dict) -> dict | None:
    """将单个 Clash SS 节点转为 Sing-box shadowsocks 出站格式。"""
    if clash_node.get('type') != 'ss':
        return None

    outbound = {
        'type': 'shadowsocks',
        'tag': clash_node.get('name', ''),
        'server': clash_node.get('server', ''),
        'server_port': clash_node.get('port', 443),
        'method': clash_node.get('cipher', 'aes-256-gcm'),
        'password': clash_node.get('password', ''),
    }
    if clash_node.get('udp'):
        outbound['udp_over_tcp'] = True
    if clash_node.get('plugin'):
        outbound['plugin'] = clash_node['plugin']
    if clash_node.get('plugin-opts'):
        outbound['plugin_opts'] = clash_node['plugin-opts']
    return outbound


def convert_trojan(clash_node: dict) -> dict | None:
    """将单个 Clash Trojan 节点转为 Sing-box trojan 出站格式。"""
    if clash_node.get('type') != 'trojan':
        return None

    return {
        'type': 'trojan',
        'tag': clash_node.get('name', ''),
        'server': clash_node.get('server', ''),
        'server_port': clash_node.get('port', 443),
        'password': clash_node.get('password', ''),
        'tls': _build_tls(clash_node),
    }


def convert(node: dict) -> dict | None:
    """按协议类型分派到对应转换器。"""
    func_name = _CONVERTERS.get(node.get('type'))
    if not func_name:
        return None
    return globals()[func_name](node)
