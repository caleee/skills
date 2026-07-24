"""区域识别：从节点名中的 emoji 国旗提取区域代码。

ALL_FLAGS（所有国旗，用于过滤非代理节点）与 REGION_MAP（区域映射）共享此来源，
新增区域时只需更新 REGION_MAP。
"""

# 用于识别代理节点的 emoji 国旗集合（过滤非代理节点如"当前流量"、"到期时间"）
ALL_FLAGS = set('🇭🇰🇺🇸🇯🇵🇸🇬🇨🇳🇬🇧🇩🇪🇫🇷🇰🇷🇮🇳🇨🇦🇦🇺🇷🇺🇧🇷🇳🇱🇸🇪🇳🇴🇫🇮🇩🇰🇵🇱🇨🇿🇭🇺🇷🇴🇹🇷🇮🇱🇦🇪🇿🇦🇲🇽🇦🇷🇨🇱🇵🇪🇵🇭')

# emoji 国旗到区域代码的映射（只有这些区域会生成策略组）
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
