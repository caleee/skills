"""
Base64 编码订阅提取 - 解码后递归检测格式并分派
"""

import base64
import importlib


def extract(content: str, format: str | None = None) -> list:
    """Base64 解码后递归分派到对应 extractor。"""
    stripped = content.strip()
    if not stripped:
        return []

    try:
        decoded = base64.b64decode(stripped).decode('utf-8')
    except Exception:
        return []

    from detect import detect, EXTRACTOR_MODULES
    fmt = detect(decoded)

    # 分派到对应格式的提取器（复用 EXTRACTOR_MODULES 注册表，避免重复维护映射）
    module_path = EXTRACTOR_MODULES.get(fmt)
    if module_path:
        mod = importlib.import_module(module_path)
        return mod.extract(decoded, fmt)

    # 未知格式（detect 未识别为已知格式）：回退到 shadowrocket URI 解析
    from extract.shadowrocket import extract as extract_shadowrocket
    return extract_shadowrocket(decoded)
