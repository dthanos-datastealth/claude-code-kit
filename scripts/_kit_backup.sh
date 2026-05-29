#!/usr/bin/env bash
# Shared backup + version-marker helpers used by install.sh AND scripts/upgrade.sh.
# Sourced by both; not meant to be executed directly.
#
# Requires the caller to have defined CLAUDE_HOME + (for kit_write_version_marker)
# REPO_DIR.

# Create timestamped backup of CLAUDE.md + settings.json under
# ~/.claude/backups/<ISO-timestamp>/. Echoes the backup directory path on
# success. No-op (echo nothing, return 0) if neither file exists.
kit_backup_files() {
    local ts bk_dir backed_up=0
    ts="$(date -u +'%Y-%m-%dT%H-%M-%SZ')"
    bk_dir="${CLAUDE_HOME}/backups/${ts}"
    for f in CLAUDE.md settings.json; do
        if [ -f "${CLAUDE_HOME}/${f}" ]; then
            mkdir -p "${bk_dir}"
            cp "${CLAUDE_HOME}/${f}" "${bk_dir}/${f}"
            backed_up=1
        fi
    done
    if [ "${backed_up}" -eq 1 ]; then
        echo "${bk_dir}"
    fi
}

# Write ~/.claude/.kit-version with SHAs of the currently-installed
# CLAUDE.md, settings.json, and the kit's manifest. Optionally accepts
# an extra "rolled_back_to" field via $1 (passed only by upgrade.sh
# rollback path).
kit_write_version_marker() {
    local rollback_target="${1:-}"
    local ts sha_md sha_settings sha_manifest
    ts="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    sha_md="$(shasum -a 256 "${CLAUDE_HOME}/CLAUDE.md" 2>/dev/null | awk '{print $1}')"
    sha_settings="$(shasum -a 256 "${CLAUDE_HOME}/settings.json" 2>/dev/null | awk '{print $1}')"
    sha_manifest="$(shasum -a 256 "${REPO_DIR}/claude/CLAUDE.md.manifest.json" 2>/dev/null | awk '{print $1}')"
    local extra=""
    if [ -n "${rollback_target}" ]; then
        extra=",\n  \"rolled_back_to\": \"${rollback_target}\""
    fi
    printf '{\n  "installed_at": "%s",\n  "manifest_sha256": "%s",\n  "claude_md_sha256": "%s",\n  "settings_sha256": "%s"%b\n}\n' \
        "${ts}" "${sha_manifest}" "${sha_md}" "${sha_settings}" "${extra}" > "${CLAUDE_HOME}/.kit-version"
}

# Snapshot the kit's CLAUDE.md into ~/.claude/.kit-cache/ for future
# 3-way merge in upgrade.sh.
kit_cache_snapshot() {
    mkdir -p "${CLAUDE_HOME}/.kit-cache"
    cp "${REPO_DIR}/claude/CLAUDE.md" "${CLAUDE_HOME}/.kit-cache/CLAUDE.md"
}

# Append a single-line JSON event to ~/.claude/.kit-version.history.jsonl.
# Usage: kit_log_history <event-name> [extra-key=value ...]
# Example: kit_log_history install
#          kit_log_history rollback "backup=$bk_id"
kit_log_history() {
    local event="$1"
    shift
    local ts extras=""
    ts="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    for kv in "$@"; do
        local k="${kv%%=*}" v="${kv#*=}"
        extras="${extras},\"${k}\":\"${v}\""
    done
    printf '{"event":"%s","when":"%s"%s}\n' "${event}" "${ts}" "${extras}" \
        >> "${CLAUDE_HOME}/.kit-version.history.jsonl"
}
