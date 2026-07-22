#!/usr/bin/env python3
"""
sub2cfg 验证脚本 — 测试所有模块和流水线

用法: python3 verify.py [--verbose]

依赖: 仅需 Python 3.10+ 和 PyYAML（sub2cfg 本身依赖）
"""
import sys
import os
import yaml
import tempfile
import subprocess
import traceback

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'scripts'))


def run_sub2cfg(input_path, *args):
    """运行 sub2cfg.py 并返回结果。"""
    scripts_dir = os.path.join(SCRIPT_DIR, 'scripts')
    cmd = [sys.executable, os.path.join(scripts_dir, 'sub2cfg.py'), input_path] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, cwd=scripts_dir)


PASS = 0
FAIL = 0
VERBOSE = False


def pass_msg(msg):
    print(f'  PASS: {msg}')


def fail_msg(msg):
    print(f'  FAIL: {msg}')


def section(title):
    print()
    print(f'--- {title} ---')


def check(description, ok):
    global PASS, FAIL
    if ok:
        pass_msg(description)
        PASS += 1
    else:
        fail_msg(description)
        FAIL += 1


def node_count_from_yaml(yaml_text):
    """统计 output YAML 中的节点数。"""
    try:
        data = yaml.safe_load(yaml_text)
        if not data:
            return 0
        if 'proxies' in data:
            return len(data['proxies'])
        if 'outbounds' in data:
            # 只统计代理类型 outbound，跳过 group/direct
            return sum(1 for o in data['outbounds'] if o.get('type') in ('anytls', 'shadowsocks', 'trojan'))
        return 0
    except Exception as e:
        print(f'  [警告] node_count 解析失败: {e}', file=sys.stderr)
        return 0


