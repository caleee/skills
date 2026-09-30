#!/usr/bin/env python3
"""llm-wiki CLI 冒烟测试 —— stdlib `unittest`，零第三方依赖。

CLI 本体是没有 `.py` 后缀的单文件（`llm-wiki/cli/llmwiki`），用 `SourceFileLoader` 载入。
构建类子命令（`deploy`）通过 monkeypatch `subprocess.run` 隔离，**不要求装 mkdocs**——
这样 CI 与本地都能跑，且 P0-1（`shutil` 漏 import）这类崩溃会被直接测出。

运行：`python3 -m unittest discover -s tests -v`（需 Python 3.11+，`tomllib`）
"""
from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import io
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock

CLI = Path(__file__).resolve().parents[1] / "llm-wiki" / "cli" / "llmwiki"


def _load_cli():
    loader = importlib.machinery.SourceFileLoader("llmwiki_cli", str(CLI))
    spec = importlib.util.spec_from_loader("llmwiki_cli", loader)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


wiki = _load_cli()


class Fixture(unittest.TestCase):
    """最小项目：`docs/` + `mkdocs.yml` + 由 DEFAULTS 生成的配置。"""

    nav_mode = "auto"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        (self.root / "docs").mkdir()
        (self.root / "mkdocs.yml").write_text("site_name: t\n", encoding="utf-8")
        self.cfg = wiki.load_cfg(self.root)
        self.cfg["site.nav_mode"] = self.nav_mode

    def tearDown(self):
        self._tmp.cleanup()

    def md(self, rel: str, text: str = "x\n") -> Path:
        p = self.root / "docs" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def run_cli(self, fn, ns) -> tuple[int, str]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = fn(self.cfg, ns) or 0
        return code, buf.getvalue()


# ─────────────────────── M2 · nav build / render_pages ───────────────────────
class TestRenderPages(Fixture):
    def test_no_index_returns_none(self):
        d = self.root / "docs" / "b"
        d.mkdir()
        self.assertIsNone(wiki.render_pages(d), "无 index.md 时不得产出 .pages（绝不能用空 nav 占位）")

    def test_index_without_h1_returns_none(self):
        self.md("b/index.md", "no heading here\n")
        self.assertIsNone(wiki.render_pages(self.root / "docs" / "b"))

    def test_empty_nav_is_dropped_so_none(self):
        self.md("b/index.md", "no heading here\n")
        (self.root / "docs" / "b" / ".pages").write_text("nav: []\n", encoding="utf-8")
        self.assertIsNone(wiki.render_pages(self.root / "docs" / "b"))

    def test_title_updated_and_handwritten_keys_kept(self):
        self.md("d/index.md", "# New\n")
        pages = self.root / "docs" / "d" / ".pages"
        pages.write_text("title: Old\nhide: true\nnav:\n  - a.md\ncollapse: true\n", encoding="utf-8")
        self.assertEqual(wiki.render_pages(pages.parent),
                         "title: New\nhide: true\nnav:\n  - a.md\ncollapse: true\n")

    def test_nonempty_nav_never_dropped(self):
        self.md("d/index.md", "# D\n")
        pages = self.root / "docs" / "d" / ".pages"
        pages.write_text("nav:\n  - a.md\n", encoding="utf-8")
        self.assertEqual(wiki.render_pages(pages.parent), "title: D\nnav:\n  - a.md\n")


class TestNavBuild(Fixture):
    def test_cleans_legacy_empty_nav_and_writes_title(self):
        self.md("a/index.md", "# A\n")
        self.md("a/x.md")
        self.md("b/c/y.md")
        legacy = self.root / "docs" / "b" / ".pages"
        legacy.write_text("nav: []\n", encoding="utf-8")

        code, out = self.run_cli(wiki.cmd_nav_build, Namespace(dry_run=False))

        self.assertEqual(code, 0)
        self.assertIn("DELETE b/.pages", out)
        self.assertFalse(legacy.exists(), "存量空 nav 必须被清理（否则其下页面永久掉出导航）")
        self.assertEqual((self.root / "docs" / "a" / ".pages").read_text(encoding="utf-8"), "title: A\n")
        self.assertFalse((self.root / "docs" / "b" / ".pages").exists())

    def test_dry_run_touches_nothing(self):
        self.md("b/c/y.md")
        legacy = self.root / "docs" / "b" / ".pages"
        legacy.write_text("nav: []\n", encoding="utf-8")
        code, out = self.run_cli(wiki.cmd_nav_build, Namespace(dry_run=True))
        self.assertEqual(code, 0)
        self.assertIn("DELETE b/.pages", out)
        self.assertTrue(legacy.exists())
        self.assertEqual(legacy.read_text(encoding="utf-8"), "nav: []\n")

    def test_idempotent(self):
        self.md("a/index.md", "# A\n")
        self.md("a/x.md")
        self.run_cli(wiki.cmd_nav_build, Namespace(dry_run=False))
        _, out = self.run_cli(wiki.cmd_nav_build, Namespace(dry_run=False))
        self.assertIn("已生成/刷新 0 个", out)


