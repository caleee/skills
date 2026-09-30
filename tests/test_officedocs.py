#!/usr/bin/env python3
"""office-docs CLI 冒烟测试 —— stdlib `unittest`，零第三方依赖。

CLI 本体是没有 `.py` 后缀的单文件（`office-docs/cli/office-docs`），用 `SourceFileLoader` 载入。
fixture **程序化构造**（最小但 XML 良构的 pptx／xlsx），不依赖任何外部模板——CI 与本地都能跑。

覆盖要点：pptx 定点替换的保真性（只改目标条目）＋ 多 run 拒绝语义；`resize` 分派**可达**
（tenant 侧原是 `add-connector` 分支后的不可达死代码）；只读基线护栏的**配置化**（不再硬编码
`/report/template/`）；全局 flag 解析；xlsx md→xlsx 往返。

运行：`python3 -m unittest discover -s tests -v`（需 Python 3.11+，`tomllib`）
"""
from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

CLI = Path(__file__).resolve().parents[1] / "office-docs" / "cli" / "office-docs"


def _load_cli():
    loader = importlib.machinery.SourceFileLoader("office_docs_cli", str(CLI))
    spec = importlib.util.spec_from_loader("office_docs_cli", loader)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


od = _load_cli()

_NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
       'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
       'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
_DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'


