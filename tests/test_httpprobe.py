#!/usr/bin/env python3
"""http-probe CLI 冒烟测试 —— stdlib `unittest`，零第三方依赖。

CLI 本体是没有 `.py` 后缀的单文件（`http-probe/cli/http-probe`），用 `SourceFileLoader` 载入。
覆盖：`.env` 解析、`${ENV}` 展开、base_url/鉴权取值环、URL 拼接、`http_request` 的
2xx 与非 2xx（`HTTPError` 也回显体）分支、响应契约解包（业务码成败与退出码）、`--json`。**不起网络**。

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
import urllib.error
from pathlib import Path
from unittest import mock

CLI = Path(__file__).resolve().parents[1] / "http-probe" / "cli" / "http-probe"


def _load_cli():
    loader = importlib.machinery.SourceFileLoader("http_probe_mod", str(CLI))
    spec = importlib.util.spec_from_loader("http_probe_mod", loader)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


hp = _load_cli()


def _ctx(root, cfg=None, cli_opts=None, json_mode=False, env_files=None):
    return hp.Context(Path(root), cfg or {}, env_files or [], cli_opts or {"header": []}, json_mode)


def _resp(status=200, body=b"{}", headers=None):
    m = mock.MagicMock()
    m.status = status
    m.headers = headers if headers is not None else {"Content-Type": "application/json"}
    m.read.return_value = body
    cm = mock.MagicMock()
    cm.__enter__.return_value = m
    cm.__exit__.return_value = False
    return cm


class TestEnvAndExpand(unittest.TestCase):
    def test_parse_env_text(self):
        env = hp.parse_env_text("export A=1\nB='x y'\n# c\n\nC=\"q\"\n")
        self.assertEqual(env, {"A": "1", "B": "x y", "C": "q"})

    def test_expand_known_and_unknown(self):
        self.assertEqual(hp._expand("http://${H}:${P}", {"H": "h", "P": "1"}), "http://h:1")
        self.assertEqual(hp._expand("$TOKEN/x", {"TOKEN": "t"}), "t/x")
        self.assertEqual(hp._expand("${MISSING}", {}), "${MISSING}")   # 未知保持原样
        self.assertEqual(hp._expand("a${X}b$Y", {"X": "1", "Y": "2"}), "a1b2")


class TestContext(unittest.TestCase):
    def test_base_url_priority(self):
        cfg = {"client": {"base_url": "http://toml"}}
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(_ctx(".", cfg).base_url(), "http://toml")
            self.assertEqual(_ctx(".", cfg, {"base-url": "http://cli"}).base_url(), "http://cli")
        with mock.patch.dict(os.environ, {"HTTP_PROBE_BASE_URL": "http://env"}, clear=True):
            self.assertEqual(_ctx(".", cfg).base_url(), "http://env")

    def test_default_base_url(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(_ctx(".").base_url(), hp.DEFAULTS["base_url"])

    def test_env_file_expand(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.env").write_text("API_BASE=http://h.test\nTOK=secret\n", encoding="utf-8")
            cfg = {"client": {"env_file": "a.env", "base_url": "${API_BASE}"},
                   "auth": {"token": "${TOK}"}}
            with mock.patch.dict(os.environ, {}, clear=True):
                ctx = _ctx(tmp, cfg)
                self.assertEqual(ctx.base_url(), "http://h.test")
                self.assertEqual(ctx.headers()["Authorization"], "Bearer secret")

    def test_headers_default_and_overrides(self):
        cfg = {"auth": {"headers": {"X-Api-Key": "k"}}}
        with mock.patch.dict(os.environ, {}, clear=True):
            h = _ctx(".", cfg, {"header": ["X-Extra: v:1"]}).headers()
        self.assertEqual(h["Accept"], "application/json")
        self.assertEqual(h["X-Api-Key"], "k")
        self.assertEqual(h["X-Extra"], "v:1")        # 冒号后原样
        self.assertNotIn("Authorization", h)          # 无 token 不设

    def test_timeout(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(_ctx(".").timeout(), 15)
            self.assertEqual(_ctx(".", {"client": {"timeout": 30}}).timeout(), 30)
            self.assertEqual(_ctx(".", cli_opts={"header": [], "timeout": "5"}).timeout(), 5)


class TestBuildUrlAndParse(unittest.TestCase):
    def test_build_url(self):
        self.assertEqual(hp._build_url("http://h", "/api", {}), "http://h/api")
        self.assertEqual(hp._build_url("http://h", "api", {}), "http://h/api")
        self.assertEqual(hp._build_url("http://h/api", "/x", {"a": "1", "b": ""}),
                         "http://h/api/x?a=1")

    def test_build_url_appends_with_amp(self):
        self.assertEqual(hp._build_url("http://h", "/x?k=v", {"a": "1"}), "http://h/x?k=v&a=1")

    def test_parse_repeats(self):
        pos, opts = hp._parse(["/x", "--param", "a=1", "--param=b=2", "--data", "{}", "--json"])
        self.assertEqual(pos, ["/x"])
        self.assertEqual(opts["param"], ["a=1", "b=2"])
        self.assertEqual(opts["data"], "{}")
        self.assertTrue(opts["json"])


class TestHttpRequest(unittest.TestCase):
    def test_2xx(self):
        with mock.patch("urllib.request.urlopen", return_value=_resp(200, b'{"a":1}')):
            status, headers, body = hp.http_request("GET", "http://h/x")
        self.assertEqual(status, 200)
        self.assertEqual(body, '{"a":1}')

    def test_http_error_body_still_read(self):
        err = urllib.error.HTTPError("http://h/x", 500, "boom",
                                     {"Content-Type": "text/plain"}, io.BytesIO(b"kaboom"))
        with mock.patch("urllib.request.urlopen", side_effect=err):
            status, headers, body = hp.http_request("GET", "http://h/x")
        self.assertEqual(status, 500)
        self.assertEqual(body, "kaboom")

    def test_connection_error_raises(self):
        with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
            with self.assertRaises(hp.HttpError):
                hp.http_request("GET", "http://h/x")

    def test_post_sends_json_body(self):
        captured = {}

        def fake(req, timeout=None):
            captured["data"] = req.data
            captured["method"] = req.get_method()
            return _resp(200, b"{}")

        with mock.patch("urllib.request.urlopen", side_effect=fake):
            hp.http_request("POST", "http://h/x", data={"n": 1})
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(json.loads(captured["data"]), {"n": 1})


class TestContractUnwrap(unittest.TestCase):
    def test_success_unwraps_data(self):
        cfg = {"response": {"code_field": "code", "success_value": 0, "data_field": "data"}}
        ctx = _ctx(".", cfg)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = hp._emit(ctx, "GET", "http://h/x", 200, {}, '{"code":0,"data":{"a":1}}')
        self.assertEqual(rc, 0)
        self.assertIn('"a": 1', buf.getvalue())

    def test_business_error_exit_1(self):
        cfg = {"response": {"code_field": "code", "success_value": 0, "data_field": "data"}}
        ctx = _ctx(".", cfg)
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            rc = hp._emit(ctx, "GET", "http://h/x", 200, {},
                          '{"code":1004,"message":"need tenant"}')
        self.assertEqual(rc, 1)
        self.assertIn("need tenant", err.getvalue())

    def test_http_status_governs_without_contract(self):
        ctx = _ctx(".")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(hp._emit(ctx, "GET", "http://h/x", 200, {}, "{}"), 0)
            self.assertEqual(hp._emit(ctx, "GET", "http://h/x", 500, {}, "oops"), 1)

    def test_json_output_shape(self):
        ctx = _ctx(".", json_mode=True)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            hp._emit(ctx, "GET", "http://h/x", 200, {"Content-Type": "application/json"},
                     '{"a":1}')
        data = json.loads(buf.getvalue())
        self.assertEqual(data["status"], 200)
        self.assertEqual(data["body"], {"a": 1})

    def test_json_output_non_json_body_falls_back_to_text(self):
        ctx = _ctx(".", json_mode=True)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            hp._emit(ctx, "GET", "http://h/x", 200, {"Content-Type": "text/html"}, "<h1>hi</h1>")
        self.assertEqual(json.loads(buf.getvalue())["body"], "<h1>hi</h1>")


class TestDispatch(unittest.TestCase):
    def test_get_alias(self):
        with mock.patch("urllib.request.urlopen", return_value=_resp(200, b'{"ok":true}')):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = hp.dispatch(["get", "/health"], _ctx(".", cli_opts={"header": []}))
        self.assertEqual(rc, 0)
        self.assertIn("HTTP 200", buf.getvalue())

    def test_request_method(self):
        with mock.patch("urllib.request.urlopen", return_value=_resp(204, b"")):
            with contextlib.redirect_stdout(io.StringIO()):
                rc = hp.dispatch(["request", "DELETE", "/x/1"], _ctx(".", cli_opts={"header": []}))
        self.assertEqual(rc, 0)

    def test_unknown_command_exit_2(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(hp.dispatch(["nope"], _ctx(".")), 2)

    def test_help_exit_0(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(hp.main(["--help"]), 0)
        self.assertIn("http-probe", buf.getvalue())

    def test_data_and_file_mutually_exclusive(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "b.json").write_text("{}", encoding="utf-8")
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                rc = hp.main(["post", "/x", "--data", "{}",
                              "--data-file", str(Path(tmp, "b.json")), "--root", tmp])
        self.assertEqual(rc, 1)
        self.assertIn("不能同时给", err.getvalue())


if __name__ == "__main__":
    unittest.main()