def main():
    global VERBOSE
    VERBOSE = '--verbose' in sys.argv

    print('=========================================')
    print(' sub2cfg 验证')
    print('=========================================')

    # ---- 0. 环境检查 ----
    section('0. 环境检查')
    check('Python 3.10+', sys.version_info >= (3, 10))
    check('PyYAML 已安装', True)

    # ---- 1. 模块导入测试 ----
    section('1. 模块导入')
    modules = [
        'detect', 'extract.clash', 'extract.surge',
        'extract.shadowrocket', 'extract.base64', 'extract.singbox',
        'convert.to_singbox', 'group.clash', 'group.singbox',
    ]
    for import_path in modules:
        try:
            __import__(import_path)
            check(f'导入 {import_path}', True)
        except Exception as e:
            check(f'导入 {import_path}', False)
            if VERBOSE:
                traceback.print_exc()

    # ---- 2. detect.py 格式检测 ----
    section('2. 格式检测')
    from detect import detect

    SAMPLE_DIR = os.path.join(SCRIPT_DIR, 'sample')

    with open(os.path.join(SAMPLE_DIR, 'clash-subscribe.yaml'), 'r', encoding='utf-8') as f:
        check('detect: Clash', detect(f.read()) == 'clash')

    with open(os.path.join(SAMPLE_DIR, 'surge-subscribe.conf'), 'r', encoding='utf-8') as f:
        check('detect: Surge', detect(f.read()) == 'surge')

    with open(os.path.join(SAMPLE_DIR, 'shadowrocket-uri.txt'), 'r', encoding='utf-8') as f:
        check('detect: Shadowrocket', detect(f.read()) == 'shadowrocket')

    with open(os.path.join(SAMPLE_DIR, 'loon-subscribe.conf'), 'r', encoding='utf-8') as f:
        check('detect: Loon', detect(f.read()) == 'loon')

    check('detect: 未知格式', detect('random text') == 'unknown')

    # ---- 3. extractor 单元测试 ----
    section('3. 提取器测试')

    # 3.1 Clash extractor
    from extract.clash import extract as extract_clash
    content = """
proxies:
  - {name: "🇭🇰 香港 01", server: ex.com, port: 443, type: anytls, password: "x"}
  - {name: "🇺🇸 美国 01", server: us.com, port: 443, type: anytls, password: "y"}
  - {name: "当前流量：1.23G", server: a.com, port: 80, type: anytls, password: "z"}
"""
    nodes = extract_clash(content)
    check('Clash 提取: 过滤信息条目', len(nodes) == 2)
    check('Clash 提取: 保留区域节点', nodes[0]['name'] == '🇭🇰 香港 01')

    # 3.2 Surge extractor
    from extract.surge import extract as extract_surge
    content = """
[Proxy]
🇭🇰 香港 01 = ss, ex.com, 443, encrypt-method=chacha20-ietf-poly1305, password=pass, udp-relay=true
🇭🇰 香港 02 = trojan, trojan.ex.com, 443, password=pass2, sni=ts.ex.com, skip-cert-verify=true
"""
    nodes = extract_surge(content)
    check('Surge 提取: 数量', len(nodes) == 2)
    check('Surge 提取: SS 字段', nodes[0]['cipher'] == 'chacha20-ietf-poly1305')
    check('Surge 提取: udp-relay 映射', nodes[0]['udp'] is True)
    check('Surge 提取: Trojan 字段', nodes[1]['sni'] == 'ts.ex.com')

    # 3.2b Loon extractor — Loon 格式不含 udp-relay
    from extract.surge import extract as extract_loon
    loon_content = """
[Proxy]
🇭🇰 香港 01 = ss, ex.com, 443, encrypt-method=chacha20-ietf-poly1305, password=pass
🇭🇰 香港 02 = trojan, trojan.ex.com, 443, password=pass2, sni=ts.ex.com
"""
    nodes = extract_loon(loon_content)
    check('Loon 提取: 数量', len(nodes) == 2)
    check('Loon 提取: 无 udp 字段', 'udp' not in nodes[1])

    # 3.3 Shadowrocket extractor
    from extract.shadowrocket import extract as extract_uri
    content = "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpzc3Bhc3MxMjNAZXhhbXBsZS5jb206NDQz#🇭🇰香港01"
    nodes = extract_uri(content)
    check('Shadowrocket 提取: ss://', len(nodes) == 1)
    if nodes:
        check('Shadowrocket 提取: ss 字段', nodes[0]['cipher'] == 'chacha20-ietf-poly1305')

    content = "trojan://trojpass456@trojan.ex.com:443?peer=ts.ex.com&allowInsecure=1&fp=chrome#node"
    nodes = extract_uri(content)
    check('Shadowrocket 提取: trojan://', len(nodes) == 1)
    if nodes:
        check('Shadowrocket 提取: trojan sni', nodes[0].get('sni') == 'ts.ex.com')
        check('Shadowrocket 提取: trojan skip-cert-verify', nodes[0].get('skip-cert-verify') is True)

    # 3.4 Sing-box extractor
    from extract.singbox import extract as extract_sb
    content = """{
  "outbounds": [
    {"type": "direct", "tag": "DIRECT"},
    {"type": "anytls", "tag": "🇭🇰 香港 01", "server": "ex.com", "server_port": 443,
     "password": "x", "tls": {"enabled": true, "server_name": "sni.ex.com"}},
    {"type": "shadowsocks", "tag": "ss-out", "server": "ss.ex.com", "server_port": 443,
     "method": "aes-256-gcm", "password": "sspass"}
  ]
}"""
    nodes = extract_sb(content)
    check('Sing-box 提取: 跳过 direct', len(nodes) == 2)
    check('Sing-box 提取: anytls', any(n['type'] == 'anytls' for n in nodes))
    check('Sing-box 提取: ss', any(n['type'] == 'ss' for n in nodes))

    # ---- 4. converter 单元测试 ----
    section('4. 转换器测试')
    from convert.to_singbox import convert_anytls, convert_ss, convert_trojan

    # anytls
    node = {'name': 'n1', 'type': 'anytls', 'server': 'ex.com', 'port': 443, 'password': 'p'}
    outbound = convert_anytls(node)
    check('anytls 转换: 基本字段', outbound is not None and outbound['type'] == 'anytls' and outbound['server_port'] == 443)
    node.update({'sni': 'sni.ex.com', 'skip-cert-verify': True, 'alpn': ['h2'], 'client-fingerprint': 'firefox'})
    outbound = convert_anytls(node)
    check('anytls 转换: tls 嵌套', outbound['tls']['server_name'] == 'sni.ex.com')
    check('anytls 转换: utls', outbound['tls']['utls']['fingerprint'] == 'firefox')
    check('anytls 转换: 跳过非 anytls', convert_anytls({'type': 'ss'}) is None)

    # ss
    node = {'name': 'n1', 'type': 'ss', 'server': 'ex.com', 'port': 443, 'cipher': 'chacha20', 'password': 'p'}
    outbound = convert_ss(node)
    check('SS 转换: 基本字段', outbound is not None and outbound['type'] == 'shadowsocks' and outbound['method'] == 'chacha20')
    check('SS 转换: 跳过非 ss', convert_ss({'type': 'trojan'}) is None)

    # trojan
    node = {'name': 'n1', 'type': 'trojan', 'server': 'ex.com', 'port': 443, 'password': 'p'}
    outbound = convert_trojan(node)
    check('Trojan 转换: 基本字段', outbound is not None and outbound['type'] == 'trojan' and outbound['tls']['enabled'] is True)
    check('Trojan 转换: 跳过非 trojan', convert_trojan({'type': 'ss'}) is None)

    # ---- 5. 端到端流水线测试 ----
    section('5. 端到端测试')

    # 5.1 Clash
    r = run_sub2cfg(os.path.join(SAMPLE_DIR, 'clash-subscribe.yaml'), '-g')
    check('Clash → Clash (带组)', r.returncode == 0 and '提取到' in r.stderr)
    n = node_count_from_yaml(r.stdout)
    check(f'Clash 节点数: {n}', n == 56)

    r = run_sub2cfg(os.path.join(SAMPLE_DIR, 'clash-subscribe.yaml'), '-t', 'sing-box', '-g')
    check('Clash → Sing-box (带组)', r.returncode == 0 and '提取到' in r.stderr)
    n = node_count_from_yaml(r.stdout)
    check(f'Sing-box 节点数: {n}', n == 56)

    # 5.2 Surge
    r = run_sub2cfg(os.path.join(SAMPLE_DIR, 'surge-subscribe.conf'))
    check('Surge 自动检测', r.returncode == 0)
    n = node_count_from_yaml(r.stdout)
    check(f'Surge 节点数: {n}', n == 8)

    r = run_sub2cfg(os.path.join(SAMPLE_DIR, 'surge-subscribe.conf'), '-f', 'surge', '-t', 'sing-box', '-g')
    check('Surge → Sing-box (带组)', r.returncode == 0)

    # 5.3 Shadowrocket
    r = run_sub2cfg(os.path.join(SAMPLE_DIR, 'shadowrocket-uri.txt'))
    check('Shadowrocket 自动检测', r.returncode == 0)
    n = node_count_from_yaml(r.stdout)
    check(f'Shadowrocket 节点数: {n}', n == 4)

    # 5.4 Loon
    r = run_sub2cfg(os.path.join(SAMPLE_DIR, 'loon-subscribe.conf'))
    check('Loon 自动检测', r.returncode == 0)
    n = node_count_from_yaml(r.stdout)
    check(f'Loon 节点数: {n}', n == 5)

    # 5.5 Base64
    r = run_sub2cfg(os.path.join(SAMPLE_DIR, 'base64-uri.txt'), '-f', 'base64-uri')
    check('Base64-URI 提取', r.returncode == 0)
    n = node_count_from_yaml(r.stdout)
    check(f'Base64 节点数: {n}', n == 2)

    # 5.6 输出文件
    tmp = os.path.join(tempfile.gettempdir(), 'sub2cfg-test-output.yaml')
    r = run_sub2cfg(os.path.join(SAMPLE_DIR, 'clash-subscribe.yaml'), '-o', tmp)
    check('输出文件', r.returncode == 0 and os.path.exists(tmp))
    if os.path.exists(tmp):
        os.unlink(tmp)

    # 5.7 错误处理
    r = run_sub2cfg('/nonexistent/file.yaml')
    check('错误: 文件不存在', r.returncode == 1 and '文件不存在' in r.stderr)

    with tempfile.NamedTemporaryFile(suffix='.txt', mode='w', delete=False) as f:
        f.write('random text without format\n')
        tmp = f.name
    r = run_sub2cfg(tmp)
    check('错误: 无法识别格式', r.returncode == 1 and '无法识别' in r.stderr)
    os.unlink(tmp)

    # ---- 汇总 ----
    print()
    print('=========================================')
    print(f' 结果: {PASS} 通过, {FAIL} 失败')
    print('=========================================')

    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
