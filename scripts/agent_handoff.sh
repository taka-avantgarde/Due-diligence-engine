#!/usr/bin/env bash
# agent_handoff.sh — Multi-Agent Order Ledger & Gate Orchestrator
# For Due Diligence Engine (ATLAS.md §2: Astra Ultra + Antigravity, then Antigravity only)
#
# SSOT: ATLAS.md
# Local state storage: .dde_handoff/ (gitignored)

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
HANDOFF_DIR="$ROOT/.dde_handoff"
ORDER_DIR="$HANDOFF_DIR/orders"
TASK_DIR="$HANDOFF_DIR/tasks"
RESULT_DIR="$HANDOFF_DIR/results"

TODAY="$(date +%Y-%m-%d)"
STAMP="$(date +%Y%m%d)"

# Initialize handoff directory and local gitignore
init_dirs() {
  mkdir -p "$ORDER_DIR" "$TASK_DIR" "$RESULT_DIR"
  if [ ! -f "$HANDOFF_DIR/.gitignore" ]; then
    printf '*\n' > "$HANDOFF_DIR/.gitignore"
  fi
}

die()  { printf '\033[31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }
warn() { printf '⚠️  %s\n' "$*" >&2; }
info() { printf '\033[36m%s\033[0m\n' "$*"; }
ok()   { printf '\033[32m✓ %s\033[0m\n' "$*"; }

is_agent() {
  case "${1:-}" in
    antigravity|gemini|human) return 0 ;;
    codex) [[ "$TODAY" < "2026-11-09" ]] ;;
    *) return 1 ;;
  esac
}

# ------------------------------------------------------------------ Frontmatter Helpers

fm_get() {
  local file="$1" key="$2"
  [ -f "$file" ] || return 1
  awk -v key="$key" '
    NR == 1 && $0 == "---" { inside = 1; next }
    inside && $0 == "---" { exit }
    inside && index($0, key ":") == 1 {
      sub("^" key ":[ \t]*", ""); print; exit
    }
  ' "$file"
}

fm_set() {
  local file="$1" key="$2" val="$3" tmp
  [ -f "$file" ] || die "File not found: $file"
  tmp="$(mktemp "${file}.tmp.XXXXXX")"
  awk -v key="$key" -v val="$val" '
    NR == 1 && $0 == "---" { inside = 1; print; next }
    inside && $0 == "---" {
      if (!done) { print key ": " val; done = 1 }
      inside = 0; print; next
    }
    inside {
      eq = index($0, ":")
      if (eq > 0) {
        k = substr($0, 1, eq - 1)
        if (k == key) { print key ": " val; done = 1; next }
      }
    }
    { print }
    END {
      if (!done) { print key ": " val }
    }
  ' "$file" > "$tmp"
  mv -f "$tmp" "$file"
}

validate_id() {
  [[ "${1:-}" =~ ^[A-Za-z0-9_-]+$ ]] || die "Invalid Order ID: ${1:-}"
}

require_state() {
  local file="$1" allowed="$2" current
  current="$(fm_get "$file" status)"
  case " $allowed " in
    *" $current "*) ;;
    *) die "Invalid transition from '$current'; expected: $allowed" ;;
  esac
}

order_file() {
  local id="$1"
  validate_id "$id"
  printf '%s/%s.md' "$ORDER_DIR" "$id"
}

task_file() {
  local id="$1"
  validate_id "$id"
  printf '%s/%s.md' "$TASK_DIR" "$id"
}

result_file() {
  local id="$1"
  validate_id "$id"
  printf '%s/%s.md' "$RESULT_DIR" "$id"
}

# ------------------------------------------------------------------ Core Verification Gate

