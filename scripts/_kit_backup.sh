#!/usr/bin/env bash
# Shared backup + version-marker helpers used by install.sh AND scripts/upgrade.sh.
# Sourced by both; not meant to be executed directly.
#
# Requires the caller to have defined CLAUDE_HOME + (for kit_write_version_marker)
# REPO_DIR.

# Create timestamped backup of CLAUDE.md, settings.json and rules/ under
# ~/.claude/backups/<ISO-timestamp>/. Echoes the backup directory path on
# success. No-op (echo nothing, return 0) if none of them exist.
#
# rules/ is in the set because that is where the kit's instructions live now.
# kit_copy_rules replaces all six kit files wholesale on every upgrade, so a
# backup without them cannot undo a release that ships a bad rule — and
# docs/upgrading.md offers rollback as the remedy for exactly that. The
# directory also holds 00-user-overrides.md and anything else the user wrote,
# which is the part they cannot recover from the repository.
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
    if [ -d "${CLAUDE_HOME}/rules" ] && [ -n "$(ls -A "${CLAUDE_HOME}/rules" 2>/dev/null)" ]; then
        mkdir -p "${bk_dir}/rules"
        cp "${CLAUDE_HOME}/rules/"*.md "${bk_dir}/rules/" 2>/dev/null || true
        backed_up=1
    fi
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
    local ts sha_md sha_settings sha_manifest channel commit
    ts="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    # `|| true` because of `set -o pipefail`: on the rules path there is no
    # ~/.claude/CLAUDE.md at all, shasum exits non-zero, and the whole pipeline
    # would take the installer down with it. A missing file means an empty sha,
    # which is what the marker should record.
    sha_md="$(shasum -a 256 "${CLAUDE_HOME}/CLAUDE.md" 2>/dev/null | awk '{print $1}' || true)"
    sha_settings="$(shasum -a 256 "${CLAUDE_HOME}/settings.json" 2>/dev/null | awk '{print $1}' || true)"
    sha_manifest="$(shasum -a 256 "${REPO_DIR}/claude/CLAUDE.md.manifest.json" 2>/dev/null | awk '{print $1}' || true)"
    # Which channel this install came from, so `:status` can answer it without
    # the reader inspecting the checkout. Tolerates a non-git checkout (tarball)
    # the same way the shasum calls above tolerate a missing file.
    channel="$(git -C "${REPO_DIR}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
    commit="$(git -C "${REPO_DIR}" rev-parse --short HEAD 2>/dev/null || echo unknown)"
    local extra=""
    if [ -n "${rollback_target}" ]; then
        extra=",\n  \"rolled_back_to\": \"${rollback_target}\""
    fi
    # Where the kit was installed FROM. The plugin's upgrade/rollback/status
    # skills drive scripts that live in the checkout, not in the plugin, and a
    # slash command runs in whatever project the user is in — so without this
    # they resolve `scripts/upgrade.sh` relative to the wrong directory and
    # fail with "No such file or directory". Recorded here because install.sh
    # is the only thing that knows the answer.
    printf '{\n  "installed_at": "%s",\n  "channel": "%s",\n  "commit": "%s",\n  "repo_dir": "%s",\n  "manifest_sha256": "%s",\n  "claude_md_sha256": "%s",\n  "settings_sha256": "%s"%b\n}\n' \
        "${ts}" "${channel}" "${commit}" "${REPO_DIR}" "${sha_manifest}" "${sha_md}" "${sha_settings}" "${extra}" > "${CLAUDE_HOME}/.kit-version"
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
