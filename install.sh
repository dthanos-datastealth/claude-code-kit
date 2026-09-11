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
# Reference-doc install (TOP_LEVEL_DOCS, kit_copy_docs), shared with upgrade.sh.
# shellcheck source=scripts/_kit_docs.sh
. "${REPO_DIR}/scripts/_kit_docs.sh"
# Rule-file install (kit_copy_rules), shared with upgrade.sh.
# shellcheck source=scripts/_kit_rules.sh
. "${REPO_DIR}/scripts/_kit_rules.sh"
# Runtime env (kit_compute_path, kit_write_runtime_env), shared with upgrade.sh.
# shellcheck source=scripts/_kit_env.sh
. "${REPO_DIR}/scripts/_kit_env.sh"

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

# A prerequisite can be present and still be too old to use. `require` answers
# "is it on PATH"; this answers "is it the version the kit needs", which is a
# different question and the one that bit: the macOS system python3 is 3.9,
# preflight passed, and the security-guidance plugin then silently dropped its
# cross-file reviewer with "the hook is running on 3.9".
require_python_version() {
    local want_major="$1" want_minor="$2"
    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (${want_major}, ${want_minor}) else 1)" 2>/dev/null; then
        local have
        have="$(python3 --version 2>&1 || echo 'unknown')"
        err "python3 is too old: found ${have}, need ${want_major}.${want_minor} or newer"
        err "  The kit's lint scripts and test suite need ${want_major}.${want_minor}+, and"
        err "  plugins that shell out to python3 inherit whichever one is first"
        err "  on your PATH."
        err "  macOS: brew install python@3.12, then put its libexec dir first —"
        err "    export PATH=\"/opt/homebrew/opt/python@3.12/libexec/bin:\$PATH\""
        err "    (the formula installs python3.12 but does NOT link 'python3')"
        err "  See docs/prereqs.md section 4."
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

# The kit's instructions go to ONE place, never both. On a CLI that supports
# ~/.claude/rules they ship as rule files and CLAUDE.md is left alone, because
# it belongs to the user. Below the floor the directory is ignored, so the
# CLAUDE.md template is the only thing that reaches Claude at all.
copy_templates() {
    if kit_rules_supported; then
        log "Instructions: shipping rule files; leaving ${CLAUDE_HOME}/CLAUDE.md to you"
        mkdir -p "${CLAUDE_HOME}"
        kit_migrate_claude_md
        return 0
    fi
    warn "claude < ${KIT_RULES_MIN_VERSION}: ~/.claude/rules is not supported here,"
    warn "  so the kit installs its CLAUDE.md template instead."
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

# No missing-npx guard here: preflight requires npx and exits 1 long before
# this runs, so a guard would be unreachable — and an unreachable guard is
# worse than none, because it documents a fallback that cannot happen.
prewarm_npx_mcps() {
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
    # Derived from KIT_RUNTIME_TOOLS in scripts/_kit_env.sh rather than
    # repeated here. The two lists were identical and had to be edited
    # together when node and npx were added, which is the argument for one of
    # them. What preflight checks and what gets recorded in the runtime PATH
    # are the same set by definition: a tool the kit needs at runtime is a
    # tool the install must find.
    local tool
    for tool in "${KIT_RUNTIME_TOOLS[@]}"; do
        require "${tool}"
    done
    require_python_version 3 11
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
    kit_copy_docs
    kit_copy_rules
    merge_settings
    kit_write_runtime_env
    install_memory_index
    register_marketplaces
    install_plugins
    prewarm_npx_mcps
    write_version_marker
    log "Done. Restart Claude Code. See ~/.claude/docs/workflow.md for next steps."
}

main "$@"
