#!/usr/bin/env python3
"""skills 清单（`skills.json`）与安装脚本（`install.sh`）的回归测试。

- `skills.json` 是**派生**物：断言它与真源（各 `<name>.md` frontmatter ＋ `<name>/VERSION`）
  **逐字一致**——漂移即红（防止加 skill／改 description 忘了重生成）。
- 每个 skill 单元结构完整（`SKILL.md`／`AGENT.md`／`VERSION`，名合法、版本合法）。
- `install.sh`：`--list` 可用、能把 skill 软链进临时工程、遇到**实体副本**拒绝覆盖、支持 `--from-file`。

运行：`python3 -m unittest discover -s tests -v`
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "scripts" / "gen_skills_json.py"
INSTALL = ROOT / "install.sh"


def _load_gen():
    loader = importlib.machinery.SourceFileLoader("gen_skills_json", str(GEN))
    spec = importlib.util.spec_from_loader("gen_skills_json", loader)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


gen = _load_gen()


class TestManifest(unittest.TestCase):
    def test_skills_json_in_sync(self):
        expected = gen.render(gen.collect(ROOT))
        actual = (ROOT / "skills.json").read_text(encoding="utf-8")
        self.assertEqual(actual, expected,
                         "skills.json 与真源漂移——跑 `python3 scripts/gen_skills_json.py`")

    def test_every_skill_unit_complete(self):
        skills = gen.collect(ROOT)
        self.assertTrue(skills, "至少应发现一个 skill")
        for s in skills:
            d = ROOT / s["name"]
            for f in ("SKILL.md", "AGENT.md", "VERSION"):
                self.assertTrue((d / f).is_file(), f"{s['name']}/{f} 缺失")
            self.assertRegex(s["version"] or "", r"^\d+\.\d+\.\d+$", f"{s['name']} VERSION 非法")
            self.assertNotRegex(s["name"], r"[^a-zA-Z0-9_-]", f"{s['name']} 名含非法字符")

    def test_name_matches_dir(self):
        for s in gen.collect(ROOT):
            self.assertEqual(s["path"], f"{s['name']}/")


class TestInstallScript(unittest.TestCase):
    def test_list_runs(self):
        r = subprocess.run(["bash", str(INSTALL), "--list"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("office-docs", r.stdout)

    def test_links_into_project(self):
        with tempfile.TemporaryDirectory() as t:
            proj = Path(t)
            r = subprocess.run(["bash", str(INSTALL), str(proj), "office-docs"],
                               capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stderr)
            a = proj / ".agents/skills/office-docs"
            c = proj / ".claude/skills/office-docs"
            self.assertTrue(a.is_symlink())
            self.assertEqual(a.resolve(), (ROOT / "office-docs").resolve())
            self.assertTrue(c.is_symlink())
            self.assertIn("office-docs", (proj / ".agents/skills.lock").read_text(encoding="utf-8"))

    def test_refuses_entity_copy(self):
        with tempfile.TemporaryDirectory() as t:
            proj = Path(t)
            (proj / ".agents/skills/office-docs").mkdir(parents=True)   # 实体副本
            r = subprocess.run(["bash", str(INSTALL), str(proj), "office-docs"],
                               capture_output=True, text=True, encoding="utf-8")
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("不是软链", r.stderr)

    def test_from_file(self):
        with tempfile.TemporaryDirectory() as t:
            proj = Path(t)
            (proj / ".agents").mkdir()
            (proj / ".agents/skills.txt").write_text("# 注释\noffice-docs\n", encoding="utf-8")
            r = subprocess.run(["bash", str(INSTALL), str(proj)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue((proj / ".agents/skills/office-docs").is_symlink())

    def test_unknown_skill_dies(self):
        with tempfile.TemporaryDirectory() as t:
            r = subprocess.run(["bash", str(INSTALL), t, "no-such-skill"],
                               capture_output=True, text=True, encoding="utf-8")
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("本库无此 skill", r.stderr)


if __name__ == "__main__":
    unittest.main()
