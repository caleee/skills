"""
Surge / Loon 订阅格式提取 — 解析 [Proxy] 段落
"""

import re


def _is_loon(content: str) -> bool:
    """判断内容是否为 Loon 格式：不含 udp-relay 参数。"""
    return not bool(re.search(r'udp-relay\s*=', content))


def _parse_kv_pairs(pairs: list[str], protocol: str) -> dict:
    """将 key=value 标记列表解析为字段字典。"""
    fields = {}
    for token in pairs:
        if '=' not in token:
            continue
        k, _, v = token.partition('=')
        k = k.strip()
        v = v.strip()
        if not k:
            continue
        # Surge → Clash 字段映射
        if k == 'encrypt-method':
            fields['cipher'] = v
        elif k == 'udp-relay':
            fields['udp'] = v.lower() == 'true'
        elif k == 'skip-cert-verify':
            fields['skip-cert-verify'] = v.lower() == 'true'
        elif k == 'client-fingerprint':
            fields['client-fingerprint'] = v
        elif k == 'tfo':
            fields['tfo'] = v.lower() == 'true'
        else:
            fields[k] = v
    return fields


def _parse_line(line: str, protocol: str) -> dict | None:
    """解析单行 Surge/Loon 代理配置。"""
    line = line.strip()
    if not line or line.startswith('[') or line.startswith('#'):
        return None

    # 格式: name = protocol, server, port, key=value, ...
    if '=' not in line:
        return None

    name_part, _, rest = line.partition('=')
    name = name_part.strip()
    if not name:
        return None

    tokens = [t.strip() for t in rest.split(',')]
    if len(tokens) < 3:
        return None

    proto = tokens[0].strip()
    server = tokens[1].strip()
    port_str = tokens[2].strip()

    if proto not in ('ss', 'trojan', 'anytls', 'http', 'socks5', 'vmess'):
        return None

    try:
        port = int(port_str)
    except ValueError:
        return None

    node = {
        'name': name,
        'type': proto,
        'server': server,
        'port': port,
    }

    # Loon 不支持 udp-relay；如果行中出现了该参数则忽略
    if protocol == 'loon':
        filtered_tokens = [t for t in tokens[3:] if not t.startswith('udp-relay=')]
        fields = _parse_kv_pairs(filtered_tokens, proto)
    else:
        fields = _parse_kv_pairs(tokens[3:], proto)
    node.update(fields)

    return node


def extract(content: str) -> list:
    """从 Surge/Loon 配置文本中提取代理节点列表。"""
    protocol = 'loon' if _is_loon(content) else 'surge'
    nodes = []
    for line in content.splitlines():
        node = _parse_line(line, protocol)
        if node:
            nodes.append(node)
    return nodes
