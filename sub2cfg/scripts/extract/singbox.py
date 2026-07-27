"""
Sing-box JSON 格式提取 - 从 outbounds 中提取代理节点
"""

import json

from idle_session_fields import SINGBOX_TO_CLASH_IDLE_FIELDS, convert_idle_fields
from protocol import SINGBOX_TO_CLASH_TYPE


def _extract_tls(outbound: dict, node: dict) -> None:
    """从 sing-box outbound 的 tls 对象提取 TLS 字段到 Clash node。"""
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


def _extract_shadowsocks(outbound: dict, node: dict) -> None:
    node['cipher'] = outbound.get('method', 'aes-256-gcm')
    node['password'] = outbound.get('password', '')
    if outbound.get('udp_over_tcp'):
        node['udp'] = True


def _extract_password_tls(outbound: dict, node: dict) -> None:
    """trojan / anytls: password + TLS 字段。"""
    node['password'] = outbound.get('password', '')
    _extract_tls(outbound, node)


def _extract_hysteria2(outbound: dict, node: dict) -> None:
    node['password'] = outbound.get('password', '')
    _extract_tls(outbound, node)
    obfs = outbound.get('obfs', {})
    if obfs.get('type'):
        node['obfs'] = obfs['type']
        if obfs.get('password'):
            node['obfs-password'] = obfs['password']
    if outbound.get('up_mbps') is not None:
        node['up'] = f"{outbound['up_mbps']} Mbps"
    if outbound.get('down_mbps') is not None:
        node['down'] = f"{outbound['down_mbps']} Mbps"


# 按出站类型分派到对应提取器（与 to_singbox.py 的 _CONVERTERS 模式对齐）
_EXTRACTORS = {
    'shadowsocks': _extract_shadowsocks,
    'trojan': _extract_password_tls,
    'anytls': _extract_password_tls,
    'hysteria2': _extract_hysteria2,
}

if set(_EXTRACTORS) != set(SINGBOX_TO_CLASH_TYPE):
    raise RuntimeError(
        '_EXTRACTORS 必须覆盖 protocol.SINGBOX_TO_CLASH_TYPE 中的所有类型'
    )


def _singbox_to_clash(outbound: dict) -> dict | None:
    """将单个 Sing-box 出站转为 Clash 格式节点。"""
    out_type = outbound.get('type', '')
    if out_type not in SINGBOX_TO_CLASH_TYPE:
        return None

    node = {
        'name': outbound.get('tag', ''),
        'type': SINGBOX_TO_CLASH_TYPE[out_type],
        'server': outbound.get('server', ''),
        'port': outbound.get('server_port', 443),
    }

    _EXTRACTORS[out_type](outbound, node)

    # 空闲会话字段 (anytls): Sing-box 下划线命名 duration(如 "30s") -> Clash 连字符命名 int(秒)
    convert_idle_fields(outbound, node, SINGBOX_TO_CLASH_IDLE_FIELDS)

    return node


def extract(content: str, format: str | None = None) -> list:
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
