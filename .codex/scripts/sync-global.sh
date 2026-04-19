#!/usr/bin/env bash
# sync-global.sh — Sync project Codex config + skills to global user scope
#
# Targets (per CODEX_GLOBAL_ARCHITECTURE.md):
#   ~/.codex/AGENTS.md          ← .codex/AGENTS.md
#   ~/.codex/agents/*.toml      ← .codex/agents/*.toml
#   ~/.codex/scripts/*          ← .codex/scripts/* (self-include)
#   ~/.agents/skills/           ← .agents/skills/
#
# Usage:
#   bash .codex/scripts/sync-global.sh           # sync all
#   bash .codex/scripts/sync-global.sh --dry-run # preview changes
#   bash .codex/scripts/sync-global.sh agents    # sync only agents
#   bash .codex/scripts/sync-global.sh skills    # sync only skills
#   bash .codex/scripts/sync-global.sh agents-md # sync only AGENTS.md

set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

ok()   { echo -e "${GREEN}  ✅ $*${RESET}"; }
warn() { echo -e "${YELLOW}  ⚠️  $*${RESET}"; }
fail() { echo -e "${RED}  ❌ $*${RESET}"; }
info() { echo -e "${CYAN}  ➜ $*${RESET}"; }
hdr()  { echo -e "\n${BOLD}$*${RESET}"; }

# ── Resolve repo root (script can be called from anywhere) ───────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PROJ_CODEX="$REPO_ROOT/.codex"
PROJ_SKILLS="$REPO_ROOT/.agents/skills"
GLOBAL_CODEX="$HOME/.codex"
GLOBAL_SKILLS="$HOME/.agents/skills"

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true
SCOPE="${1:-all}"
[[ "$SCOPE" == "--dry-run" ]] && SCOPE="${2:-all}"

# ── Helpers ──────────────────────────────────────────────────────────────────
do_cp() {
  local src="$1" dst="$2" label="$3"
  if $DRY_RUN; then
    info "[DRY-RUN] cp \"$src\" → \"$dst\""
    return 0
  fi
  if cp -r "$src" "$dst" 2>/dev/null; then
    ok "$label"
  else
    fail "$label (cp exited $?)"
    return 1
  fi
}

check_path_accessible() {
  local path="$1" name="$2"
  if ! timeout 5 ls "$path" > /dev/null 2>&1; then
    fail "$name unreachable (timeout / mount error): $path"
    return 1
  fi
}

md5_eq() {
  local a b
  a=$(md5sum "$1" 2>/dev/null | cut -d' ' -f1)
  b=$(md5sum "$2" 2>/dev/null | cut -d' ' -f1)
  [[ "$a" == "$b" ]]
}

# ── Ensure global dirs exist ─────────────────────────────────────────────────
mkdir -p "$GLOBAL_CODEX/agents"
mkdir -p "$GLOBAL_SKILLS"

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║    Codex Global Sync — vibecode-1            ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════════════╝${RESET}"
$DRY_RUN && warn "DRY-RUN mode — no files will be written"
echo ""

ERRORS=0

# ── 1. AGENTS.md ─────────────────────────────────────────────────────────────
sync_agents_md() {
  hdr "1. AGENTS.md → ~/.codex/AGENTS.md"
  local src="$PROJ_CODEX/AGENTS.md"
  local dst="$GLOBAL_CODEX/AGENTS.md"

  if [[ ! -f "$src" ]]; then
    fail "Source not found: $src"; ERRORS=$((ERRORS+1)); return
  fi

  if [[ -f "$dst" ]] && md5_eq "$src" "$dst"; then
    ok "AGENTS.md already up-to-date (md5 match)"
    return
  fi

  do_cp "$src" "$dst" "AGENTS.md synced" || ERRORS=$((ERRORS+1))

  # Verify after copy
  if ! $DRY_RUN && ! md5_eq "$src" "$dst"; then
    fail "AGENTS.md verify failed after copy"; ERRORS=$((ERRORS+1))
  fi
}

