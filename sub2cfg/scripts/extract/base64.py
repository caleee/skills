"""
Base64 编码订阅提取 — 解码后递归检测格式并分派
"""

import base64


def extract(content: str) -> list:
    """Base64 解码后递归分派到对应 extractor。"""
    stripped = content.strip()
    if not stripped:
        return []

    try:
        decoded = base64.b64decode(stripped).decode('utf-8')
    except Exception:
        return []

    from extract.shadowrocket import extract as extract_shadowrocket
    from extract.clash import extract as extract_clash
    from detect import detect

    # detect() 会再次扫描文本，但仅为确定格式，无需额外解码
    fmt = detect(decoded)
    if fmt == 'clash':
        return extract_clash(decoded)
    return extract_shadowrocket(decoded)