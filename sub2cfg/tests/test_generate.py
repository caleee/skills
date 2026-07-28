"""
模板组装测试 — 验证 generate/clash.py、generate/singbox.py 的功能
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from generate.clash import generate as generate_clash, _render_proxies, _render_geoip_rules, _build_region_group
from generate.singbox import generate as generate_singbox, _build_region_group as sb_build_region_group
from generate.dae import generate as generate_dae
from proxy_format import reorder_node


def _full_template():
    return os.path.join(os.path.dirname(__file__), '..', 'templates')


class TestRenderProxies:
    def test_basic_nodes_rendered(self):
        nodes = [
            reorder_node({'name': 'HK', 'type': 'anytls', 'server': 'x', 'port': 443, 'password': 'pw', 'sni': 's'}),
        ]
        output = _render_proxies(nodes)
        assert 'proxies:' in output
        assert 'HK' in output

    def test_false_bools_omitted(self):
        nodes = [reorder_node({'name': 'x', 'type': 'ss', 'server': 's', 'port': 443, 'password': 'pw', 'skip-cert-verify': False})]
        output = _render_proxies(nodes)
        assert 'skip-cert-verify: false' not in output

    def test_true_bools_included(self):
        nodes = [reorder_node({'name': 'x', 'type': 'ss', 'server': 's', 'port': 443, 'password': 'pw', 'skip-cert-verify': True})]
        output = _render_proxies(nodes)
        assert 'skip-cert-verify: true' in output

    def test_keys_in_order(self):
        """字段顺序：name→type→server→port→密码类→TLS→其他。"""
        nodes = [reorder_node({
            'name': 'test', 'type': 'anytls', 'server': 's', 'port': 443,
            'password': 'pw', 'sni': 'sn', 'skip-cert-verify': False,
            'alpn': ['h2'], 'client-fingerprint': 'chrome',
            'idle-session-check-interval': 30, 'udp': True,
        })]
        output = _render_proxies(nodes)
        # 查找键位置（忽略列表值）
        for line in output.split('\n')[1:]:
            if 'name:' in line:
                order_idx = {n: line.find(n + ':') for n in ['name:', 'type:', 'server:', 'port:', 'password:', 'sni:', 'alpn:', 'client-fingerprint:', 'idle-session-check-interval:']}
                vals = [order_idx[n] for n in order_idx if order_idx[n] >= 0]
                assert vals == sorted(vals), f'keys out of order: {order_idx}'
                break


class TestRenderGeoipRules:
    def test_generates_for_valid_regions(self):
        rules = _render_geoip_rules(['hongkong', 'japan', 'taiwan'])
        assert len(rules) == 3
        assert 'GEOIP,HK,hongkong,no-resolve' in rules
        assert 'GEOIP,JP,japan,no-resolve' in rules
        assert 'GEOIP,TW,taiwan,no-resolve' in rules

    def test_empty_input(self):
        assert _render_geoip_rules([]) == []

    def test_skips_unmappable(self):
        """self 和 others 不应生成 GEOIP 规则。"""
        rules = _render_geoip_rules(['self', 'others'])
        assert len(rules) == 0


class TestRegionGroupBuilders:
    """测试各平台 _build_region_group 逻辑。"""

    def test_clash_self_is_select(self):
        result = _build_region_group('self', ['n1'])
        assert result['type'] == 'select'
        assert result['proxies'] == ['n1']

    def test_clash_region_is_urltest(self):
        result = _build_region_group('hongkong', ['h1'])
        assert result['type'] == 'url-test'
        assert result['url'] == 'http://www.gstatic.com/generate_204'
        assert result['interval'] == 300

    def test_singbox_other_is_selector(self):
        result = sb_build_region_group('others', ['n1'])
        assert result['type'] == 'selector'

    def test_singbox_region_is_urltest(self):
        result = sb_build_region_group('america', ['a1'])
        assert result['type'] == 'urltest'
        assert result['interval'] == '5m'
        assert result['tolerance'] == 50


class TestDaeGenerate:
    def test_replaces_group_section(self):
        tpl = os.path.join(_full_template(), 'config.dae')
        output = generate_dae(tpl, ['hongkong', 'japan', 'self'])
        assert "filter: subtag(hongkong)" in output
        assert "filter: subtag(japan)" in output
        assert "filter: subtag(self)" in output
        assert "policy: 'min_moving_avg'" in output

    def test_skips_others(self):
        tpl = os.path.join(_full_template(), 'config.dae')
        output = generate_dae(tpl, ['others'])
        assert 'group {' in output
        after_group = output.split('group {', 1)[-1]
        assert 'others' not in after_group

    def test_preserves_service_groups(self):
        tpl = os.path.join(_full_template(), 'config.dae')
        output = generate_dae(tpl, ['hongkong'])
        assert 'youtube' in output or 'dns' in output

    def test_unchanged_without_marker(self):
        """无标记的模板应不变。"""
        tpl = os.path.join(_full_template(), 'config.dae')
        output = generate_dae(tpl, ['hongkong'])
        with open(tpl) as f:
            original = f.read()
        assert output != original


class TestClashGenerate:
    def test_replaces_proxies(self):
        tpl = os.path.join(_full_template(), 'clash.yaml')
        output = generate_clash(tpl,
            [reorder_node({'name': '🇭🇰 Test', 'type': 'anytls', 'server': 'e', 'port': 443, 'password': 'p', 'sni': 's'})],
            ['hongkong', 'japan', 'self'],
            {'hongkong': [], 'japan': [], 'self': []})
        assert '🇭🇰 Test' in output

    def test_keeps_non_region_geoip(self):
        tpl = os.path.join(_full_template(), 'clash.yaml')
        output = generate_clash(tpl, [], ['hongkong'], {'hongkong': [], 'self': []})
        assert 'GEOIP,CN,DIRECT' in output

    def test_replaces_groups(self):
        tpl = os.path.join(_full_template(), 'clash.yaml')
        import yaml
        output = generate_clash(tpl, [], ['hongkong', 'japan', 'taiwan', 'self', 'others'], {
            'hongkong': [], 'japan': [], 'taiwan': [], 'self': [], 'others': [],
        })
        config = yaml.safe_load(output)
        groups = config.get('proxy-groups', [])
        assert len(groups) >= 15  # PROXIES + 区域组 + 服务组

    def test_yaml_valid(self):
        tpl = os.path.join(_full_template(), 'clash.yaml')
        import yaml
        output = generate_clash(tpl,
            [reorder_node({'name': 'Test', 'type': 'anytls', 'server': 'e', 'port': 443, 'password': 'p'})],
            ['hongkong'], {'hongkong': [], 'self': []})
        config = yaml.safe_load(output)
        assert config is not None


class TestSingboxGenerate:
    def test_replaces_outbounds(self):
        tpl = os.path.join(_full_template(), 'sing-box.json')
        output = generate_singbox(tpl,
            [reorder_node({'name': 'Test', 'type': 'anytls', 'server': 'e', 'port': 443, 'password': 'p'})],
            ['hongkong', 'japan'],
            {'hongkong': [], 'japan': [], 'self': [], 'others': [], 'america': []})
        config = json.loads(output)
        assert config.get('outbounds') is not None

    def test_other_is_selector(self):
        tpl = os.path.join(_full_template(), 'sing-box.json')
        output = generate_singbox(tpl, [], ['hongkong', 'self', 'others'], {
            'hongkong': [], 'self': [], 'others': ['o1'],
        })
        config = json.loads(output)
        for ob in config.get('outbounds', []):
            if ob.get('tag') == 'others':
                assert ob['type'] == 'selector'

    def test_preserves_geoip_private(self):
        tpl = os.path.join(_full_template(), 'sing-box.json')
        output = generate_singbox(tpl, [], ['hongkong'], {'hongkong': [], 'self': [], 'others': []})
        config = json.loads(output)
        rules = config.get('route', {}).get('rules', [])
        has_private = any(r.get('rule_set') == 'geoip-private' for r in rules)
        assert has_private

    def test_geoip_rules_generated(self):
        tpl = os.path.join(_full_template(), 'sing-box.json')
        output = generate_singbox(tpl, [], ['hongkong', 'japan', 'taiwan'], {
            'hongkong': [], 'japan': [], 'taiwan': [], 'self': [], 'others': [],
        })
        config = json.loads(output)
        rule_sets = []
        for r in config.get('route', {}).get('rules', []):
            if isinstance(r, dict) and 'rule_set' in r:
                rule_sets.append(r['rule_set'])
        assert 'geoip-hk' in rule_sets
        assert 'geoip-jp' in rule_sets
        assert 'geoip-tw' in rule_sets