# ── 2. Custom agents ──────────────────────────────────────────────────────────
sync_agents() {
  hdr "2. .codex/agents/*.toml → ~/.codex/agents/"
  local src_dir="$PROJ_CODEX/agents"
  local dst_dir="$GLOBAL_CODEX/agents"

  if [[ ! -d "$src_dir" ]]; then
    fail "Source dir not found: $src_dir"; ERRORS=$((ERRORS+1)); return
  fi

  local count=0
  local stale=0

  while IFS= read -r -d '' src_file; do
    local name; name=$(basename "$src_file")
    local dst_file="$dst_dir/$name"

    if [[ -f "$dst_file" ]] && md5_eq "$src_file" "$dst_file"; then
      ok "$name (already up-to-date)"
    else
      do_cp "$src_file" "$dst_file" "$name" || ERRORS=$((ERRORS+1))
      stale=$((stale+1))
    fi
    count=$((count+1))
  done < <(find "$src_dir" -maxdepth 1 -name "*.toml" -print0 | sort -z)

  if [[ $count -eq 0 ]]; then
    warn "No .toml files found in $src_dir"
  else
    info "Processed $count agents ($stale updated)"
  fi
}

# ── 3. Scripts (self-sync) ────────────────────────────────────────────────────
sync_scripts() {
  hdr "3. .codex/scripts/* → ~/.codex/scripts/"
  local src_dir="$PROJ_CODEX/scripts"
  local dst_dir="$GLOBAL_CODEX/scripts"

  if [[ ! -d "$src_dir" ]]; then
    warn "No .codex/scripts/ dir found — skipping"; return
  fi

  mkdir -p "$dst_dir"
  do_cp "$src_dir/." "$dst_dir/" "scripts/" || ERRORS=$((ERRORS+1))
  # Make scripts executable
  $DRY_RUN || chmod +x "$dst_dir"/*.sh 2>/dev/null || true
}

# ── 4. Skills ─────────────────────────────────────────────────────────────────
sync_skills() {
  hdr "4. .agents/skills/ → ~/.agents/skills/"
  local src_dir="$PROJ_SKILLS"
  local dst_dir="$GLOBAL_SKILLS"

  if [[ ! -d "$src_dir" ]]; then
    fail "Source dir not found: $src_dir"; ERRORS=$((ERRORS+1)); return
  fi

  # Accessibility check (this path can be a slow/stale mount)
  info "Checking ${dst_dir} accessibility..."
  if ! check_path_accessible "$dst_dir" "~/.agents/skills"; then
    ERRORS=$((ERRORS+1)); return
  fi

  local count=0
  local stale=0

  for src_skill in "$src_dir"/*/; do
    [[ -d "$src_skill" ]] || continue
    local name; name=$(basename "$src_skill")
    local dst_skill="$dst_dir/$name"
    local src_skillmd="$src_skill/SKILL.md"
    local dst_skillmd="$dst_skill/SKILL.md"

    if [[ -d "$dst_skill" ]] && [[ -f "$dst_skillmd" ]] && md5_eq "$src_skillmd" "$dst_skillmd" 2>/dev/null; then
      ok "$name (up-to-date)"
    else
      if $DRY_RUN; then
        info "[DRY-RUN] update skill: $name"
      else
        do_cp "$src_skill" "$dst_dir/" "$name" || ERRORS=$((ERRORS+1))
      fi
      stale=$((stale+1))
    fi
    count=$((count+1))
  done

  if [[ $count -eq 0 ]]; then
    warn "No skills found in $src_dir"
  else
    info "Processed $count skills ($stale updated)"
  fi
}

# ── Dispatch by scope ─────────────────────────────────────────────────────────
case "$SCOPE" in
  agents-md)  sync_agents_md ;;
  agents)     sync_agents_md; sync_agents ;;
  skills)     sync_skills ;;
  scripts)    sync_scripts ;;
  all)
    sync_agents_md
    sync_agents
    sync_scripts
    sync_skills
    ;;
  *)
    echo "Usage: $0 [--dry-run] [all|agents-md|agents|skills|scripts]"
    exit 1
    ;;
esac

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}══════════════════════════════════════════════${RESET}"
if [[ $ERRORS -eq 0 ]]; then
  echo -e "${GREEN}${BOLD}  ✅ Sync completed successfully (0 errors)${RESET}"
else
  echo -e "${RED}${BOLD}  ❌ Sync completed with $ERRORS error(s) — check output above${RESET}"
fi
echo -e "${BOLD}══════════════════════════════════════════════${RESET}"
echo ""

exit $ERRORS
