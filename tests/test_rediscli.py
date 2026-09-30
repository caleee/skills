#!/usr/bin/env python3
"""redis-cli CLI 冒烟测试 —— stdlib `unittest`，零第三方依赖。

CLI 本体是没有 `.py` 后缀的单文件（`redis-cli/cli/redis-cli`），用 `SourceFileLoader` 载入。
覆盖：`.env` 解析；全局旗标解析；连接取值环（命令行 → env → toml → 默认）；命令构造
（`-h/-p/-n`）与口令只进 `REDISCLI_AUTH`（不出现在 argv）；`ping`/`exec`/`keys` 的分派与 `--json`。
**不连真 Redis**（`subprocess.run` 全部 mock）。

运行：`python3 -m unittest discover -s tests -v`
"""
from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

CLI = Path(__file__).resolve().parents[1] / "redis-cli" / "cli" / "redis-cli"


def _load_cli():
    loader = importlib.machinery.SourceFileLoader("redis_cli_mod", str(CLI))
    spec = importlib.util.spec_from_loader("redis_cli_mod", loader)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


rc = _load_cli()


def _ctx(root, cfg=None, env_files=None, conn_opts=None, json_mode=False):
    return rc.Context(Path(root), cfg or {}, env_files or [], conn_opts or {}, json_mode)


def _ok(stdout=""):
    return mock.Mock(returncode=0, stdout=stdout, stderr="")


class TestEnvParse(unittest.TestCase):
    def test_parse_env_text(self):
        text = ("# comment\nexport A=1\nB='x y'\nC=\"q\"\n\nD=has space\n")
        env = rc.parse_env_text(text)
        self.assertEqual(env, {"A": "1", "B": "x y", "C": "q", "D": "has space"})

    def test_unquote(self):
        self.assertEqual(rc._unquote("'abc'"), "abc")
        self.assertEqual(rc._unquote('"abc"'), "abc")
        self.assertEqual(rc._unquote(" abc "), "abc")
        self.assertEqual(rc._unquote("'"), "'")


class TestSplitGlobals(unittest.TestCase):
    def test_split(self):
        root, envs, js, co, rest = rc._split_globals(
            ["--root", "/p", "--env-file", "a.env", "--host=h", "--port", "6380", "--json",
             "exec", "GET", "k"])
        self.assertEqual(root, "/p")
        self.assertEqual(envs, ["a.env"])
        self.assertTrue(js)
        self.assertEqual(co, {"host": "h", "port": "6380"})
        self.assertEqual(rest, ["exec", "GET", "k"])


class TestPick(unittest.TestCase):
    def test_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            ctx = _ctx(".")
            self.assertEqual((ctx.host(), ctx.port(), ctx.password()), ("127.0.0.1", "6379", ""))

    def test_toml_then_cli(self):
        cfg = {"connection": {"host": "redis.internal", "port": 6380}}
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(_ctx(".", cfg=cfg).host(), "redis.internal")
            self.assertEqual(_ctx(".", cfg=cfg, conn_opts={"host": "cli.host"}).host(), "cli.host")

    def test_env_file_beats_toml(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "r.env").write_text("REDIS_HOST=env.host\nREDIS_PASSWORD=pw\n", encoding="utf-8")
            cfg = {"connection": {"env_file": "r.env", "host": "toml.host"}}
            with mock.patch.dict(os.environ, {}, clear=True):
                ctx = _ctx(tmp, cfg=cfg)
                self.assertEqual(ctx.host(), "env.host")
                self.assertEqual(ctx.password(), "pw")

    def test_var_name_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "r.env").write_text("MY_REDIS_PW=s3cret\n", encoding="utf-8")
            cfg = {"connection": {"env_file": "r.env", "password_var": "MY_REDIS_PW"}}
            with mock.patch.dict(os.environ, {}, clear=True):
                self.assertEqual(_ctx(tmp, cfg=cfg).password(), "s3cret")

    def test_db_default(self):
        cfg = {"connection": {"db": 2}}
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(_ctx(".", cfg=cfg).db(), "2")
            self.assertEqual(_ctx(".", cfg=cfg, conn_opts={"db": "5"}).db(), "5")


class TestRedisRun(unittest.TestCase):
    def test_cmd_and_auth_env(self):
        with mock.patch("subprocess.run") as run:
            run.return_value = _ok("PONG\n")
            out = rc.redis_run("h", "6379", "sekret", "PING", timeout=3, db="2")
        self.assertEqual(out, "PONG")
        cmd = run.call_args[0][0]
        env = run.call_args[1]["env"]
        self.assertEqual(cmd, ["redis-cli", "-h", "h", "-p", "6379", "-n", "2", "PING"])
        self.assertEqual(env["REDISCLI_AUTH"], "sekret")
        self.assertNotIn("sekret", cmd)

    def test_no_auth_env_when_blank(self):
        with mock.patch("subprocess.run") as run:
            run.return_value = _ok("PONG\n")
            rc.redis_run("h", "6379", "", "PING")
        self.assertNotIn("REDISCLI_AUTH", run.call_args[1]["env"])

    def test_raises_on_error(self):
        with mock.patch("subprocess.run") as run:
            run.return_value = mock.Mock(returncode=1, stdout="", stderr="ERR boom")
            with self.assertRaises(rc.RedisError):
                rc.redis_run("h", "6379", "", "PING")


class TestCommands(unittest.TestCase):
    def test_ping_true_and_false(self):
        with mock.patch("subprocess.run") as run:
            run.return_value = _ok("PONG\n")
            with mock.patch.dict(os.environ, {}, clear=True), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(rc.cmd_ping([], _ctx(".")), 0)
        with mock.patch("subprocess.run") as run:
            run.return_value = _ok("nope\n")
            with mock.patch.dict(os.environ, {}, clear=True), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(rc.cmd_ping([], _ctx(".")), 1)

    def test_exec_passthrough(self):
        with mock.patch("subprocess.run") as run:
            run.return_value = _ok("bar\n")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc.cmd_exec(["GET", "foo"], _ctx("."))
        self.assertEqual(buf.getvalue().strip(), "bar")
        self.assertEqual(run.call_args[0][0][-2:], ["GET", "foo"])

    def test_keys_warns_on_stderr(self):
        with mock.patch("subprocess.run") as run:
            run.return_value = _ok("k:1\nk:2\n")
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc.cmd_keys(["k:*"], _ctx("."))
        self.assertIn("k:1", out.getvalue())
        self.assertIn("KEYS", err.getvalue())

    def test_exec_json_arrays_lines(self):
        with mock.patch("subprocess.run") as run:
            run.return_value = _ok("a\nb\n")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc.cmd_exec(["LRANGE", "l", "0", "-1"], _ctx(".", json_mode=True))
        self.assertEqual(json.loads(buf.getvalue()), ["a", "b"])

    def test_unknown_command_exit_2(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(rc.dispatch(["nope"], _ctx(".")), 2)

    def test_help_exit_0(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(rc.main(["--help"]), 0)
        self.assertIn("redis-cli ping", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
