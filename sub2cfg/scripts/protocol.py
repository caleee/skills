"""协议类型注册表：Clash 与 Sing-box 之间的协议类型映射。

提取器（extract/singbox.py）和转换器（convert/to_singbox.py）共享此映射，
新增协议时只需在 CLASH_TO_SINGBOX_TYPE 注册，反向映射自动派生。
"""

# Clash 协议类型 -> Sing-box 出站类型（单一事实来源）
CLASH_TO_SINGBOX_TYPE = {
    'ss': 'shadowsocks',
    'trojan': 'trojan',
    'anytls': 'anytls',
}

# Sing-box 出站类型 -> Clash 协议类型（由正向映射派生）
SINGBOX_TO_CLASH_TYPE = {v: k for k, v in CLASH_TO_SINGBOX_TYPE.items()}

# 支持的协议列表
SUPPORTED_PROTOCOLS = tuple(CLASH_TO_SINGBOX_TYPE.keys())
