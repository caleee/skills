"""
Clash -> Sing-box 节点转换
"""

import re

from idle_session_fields import CLASH_TO_SINGBOX_IDLE_FIELDS, convert_idle_fields
from protocol import SUPPORTED_PROTOCOLS


_CONVERTERS = {
    'anytls': 'convert_anytls',
    'ss': 'convert_ss',
    'trojan': 'convert_trojan',
    'hysteria2': 'convert_hysteria2',
}

# 确保 _CONVERTERS 覆盖所有已注册协议（protocol.py 为单一事实来源）
if set(_CONVERTERS) != set(SUPPORTED_PROTOCOLS):
    raise RuntimeError(
        '_CONVERTERS 必须覆盖 protocol.SUPPORTED_PROTOCOLS 中的所有协议'
    )


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

    # 空闲会话字段: Clash 连字符命名 int(秒) -> Sing-box 下划线命名 duration(如 "30s")
    convert_idle_fields(clash_node, outbound, CLASH_TO_SINGBOX_IDLE_FIELDS)

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


def _parse_bandwidth(value) -> int | None:
    """从 Clash 带宽字符串（如 "30 Mbps"）提取数字（30）；无法解析返回 None。"""
    if isinstance(value, int):
        return value
    m = re.search(r'\d+', str(value))
    return int(m.group()) if m else None


def convert_hysteria2(clash_node: dict) -> dict | None:
    """将单个 Clash hysteria2 节点转为 Sing-box 出站格式。"""
    if clash_node.get('type') != 'hysteria2':
        return None

    outbound = {
        'type': 'hysteria2',
        'tag': clash_node.get('name', ''),
        'server': clash_node.get('server', ''),
        'server_port': clash_node.get('port', 443),
        'password': clash_node.get('password', ''),
        'tls': _build_tls(clash_node),
    }

    # obfs: Clash obfs=salamander + obfs-password -> sing-box obfs 对象
    if clash_node.get('obfs'):
        obfs = {'type': clash_node['obfs']}
        if clash_node.get('obfs-password'):
            obfs['password'] = clash_node['obfs-password']
        outbound['obfs'] = obfs

    # 带宽: Clash "30 Mbps" -> sing-box int 30；无法解析时省略字段
    if clash_node.get('up') is not None:
        bw = _parse_bandwidth(clash_node['up'])
        if bw is not None:
            outbound['up_mbps'] = bw
    if clash_node.get('down') is not None:
        bw = _parse_bandwidth(clash_node['down'])
        if bw is not None:
            outbound['down_mbps'] = bw

    return outbound


def convert(node: dict) -> dict | None:
    """按协议类型分派到对应转换器。"""
    func_name = _CONVERTERS.get(node.get('type'))
    if not func_name:
        return None
    return globals()[func_name](node)
