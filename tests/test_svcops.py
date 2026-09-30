#!/usr/bin/env python3
"""svc-ops CLI 冒烟测试 —— stdlib `unittest`，零第三方依赖。

CLI 本体是没有 `.py` 后缀的单文件（`svc-ops/cli/svc-ops`），用 `SourceFileLoader` 载入。
覆盖：端口回收**只杀监听者**（`-sTCP:LISTEN`，`MT-084` 教训）、`lsof`/`ps` 解析、服务表校验、
环境叠加顺序、`--dry-run` 不起进程、`status`/`health` 渲染与退出码。**不真起进程**（外部调用全 mock）。

运行：`python3 -m unittest discover -s tests -v`
"""
from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
import signal
import tempfile
import unittest
from pathlib import Path
from unittest import mock

CLI = Path(__file__).resolve().parents[1] / "svc-ops" / "cli" / "svc-ops"


def _load_cli():
    loader = importlib.machinery.SourceFileLoader("svc_ops_mod", str(CLI))
    spec = importlib.util.spec_from_loader("svc_ops_mod", loader)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


svc = _load_cli()


def _ctx(root, cfg, json_mode=False, dry_run=False):
    return svc.Context(Path(root), cfg, json_mode, dry_run)


def _cfg(**services):
    return {"services": {name: dict(spec) for name, spec in services.items()}}


class TestPortReclaim(unittest.TestCase):
    def test_free_port_kills_only_listeners(self):
        with mock.patch("subprocess.run") as run, mock.patch("os.kill") as kill:
            run.return_value = mock.Mock(stdout="4321\n")
            svc._free_port(8080)
        cmd = run.call_args[0][0]
        self.assertEqual(cmd[:2], ["lsof", "-ti"])
        self.assertIn("-sTCP:LISTEN", cmd)
        self.assertIn("tcp:8080", cmd)
        kill.assert_called_once_with(4321, signal.SIGTERM)

    def test_free_port_tolerates_vanished_pid(self):
        with mock.patch("subprocess.run") as run, mock.patch("os.kill", side_effect=ProcessLookupError):
            run.return_value = mock.Mock(stdout="4321\n")
            svc._free_port(5173)          # 不抛

    def test_listen_pid_none_when_idle(self):
        with mock.patch("subprocess.run") as run:
            run.return_value = mock.Mock(stdout="")
            self.assertIsNone(svc._listen_pid(5173))

    def test_listen_pid_returns_first(self):
        with mock.patch("subprocess.run") as run:
            run.return_value = mock.Mock(stdout="111\n222\n")
            self.assertEqual(svc._listen_pid(5173), 111)
            self.assertIn("-sTCP:LISTEN", run.call_args[0][0])

    def test_pgid_of_parses_ps(self):
        with mock.patch("subprocess.run") as run:
            run.return_value = mock.Mock(stdout="  4321\n")
            self.assertEqual(svc._pgid_of(67990), 4321)
            self.assertEqual(run.call_args[0][0][:2], ["ps", "-o"])

    def test_pgid_of_none_for_dead_pid(self):
        with mock.patch("subprocess.run") as run:
            run.return_value = mock.Mock(stdout="")
            self.assertIsNone(svc._pgid_of(67990))


