#!/usr/bin/env bash
# claude-code-kit installer — macOS + Linux.
# Idempotent. Reversible via uninstall.sh.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_HOME="${HOME}/.claude"

log()  { printf '\033[1;34m[cck]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[cck]\033[0m %s\n' "$*" >&2; }
err()  { printf '\033[1;31m[cck]\033[0m %s\n' "$*" >&2; }

require() {
    local tool="$1"
    if ! command -v "$tool" >/dev/null 2>&1; then
        err "missing prerequisite: $tool"
        err "  Install it before re-running. See docs/prereqs.md."
        exit 1
    fi
}

backup_existing() {
    local ts
    ts="$(date -u +'%Y-%m-%dT%H-%M-%SZ')"
    local backup_dir="${CLAUDE_HOME}/backups/${ts}"
    local backed_up_anything=0

    for f in CLAUDE.md settings.json; do
        if [ -f "${CLAUDE_HOME}/${f}" ]; then
            mkdir -p "${backup_dir}"
            cp "${CLAUDE_HOME}/${f}" "${backup_dir}/${f}"
            log "  Backed up ${f} -> ${backup_dir}/${f}"
            backed_up_anything=1
        fi
    done

    if [ "${backed_up_anything}" -eq 0 ]; then
        log "Backup: nothing to back up (fresh install)"
    fi
}

copy_templates() {
    log "Copying templates into ${CLAUDE_HOME}/..."
    mkdir -p "${CLAUDE_HOME}"
    cp "${REPO_DIR}/claude/CLAUDE.md" "${CLAUDE_HOME}/CLAUDE.md"
    log "  CLAUDE.md installed"
}

merge_settings() {
    log "Merging settings.json (preserving your env block)..."
    python3 "${REPO_DIR}/scripts/merge-settings.py" \
        "${REPO_DIR}/claude/settings.json" \
        "${CLAUDE_HOME}/settings.json"
    log "  settings.json merged"
}

install_memory_index() {
    local mem_dir="${CLAUDE_HOME}/memory"
    local mem_file="${mem_dir}/MEMORY.md"
    mkdir -p "${mem_dir}"
    if [ -f "${mem_file}" ]; then
        log "Memory: MEMORY.md already exists, leaving untouched"
    else
        cp "${REPO_DIR}/claude/memory/MEMORY.md" "${mem_file}"
        log "Memory: installed MEMORY.md template at ${mem_file}"
    fi
}

preflight() {
    log "Preflight: checking required tools..."
    require claude
    require git
    require gh
    require python3
    require uv
    log "Preflight: OK"
}

main() {
    preflight
    backup_existing
    copy_templates
    merge_settings
    install_memory_index
    # Subsequent steps added in later tasks.
}

main "$@"