cmd_check() {
  info "===> Running Verification Gates for Due Diligence Engine"
  cd "$ROOT"
  local exit_code=0
  local python_bin="python3"
  if [ -x "$ROOT/.venv/bin/python" ]; then
    python_bin="$ROOT/.venv/bin/python"
  fi

  # 1. Maintenance SSOT consistency check
  printf '\n[Gate 1/2] Checking SSOT Consistency (maintenance check --profile quick)...\n'
  if "$python_bin" -c "import due_diligence_engine.maintenance" 2>/dev/null; then
    if "$python_bin" -m due_diligence_engine.maintenance check --profile quick; then
      ok "Maintenance quick check passed."
    else
      warn "Maintenance quick check reported issues."
      exit_code=1
    fi
  else
    warn "due_diligence_engine.maintenance not available yet; falling back to zero-drift tests."
    if "$python_bin" -m pytest tests/test_zero_drift_invariants.py -q; then
      ok "Zero-drift invariant tests passed."
    else
      warn "Zero-drift invariant tests failed."
      exit_code=1
    fi
  fi

  # 2. Pytest suite
  printf '\n[Gate 2/2] Running Pytest Suite (pytest tests/ -q)...\n'
  if "$python_bin" -m pytest tests/ -q; then
    ok "Full test suite passed."
  else
    warn "Pytest suite failed."
    exit_code=1
  fi

  if [ "$exit_code" -eq 0 ]; then
    printf '\n\033[32m========================================\033[0m\n'
    ok "ALL VERIFICATION GATES PASSED (exit 0)"
    printf '\033[32m========================================\033[0m\n'
  else
    printf '\n\033[31m========================================\033[0m\n'
    die "VERIFICATION GATES FAILED"
  fi
  return "$exit_code"
}

# ------------------------------------------------------------------ Doctor Command

cmd_doctor() {
  info "===> Checking Due Diligence Engine Environment & Governance"
  local ok_count=0 ng_count=0

  chk() {
    local desc="$1" res="$2"
    if [ "$res" -eq 0 ]; then
      printf '  \033[32m✓\033[0m %s\n' "$desc"
      ok_count=$((ok_count + 1))
    else
      printf '  \033[31m✗\033[0m %s\n' "$desc"
      ng_count=$((ng_count + 1))
    fi
  }

  chk "ATLAS.md exists and is canonical SSOT" "$([ -f "$ROOT/ATLAS.md" ] && printf 0 || printf 1)"
  chk "AGENTS.md exists" "$([ -f "$ROOT/AGENTS.md" ] && printf 0 || printf 1)"
  chk ".gemini/settings.json exists and points to ATLAS.md" "$([ -f "$ROOT/.gemini/settings.json" ] && printf 0 || printf 1)"
  chk "Claude development agents disabled (ATLAS.md §2)" \
    "$(is_agent claude && printf 1 || printf 0)"

  chk ".agents/rules/00_ssot_invariants.md exists" "$([ -f "$ROOT/.agents/rules/00_ssot_invariants.md" ] && printf 0 || printf 1)"
  chk ".agents/rules/10_security_boundaries.md exists" "$([ -f "$ROOT/.agents/rules/10_security_boundaries.md" ] && printf 0 || printf 1)"
  chk ".agents/rules/20_pdf_typography.md exists" "$([ -f "$ROOT/.agents/rules/20_pdf_typography.md" ] && printf 0 || printf 1)"

  chk ".agents/skills/dde-audit exists" "$([ -f "$ROOT/.agents/skills/dde-audit/SKILL.md" ] && printf 0 || printf 1)"
  chk ".agents/skills/dde-consulting-report exists" "$([ -f "$ROOT/.agents/skills/dde-consulting-report/SKILL.md" ] && printf 0 || printf 1)"
  chk ".agents/skills/dde-dev-change exists" "$([ -f "$ROOT/.agents/skills/dde-dev-change/SKILL.md" ] && printf 0 || printf 1)"
  chk ".agents/skills/dde-dev-pdf-qa exists" "$([ -f "$ROOT/.agents/skills/dde-dev-pdf-qa/SKILL.md" ] && printf 0 || printf 1)"
  chk ".agents/skills/dde-dev-release exists" "$([ -f "$ROOT/.agents/skills/dde-dev-release/SKILL.md" ] && printf 0 || printf 1)"

  chk ".agents/hooks.json exists" "$([ -f "$ROOT/.agents/hooks.json" ] && printf 0 || printf 1)"
  chk "Python virtual environment (.venv) available" "$([ -d "$ROOT/.venv" ] && printf 0 || printf 1)"

  printf '\nSummary: %d OK / %d FAILED\n' "$ok_count" "$ng_count"
  [ "$ng_count" -eq 0 ]
}