def _sp(shape_id: int, runs: list[str], x_emu: int = 1270000, y_emu: int = 635000) -> str:
    body = "".join(f'<a:r><a:rPr lang="zh-CN"/><a:t>{t}</a:t></a:r>' for t in runs)
    return ('<p:sp><p:nvSpPr>'
            f'<p:cNvPr id="{shape_id}" name="Shape {shape_id}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x_emu}" y="{y_emu}"/>'
            '<a:ext cx="2540000" cy="1270000"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
            f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p>{body}</a:p></p:txBody></p:sp>')


def _write_deck(path: str, runs: list[str] | None = None) -> None:
    """最小可编辑 pptx：1 页 + 1 形状（+ 一个 layout，供 add-slide 用）。"""
    runs = runs or ["Hello"]
    slide = (_DECL + f'<p:sld {_NS}><p:cSld><p:spTree>'
             '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
             '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
             '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
             + _sp(2, runs) +
             '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')
    pres = (_DECL + f'<p:presentation {_NS}><p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst>'
            '<p:sldSz cx="9144000" cy="5143500"/></p:presentation>')
    pres_rels = (_DECL + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                 '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                 'relationships/slide" Target="slides/slide1.xml"/>'
                 '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                 'relationships/slideLayout" Target="slideLayouts/slideLayout1.xml"/></Relationships>')
    root_rels = (_DECL + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                 '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                 'relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>')
    layout = _DECL + f'<p:sldLayout {_NS}><p:cSld><p:spTree/></p:cSld></p:sldLayout>'
    ct = (_DECL + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-'
          'officedocument.presentationml.presentation.main+xml"/>'
          '<Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-'
          'officedocument.presentationml.slide+xml"/>'
          '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-'
          'officedocument.presentationml.slideLayout+xml"/></Types>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", root_rels)
        z.writestr("ppt/presentation.xml", pres)
        z.writestr("ppt/_rels/presentation.xml.rels", pres_rels)
        z.writestr("ppt/slides/slide1.xml", slide)
        z.writestr("ppt/slideLayouts/slideLayout1.xml", layout)


def _entries(path: str) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as z:
        return {i.filename: z.read(i.filename) for i in z.infolist()}


class Fixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name).resolve()
        self.deck = str(self.dir / "deck.pptx")
        _write_deck(self.deck)
        od.CFG["baseline"] = None          # 每个用例隔离：默认无护栏

    def tearDown(self):
        od.CFG["baseline"] = None
        self._tmp.cleanup()

    def run_cli(self, args: list[str]) -> tuple[int, str]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = od.dispatch(args, od.Context(False, False)) or 0
        return code, buf.getvalue()


# ─────────────────────── pptx · 结构 / 定点替换 ───────────────────────
class TestPptx(Fixture):
    def test_dump_lists_text_shape_in_pt(self):
        d = od.dump(self.deck)
        sh = d["slides"][0]["shapes"]
        self.assertEqual([x["ref"] for x in sh], ["slide1!sp[0]"])
        self.assertEqual(sh[0]["text"], "Hello")
        self.assertEqual(sh[0]["at"], {"x": 100, "y": 50, "w": 200, "h": 100})  # EMU/12700

    def test_find_locates_ref(self):
        self.assertEqual([h["ref"] for h in od.find(self.deck, "Hello")], ["slide1!sp[0]"])
        self.assertEqual(od.find(self.deck, "不在里面"), [])

    def test_set_changes_only_target_entry(self):
        before = _entries(self.deck)
        res = od.set_text(self.deck, "slide1!sp[0]", "世界")
        after = _entries(self.deck)
        self.assertEqual([n for n in before if before[n] != after[n]], ["ppt/slides/slide1.xml"])
        self.assertEqual(res["changed"], [{"run": 0, "old": "Hello", "new": "世界"}])
        self.assertEqual(od.dump(self.deck)["slides"][0]["shapes"][0]["text"], "世界")

    def test_set_writes_backup_and_wellformed(self):
        res = od.set_text(self.deck, "slide1!sp[0]", "改了")
        self.assertTrue((self.dir / "deck.bak.pptx").is_file())
        self.assertEqual(res["backup"], str(self.dir / "deck.bak.pptx"))
        self.assertEqual(od.check(self.deck), [])

    def test_set_multi_run_rejected_without_flag(self):
        _write_deck(self.deck, runs=["A", "B"])
        with self.assertRaises(od.PptxError):
            od.set_text(self.deck, "slide1!sp[0]", "X")
        # 显式 --merge 才合并
        od.set_text(self.deck, "slide1!sp[0]", "X", merge=True)
        self.assertEqual(od.dump(self.deck)["slides"][0]["shapes"][0]["text"], "X")

    def test_diff_reports_text_change(self):
        old = str(self.dir / "old.pptx")
        _write_deck(old)
        od.set_text(self.deck, "slide1!sp[0]", "新文本")
        ch = od.diff(old, self.deck)
        self.assertEqual(ch, [{"ref": "slide1!sp[0]", "old": "Hello", "new": "新文本"}])

    def test_resize_dispatch_reachable(self):
        """回归：tenant 侧 `resize` 曾是 add-connector 分支后的不可达死代码。"""
        out = str(self.dir / "r.pptx")
        code, _ = self.run_cli(["pptx", "resize", self.deck, "--at", "slide1!sp[0]",
                                "--size", "300,80", "--out", out])
        self.assertEqual(code, 0)
        at = od.dump(out)["slides"][0]["shapes"][0]["at"]
        self.assertEqual((at["w"], at["h"]), (300, 80))

    def test_add_slide_and_shape(self):
        code, _ = self.run_cli(["pptx", "add-slide", self.deck, "--out", self.deck])
        self.assertEqual(code, 0)
        self.assertEqual(od.slide_count(self.deck), 2)
        code, _ = self.run_cli(["pptx", "add-shape", self.deck, "--slide", "1",
                                "--at", "10,20", "--size", "100,30", "--text", "框图"])
        self.assertEqual(code, 0)
        self.assertIn("框图", [s["text"] for s in od.dump(self.deck)["slides"][0]["shapes"]])


# ─────────────────────── 只读基线护栏（配置化） ───────────────────────
class TestBaselineGuard(Fixture):
    def test_baseline_from_cfg_blocks_in_place(self):
        base = self.dir / "docs" / "report" / "template"
        base.mkdir(parents=True)
        tpl = str(base / "d.pptx")
        _write_deck(tpl)
        od.CFG["baseline"] = str(base.resolve())
        with self.assertRaises(od.PptxError):
            od.set_text(tpl, "slide1!sp[0]", "X")               # 就地 → 拒
        od.set_text(tpl, "slide1!sp[0]", "X", force=True)        # --force → 放行
        self.assertEqual(od.dump(tpl)["slides"][0]["shapes"][0]["text"], "X")

    def test_baseline_none_allows_in_place(self):
        od.CFG["baseline"] = None
        od.set_text(self.deck, "slide1!sp[0]", "X")             # 无护栏 → 放行
        self.assertEqual(od.check(self.deck), [])

    def test_load_baseline_precedence(self):
        (self.dir / ".office-docs.toml").write_text('[baseline]\ndir = "custom/tpl"\n', encoding="utf-8")
        # 默认（读 toml）→ 相对项目根
        self.assertEqual(od._load_baseline(self.dir, None), str((self.dir / "custom" / "tpl").resolve()))
        # CLI 覆盖 toml
        self.assertEqual(od._load_baseline(self.dir, "other"), str((self.dir / "other").resolve()))
        # 空串 ＝ 关闭护栏
        self.assertIsNone(od._load_baseline(self.dir, "-"))


# ─────────────────────── 全局 flag 解析 ───────────────────────
class TestGlobals(Fixture):
    def test_split_globals(self):
        root, base, js, dry, rest = od._split_globals(
            ["--root", "/x", "pptx", "dump", "f", "--json"])
        self.assertEqual((root, base, js, dry), ("/x", None, True, False))
        self.assertEqual(rest, ["pptx", "dump", "f"])

    def test_json_and_dryrun_anywhere(self):
        _, _, js, dry, rest = od._split_globals(["pptx", "set", "f", "--dry-run", "--json"])
        self.assertTrue(js and dry)
        self.assertEqual(rest, ["pptx", "set", "f"])

    def test_dispatch_unknown_domain_rc2(self):
        code, _ = self.run_cli(["nope"])
        self.assertEqual(code, 2)


# ─────────────────────── xlsx · 读 / md→xlsx ───────────────────────
class TestXlsx(Fixture):
    def test_from_md_roundtrip(self):
        md = self.dir / "t.md"
        md.write_text("| 名称 | 值 |\n| --- | --- |\n| 甲 | 1 |\n| 乙 | 2 |\n", encoding="utf-8")
        out = self.dir / "t.xlsx"
        code, _ = self.run_cli(["xlsx", "from-md", str(md), "--out", str(out)])
        self.assertEqual(code, 0)
        d = od.xlsx_dump(str(out))
        self.assertEqual(d["sheet"], "Sheet1")
        self.assertEqual([c["text"] for c in d["rows"][0]["cells"]], ["名称", "值"])
        self.assertEqual(d["rows"][1]["cells"][0]["text"], "甲")

    def test_from_md_refuses_overwrite(self):
        md = self.dir / "t.md"
        md.write_text("| a |\n| --- |\n| 1 |\n", encoding="utf-8")
        out = self.dir / "t.xlsx"
        od.write_table(str(out), ["a"], [["1"]])
        with self.assertRaises(od.XlsxError):
            od.write_table(str(out), ["a"], [["1"]])              # 目标已存在 → 拒
        od.write_table(str(out), ["a"], [["1"]], force=True)      # force 放行


class TestJsonFlag(Fixture):
    def test_dump_json_output(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            od.dispatch(["pptx", "dump", self.deck], od.Context(True, False))
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["slides"][0]["shapes"][0]["text"], "Hello")


if __name__ == "__main__":
    unittest.main()
