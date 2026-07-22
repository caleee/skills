"""区域识别：从节点名中的 emoji 国旗提取区域代码"""

REGION_MAP = [
    ('🇭🇰', 'HK'),
    ('🇺🇸', 'US'),
    ('🇯🇵', 'JP'),
    ('🇸🇬', 'SG'),
    ('🇨🇳', 'TW'),
]


def get_region(name: str) -> str | None:
    """从节点名提取区域代码"""
    for emoji, code in REGION_MAP:
        if emoji in name:
            return code
    return None
