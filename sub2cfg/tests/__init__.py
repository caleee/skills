"""sub2cfg 测试包 — 共享测试基础设施"""

import os
import subprocess
import sys

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')
SAMPLE_DIR = os.path.join(os.path.dirname(__file__), '..', 'sample')
sys.path.insert(0, SCRIPTS_DIR)


def run_script(input_path, *args):
    """运行 sub2cfg.py 并返回结果。"""
    cmd = [sys.executable, os.path.join(SCRIPTS_DIR, 'sub2cfg.py'), input_path] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, cwd=SCRIPTS_DIR)
