#!/usr/bin/env bash
# agent-doctor — 本机多 agent 能力自检（零依赖）
#
# 为什么本体是脚本而不是 skill：
#   自检的目的是发现"能力是否真的生效"，而 skill 本身也是一种能力 ——
#   skill 机制失效时，恰是最需要自检的时候。故本体零 agent 依赖，
#   人、cc、pi、codex、opencode 都能直接跑。
#
# 设计：读配置决定检查什么（通用逻辑），不写死本机包名/路径（私有配置在外部文件）。
#
# 用法：
#   doctor.sh              全部检查（人类可读）
#   doctor.sh --json       机器可读 JSON
#   doctor.sh --quiet      只输出 warn/fail
#   doctor.sh --online     额外探测 URL 型 MCP 连通性（联网）
#   doctor.sh --help
#
# 退出码：0 = 无 FAIL；1 = 存在 FAIL；2 = 用法错误
set -uo pipefail

VERSION="0.1.0"

# ── 契约路径（与 ~/.agents/install.sh 一致）─────────────────────────────────
AGENTS_SRC="$HOME/.agents/AGENTS.md"
BLOCK_BEGIN='<!-- >>> shared-agents:begin'
BLOCK_END='<!-- <<< shared-agents:end'
OC_JSON="$HOME/.config/opencode/opencode.json"
PI_SETTINGS="$HOME/.pi/agent/settings.json"
PI_NM="$HOME/.pi/agent/npm/node_modules"
PI_MCP="$HOME/.config/mcp/mcp.json"
CC_JSON="$HOME/.claude.json"
CC_SETTINGS="$HOME/.claude/settings.json"
CC_MCP_JSON="$HOME/.mcp.json"

MODE="human"; QUIET=0; ONLINE=0

# ── 结果收集 ─────────────────────────────────────────────────────────────────
declare -a R_CHK=() R_TGT=() R_ST=() R_DET=()
N_PASS=0; N_WARN=0; N_FAIL=0; N_INFO=0

rec() { # check target status detail
  R_CHK+=("$1"); R_TGT+=("$2"); R_ST+=("$3"); R_DET+=("$4")
  case "$3" in
    pass) N_PASS=$((N_PASS + 1)) ;;
    warn) N_WARN=$((N_WARN + 1)) ;;
    fail) N_FAIL=$((N_FAIL + 1)) ;;
    *)    N_INFO=$((N_INFO + 1)) ;;
  esac
}

has_jq() { command -v jq >/dev/null 2>&1; }
short()  { printf '%s' "${1/#$HOME/~}"; }
base()   { printf '%s' "${1##*/}"; }

CHK_NAMES_KEYS=(instructions pi-packages pi-tools mcp skills hooks secrets)
chk_name() {
  case "$1" in
    instructions) printf '全局指令分发（install.sh 产物）' ;;
    pi-packages)  printf 'pi 扩展加载（已安装 ≠ 已加载）' ;;
    pi-tools)     printf 'pi 内置工具启用情况' ;;
    mcp)          printf 'MCP server 有效性' ;;
    skills)       printf 'skills 软链完整性' ;;
    hooks)        printf 'hooks 脚本有效性' ;;
    secrets)      printf '明文密钥扫描' ;;
    *)            printf '%s' "$1" ;;
  esac
}
chk_no() {
  local i=0 k
  for k in "${CHK_NAMES_KEYS[@]}"; do
    i=$((i + 1)); [ "$k" = "$1" ] && { printf '%s' "$i"; return; }; done
  printf '?'
}

