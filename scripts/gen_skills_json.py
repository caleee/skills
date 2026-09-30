#!/usr/bin/env python3
"""从各 `<name>.md` frontmatter ＋ `<name>/VERSION` 生成/校验仓根 `skills.json`。

**单一真源**：`name`/`description` 来自 `<name>.md` frontmatter，`version` 来自
`<name>/VERSION`；`skills.json` 是**派生**的机器可读清单（供脚本与 agent 快速查询，
不手工维护）。`--check` 在 CI／测试里拦漂移——生成物与真源不一致即红。

用法：
  python3 scripts/gen_skills_json.py           # 重写 skills.json
  python3 scripts/gen_skills_json.py --check    # 与现有比对，漂移则 exit 1
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = "各 <name>.md frontmatter + <name>/VERSION"


def _frontmatter(text: str) -> dict[str, str]:
    """取 YAML frontmatter 的顶层标量（行级提取，不引 YAML 依赖）。"""
    if not text.startswith("---"):
        return {}
    out: dict[str, str] = {}
    for ln in text.splitlines()[1:]:
        if ln.strip() == "---":
            break
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.+?)\s*$", ln)
        if m:
            out[m.group(1)] = m.group(2).strip().strip("\"'")
    return out


def collect(root: Path) -> list[dict]:
    """扫描「`<name>.md` ＋ 同名目录」的 skill 单元 → 清单（按名排序）。"""
    skills: list[dict] = []
    for md in sorted(root.glob("*.md")):
        d = root / md.stem
        if not d.is_dir():
            continue                              # 根文档（README/AGENTS/…）无同名目录，跳过
        fm = _frontmatter(md.read_text(encoding="utf-8"))
        if "name" not in fm or "description" not in fm:
            continue
        ver = d / "VERSION"
        skills.append({
            "name": fm["name"],
            "description": fm["description"],
            "version": ver.read_text(encoding="utf-8").strip() if ver.is_file() else None,
            "path": f"{md.stem}/",
        })
    return sorted(skills, key=lambda s: s["name"])


def render(skills: list[dict]) -> str:
    return json.dumps({"_generated_from": DOC, "skills": skills},
                      ensure_ascii=False, indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="生成/校验 skills.json")
    ap.add_argument("--check", action="store_true", help="与现有 skills.json 比对，漂移则 exit 1")
    a = ap.parse_args(argv)
    target = ROOT / "skills.json"
    skills = collect(ROOT)
    new = render(skills)
    if a.check:
        old = target.read_text(encoding="utf-8") if target.is_file() else ""
        if old != new:
            print("✗ skills.json 与真源（各 <name>.md / VERSION）不一致——跑 "
                  "`python3 scripts/gen_skills_json.py` 重生成", file=sys.stderr)
            return 1
        print(f"✓ skills.json 与真源一致（{len(skills)} 个 skill）")
        return 0
    target.write_text(new, encoding="utf-8")
    print(f"已写 {target}（{len(skills)} 个 skill）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
