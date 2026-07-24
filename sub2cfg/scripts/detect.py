"""
订阅格式检测 — 判断订阅返回内容的格式类型
"""

import re
import base64


# 格式标识 -> 提取器模块路径（sub2cfg.py 与 extract/base64.py 共享此注册表）
EXTRACTOR_MODULES = {
    'clash': 'extract.clash',
    'surge': 'extract.surge',
    'loon': 'extract.surge',
    'shadowrocket': 'extract.shadowrocket',
    'base64-uri': 'extract.base64',
    'sing-box': 'extract.singbox',
}


def _try_base64_decode(content: str) -> str | None:
    """尝试将内容作为 base64 解码，失败返回 None。"""
    stripped = content.strip()
    if not stripped:
        return None
    # base64 通常只包含字母数字、+、/、=
    if not re.match(r'^[A-Za-z0-9+/=]+$', stripped):
        return None
    try:
        return base64.b64decode(stripped).decode('utf-8')
    except Exception:
        return None


def detect(content: str) -> str:
    """检测订阅内容格式，返回格式标识"""
    # 优先检测 URI 格式（ss:// trojan:// 开头的行）
    lines = [l.strip() for l in content.splitlines() if l.strip() and not l.strip().startswith('#')]
    if lines:
        first_line = lines[0]
        if first_line.startswith('ss://') or first_line.startswith('trojan://'):
            return 'shadowrocket'

    # 尝试 base64 解码后重新检测
    decoded = _try_base64_decode(content)
    if decoded:
        inner_lines = [l.strip() for l in decoded.splitlines() if l.strip() and not l.strip().startswith('#')]
        if inner_lines and (inner_lines[0].startswith('ss://') or inner_lines[0].startswith('trojan://')):
            return 'shadowrocket'

    # Clash YAML
    if 'proxies:' in content and ('type: anytls' in content or 'type: ss' in content or '- name:' in content):
        return 'clash'

    # Sing-box JSON
    if content.strip().startswith('{') and '"outbounds"' in content:
        return 'sing-box'

    # Surge / Loon
    if re.search(r'^\s*\[Proxy\]', content, re.MULTILINE) or re.search(r'^\w+\s*=\s*(http|socks5|ss|trojan|anytls)', content, re.MULTILINE):
        return detect_surge_or_loon(content)

    return 'unknown'


def detect_surge_or_loon(content: str) -> str:
    """区分 Surge 和 Loon：Loon 不支持 udp-relay，因此若内容中完全不含 udp-relay 参数则判定为 Loon。

    注意：这是一条启发式规则。如果用户同时提供纯 Surge（不含 udp-relay）和纯 Loon 订阅，
    两者会被误判为同一种格式。此时应使用 -f 强制指定。
    """
    has_udp_relay = bool(re.search(r'udp-relay\s*=', content))
    return 'surge' if has_udp_relay else 'loon'


if __name__ == '__main__':
    import sys
    content = sys.stdin.read()
    fmt = detect(content)
    print(f'检测结果: {fmt}')
    sys.exit(0 if fmt != 'unknown' else 1)