# ------------------------------------------------------------------ Board Command

cmd_board() {
  init_dirs
  info "===> Agent Handoff Board (.dde_handoff/)"
  printf '\n%-28s | %-12s | %-12s | %s\n' "ORDER ID" "STATUS" "OWNER" "TITLE"
  printf '%s\n' "--------------------------------------------------------------------------------"

  local count=0
  for f in "$ORDER_DIR"/*.md; do
    [ -e "$f" ] || continue
    local id; id="$(basename "$f" .md)"
    local status; status="$(fm_get "$f" "status" || echo "unknown")"
    local owner; owner="$(fm_get "$f" "owner" || echo "-")"
    local title; title="$(fm_get "$f" "title" || echo "Untitled")"

    local color="\033[0m"
    case "$status" in
      ready) color="\033[36m" ;;
      in_progress) color="\033[33m" ;;
      done) color="\033[32m" ;;
      blocked) color="\033[31m" ;;
    esac

    printf '%-28s | %b%-12s\033[0m | %-12s | %s\n' "$id" "$color" "$status" "$owner" "$title"
    count=$((count + 1))
  done

  if [ "$count" -eq 0 ]; then
    printf '  (No active orders found. Create one with: ./scripts/agent_handoff.sh new <type> <slug>)\n'
  fi
  printf '\n'
}

# ------------------------------------------------------------------ Order Lifecycle Commands

cmd_new() {
  init_dirs
  local type="${1:-}" slug="${2:-}" title="${3:-}"
  case "$type" in
    feat|fix|chore|docs|refactor|perf|test) ;;
    *) die "Usage: agent_handoff.sh new <feat|fix|chore|docs|refactor|perf|test> <slug> [title]" ;;
  esac
  validate_id "$slug"
  [ -n "$title" ] || title="${type}: ${slug}"

  local id="${STAMP}_${type}-${slug}"
  local file; file="$(order_file "$id")"
  [ ! -f "$file" ] || die "Order already exists: $id"

  cat > "$file" <<EOF
---
id: $id
title: $title
type: $type
status: draft
owner: -
created: $TODAY
updated: $TODAY
verified: false
---

# Order: $title

## 0. Scope & Objectives
Describe the task and exact file boundaries.

## 1. Specifications & SSOT References
- Ref: ATLAS.md

## 2. Implementation Checklist
- [ ] Task item 1
- [ ] Task item 2

## 3. Acceptance Verification
- Run: ./scripts/agent_handoff.sh check
EOF

  ok "Created draft order: $id ($file)"
  info "Review and edit the order, then run: ./scripts/agent_handoff.sh ready $id"
}

cmd_ready() {
  init_dirs
  local id="${1:-}"
  [ -n "$id" ] || die "Usage: agent_handoff.sh ready <id>"
  local file; file="$(order_file "$id")"
  [ -f "$file" ] || die "Order not found: $id"
  require_state "$file" "draft blocked"

  fm_set "$file" "verified" "false"
  fm_set "$file" "verified_sha" ""
  fm_set "$file" "status" "ready"
  fm_set "$file" "updated" "$TODAY"
  ok "Order marked ready: $id"
  info "Dispatch with: ./scripts/agent_handoff.sh dispatch $id --to <antigravity|codex|human> (codex through 2026-11-08 only)"
}

cmd_dispatch() {
  init_dirs
  local id="${1:-}" tool=""
  shift || true
  while [ $# -gt 0 ]; do
    case "$1" in
      --to) tool="${2:-}"; shift 2 ;;
      *) die "Unknown option: $1" ;;
    esac
  done
  [ -n "$id" ] && [ -n "$tool" ] || die "Usage: agent_handoff.sh dispatch <id> --to <antigravity|codex|human>"
  is_agent "$tool" || die "Agent tool not permitted by ATLAS.md §2 on $TODAY: $tool"

  local file; file="$(order_file "$id")"
  [ -f "$file" ] || die "Order not found: $id"
  require_state "$file" "ready"

  printf '\n===== Dispatch Instructions for %s =====\n' "$tool"
  printf 'You are assigned order: %s\n' "$id"
  printf '1. Claim the order:\n   ./scripts/agent_handoff.sh claim %s --as %s\n' "$id" "$tool"
  printf '2. Read specifications in:\n   %s\n' "$file"
  printf '3. Implement only assigned scope and verify with:\n   ./scripts/agent_handoff.sh verify %s\n' "$id"
  printf '4. Complete order when exit 0:\n   ./scripts/agent_handoff.sh done %s\n' "$id"
  printf '========================================\n\n'
}

cmd_claim() {
  init_dirs
  local id="${1:-}" tool=""
  shift || true
  while [ $# -gt 0 ]; do
    case "$1" in
      --as) tool="${2:-}"; shift 2 ;;
      *) die "Unknown option: $1" ;;
    esac
  done
  [ -n "$id" ] && [ -n "$tool" ] || die "Usage: agent_handoff.sh claim <id> --as <agent>"
  is_agent "$tool" || die "Agent tool not permitted by ATLAS.md §2 on $TODAY: $tool"

  local file; file="$(order_file "$id")"
  [ -f "$file" ] || die "Order not found: $id"
  require_state "$file" "ready"

  fm_set "$file" "verified" "false"
  fm_set "$file" "verified_sha" ""
  fm_set "$file" "status" "in_progress"
  fm_set "$file" "owner" "$tool"
  fm_set "$file" "updated" "$TODAY"

  local tfile; tfile="$(task_file "$id")"
  if [ ! -f "$tfile" ]; then
    cat > "$tfile" <<EOF
# Task Log: $id
Claimed by: $tool on $TODAY
Status: in_progress

## Progress Entries
- $TODAY: Claimed order by $tool
EOF
  else
    printf -- '- %s: Claimed order by %s\n' "$TODAY" "$tool" >> "$tfile"
  fi

  ok "Order $id claimed by $tool (in_progress)"
}

cmd_verify() {
  init_dirs
  local id="${1:-}"
  [ -n "$id" ] || die "Usage: agent_handoff.sh verify <id>"
  local file; file="$(order_file "$id")"
  [ -f "$file" ] || die "Order not found: $id"
  require_state "$file" "in_progress"

  info "Verifying Order $id..."
  fm_set "$file" "verified" "false"
  fm_set "$file" "verified_sha" ""
  local checked_sha; checked_sha="$(git -C "$ROOT" rev-parse HEAD)"
  if (cmd_check) && [ "$checked_sha" = "$(git -C "$ROOT" rev-parse HEAD)" ]; then
    fm_set "$file" "verified_sha" "$checked_sha"
    fm_set "$file" "verified" "true"
    fm_set "$file" "updated" "$TODAY"
    ok "Verification PASSED for $id"
    return 0
  else
    fm_set "$file" "verified" "false"
    fm_set "$file" "updated" "$TODAY"
    die "Verification FAILED for $id"
  fi
}

cmd_done() {
  init_dirs
  local id="${1:-}"
  [ -n "$id" ] || die "Usage: agent_handoff.sh done <id>"
  local file; file="$(order_file "$id")"
  [ -f "$file" ] || die "Order not found: $id"
  require_state "$file" "in_progress"

  local verified; verified="$(fm_get "$file" "verified" || echo "false")"
  [ "$verified" = "true" ] || die "Run verify successfully before done"
  [ "$(fm_get "$file" verified_sha)" = "$(git -C "$ROOT" rev-parse HEAD)" ] || die "HEAD changed; run verify again"

  local rfile; rfile="$(result_file "$id")"
  if [ ! -f "$rfile" ]; then
    cat > "$rfile" <<EOF
# Result: $id
Date: $TODAY
Owner: $(fm_get "$file" "owner")
Status: completed

## Summary of Changes
- TODO: Describe the completed changes and remaining limitations.

## Verification Evidence
- TODO: Record verification commands, results, and risks.
EOF
  fi

  if grep -q 'TODO:' "$rfile"; then
    info "Fill the Result artifact, then run done again: $rfile"
    return 0
  fi

  fm_set "$file" "status" "done"
  fm_set "$file" "updated" "$TODAY"
  ok "Order $id marked DONE! (Result saved in $rfile)"
}

cmd_handback() {
  init_dirs
  local id="${1:-}" reason="${2:-}"
  [ -n "$id" ] && [ -n "$reason" ] || die "Usage: agent_handoff.sh handback <id> \"reason\""
  local file; file="$(order_file "$id")"
  [ -f "$file" ] || die "Order not found: $id"
  require_state "$file" "in_progress"

  fm_set "$file" "verified" "false"
  fm_set "$file" "verified_sha" ""
  fm_set "$file" "owner" "-"
  fm_set "$file" "status" "blocked"
  fm_set "$file" "updated" "$TODAY"

  local tfile; tfile="$(task_file "$id")"
  printf -- '- %s: **HANDBACK / BLOCKED**: %s\n' "$TODAY" "$reason" >> "$tfile"

  warn "Order $id handed back (status: blocked). Reason: $reason"
}

# ------------------------------------------------------------------ Usage & Dispatch

usage() {
  cat <<'USAGE'
agent_handoff.sh — Multi-Agent Order Ledger & Gate Orchestrator

Commands:
  check                         Run full verification gates (maintenance quick check + pytest)
  doctor                        Check repository setup, governance files, rules & skills
  board                         Display current order board
  new <type> <slug> [title]     Create a new draft order (feat|fix|chore|docs|refactor|test)
  ready <id>                    Mark an order as ready for dispatch
  dispatch <id> --to <tool>     Output execution prompt for specified agent
  claim <id> --as <tool>        Claim an order and transition to in_progress
  verify <id>                   Execute verification gates and record verification status
  done <id>                     Mark an order as completed and generate result artifact
  handback <id> "reason"        Halt execution and return order to orchestrator (status: blocked)

Supported Agents:
  Through 2026-11-08: codex (Astra Ultra, gpt-6-astra, xhigh)
                     + antigravity (Gemini 4 Argon, High)
  From 2026-11-09:    antigravity (Gemini 4 Argon, High) only
  human remains available for oversight. Claude development agents are not used.

SSOT Reference: ATLAS.md
USAGE
}

main() {
  local cmd="${1:-}"
  shift || true
  case "$cmd" in
    check)    cmd_check "$@" ;;
    doctor)   cmd_doctor "$@" ;;
    board)    cmd_board "$@" ;;
    new)      cmd_new "$@" ;;
    ready)    cmd_ready "$@" ;;
    dispatch) cmd_dispatch "$@" ;;
    claim)    cmd_claim "$@" ;;
    verify)   cmd_verify "$@" ;;
    done)     cmd_done "$@" ;;
    handback) cmd_handback "$@" ;;
    ""|-h|--help|help) usage ;;
    *) die "Unknown command: $cmd (run --help for usage)" ;;
  esac
}

main "$@"
