"""
转换器测试 — 验证 convert/to_singbox.py 的协议转换
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


class TestConvertAnyTLS:
    def test_convert_anytls_basic(self):
        from convert.to_singbox import convert_anytls
        node = {
            'name': '🇭🇰 香港 01',
            'type': 'anytls',
            'server': 'example.com',
            'port': 443,
            'password': 'testpass',
        }
        result = convert_anytls(node)
        assert result is not None
        assert result['type'] == 'anytls'
        assert result['tag'] == '🇭🇰 香港 01'
        assert result['server'] == 'example.com'
        assert result['server_port'] == 443
        assert result['password'] == 'testpass'
        assert result['tls']['enabled'] is True

    def test_convert_anytls_with_tls(self):
        from convert.to_singbox import convert_anytls
        node = {
            'name': 'test',
            'type': 'anytls',
            'server': 'example.com',
            'port': 443,
            'password': 'pass',
            'sni': 'sni.example.com',
            'skip-cert-verify': True,
            'alpn': ['h2'],
            'client-fingerprint': 'firefox',
        }
        result = convert_anytls(node)
        assert result['tls']['server_name'] == 'sni.example.com'
        assert result['tls']['insecure'] is True
        assert result['tls']['alpn'] == ['h2']
        assert result['tls']['utls']['fingerprint'] == 'firefox'

    def test_skip_non_anytls(self):
        from convert.to_singbox import convert_anytls
        assert convert_anytls({'type': 'ss'}) is None
        assert convert_anytls({'type': 'trojan'}) is None


class TestConvertSS:
    def test_convert_ss_basic(self):
        from convert.to_singbox import convert_ss
        node = {
            'name': '🇭🇰 香港 01',
            'type': 'ss',
            'server': 'ss.example.com',
            'port': 443,
            'cipher': 'chacha20-ietf-poly1305',
            'password': 'sspass',
        }
        result = convert_ss(node)
        assert result is not None
        assert result['type'] == 'shadowsocks'
        assert result['tag'] == '🇭🇰 香港 01'
        assert result['method'] == 'chacha20-ietf-poly1305'
        assert result['password'] == 'sspass'

    def test_convert_ss_with_udp(self):
        from convert.to_singbox import convert_ss
        node = {'name': 't', 'type': 'ss', 'server': 's', 'port': 443, 'cipher': 'aes', 'password': 'p', 'udp': True}
        result = convert_ss(node)
        assert result['udp_over_tcp'] is True

    def test_skip_non_ss(self):
        from convert.to_singbox import convert_ss
        assert convert_ss({'type': 'trojan'}) is None


class TestConvertTrojan:
    def test_convert_trojan_basic(self):
        from convert.to_singbox import convert_trojan
        node = {
            'name': '🇭🇰 香港 01',
            'type': 'trojan',
            'server': 'trojan.example.com',
            'port': 443,
            'password': 'trojpass',
        }
        result = convert_trojan(node)
        assert result is not None
        assert result['type'] == 'trojan'
        assert result['tls']['enabled'] is True

    def test_convert_trojan_with_tls(self):
        from convert.to_singbox import convert_trojan
        node = {
            'name': 'test',
            'type': 'trojan',
            'server': 'ex.com',
            'port': 443,
            'password': 'pass',
            'sni': 'sni.ex.com',
            'skip-cert-verify': True,
            'alpn': ['h2'],
            'client-fingerprint': 'chrome',
        }
        result = convert_trojan(node)
        assert result['tls']['server_name'] == 'sni.ex.com'
        assert result['tls']['insecure'] is True
        assert result['tls']['alpn'] == ['h2']
        assert result['tls']['utls']['fingerprint'] == 'chrome'

    def test_skip_non_trojan(self):
        from convert.to_singbox import convert_trojan
        assert convert_trojan({'type': 'ss'}) is None