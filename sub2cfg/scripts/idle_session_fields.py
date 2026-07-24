"""Clash ↔ Sing-box 空闲会话字段映射。

Clash 使用连字符命名 + int（秒），Sing-box 使用下划线命名 + duration 字符串（如 "30s"）。
idle_session_check_interval 和 idle_session_timeout 需要 int<->duration 转换；
min_idle_session 在两边都是 int，直接映射。反向映射由正向映射派生。
"""


def _to_singbox_duration(value) -> str:
    """Clash int（秒）-> Sing-box duration 字符串。"""
    return f'{value}s'


def _to_clash_int(value) -> int:
    """Sing-box duration 字符串（如 "30s"/"5m"/"1h"/"1h30m"）-> Clash int（秒）。"""
    if not isinstance(value, str):
        return int(value)
    import re
    total = 0
    found = False
    for n, unit in re.findall(r'(\d+)([smh])', value):
        found = True
        total += int(n) * {'s': 1, 'm': 60, 'h': 3600}[unit]
    return total if found else int(value)


# Clash -> Sing-box 映射；第三项为转换函数（None 表示直接映射）
CLASH_TO_SINGBOX_IDLE_FIELDS = [
    ('idle-session-check-interval', 'idle_session_check_interval', _to_singbox_duration),
    ('idle-session-timeout', 'idle_session_timeout', _to_singbox_duration),
    ('min-idle-session', 'min_idle_session', None),
]

# Sing-box -> Clash 映射（由正向映射派生，反向转换用 _to_clash_int）
SINGBOX_TO_CLASH_IDLE_FIELDS = [
    (sb, cl, _to_clash_int if conv else None)
    for cl, sb, conv in CLASH_TO_SINGBOX_IDLE_FIELDS
]


def convert_idle_fields(src: dict, dst: dict, mapping) -> None:
    """按 mapping 将 src 中的空闲会话字段转换写入 dst。

    mapping 是 (src_key, dst_key, converter) 列表；converter 为 None 时直接赋值。
    提取器与转换器共享此逻辑，避免两处重复循环。
    """
    for src_key, dst_key, converter in mapping:
        if src_key in src:
            value = src[src_key]
            if converter:
                value = converter(value)
            dst[dst_key] = value
