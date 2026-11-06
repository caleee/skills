#!/usr/bin/env python3
"""md-bundle CLI 单测 —— stdlib `unittest`，零第三方依赖。

CLI 本体是没有 `.py` 后缀的单文件（`md-bundle/cli/md-bundle`），用 `SourceFileLoader` 载入。

覆盖的是**两次真实返工**：
  ① `relativize` 把属性等号吃掉（`href="./assets/` 子串替换成 `href"../assets/`），
     页面无样式但无报错 —— 这里锁「等号必须保留」，并锁 `check` 能报出来；
  ② VitePress 对正文 md 链接已生成 `./xx.html`，再相对化一次会变成 `../xx.html`（全站断链）
     —— 这里锁「`./` 不碰」。

运行：`python3 -m unittest discover -s tests -v`
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

CLI = Path(__file__).resolve().parents[1] / "md-bundle" / "cli" / "md-bundle"

_loader = importlib.machinery.SourceFileLoader("mdbundle", str(CLI))
_spec = importlib.util.spec_from_loader("mdbundle", _loader)
mdbundle = importlib.util.module_from_spec(_spec)
_loader.exec_module(mdbundle)


def _strip_utf8_flag(path: Path) -> None:
    """字节层清掉 UTF-8 标志（本地头 offset 6、中央目录 offset 8）。"""
    data = bytearray(path.read_bytes())
    for sig, off in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):
        idx = 0
        while (idx := data.find(sig, idx)) >= 0:
            flags = (data[idx + off] | (data[idx + off + 1] << 8)) & ~0x800
            data[idx + off] = flags & 0xFF
            data[idx + off + 1] = (flags >> 8) & 0xFF
            idx += 4
    path.write_bytes(data)


class RelativizeTest(unittest.TestCase):
    def test_absolute_asset_gets_depth_prefix(self):
        html = '<link rel="stylesheet" href="/assets/style.css">'
        self.assertEqual(mdbundle.relativize(html, 2),
                         '<link rel="stylesheet" href="../../assets/style.css">')

    def test_equals_sign_is_preserved(self):
        """等号绝不能丢——`href"…"` 会被浏览器当成未知属性，样式与脚本静默失效。"""
        out = mdbundle.relativize('<a href="./x.md">', 1)
        self.assertNotIn('href"', out)
        self.assertIn('href="', out)

    def test_relative_link_is_not_rewritten(self):
        """VitePress 已生成的 `./xx.html` 不得再变 `../xx.html`（全站断链的真实事故）。"""
        self.assertEqual(mdbundle.relativize('<a href="./05-组织与成员.html">', 1),
                         '<a href="./05-组织与成员.html">')

    def test_vitepress_parent_link_is_normalized(self):
        self.assertEqual(mdbundle.relativize('<a href="./../02-数据库设计/x.html">', 1),
                         '<a href="../02-数据库设计/x.html">')

    def test_site_root_keeps_trailing_slash(self):
        self.assertEqual(mdbundle.relativize('<a href="/">', 1), '<a href="../">')
        self.assertEqual(mdbundle.relativize('<a href="/">', 0), '<a href="./">')

    def test_external_and_anchor_untouched(self):
        html = '<a href="https://example.com/x">x</a><a href="#a">a</a>'
        self.assertEqual(mdbundle.relativize(html, 1), html)


class VerifyTest(unittest.TestCase):
    def test_malformed_attr_is_reported(self):
        with tempfile.TemporaryDirectory() as td:
            page = Path(td) / "a.html"
            page.write_text('<link href"assets/x.css">', encoding="utf-8")
            probs = mdbundle.html_problems(page.read_text(encoding="utf-8"), page, Path(td))
        self.assertTrue(any("缺等号" in p for p in probs), probs)

    def test_broken_relative_ref_is_reported(self):
        with tempfile.TemporaryDirectory() as td:
            page = Path(td) / "a.html"
            probs = mdbundle.html_problems('<a href="./nope.html">', page, Path(td))
            page.write_text("", encoding="utf-8")
        self.assertTrue(any("断链" in p for p in probs), probs)


class ZipTest(unittest.TestCase):
    def _tree(self, root: Path) -> None:
        (root / "01-设计文稿").mkdir(parents=True)
        (root / "00-交付说明.md").write_text("# 标题\n\n[同目录](./01-设计文稿/a.md)\n", encoding="utf-8")
        (root / "01-设计文稿/a.md").write_text("# A\n", encoding="utf-8")

    def test_pack_sets_utf8_flag_and_single_top(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "src"
            self._tree(src)
            out = Path(td) / "out.zip"
            count = mdbundle.zip_tree(src, out, "交付稿_2026-11-05")
            self.assertEqual(count, 2)
            with zipfile.ZipFile(out) as zf:
                infos = zf.infolist()
            tops = {i.filename.split("/")[0] for i in infos}
            self.assertEqual(tops, {"交付稿_2026-11-05"})
            for info in infos:
                if not info.filename.isascii():
                    self.assertTrue(info.flag_bits & 0x800, info.filename)

    def test_check_accepts_good_pack(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "src"
            self._tree(src)
            out = Path(td) / "good.zip"
            mdbundle.zip_tree(src, out, "交付稿")
            self.assertEqual(mdbundle.check_zip(out), [])

    def test_check_rejects_missing_utf8_flag(self):
        """Python 的 zipfile **会自动**给非 ASCII 名置 0x800，所以坏包只能在字节层造
        （外部工具产生的包未必带）——这条锁的是校验器真的在读 flag，而不是恒真。"""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "bad.zip"
            with zipfile.ZipFile(out, "w") as zf:
                zf.writestr(zipfile.ZipInfo("交付稿/00-说明.md"), "# x\n")
            _strip_utf8_flag(out)
            probs = mdbundle.check_zip(out)
        self.assertTrue(any("UTF-8" in p for p in probs), probs)

    def test_check_reports_broken_md_link(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "src"
            (src).mkdir()
            (src / "a.md").write_text("[缺](不存在.md)\n", encoding="utf-8")
            out = Path(td) / "broken.zip"
            mdbundle.zip_tree(src, out, "稿")
            probs = mdbundle.check_zip(out)
        self.assertTrue(any("断链" in p for p in probs), probs)


if __name__ == "__main__":
    unittest.main()