class TestServiceTable(unittest.TestCase):
    def test_parse_and_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _ctx(tmp, _cfg(api={"port": 8080, "command": ["mvn"]}))
            t = ctx.services()
        self.assertEqual(t["api"]["command"], ["mvn"])
        self.assertEqual(t["api"]["cwd"], Path(tmp))          # cwd 默认项目根
        self.assertEqual(t["api"]["ready_timeout"], 90)

    def test_string_command_is_split(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _ctx(tmp, _cfg(web={"port": 5173, "command": "pnpm run dev"}))
            self.assertEqual(ctx.services()["web"]["command"], ["pnpm", "run", "dev"])

    def test_missing_port_or_command_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(svc.SvcError):
                _ctx(tmp, _cfg(a={"command": ["x"]})).services()      # 缺 port
            with self.assertRaises(svc.SvcError):
                _ctx(tmp, _cfg(a={"port": 1})).services()             # 缺 command

    def test_empty_services_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(svc.SvcError):
                _ctx(tmp, {}).services()

    def test_targets(self):
        table = {"a": {}, "b": {}}
        self.assertEqual(svc._targets([], table), ["a", "b"])
        self.assertEqual(svc._targets(["a"], table), ["a"])
        with self.assertRaises(svc.SvcError):
            svc._targets(["zzz"], table)


class TestServiceEnv(unittest.TestCase):
    def test_overlay_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "run.env").write_text("FOO=run\nBAR=run\n", encoding="utf-8")
            Path(tmp, "svc.env").write_text("BAR=svc\n", encoding="utf-8")
            cfg = {"run": {"env_file": "run.env"},
                   "services": {"a": {"port": 1, "command": ["x"],
                                      "env_file": "svc.env", "env": {"BAZ": "z"}}}}
            ctx = _ctx(tmp, cfg)
            with mock.patch.dict(os.environ, {"FOO": "proc"}, clear=True):
                env = svc._service_env(ctx.services()["a"], ctx)
        self.assertEqual(env["FOO"], "run")      # run.env 覆盖本机环境
        self.assertEqual(env["BAR"], "svc")      # svc.env 覆盖 run.env
        self.assertEqual(env["BAZ"], "z")        # 服务 env 最高


class TestCommands(unittest.TestCase):
    def test_start_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _ctx(tmp, _cfg(api={"port": 8080, "command": ["mvn", "-B"]}), dry_run=True)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = svc.cmd_start([], ctx)
        self.assertEqual(rc, 0)
        self.assertIn("dry-run", buf.getvalue())
        self.assertIn("mvn -B", buf.getvalue())

    def test_start_skips_running(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _ctx(tmp, _cfg(api={"port": 8080, "command": ["mvn"]}))
            with mock.patch.object(svc, "_read_pid", return_value=123), \
                 mock.patch.object(svc, "_alive", return_value=True):
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc = svc.cmd_start([], ctx)
        self.assertEqual(rc, 0)
        self.assertIn("已在运行", buf.getvalue())

    def test_status_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _ctx(tmp, _cfg(api={"port": 8080, "command": ["mvn"],
                                      "health": "http://localhost:8080/actuator/health"}))
            with mock.patch.object(svc, "_read_pid", return_value=123), \
                 mock.patch.object(svc, "_listen_pid", return_value=123), \
                 mock.patch.object(svc, "_alive", return_value=True), \
                 mock.patch.object(svc, "_pgid_of", return_value=123), \
                 mock.patch.object(svc, "_ready_probe", return_value=True):
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc = svc.cmd_status([], ctx)
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertIn("运行中", out)
        self.assertIn("健康", out)

    def test_health_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _ctx(tmp, _cfg(api={"port": 8080, "command": ["mvn"]}))
            with mock.patch.object(svc, "_ready_probe", return_value=True):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(svc.cmd_health([], ctx), 0)
            with mock.patch.object(svc, "_ready_probe", return_value=False):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(svc.cmd_health([], ctx), 1)

    def test_status_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _ctx(tmp, _cfg(api={"port": 8080, "command": ["mvn"]}), json_mode=True)
            with mock.patch.object(svc, "_read_pid", return_value=None), \
                 mock.patch.object(svc, "_listen_pid", return_value=None), \
                 mock.patch.object(svc, "_ready_probe", return_value=False):
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    svc.cmd_status([], ctx)
        data = json.loads(buf.getvalue())
        self.assertEqual(data[0]["service"], "api")

    def test_unknown_command_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(svc.dispatch(["nope"], _ctx(tmp, _cfg())), 2)

    def test_help_exit_0(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(svc.main(["--help"]), 0)
        self.assertIn("svc-ops start", buf.getvalue())

    def test_missing_table_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                rc = svc.main(["status", "--root", tmp])
        self.assertEqual(rc, 1)
        self.assertIn("未找到服务表", err.getvalue())


if __name__ == "__main__":
    unittest.main()
