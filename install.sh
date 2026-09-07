#!/usr/bin/env bash
# claude-code-kit installer — macOS + Linux.
# Idempotent. Reversible via uninstall.sh.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_HOME="${HOME}/.claude"

log()  { printf '\033[1;34m[cck]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[cck]\033[0m %s\n' "$*" >&2; }
err()  { printf '\033[1;31m[cck]\033[0m %s\n' "$*" >&2; }

# Shared backup / version-marker helpers (kit_backup_files, kit_write_version_marker,
# kit_cache_snapshot, kit_log_history). Used by install.sh AND scripts/upgrade.sh.
# shellcheck source=scripts/_kit_backup.sh
. "${REPO_DIR}/scripts/_kit_backup.sh"

# Directories a prerequisite installer commonly writes to. `curl ... | sh`
# installers export PATH for their own process only, so a tool installed in one
# shell invocation is invisible to a later, separate ./install.sh invocation
# even though it is on disk. When that happens, say where it is and how to fix
# it rather than reporting it missing.
#
# Override with CCK_PREREQ_SEARCH_DIRS (colon-separated) — the tests rely on
# this, because two of the defaults are not HOME-relative and would otherwise
# find the developer's own binaries.
: "${CCK_PREREQ_SEARCH_DIRS:=${HOME}/.local/bin:${HOME}/.cargo/bin:${HOME}/bin:${HOME}/.npm-global/bin:/opt/homebrew/bin:/usr/local/bin}"

# Echo the directory holding an executable $1, searching the list above.
find_off_path() {
    local tool="$1" dir
    local IFS=:
    for dir in ${CCK_PREREQ_SEARCH_DIRS}; do
        [ -n "${dir}" ] || continue
        if [ -x "${dir}/${tool}" ]; then
            printf '%s' "${dir}"
            return 0
        fi
    done
    return 1
}

require() {
    local tool="$1" found
    if ! command -v "$tool" >/dev/null 2>&1; then
        err "missing prerequisite: $tool"
        if found="$(find_off_path "$tool")"; then
            err "  Found it at ${found}/${tool}, but that directory is not on your PATH."
            err "  An installer that writes there exports PATH only for its own"
            err "  process, so this invocation cannot see it. Fix either way:"
            err "    export PATH=\"${found}:\$PATH\"   # this shell, then re-run"
            err "    or start a new login shell and re-run"
        else
            err "  Install it before re-running. See docs/prereqs.md."
        fi
        exit 1
    fi
}

backup_existing() {
    local bk
    bk="$(kit_backup_files)"
    if [ -n "${bk}" ]; then
        log "  Backed up CLAUDE.md + settings.json -> ${bk}"
    else
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
    "verification-standards.md"
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

# The marketplace list is derived from claude/settings.json's
# extraKnownMarketplaces rather than duplicated here — the same way
# install_plugins() derives from enabledPlugins. One source means the release
# channel (the per-entry "ref") is declared in exactly one file, and the array
# can no longer drift from the settings the installer writes.
marketplace_specs() {
    python3 -c "
import json
d = json.load(open('${REPO_DIR}/claude/settings.json'))
for name, entry in (d.get('extraKnownMarketplaces') or {}).items():
    src = entry.get('source') or {}
    if src.get('source') != 'github' or not src.get('repo'):
        raise SystemExit(f'unsupported marketplace source for {name}: {src!r}')
    # Add by the owner/repo shorthand, matching the declared 'github' source
    # kind. A https://…/repo.git URL is a DIFFERENT kind, and Claude Code
    # refuses an add whose source differs from the declaration for that name.
    # CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1 (exported below) is what keeps the
    # shorthand cloning over HTTPS instead of SSH on keyless boxes.
    spec = src['repo']
    if src.get('ref'):
        spec += '@' + src['ref']
    print(spec)
"
}

register_marketplaces() {
    log "Registering plugin marketplaces (reads extraKnownMarketplaces from claude/settings.json)..."
    export CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1
    local specs
    if ! specs="$(marketplace_specs)"; then
        err "  failed to derive the marketplace list from claude/settings.json"
        return 1
    fi
    while IFS= read -r mp; do
        [ -z "${mp}" ] && continue
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
    done <<< "${specs}"
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

write_version_marker() {
    log "Writing ~/.claude/.kit-version + cache snapshot..."
    # "" is the optional rollback target: a fresh install has none.
    kit_write_version_marker ""
    kit_cache_snapshot
    kit_log_history install
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
    write_version_marker
    log "Done. Restart Claude Code. See ~/.claude/docs/workflow.md for next steps."
}

main "$@"