# ── [1/7] 全局指令分发 ───────────────────────────────────────────────────────
check_instructions() {
  local id=instructions

  # A 类：Claude Code —— 期望 @ 引用行
  local cc="$HOME/.claude/CLAUDE.md"
  if [ ! -f "$cc" ]; then
    rec "$id" "claude" info "未安装（无 $CC_SETTINGS 的参照文件）"
  elif grep -qxF "@$AGENTS_SRC" "$cc" 2>/dev/null || grep -qF "$BLOCK_BEGIN" "$cc" 2>/dev/null; then
    rec "$id" "claude" pass "$(short "$cc") 已接入真源"
  else
    rec "$id" "claude" fail "$(short "$cc") 既无 @ 引用行也无受管区块"
  fi

  # C 类：pi / Codex —— 期望受管区块；顺带查"死文本"残留
  local pair name file
  for pair in "pi:$HOME/.pi/agent/AGENTS.md" "codex:$HOME/.codex/AGENTS.md"; do
    name="${pair%%:*}"; file="${pair#*:}"
    if [ ! -f "$file" ]; then
      rec "$id" "$name" info "未安装（无 $(short "$file")）"
    elif grep -qF "$BLOCK_BEGIN" "$file" 2>/dev/null; then
      if grep -qxF "@$AGENTS_SRC" "$file" 2>/dev/null; then
        rec "$id" "$name" warn "受管区块 OK，但残留整行 @ 引用（死文本，pi 不解析）"
      else
        rec "$id" "$name" pass "含受管区块，无死文本"
      fi
    else
      rec "$id" "$name" fail "缺受管区块（跑 bash ~/.agents/install.sh）"
    fi
  done

  # B 类：opencode —— 期望 instructions 数组
  if [ ! -f "$OC_JSON" ]; then
    rec "$id" "opencode" info "未安装（无 $(short "$OC_JSON")）"
  elif ! has_jq; then
    rec "$id" "opencode" warn "无 jq，无法核对 instructions"
  elif jq -e --arg p "$AGENTS_SRC" '(.instructions // []) | index($p)' "$OC_JSON" >/dev/null 2>&1; then
    rec "$id" "opencode" pass "instructions 含真源"
  else
    rec "$id" "opencode" fail "instructions 未含真源（跑 bash ~/.agents/install.sh）"
  fi
}

# ── [2/7] pi 扩展加载 ────────────────────────────────────────────────────────
check_pi_packages() {
  local id=pi-packages
  [ -f "$PI_SETTINGS" ] || { rec "$id" "-" info "无 $(short "$PI_SETTINGS")"; return; }
  has_jq || { rec "$id" "-" warn "无 jq，跳过"; return; }

  local pkgs pkg name dir pj exts entry bad
  pkgs="$(jq -r '(.packages // [])[]? // empty' "$PI_SETTINGS" 2>/dev/null)"
  [ -n "$pkgs" ] || { rec "$id" "-" info "settings 未声明 packages"; return; }

  while IFS= read -r pkg; do
    [ -n "$pkg" ] || continue
    name="${pkg#npm:}"; name="${name#git:}"; name="${name##*:}"
    dir="$PI_NM/$name"
    if [ ! -d "$dir" ]; then
      case "$pkg" in
        npm:*) rec "$id" "$name" fail "未安装：${pkg}（目录不存在）" ;;
        *)     rec "$id" "$name" info "非 npm 源（${pkg}），目录未在 node_modules" ;;
      esac
      continue
    fi
    pj="$dir/package.json"
    if [ ! -f "$pj" ]; then rec "$id" "$name" warn "缺 package.json"; continue; fi

    exts="$(jq -r '(.pi.extensions // [])[]? // empty' "$pj" 2>/dev/null)"
    if [ -z "$exts" ]; then
      exts="$(jq -r '.main // empty' "$pj" 2>/dev/null)"
      [ -n "$exts" ] || { rec "$id" "$name" info "无 pi.extensions / main 字段"; continue; }
    fi

    bad=0
    while IFS= read -r entry; do
      [ -n "$entry" ] || continue
      if [ ! -e "$dir/$entry" ]; then
        rec "$id" "$name" fail "入口文件不存在：${entry}（已安装 ≠ 已加载）"
        bad=1
      fi
    done <<< "$exts"
    [ "$bad" = 0 ] && rec "$id" "$name" pass "入口存在：$(printf '%s' "$exts" | tr '\n' ' ' | sed 's/ *$//')"
  done <<< "$pkgs"
}