# ─────────────────────── M3 · lint 导航可达性 ───────────────────────
class TestLintNavCoverage(Fixture):
    def test_reports_hidden_pages(self):
        self.md("a/x.md")
        self.md("b/c/y.md")
        (self.root / "docs" / "b" / ".pages").write_text("nav: []\n", encoding="utf-8")
        code, out = self.run_cli(wiki.cmd_lint, Namespace(semantic=False, max=None))
        self.assertEqual(code, 1)
        self.assertIn("[导航] b/.pages 的 nav 为空", out)
        self.assertIn("导航覆盖 1/2 页", out)

    def test_clean_fixture_is_green(self):
        self.md("a/x.md")
        code, out = self.run_cli(wiki.cmd_lint, Namespace(semantic=False, max=None))
        self.assertEqual(code, 0, out)
        self.assertIn("问题 0", out)

    def test_switch_off_disables_check(self):
        self.md("a/x.md")
        self.md("b/c/y.md")
        (self.root / "docs" / "b" / ".pages").write_text("nav: []\n", encoding="utf-8")
        self.cfg["lint.nav_coverage"] = False
        code, _ = self.run_cli(wiki.cmd_lint, Namespace(semantic=False, max=None))
        self.assertEqual(code, 0)

    def test_manual_mode_keeps_orphan_check(self):
        self.md("a/x.md")
        self.cfg["site.nav_mode"] = "manual"
        code, out = self.run_cli(wiki.cmd_lint, Namespace(semantic=False, max=None))
        self.assertEqual(code, 1)
        self.assertIn("[孤儿]", out)


# ─────────────────────── M1 · deploy ───────────────────────
class TestDeploy(Fixture):
    def _ns(self, dest=None, force=False):
        return Namespace(dest=dest, force=force)

    def test_rejects_root_home_and_project_paths(self):
        home = str(Path.home())
        for dest in ("/", home, str(self.root), str(self.root / "docs"), str(self.root / "site")):
            with self.subTest(dest=dest), self.assertRaises(SystemExit):
                with contextlib.redirect_stderr(io.StringIO()):
                    wiki.cmd_deploy(self.cfg, self._ns(dest))

    def test_rejects_nonempty_without_marker(self):
        junk = self.root / "out"
        junk.mkdir()
        (junk / "keepme").write_text("x", encoding="utf-8")
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            wiki.cmd_deploy(self.cfg, self._ns(str(junk)))
        self.assertTrue((junk / "keepme").exists(), "被拒绝时不得删除任何东西")

    def test_copies_marks_and_redeploys(self):
        out = self.root / "out"
        with mock.patch.object(wiki.subprocess, "run", lambda *a, **k: mock.Mock(returncode=0)):
            (self.root / "site").mkdir()
            (self.root / "site" / "index.html").write_text("<html/>", encoding="utf-8")
            code, _ = self.run_cli(wiki.cmd_deploy, self._ns(str(out)))
            self.assertEqual(code, 0)
            self.assertTrue((out / "index.html").exists())
            self.assertTrue((out / wiki.DEPLOY_MARKER).exists())
            (out / "stale.html").write_text("old", encoding="utf-8")
            code, _ = self.run_cli(wiki.cmd_deploy, self._ns(str(out)))   # 有标记 ⇒ 无需 --force
            self.assertEqual(code, 0)
            self.assertFalse((out / "stale.html").exists())

    def test_force_overwrites_foreign_dir(self):
        out = self.root / "out"
        out.mkdir()
        (out / "junk").write_text("x", encoding="utf-8")
        with mock.patch.object(wiki.subprocess, "run", lambda *a, **k: mock.Mock(returncode=0)):
            (self.root / "site").mkdir()
            code, _ = self.run_cli(wiki.cmd_deploy, self._ns(str(out), force=True))
        self.assertEqual(code, 0)
        self.assertFalse((out / "junk").exists())

    def test_build_failure_leaves_dest_untouched(self):
        out = self.root / "out"
        with mock.patch.object(wiki.subprocess, "run", lambda *a, **k: mock.Mock(returncode=2)):
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                wiki.cmd_deploy(self.cfg, self._ns(str(out)))
        self.assertFalse(out.exists())

    def test_default_dest_is_project_dist(self):
        with mock.patch.object(wiki.subprocess, "run", lambda *a, **k: mock.Mock(returncode=0)):
            (self.root / "site").mkdir()
            code, out_txt = self.run_cli(wiki.cmd_deploy, self._ns(None))
        self.assertEqual(code, 0)
        self.assertIn(str(self.root / "dist"), out_txt)


# ─────────────────────── 装配（parse + load_cfg） ───────────────────────
class TestWiring(Fixture):
    def test_check_deps_requires_awesome_pages_only_in_auto(self):
        self.assertIn("mkdocs-awesome-pages-plugin", wiki.NAV_DEPS)
        self.assertNotIn("mkdocs-awesome-pages-plugin", wiki.DEPS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
