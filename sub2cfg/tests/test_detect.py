"""
格式检测测试 — 验证 detect.py 能正确识别各种订阅格式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from detect import detect


def test_detect_clash():
    content = """
proxies:
  - name: "test"
    type: anytls
"""
    assert detect(content) == 'clash'


def test_detect_surge():
    content = """
[Proxy]
test = ss, example.com, 443, encrypt-method=chacha20, password=xxx, udp-relay=true
"""
    assert detect(content) == 'surge'


def test_detect_shadowrocket():
    content = "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpwYXNzd29yZEBleGFtcGxlLmNvbTo0NDM=#test"
    assert detect(content) == 'shadowrocket'


def test_detect_shadowrocket_trojan():
    content = "trojan://password@example.com:443?peer=example.com#test"
    assert detect(content) == 'shadowrocket'


def test_detect_singbox():
    content = '{"outbounds": [{"type": "direct", "tag": "DIRECT"}]}'
    assert detect(content) == 'sing-box'


def test_detect_base64():
    """Base64 编码的 URI 会被检测为 shadowrocket（解码后是 ss://）。"""
    import base64
    content = base64.b64encode(b"ss://dGVzdDpwYXNzQGV4YW1wbGUuY29tOjQ0Mw==#test").decode()
    assert detect(content) == 'shadowrocket'


def test_detect_loon():
    """Loon 格式：无 udp-relay 参数时检测为 loon。"""
    content = """
[Proxy]
test = ss, example.com, 443, encrypt-method=chacha20, password=xxx
"""
    assert detect(content) == 'loon'


def test_detect_surge_with_udp_relay():
    """Surge 格式：有 udp-relay 参数时检测为 surge。"""
    content = """
[Proxy]
test = ss, example.com, 443, encrypt-method=chacha20, password=xxx, udp-relay=true
"""
    assert detect(content) == 'surge'


def test_detect_unknown():
    assert detect("hello world") == 'unknown'


def test_detect_empty():
    assert detect("") == 'unknown'