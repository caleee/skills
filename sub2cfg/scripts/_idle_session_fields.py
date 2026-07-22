"""Clash ↔ Sing-box 空闲会话字段映射（Clash 连字符命名 → Sing-box 下划线命名）"""

# Clash → Sing-box 单向映射
CLASH_TO_SINGBOX_IDLE_FIELDS = [
    ('idle-session-check-interval', 'idle_session_check_interval'),
    ('idle-session-timeout', 'idle_session_timeout'),
    ('min-idle-session', 'min_idle_session'),
]

# Sing-box → Clash 单向映射
SINGBOX_TO_CLASH_IDLE_FIELDS = [
    ('idle_session_check_interval', 'idle-session-check-interval'),
    ('idle_session_timeout', 'idle-session-timeout'),
    ('min_idle_session', 'min-idle-session'),
]
