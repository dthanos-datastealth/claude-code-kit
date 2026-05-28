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

# Ship the kit's reference docs into ~/.claude/docs/ so CLAUDE.md
# can reference them at a stable, machine-local path. Without this
# step the docs only exist in the cloned kit repo, which Claude
# Code sessions can't reliably locate.
TOP_LEVEL_DOCS=(
    "philosophy.md"
    "workflow.md"
    "prereqs.md"
    "corporate-tls.md"
    "memory-system.md"
    "tracker-system.md"
)

copy_docs() {
    log "Copying kit reference docs into ${CLAUDE_HOME}/docs/..."
    local dst="${CLAUDE_HOME}/docs"
    mkdir -p "${dst}/tools"

    # Top-level guides (skip silently if any are missing from the kit)
    for f in "${TOP_LEVEL_DOCS[@]}"; do
        if [ -f "${REPO_DIR}/docs/${f}" ]; then
            cp "${REPO_DIR}/docs/${f}" "${dst}/${f}"
        fi
    done

    # Per-tool rationale docs (explicit glob, fails loudly if missing)
    cp "${REPO_DIR}/docs/tools/"*.md "${dst}/tools/"
    log "  Reference docs copied: ${#TOP_LEVEL_DOCS[@]} top-level + tools/"
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

MARKETPLACES=(
    "anthropics/claude-plugins-official"
    "dthanos-datastealth/hallbayes"
    "multica-ai/andrej-karpathy-skills"
    "JuliusBrussee/caveman"
    "Optimal-AI/optibot-skill"
)

register_marketplaces() {
    log "Registering plugin marketplaces..."
    for mp in "${MARKETPLACES[@]}"; do
        if claude plugin marketplace add "${mp}" 2>&1; then
            log "  + ${mp}"
        else
            # Retry once on network blip
            warn "  retry ${mp}"
            if ! claude plugin marketplace add "${mp}" 2>&1; then
                err "  failed: claude plugin marketplace add ${mp}"
                err "  Re-run manually after resolving network issue."
                return 1
            fi
        fi
    done
}

# Pre-warm npm cache for npx-based MCP servers (playwright, chrome-devtools,
# context7) so they don't fail on first MCP-server startup waiting for npm
# to download. Without this, a fresh Claude Code session shows those MCPs
# as ✘ failed for the first 30-60s after install while npx downloads in
# the background.
NPX_MCP_PACKAGES=(
    "@playwright/mcp@latest"
    "chrome-devtools-mcp@latest"
    "@upstash/context7-mcp"
)

prewarm_npx_mcps() {
    if ! command -v npx >/dev/null 2>&1; then
        warn "  npx not on PATH; skipping npx-MCP pre-warm (playwright,"
        warn "  chrome-devtools, context7 will cold-start on first session)"
        return 0
    fi
    log "Pre-warming npm cache for npx-based MCP servers (parallel)..."
    local pids=()
    for pkg in "${NPX_MCP_PACKAGES[@]}"; do
        (
            if npx -y "${pkg}" --version >/dev/null 2>&1; then
                log "  + ${pkg}"
            else
                warn "  ${pkg}: pre-warm failed (non-fatal)"
            fi
        ) &
        pids+=($!)
    done
    for pid in "${pids[@]}"; do
        wait "${pid}" || true
    done
    log "Pre-warm complete"
}

install_plugins() {
    log "Installing plugins (reads enabledPlugins from settings.json)..."
    local plugins
    plugins=$(python3 -c "
import json, sys
d = json.load(open('${CLAUDE_HOME}/settings.json'))
for k, v in (d.get('enabledPlugins') or {}).items():
    if v is True:
        print(k)
")
    while IFS= read -r plugin; do
        [ -z "${plugin}" ] && continue
        if claude plugin install "${plugin}" 2>&1; then
            log "  + ${plugin}"
        else
            warn "  retry ${plugin}"
            if ! claude plugin install "${plugin}" 2>&1; then
                err "  failed: claude plugin install ${plugin}"
                err "  Continuing; re-run install.sh later to retry."
            fi
        fi
    done <<< "${plugins}"
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
    copy_docs
    merge_settings
    install_memory_index
    register_marketplaces
    install_plugins
    prewarm_npx_mcps
    log "Done. Restart Claude Code. See ~/.claude/docs/workflow.md for next steps."
}

main "$@"
