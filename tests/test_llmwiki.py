#!/usr/bin/env python3
"""llm-wiki CLI 冒烟测试 —— stdlib `unittest`，零第三方依赖。

CLI 本体是没有 `.py` 后缀的单文件（`llm-wiki/cli/llmwiki`），用 `SourceFileLoader` 载入。
构建类子命令（`deploy`）通过 monkeypatch `subprocess.run` 隔离，**不要求装 mkdocs**——
这样 CI 与本地都能跑，且 P0-1（`shutil` 漏 import）这类崩溃会被直接测出。

运行：`python3 -m unittest discover -s tests -v`（需 Python 3.11+，`tomllib`）
"""
from __future__ import annotations

import argparse
import contextlib
import importlib.machinery
import importlib.util
import io
import os
import re
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock

CLI = Path(__file__).resolve().parents[1] / "llm-wiki" / "cli" / "llmwiki"
SKILL_MD = CLI.parents[1] / "SKILL.md"
AGENT_MD = CLI.parents[1] / "AGENT.md"
TEMPLATE_MD = CLI.parents[1] / "TEMPLATE.md"
ROOT_MD = CLI.parents[2] / "llm-wiki.md"


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
            with self.assertRaises(SystemExit), contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
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


# ─────────────── M9 · find_root 分轮定位 ───────────────
class TestFindRoot(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        (self.root / "mkdocs.yml").write_text("site_name: t\n", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_embedded_repo_with_git_does_not_win(self):
        embedded = self.root / "vendor" / "sub"
        (embedded / ".git").mkdir(parents=True)
        self.assertEqual(wiki.find_root(embedded), self.root,
                         "monorepo 内嵌小仓（有 .git 无配置）不得盖过外层站点配置")

    def test_config_above_beats_nearer_git(self):
        (self.root / ".llm-wiki.toml").write_text("[site]\n", encoding="utf-8")
        near = self.root / "a" / "b"
        (near / ".git").mkdir(parents=True)
        self.assertEqual(wiki.find_root(near), self.root)

    def test_nearer_config_wins(self):
        (self.root / ".llm-wiki.toml").write_text("[site]\n", encoding="utf-8")
        near = self.root / "a"
        near.mkdir()
        (near / ".llm-wiki.toml").write_text("[site]\n", encoding="utf-8")
        self.assertEqual(wiki.find_root(near), near)

    def test_env_var(self):
        (self.root / "docs").mkdir()
        with mock.patch.dict(os.environ, {"LLMWIKI_ROOT": str(self.root / "docs")}):
            self.assertEqual(wiki._root_from_env(), (self.root / "docs").resolve())

    def test_env_var_missing_dir_dies(self):
        with mock.patch.dict(os.environ, {"LLMWIKI_ROOT": str(self.root / "nope")}):
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                wiki._root_from_env()

    def test_env_var_makes_main_skip_search(self):
        (self.root / "docs").mkdir()
        (self.root / "docs" / "a.md").write_text("# A\n", encoding="utf-8")
        with mock.patch.dict(os.environ, {"LLMWIKI_ROOT": str(self.root)}), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(wiki.main(["lint"]), 0)


# ─────────────── M8 · 两个假配置接线 ───────────────
class TestConfigWiring(Fixture):
    def test_theme_map_defaults_and_override(self):
        self.assertEqual(wiki._pdf_theme_map({}), wiki.PDF_THEME_MAP)
        merged = wiki._pdf_theme_map({"pdf.theme_map.monokai-warm": "light"})
        self.assertEqual(merged["monokai-warm"], "light")
        self.assertEqual(merged["dracula-soft"], "dark")

    def test_theme_map_survives_flatten(self):
        (self.root / ".llm-wiki.toml").write_text(
            '[pdf.theme_map]\n"monokai-warm" = "light"\n', encoding="utf-8")
        cfg = wiki.load_cfg(self.root)
        self.assertIn("pdf.theme_map.monokai-warm", cfg, "flatten 会把 pdf.theme_map 摊成前缀键")
        self.assertEqual(wiki._pdf_theme_map(cfg)["monokai-warm"], "light")

    def test_export_default_from_config(self):
        self.md("a.md", "# A\n")
        self.cfg["export.llms_txt"] = True
        code, _ = self.run_cli(wiki.cmd_export, Namespace(llms_txt=False, out=None))
        self.assertEqual(code, 0)
        self.assertTrue((self.root / "docs" / "llms.txt").exists())

    def test_export_off_by_default_is_noop(self):
        self.md("a.md", "# A\n")
        code, _ = self.run_cli(wiki.cmd_export, Namespace(llms_txt=False, out=None))
        self.assertEqual(code, 0)
        self.assertFalse((self.root / "docs" / "llms.txt").exists())


# ─────────────── M5 / M7 · 文档 ↔ 实现契约 ───────────────
class TestDocContract(unittest.TestCase):
    FORBIDDEN = ("跨页矛盾", "过时断言", "CLI 读配置的顺序", "只认这些声明值", "(级别, 说明)")

    def _subparsers(self) -> dict:
        ap = wiki.build_parser()
        sub = next(a for a in ap._actions if isinstance(a, argparse._SubParsersAction))
        return sub.choices

    def test_command_table_matches_parser(self):
        table = re.findall(r"^\|\s*`llmwiki\s+([a-z][a-z-]*)",
                           SKILL_MD.read_text(encoding="utf-8"), re.M)
        self.assertTrue(table, "SKILL.md §6 命令表解析失败")
        self.assertEqual(set(self._subparsers()), set(table))

    def test_documented_flags_exist(self):
        flags = {o for a in self._subparsers()["deploy"]._actions for o in a.option_strings}
        self.assertIn("--force", flags)
        flags = {o for a in self._subparsers()["nav"]._actions for o in a.option_strings}
        self.assertIn("--dry-run", flags)

    def test_template_documents_every_lint_key(self):
        text = TEMPLATE_MD.read_text(encoding="utf-8")
        for key in (k.split(".", 1)[1] for k in wiki.DEFAULTS if k.startswith("lint.")):
            self.assertRegex(text, rf"(?m)^{key}\s*=", f"TEMPLATE.md 未记录 lint.{key}")

    def test_no_stale_promises(self):
        blob = "\n".join(p.read_text(encoding="utf-8")
                         for p in (SKILL_MD, AGENT_MD, TEMPLATE_MD, ROOT_MD))
        for phrase in self.FORBIDDEN:
            self.assertNotIn(phrase, blob, f"文档残留已失真的表述：{phrase}")

    def test_root_doc_description_matches_skill_frontmatter(self):
        def desc(path: Path) -> str:
            m = re.search(r"(?m)^description:\s*(.+)$", path.read_text(encoding="utf-8"))
            assert m is not None
            return m.group(1).strip()
        self.assertEqual(desc(ROOT_MD), desc(SKILL_MD))


if __name__ == "__main__":
    unittest.main(verbosity=2)
