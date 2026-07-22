"""
端到端流水线测试 — 用 sample 文件跑完整流程
"""
import sys
import os
import yaml
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from tests import run_script, SAMPLE_DIR


class TestPipelineClash:
    def test_clash_to_clash(self):
        result = run_script(os.path.join(SAMPLE_DIR, 'clash-subscribe.yaml'), '-g')
        assert result.returncode == 0
        assert '提取到' in result.stderr
        data = yaml.safe_load(result.stdout)
        assert 'proxies' in data
        assert 'proxy-groups' in data
        assert len(data['proxies']) > 0

    def test_clash_to_singbox(self):
        result = run_script(os.path.join(SAMPLE_DIR, 'clash-subscribe.yaml'), '-t', 'sing-box', '-g')
        assert result.returncode == 0
        assert '提取到' in result.stderr
        data = yaml.safe_load(result.stdout)
        assert 'outbounds' in data
        assert len(data['outbounds']) > 0

    def test_clash_output_file(self):
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
            tmp = f.name
        try:
            result = run_script(os.path.join(SAMPLE_DIR, 'clash-subscribe.yaml'), '-o', tmp)
            assert result.returncode == 0
            assert '已写入' in result.stderr
            with open(tmp) as f:
                data = yaml.safe_load(f)
                assert 'proxies' in data
        finally:
            os.unlink(tmp)


class TestPipelineSurge:
    def test_surge_to_clash(self):
        result = run_script(os.path.join(SAMPLE_DIR, 'surge-subscribe.conf'), '-f', 'surge')
        assert result.returncode == 0
        data = yaml.safe_load(result.stdout)
        assert 'proxies' in data
        assert len(data['proxies']) == 8

    def test_surge_auto_detect(self):
        result = run_script(os.path.join(SAMPLE_DIR, 'surge-subscribe.conf'))
        assert result.returncode == 0
        data = yaml.safe_load(result.stdout)
        assert 'proxies' in data

    def test_surge_to_singbox(self):
        result = run_script(os.path.join(SAMPLE_DIR, 'surge-subscribe.conf'), '-f', 'surge', '-t', 'sing-box', '-g')
        assert result.returncode == 0
        data = yaml.safe_load(result.stdout)
        assert 'outbounds' in data
        tags = [o.get('tag') for o in data['outbounds']]
        assert 'DIRECT' in tags
        assert 'PROXIES' in tags
        assert 'FINAL' in tags


class TestPipelineShadowrocket:
    def test_shadowrocket_to_clash(self):
        result = run_script(os.path.join(SAMPLE_DIR, 'shadowrocket-uri.txt'), '-f', 'shadowrocket')
        assert result.returncode == 0
        data = yaml.safe_load(result.stdout)
        assert 'proxies' in data
        assert len(data['proxies']) == 4

    def test_shadowrocket_auto_detect(self):
        result = run_script(os.path.join(SAMPLE_DIR, 'shadowrocket-uri.txt'))
        assert result.returncode == 0
        data = yaml.safe_load(result.stdout)
        assert 'proxies' in data

    def test_shadowrocket_protocols(self):
        result = run_script(os.path.join(SAMPLE_DIR, 'shadowrocket-uri.txt'), '-f', 'shadowrocket')
        data = yaml.safe_load(result.stdout)
        types = {n['type'] for n in data['proxies']}
        assert 'ss' in types
        assert 'trojan' in types


class TestPipelineLoon:
    def test_loon_to_clash(self):
        result = run_script(os.path.join(SAMPLE_DIR, 'loon-subscribe.conf'))
        assert result.returncode == 0
        data = yaml.safe_load(result.stdout)
        assert 'proxies' in data
        assert len(data['proxies']) == 5


class TestPipelineBase64:
    def test_base64_to_clash(self):
        result = run_script(os.path.join(SAMPLE_DIR, 'base64-uri.txt'), '-f', 'base64-uri')
        assert result.returncode == 0
        data = yaml.safe_load(result.stdout)
        assert 'proxies' in data
        assert len(data['proxies']) >= 1


class TestPipelineErrors:
    def test_invalid_format(self):
        result = run_script(os.path.join(SAMPLE_DIR, 'clash-subscribe.yaml'), '-f', 'shadowrocket')
        assert result.returncode == 1  # 未提取到节点时报错退出
        assert '未提取到任何有效节点' in result.stderr

    def test_unknown_format(self):
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w') as f:
            f.write("some random text\n")
            tmp = f.name
        try:
            result = run_script(tmp)
            assert result.returncode == 1
            assert '无法识别' in result.stderr
        finally:
            os.unlink(tmp)

    def test_nonexistent_file(self):
        result = run_script('/nonexistent/file.yaml')
        assert result.returncode == 1
        assert '文件不存在' in result.stderr
