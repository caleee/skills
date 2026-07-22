"""
Shadowrocket / URI 订阅格式提取 — 解析 ss:// trojan:// 等 URI
"""

import base64
from collections import namedtuple
from urllib.parse import urlparse, parse_qs, unquote


SsNode = namedtuple('SsNode', ['method', 'password', 'server', 'port'])


def _parse_userinfo_hostport(userinfo: str, hostport: str) -> SsNode | None:
    """从 method:password@server:port 格式解析出 SsNode。"""
    if ':' not in userinfo:
        return None
    method, _, password = userinfo.partition(':')
    if ':' in hostport:
        server, _, port_str = hostport.partition(':')
        try:
            port = int(port_str)
        except ValueError:
            return None
    else:
        server = hostport
        port = 443
    return SsNode(method, password, server, port)


def _decode_ss_payload(payload: str) -> SsNode | None:
    """从 ss:// base64 编码的 payload 中解码出 SsNode。"""
    try:
        decoded = base64.urlsafe_b64decode(payload + '==').decode('utf-8')
    except Exception:
        return None
    if '@' not in decoded:
        return None
    userinfo, _, hostport = decoded.partition('@')
    return _parse_userinfo_hostport(userinfo, hostport)


def _parse_ss_uri_sip002(uri: str) -> dict | None:
    """解析 SIP002 格式: ss://base64(method:password@server:port)#name"""
    name = _parse_fragment(uri)
    uri = uri.split('#')[0] if '#' in uri else uri
    payload = uri[5:]

    result = _decode_ss_payload(payload)
    if not result:
        return None
    if not name:
        name = f'{result.server}:{result.port}'
    return _make_ss_node(name, result)


def _parse_ss_uri_legacy(uri: str) -> dict | None:
    """解析旧格式 ss://method:password@server:port#name（明文，非 base64 编码）。"""
    name = _parse_fragment(uri)
    uri = uri.split('#')[0] if '#' in uri else uri
    payload = uri[5:]

    if '@' not in payload:
        return None

    userinfo, _, hostport = payload.partition('@')
    ss = _parse_userinfo_hostport(userinfo, hostport)
    if not ss:
        return None
    if not name:
        name = f'{ss.server}:{ss.port}'
    return _make_ss_node(name, ss)


def _parse_fragment(uri: str) -> str:
    """提取 URI 中的 #fragment 名称。"""
    if '#' in uri:
        return unquote(uri.split('#', 1)[1])
    return ''


def _make_ss_node(name: str, ss: SsNode) -> dict:
    """构造 Clash 格式 SS 节点。"""
    return {
        'name': name,
        'type': 'ss',
        'server': ss.server,
        'port': ss.port,
        'cipher': ss.method,
        'password': ss.password,
    }


def _parse_ss_uri(uri: str) -> dict | None:
    """解析 ss:// URI 为 Clash 格式节点。"""
    if not uri.startswith('ss://'):
        return None
    # 优先尝试 SIP002（整个 payload 是 base64）
    result = _parse_ss_uri_sip002(uri)
    if result:
        return result
    # 回退旧格式
    return _parse_ss_uri_legacy(uri)


def _parse_trojan_uri(uri: str) -> dict | None:
    """解析 trojan:// URI 为 Clash 格式节点。"""
    if not uri.startswith('trojan://'):
        return None

    parsed = urlparse(uri)
    password = parsed.username or ''
    server = parsed.hostname or ''
    port = parsed.port or 443
    name = unquote(parsed.fragment) if parsed.fragment else f'{server}:{port}'

    query = parse_qs(parsed.query)
    node = {
        'name': name,
        'type': 'trojan',
        'server': server,
        'port': port,
        'password': password,
    }
    if 'peer' in query:
        node['sni'] = query['peer'][0]
    if 'allowInsecure' in query:
        node['skip-cert-verify'] = query['allowInsecure'][0] in ('1', 'true')
    if 'fp' in query:
        node['client-fingerprint'] = query['fp'][0]
    return node


def extract(content: str) -> list:
    """从 URI 格式订阅文本中提取代理节点列表。"""
    nodes = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('ss://'):
            node = _parse_ss_uri(line)
        elif line.startswith('trojan://'):
            node = _parse_trojan_uri(line)
        else:
            continue
        if node:
            nodes.append(node)
    return nodes