"""
Sing-box JSON 格式提取 — 从 outbounds 中提取代理节点
"""

import json


def _singbox_to_clash(outbound: dict) -> dict | None:
    """将单个 Sing-box 出站转为 Clash 格式节点。"""
    out_type = outbound.get('type', '')
    if out_type not in ('anytls', 'shadowsocks', 'trojan'):
        return None

    type_map = {'shadowsocks': 'ss'}
    clash_type = type_map.get(out_type, out_type)

    node = {
        'name': outbound.get('tag', ''),
        'type': clash_type,
        'server': outbound.get('server', ''),
        'port': outbound.get('server_port', 443),
    }

    if out_type == 'shadowsocks':
        node['cipher'] = outbound.get('method', 'aes-256-gcm')
        node['password'] = outbound.get('password', '')
        if outbound.get('udp_over_tcp'):
            node['udp'] = True
    elif out_type in ('trojan', 'anytls'):
        node['password'] = outbound.get('password', '')
        tls = outbound.get('tls', {})
        if tls.get('server_name'):
            node['sni'] = tls['server_name']
        if tls.get('insecure'):
            node['skip-cert-verify'] = True
        if tls.get('alpn'):
            node['alpn'] = tls['alpn']
        utls = tls.get('utls', {})
        if utls.get('fingerprint'):
            node['client-fingerprint'] = utls['fingerprint']

    # 空闲会话字段 (anytls): Sing-box 下划线命名 → Clash 连字符命名
    from _idle_session_fields import SINGBOX_TO_CLASH_IDLE_FIELDS
    for sb_key, clash_key in SINGBOX_TO_CLASH_IDLE_FIELDS:
        if sb_key in outbound:
            node[clash_key] = outbound[sb_key]

    return node


def extract(content: str) -> list:
    """从 Sing-box JSON 配置中提取代理节点列表。"""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []

    outbounds = data.get('outbounds', [])
    nodes = []
    for ob in outbounds:
        node = _singbox_to_clash(ob)
        if node and node.get('name'):
            nodes.append(node)
    return nodes