# ── [3/7] pi 内置工具 ────────────────────────────────────────────────────────
check_pi_tools() {
  local id=pi-tools
  [ -f "$PI_SETTINGS" ] || { rec "$id" "-" info "无 $(short "$PI_SETTINGS")"; return; }
  has_jq || { rec "$id" "-" warn "无 jq，跳过"; return; }

  local enabled; enabled="$(jq -r '(.defaultTools // [])[]? // empty' "$PI_SETTINGS" 2>/dev/null | tr '\n' ' ')"
  [ -n "$(printf '%s' "$enabled" | tr -d ' ')" ] || { rec "$id" "defaultTools" info "未配置（用 pi 默认 4 个）"; return; }

  local all="read bash edit write grep find ls" t missing=""
  case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) all="$all powershell" ;; esac
  for t in $all; do
    case " $enabled " in *" $t "*) ;; *) missing="$missing $t" ;; esac
  done
  if [ -n "$missing" ]; then
    rec "$id" "defaultTools" warn "未启用：$missing"
  else
    rec "$id" "defaultTools" pass "全部 8 个内置工具已启用"
  fi
}

# ── [4/7] MCP server 有效性 ──────────────────────────────────────────────────
check_one_mcp() { # id label json
  local id="$1" label="$2" cfg="$3" cmd url code
  cmd="$(printf '%s' "$cfg" | jq -r '.command // empty' 2>/dev/null)"
  url="$(printf '%s' "$cfg" | jq -r '.url // empty' 2>/dev/null)"

  if [ -n "$cmd" ]; then
    case "$cmd" in
      */*)
        if [ -x "$cmd" ]; then rec "$id" "$label" pass "可执行：$(short "$cmd")"
        else rec "$id" "$label" fail "不存在或不可执行：$(short "$cmd")"; fi ;;
      *)
        if command -v "$cmd" >/dev/null 2>&1; then rec "$id" "$label" pass "命令在 PATH：$cmd"
        else rec "$id" "$label" fail "命令不在 PATH：$cmd"; fi ;;
    esac
  elif [ -n "$url" ]; then
    if [ "$ONLINE" != 1 ]; then
      rec "$id" "$label" info "URL 型，加 --online 探测：$url"
    else
      code="$(curl -s -o /dev/null -m 4 -w '%{http_code}' "$url" 2>/dev/null || printf '000')"
      case "$code" in
        2*|3*|4*) rec "$id" "$label" pass "可达 HTTP ${code}：$url" ;;
        000)      rec "$id" "$label" fail "不可达：$url" ;;
        *)        rec "$id" "$label" warn "HTTP ${code}：$url" ;;
      esac
    fi
  else
    rec "$id" "$label" warn "配置既无 command 也无 url"
  fi
}

check_mcp() {
  local id=mcp n
  has_jq || { rec "$id" "-" warn "无 jq，跳过"; return; }

  if [ -f "$PI_MCP" ]; then
    while IFS= read -r n; do
      [ -n "$n" ] || continue
      check_one_mcp "$id" "pi/$n" "$(jq -c --arg k "$n" '.mcpServers[$k]' "$PI_MCP")"
    done <<< "$(jq -r '.mcpServers | keys[]?' "$PI_MCP" 2>/dev/null)"
  else
    rec "$id" "pi" info "无 $(short "$PI_MCP")"
  fi

  if [ -f "$CC_JSON" ]; then
    while IFS= read -r n; do
      [ -n "$n" ] || continue
      check_one_mcp "$id" "cc/$n" "$(jq -c --arg k "$n" '.mcpServers[$k]' "$CC_JSON")"
    done <<< "$(jq -r '.mcpServers | keys[]?' "$CC_JSON" 2>/dev/null)"
  fi
  if [ -f "$CC_MCP_JSON" ]; then
    while IFS= read -r n; do
      [ -n "$n" ] || continue
      check_one_mcp "$id" "cc(mcp.json)/$n" "$(jq -c --arg k "$n" '.mcpServers[$k]' "$CC_MCP_JSON")"
    done <<< "$(jq -r '.mcpServers | keys[]?' "$CC_MCP_JSON" 2>/dev/null)"
  fi
}

# ── [5/7] skills 软链完整性 ──────────────────────────────────────────────────
check_skills() {
  local id=skills d broken cnt total
  for d in "$HOME/.agents/skills" "$HOME/.pi/agent/skills" "$HOME/.claude/skills" \
           "$HOME/.codebuddy/skills" "$HOME/.config/opencode/skills"; do
    if [ ! -d "$d" ]; then
      rec "$id" "$(short "$d")" info "未安装"
      continue
    fi
    total="$(find "$d" -maxdepth 1 -mindepth 1 2>/dev/null | wc -l | tr -d ' ')"
    broken="$(find -L "$d" -maxdepth 1 -type l 2>/dev/null)"
    if [ -n "$broken" ]; then
      cnt="$(printf '%s\n' "$broken" | wc -l | tr -d ' ')"
      rec "$id" "$(short "$d")" fail "$cnt 个断链（前 3：$(printf '%s\n' "$broken" | head -3 | while IFS= read -r b; do printf '%s ' "$(base "$b")"; done)）"
    else
      rec "$id" "$(short "$d")" pass "$total 个条目，无断链"
    fi
  done
}

# ── [6/7] hooks 脚本有效性 ───────────────────────────────────────────────────
check_hooks() {
  local id=hooks
  if [ ! -f "$CC_SETTINGS" ]; then rec "$id" "claude" info "无 $(short "$CC_SETTINGS")"; return; fi
  has_jq || { rec "$id" "claude" warn "无 jq，跳过"; return; }

  local cmds c n=0
  cmds="$(jq -r '(.hooks // {}) | to_entries[] | .value[]? | .hooks[]? | .command // empty' "$CC_SETTINGS" 2>/dev/null)"
  [ -n "$cmds" ] || { rec "$id" "claude" info "未配置 hooks"; return; }

  while IFS= read -r c; do
    [ -n "$c" ] || continue
    case "$c" in
      /*) n=$((n + 1))
          if [ -x "$c" ]; then rec "$id" "claude/$(base "$c")" pass "存在且可执行"
          elif [ -f "$c" ]; then rec "$id" "claude/$(base "$c")" fail "存在但不可执行（chmod +x）"
          else rec "$id" "claude/$(base "$c")" fail "脚本不存在：$(short "$c")"; fi ;;
      *)  rec "$id" "claude/inline" info "内联命令（非文件路径），跳过" ;;
    esac
  done <<< "$cmds"
}

# ── [7/7] 明文密钥扫描 ───────────────────────────────────────────────────────
check_secrets() {
  local id=secrets
  local pat='sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}'
  local placeholder='PROXY_MANAGED|sk-xxx|sk-XXX|<.*>|\.\.\.|REDACTED'

  # (a) 最高风险：文件名暗示可外发，却含真实凭据
  local s sc=0
  while IFS= read -r s; do
    [ -n "$s" ] && [ -f "$s" ] || continue
    if grep -qE "$pat" "$s" 2>/dev/null && ! grep -qE "$placeholder" "$s" 2>/dev/null; then
      rec "$id" "$(short "$s")" fail "文件名暗示可分享，却含真实凭据 → 分享前必脱敏"
      sc=1
    fi
  done <<< "$(find "$HOME/.claude" "$HOME/.agents" "$HOME/.config" "$HOME/.codex" "$HOME/.pi" -maxdepth 3 \
      \( -iname '*public*' -o -iname '*share*' -o -iname '*.template*' -o -iname '*.example*' \) 2>/dev/null | head -20)"
  [ "$sc" = 0 ] && rec "$id" "分享型文件" pass "未发现含真实凭据的分享型文件"

  # (b) 含凭据且被 git 跟踪 —— 会进版本历史（凭据文件本身不跟踪才是对的）
  local f dir top rel tracked incident=0
  for f in "$CC_SETTINGS" "$CC_JSON" "$CC_MCP_JSON" "$PI_SETTINGS" "$PI_MCP" \
           "$HOME/.pi/agent/auth.json" "$HOME/.codex/config.toml"; do
    [ -f "$f" ] || continue
    grep -qE "$pat" "$f" 2>/dev/null || continue
    grep -qE "$placeholder" "$f" 2>/dev/null && continue
    tracked=0
    dir="$(dirname "$f")"
    if git -C "$dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      top="$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null)"
      rel="${f#$top/}"
      git -C "$top" ls-files --error-unmatch "$rel" >/dev/null 2>&1 && tracked=1
    fi
    if [ "$tracked" = 1 ]; then
      rec "$id" "$(short "$f")" fail "含真实凭据且已被 git 跟踪 → 会进版本历史"
      incident=1
    else
      rec "$id" "$(short "$f")" info "含凭据但未被跟踪（符合预期）"
    fi
  done
  [ "$incident" = 0 ] && rec "$id" "版本跟踪" pass "含凭据的文件均未被 git 跟踪"
}

# ── 渲染 ─────────────────────────────────────────────────────────────────────
json_esc() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' | tr -d '\n'; }

render_human() {
  printf 'agent-doctor %s — 本机 agent 能力自检\n' "$VERSION"
  printf '主机 %s | 源 %s\n' "$(hostname)" "$(short "$AGENTS_SRC")"
  printf '%s\n' "────────────────────────────────────────────────────────────"
  local cur="" i st sym no=0
  for i in "${!R_CHK[@]}"; do
    if [ "${R_CHK[$i]}" != "$cur" ]; then
      cur="${R_CHK[$i]}"; no=$((no + 1))
      if [ "$QUIET" = 1 ]; then
        printf '\n[%s/7] %s\n' "$no" "$(chk_name "$cur")"
      else
        printf '\n[%s/7] %s\n' "$no" "$(chk_name "$cur")"
      fi
    fi
    st="${R_ST[$i]}"
    if [ "$QUIET" = 1 ]; then
      [ "$st" = pass ] && continue
      [ "$st" = info ] && continue
    fi
    case "$st" in
      pass) sym='✓' ;; warn) sym='!' ;; fail) sym='✗' ;; *) sym='·' ;;
    esac
    printf '  %s %-30s %s\n' "$sym" "${R_TGT[$i]}" "${R_DET[$i]}"
  done
  printf '\n%s\n' "────────────────────────────────────────────────────────────"
  printf 'PASS %d | WARN %d | FAIL %d\n' "$N_PASS" "$N_WARN" "$N_FAIL"
  if [ "$N_FAIL" -gt 0 ]; then
    printf '存在 FAIL：请看上方 ✗ 行；修复指引见 agent-doctor/AGENT.md\n'
    return 1
  fi
  return 0
}

render_json() {
  printf '{\n  "version": "%s",\n  "host": "%s",\n  "summary": {"pass": %d, "warn": %d, "fail": %d},\n  "findings": [\n' \
    "$VERSION" "$(json_esc "$(hostname)")" "$N_PASS" "$N_WARN" "$N_FAIL"
  local i last=$(( ${#R_CHK[@]} - 1 ))
  for i in "${!R_CHK[@]}"; do
    printf '    {"check": "%s", "target": "%s", "status": "%s", "detail": "%s"}%s\n' \
      "$(json_esc "${R_CHK[$i]}")" "$(json_esc "${R_TGT[$i]}")" "${R_ST[$i]}" "$(json_esc "${R_DET[$i]}")" \
      "$([ "$i" -lt "$last" ] && printf ',' || printf '')"
  done
  printf '  ]\n}\n'
}

usage() {
  sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
}

# ── 主流程 ───────────────────────────────────────────────────────────────────
main() {
  while [ $# -gt 0 ]; do
    case "$1" in
      --json)   MODE="json" ;;
      --quiet)  QUIET=1 ;;
      --online) ONLINE=1 ;;
      --help|-h) usage; return 0 ;;
      *) printf '未知参数：%s\n' "$1" >&2; usage >&2; return 2 ;;
    esac
    shift
  done

  check_instructions
  check_pi_packages
  check_pi_tools
  check_mcp
  check_skills
  check_hooks
  check_secrets

  if [ "$MODE" = "json" ]; then
    render_json
    [ "$N_FAIL" -gt 0 ] && return 1 || return 0
  fi
  render_human
}

main "$@"
