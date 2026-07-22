"""
提取器测试 — 验证每个 extractor 能正确解析对应格式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


class TestExtractClash:
    def test_extract_anytls_nodes(self):
        from extract.clash import extract
        content = """
proxies:
  - {name: "🇭🇰 香港 01", server: example.com, port: 443, type: anytls, password: "xxx"}
  - {name: "🇺🇸 美国 01", server: us.example.com, port: 443, type: anytls, password: "yyy"}
  - {name: "当前流量：1.23G", server: a.com, port: 80, type: anytls, password: "zzz"}
"""
        nodes = extract(content)
        assert len(nodes) == 2
        assert nodes[0]['name'] == '🇭🇰 香港 01'
        assert nodes[1]['name'] == '🇺🇸 美国 01'

    def test_extract_invalid_yaml(self):
        from extract.clash import extract
        nodes = extract("not: yaml: content")
        assert nodes == []

    def test_extract_empty_proxies(self):
        from extract.clash import extract
        nodes = extract("other: data")
        assert nodes == []


class TestExtractSurge:
    def test_extract_ss_and_trojan(self):
        from extract.surge import extract
        content = """
[Proxy]
🇭🇰 香港 01 = ss, example.com, 443, encrypt-method=chacha20-ietf-poly1305, password=sspass123, udp-relay=true
🇭🇰 香港 02 = trojan, trojan.example.com, 443, password=trojpass456, sni=ts.example.com, skip-cert-verify=true
"""
        nodes = extract(content)
        assert len(nodes) == 2
        assert nodes[0]['type'] == 'ss'
        assert nodes[0]['cipher'] == 'chacha20-ietf-poly1305'
        assert nodes[0]['udp'] is True
        assert nodes[1]['type'] == 'trojan'
        assert nodes[1]['sni'] == 'ts.example.com'
        assert nodes[1]['skip-cert-verify'] is True

    def test_extract_anytls(self):
        from extract.surge import extract
        content = "test = anytls, any.example.com, 443, password=xxx, sni=any.example.com, client-fingerprint=firefox"
        nodes = extract(content)
        assert len(nodes) == 1
        assert nodes[0]['type'] == 'anytls'
        assert nodes[0]['client-fingerprint'] == 'firefox'

    def test_extract_skip_comments(self):
        from extract.surge import extract
        content = "# comment\n[Proxy]\n# another comment\n"
        nodes = extract(content)
        assert len(nodes) == 0

    def test_extract_loon_format(self):
        from extract.surge import extract
        content = """
[Proxy]
🇭🇰 香港 01 = ss, example.com, 443, encrypt-method=chacha20-ietf-poly1305, password=sspass123
🇸🇬 新加坡 01 = trojan, sg.example.com, 443, password=sgpass, sni=sg.example.com
"""
        nodes = extract(content)
        assert len(nodes) == 2
        assert nodes[0]['type'] == 'ss'
        assert nodes[1]['type'] == 'trojan'


class TestExtractShadowrocket:
    def test_ss_uri(self):
        from extract.shadowrocket import extract
        content = "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpzc3Bhc3MxMjNAZXhhbXBsZS5jb206NDQz#🇭🇰香港01"
        nodes = extract(content)
        assert len(nodes) == 1
        assert nodes[0]['type'] == 'ss'
        assert nodes[0]['cipher'] == 'chacha20-ietf-poly1305'
        assert nodes[0]['password'] == 'sspass123'
        assert nodes[0]['server'] == 'example.com'
        assert nodes[0]['port'] == 443

    def test_trojan_uri(self):
        from extract.shadowrocket import extract
        content = "trojan://trojpass456@trojan.example.com:443?peer=ts.example.com&allowInsecure=1&fp=chrome#🇭🇰香港02"
        nodes = extract(content)
        assert len(nodes) == 1
        assert nodes[0]['type'] == 'trojan'
        assert nodes[0]['password'] == 'trojpass456'
        assert nodes[0]['sni'] == 'ts.example.com'
        assert nodes[0]['skip-cert-verify'] is True
        assert nodes[0]['client-fingerprint'] == 'chrome'

    def test_multiple_uris(self):
        from extract.shadowrocket import extract
        content = """ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpzc3Bhc3MxMjNAZXhhbXBsZS5jb206NDQz#node1
trojan://pass@ex.com:443#node2"""
        nodes = extract(content)
        assert len(nodes) == 2

    def test_empty_content(self):
        from extract.shadowrocket import extract
        assert extract("") == []
        assert extract("# just a comment") == []


class TestExtractBase64:
    def test_base64_uri(self):
        from extract.base64 import extract
        import base64
        # ss://cipher:pass@server.com:443 的 base64 编码
        content = base64.b64encode(b"ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpzc3Bhc3MxMjNAZXhhbXBsZS5jb206NDQz#test").decode()
        nodes = extract(content)
        assert len(nodes) >= 1

    def test_invalid_base64(self):
        from extract.base64 import extract
        assert extract("not-base64!!!") == []


class TestExtractSingbox:
    def test_extract_anytls(self):
        from extract.singbox import extract
        content = """{
  "outbounds": [
    {"type": "direct", "tag": "DIRECT"},
    {"type": "anytls", "tag": "🇭🇰 香港 01", "server": "example.com", "server_port": 443,
     "password": "xxx", "tls": {"enabled": true, "server_name": "sni.example.com", "insecure": true}}
  ]
}"""
        nodes = extract(content)
        assert len(nodes) == 1
        assert nodes[0]['type'] == 'anytls'
        assert nodes[0]['sni'] == 'sni.example.com'

    def test_extract_shadowsocks(self):
        from extract.singbox import extract
        content = """{
  "outbounds": [
    {"type": "shadowsocks", "tag": "ss-out", "server": "ss.example.com",
     "server_port": 443, "method": "aes-256-gcm", "password": "sspass"}
  ]
}"""
        nodes = extract(content)
        assert len(nodes) == 1
        assert nodes[0]['type'] == 'ss'
        assert nodes[0]['cipher'] == 'aes-256-gcm'

    def test_extract_skip_selector(self):
        from extract.singbox import extract
        content = """{
  "outbounds": [
    {"type": "selector", "tag": "PROXIES", "outbounds": ["a", "b"]},
    {"type": "urltest", "tag": "HK", "outbounds": ["a"]}
  ]
}"""
        nodes = extract(content)
        assert len(nodes) == 0

    def test_invalid_json(self):
        from extract.singbox import extract
        assert extract("not json") == []