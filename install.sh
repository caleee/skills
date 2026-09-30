#!/usr/bin/env bash
# 把 skills 库的 skill 用 **软链** 装进工程——单一真源、即时生效
# （改库＝改所有已装工程；代价是工程 clone 不自举，故本脚本可随时重链补偿）。
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-python3}"
MANIFEST="$REPO/skills.json"

usage() {
  cat <<'EOF'
把 skills 库的 skill 软链进工程（单一真源、即时生效）。

用法：
  ./install.sh <工程根> [skill...]     显式安装（省略 skill 则读 <工程根>/.agents/skills.txt）
  ./install.sh <工程根> --from-file     强制读 <工程根>/.agents/skills.txt
  ./install.sh --list                   列出本库可用 skill

落点（幂等重链）：
  <工程>/.agents/skills/<skill>   → <本库>/<skill>
  <工程>/.claude/skills/<skill>   → ../../.agents/skills/<skill>   （Claude Code 兼容）
并写 <工程>/.agents/skills.lock（已链接 skill 的版本快照，供核对漂移）。
EOF
}

die() { echo "✗ $*" >&2; exit 1; }

# skills.json 是机器可读清单（由 scripts/gen_skills_json.py 生成）
_manifest() { "$PY" - "$MANIFEST" "$@" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))["skills"]
cmd = sys.argv[2] if len(sys.argv) > 2 else "list"
if cmd == "list":
    for s in data:
        print(f'  {s["name"]:<16} v{s["version"]}  {s["description"]}')
else:                                   # have / version <name>
    name = sys.argv[3]
    hit = next((s for s in data if s["name"] == name), None)
    if cmd == "have":
        sys.exit(0 if hit else 1)
    if cmd == "version":
        print(hit["version"] if hit else "?")
PY
}

link_one() {
  local proj="$1" name="$2" src="$REPO/$2" dst="$1/.agents/skills/$2"
  _manifest have "$name" || die "本库无此 skill：${name}（用 --list 看可用项）"
  # 已存在且**非软链**（实体副本）时不静默删除——留给人工迁移（回写归属要清楚）
  if [ -e "$dst" ] && [ ! -L "$dst" ]; then
    die "$dst 已存在且不是软链（实体副本）——请先手动移除或迁移；本工具不静默覆盖"
  fi
  ln -sfn "$src" "$dst"
  ln -sfn "../../.agents/skills/$name" "$proj/.claude/skills/$name"
  echo "  ✓ $name  →  $src"
}

main() {
  case "${1:-}" in
    ""|-h|--help) usage; exit 0 ;;
    --list|-l) echo "本库可用 skill（${REPO}）："; _manifest list; exit 0 ;;
  esac

  local proj="$1"; shift || true
  [ -d "$proj" ] || die "工程根不存在：$proj"
  proj="$(cd "$proj" && pwd)"
  mkdir -p "$proj/.agents/skills" "$proj/.claude/skills"

  local names=()
  if [ "$#" -gt 0 ] && [ "$1" != "--from-file" ]; then
    names=("$@")
  else
    local f="$proj/.agents/skills.txt"
    [ -f "$f" ] || die "缺 ${f}（每行一个 skill 名，'#' 起注释）；或直接 `install.sh <工程根> <skill>...`"
    while IFS= read -r line; do
      line="${line%%#*}"
      line="$(printf '%s' "$line" | tr -d '[:space:]')"
      [ -n "$line" ] && names+=("$line")
    done < "$f"
  fi
  [ "${#names[@]}" -gt 0 ] || die "未指定任何 skill"

  echo "链接到工程 $proj ："
  for n in "${names[@]}"; do link_one "$proj" "$n"; done

  {
    echo "# 由 skills 库 install.sh 生成——已链接 skill 的版本快照（供核对漂移）"
    echo "# 库：$REPO"
    for n in "${names[@]}"; do printf '%s %s\n' "$n" "$(_manifest version "$n")"; done
  } > "$proj/.agents/skills.lock"
  echo "✓ 已链接 ${#names[@]} 个 skill；快照写入 .agents/skills.lock"
}

main "$@"
