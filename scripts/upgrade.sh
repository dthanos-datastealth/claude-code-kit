#!/usr/bin/env bash
# claude-code-kit upgrade orchestrator.
#
# Modes:
#   --dry-run                 Print proposed changes, do nothing.
#   --apply                   Backup + merge + write + verify (DEFAULT).
#   --rollback <backup-id>    Restore a specific timestamped backup.
#   --status                  Report current install state + drift + unresolved conflicts.
#
# Detection:
#   * If ~/.claude/.kit-version exists, runs intelligent merge.
#   * If absent, delegates to install.sh (clean install path).
#
# Preserves user state via:
#   * scripts/intelligent-settings-merge.py (UNION + user-wins per merge-policy.json)
#   * scripts/intelligent-claude-md-merge.py (heading-based 3-way per CLAUDE.md.manifest.json)
#   * scripts/install.sh backup pattern (~/.claude/backups/<ISO>)

set -euo pipefail

# ANSI
B='\033[1;34m'; Y='\033[1;33m'; R='\033[1;31m'; N='\033[0m'
log() { printf "${B}[cck-upgrade]${N} %s\n" "$*"; }
warn() { printf "${Y}[cck-upgrade]${N} %s\n" "$*" >&2; }
err()  { printf "${R}[cck-upgrade]${N} %s\n" "$*" >&2; }

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
VERSION_FILE="${CLAUDE_HOME}/.kit-version"
KIT_CACHE_DIR="${CLAUDE_HOME}/.kit-cache"
CONFLICT_DIR="${CLAUDE_HOME}/.kit-conflicts"
HISTORY_LOG="${CLAUDE_HOME}/.kit-version.history.jsonl"

MERGER_SETTINGS="${REPO_DIR}/scripts/intelligent-settings-merge.py"
MERGER_CLAUDE_MD="${REPO_DIR}/scripts/intelligent-claude-md-merge.py"
POLICY="${REPO_DIR}/scripts/merge-policy.json"
MANIFEST="${REPO_DIR}/claude/CLAUDE.md.manifest.json"
KIT_CLAUDE_MD="${REPO_DIR}/claude/CLAUDE.md"
KIT_SETTINGS="${REPO_DIR}/claude/settings.json"

# shellcheck source=scripts/_kit_backup.sh
. "${REPO_DIR}/scripts/_kit_backup.sh"
# Reference-doc install (TOP_LEVEL_DOCS, kit_copy_docs), shared with install.sh.
# shellcheck source=scripts/_kit_docs.sh
. "${REPO_DIR}/scripts/_kit_docs.sh"
# Rule-file install (kit_copy_rules), shared with install.sh.
# shellcheck source=scripts/_kit_rules.sh
. "${REPO_DIR}/scripts/_kit_rules.sh"

MODE="apply"
ROLLBACK_TARGET=""

while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run)   MODE="dry-run"; shift ;;
        --apply)     MODE="apply"; shift ;;
        --status)    MODE="status"; shift ;;
        --rollback)
            MODE="rollback"
            ROLLBACK_TARGET="${2:-}"
            if [ -z "${ROLLBACK_TARGET}" ]; then
                err "--rollback requires a backup-id (directory name under ~/.claude/backups/)"
                exit 2
            fi
            shift 2
            ;;
        -h|--help)
            sed -n '2,18p' "$0" | sed 's/^#\s\?//'
            exit 0
            ;;
        *)
            err "unknown arg: $1"
            exit 2
            ;;
    esac
done

mkdir -p "${CLAUDE_HOME}"

# ---------- status ----------
if [ "${MODE}" = "status" ]; then
    if [ -f "${VERSION_FILE}" ]; then
        log "Installed kit version:"
        cat "${VERSION_FILE}"
    else
        log "No kit version marker — fresh install or pre-upgrade-tool era."
    fi
    log "Unresolved conflicts:"
    if [ -d "${CONFLICT_DIR}" ] && [ -n "$(ls -A "${CONFLICT_DIR}" 2>/dev/null || true)" ]; then
        ls "${CONFLICT_DIR}"
    else
        log "  (none)"
    fi
    log "Backups available:"
    if [ -d "${CLAUDE_HOME}/backups" ]; then
        # shellcheck disable=SC2012  # ls timestamp ordering by name is safe for our ISO format
        ls -1 "${CLAUDE_HOME}/backups" 2>/dev/null | head -20 || true
    fi
    exit 0
fi

# ---------- rollback ----------
if [ "${MODE}" = "rollback" ]; then
    bk="${CLAUDE_HOME}/backups/${ROLLBACK_TARGET}"
    if [ ! -d "${bk}" ]; then
        err "backup not found: ${bk}"
        exit 2
    fi
    log "Restoring from backup: ${bk}"
    for f in CLAUDE.md settings.json; do
        if [ -f "${bk}/${f}" ]; then
            cp "${bk}/${f}" "${CLAUDE_HOME}/${f}"
            log "  restored: ${f}"
        fi
    done
    # Update .kit-version to reflect restored state (SHAs of the restored files,
    # not the SHAs of the kit's current CLAUDE.md/settings.json template). Lets
    # `:status` correctly report no drift after rollback.
    if [ -f "${CLAUDE_HOME}/CLAUDE.md" ] && [ -f "${CLAUDE_HOME}/settings.json" ]; then
        kit_write_version_marker "${ROLLBACK_TARGET}"
        log "  .kit-version updated to reflect rolled-back state"
    fi
    kit_log_history rollback "backup=${ROLLBACK_TARGET}"
    log "Rollback complete. History appended to ${HISTORY_LOG}."
    exit 0
fi

# ---------- backup (uses kit_backup_files from scripts/_kit_backup.sh) ----------
backup() {
    local bk
    bk="$(kit_backup_files)"
    if [ -z "${bk}" ]; then
        log "Nothing to back up (fresh install)."
        return 0
    fi
    log "Backup written: ${bk}"
    echo "${bk}"
}

# ---------- detect mode ----------
if [ ! -f "${VERSION_FILE}" ]; then
    log "No ~/.claude/.kit-version found — delegating to install.sh (fresh install path)."
    if [ "${MODE}" = "dry-run" ]; then
        log "(dry-run: would run install.sh)"
        exit 0
    fi
    exec bash "${REPO_DIR}/install.sh"
fi

log "Existing install detected: $(tr -d '\n' < "${VERSION_FILE}" 2>/dev/null || true)"
log "Mode: ${MODE}"

# ---------- upgrade ----------
if [ "${MODE}" = "apply" ]; then
    BK="$(backup)"
fi

# The legacy path, kept until every supported CLI is above the floor.
kit_merge_claude_md_legacy() {
log "CLAUDE.md merge..."
# Expanded below as ${prev_arg[@]+"${prev_arg[@]}"}: under `set -u`, bash 3.2 —
# still the system bash on macOS — treats "${prev_arg[@]}" on an EMPTY array as
# an unbound variable and aborts. That is the path taken by any install with no
# cached previous CLAUDE.md, so the upgrade failed outright rather than merging
# without a baseline.
prev_arg=()
if [ -f "${KIT_CACHE_DIR}/CLAUDE.md" ]; then
    prev_arg=(--prev "${KIT_CACHE_DIR}/CLAUDE.md")
fi
python3 "${MERGER_CLAUDE_MD}" "${KIT_CLAUDE_MD}" "${CLAUDE_HOME}/CLAUDE.md" \
    --manifest "${MANIFEST}" \
    --conflict-dir "${CONFLICT_DIR}" \
    --mode "${MODE}" \
    ${prev_arg[@]+"${prev_arg[@]}"} || rc=$?
rc=${rc:-0}
if [ "${rc}" -ne 0 ]; then
    err "CLAUDE.md merge failed (rc=${rc}). Aborting upgrade."
    exit "${rc}"
fi
}

# CLAUDE.md: on a CLI that supports ~/.claude/rules, the kit no longer writes
# this file at all. Migrate its sections out once, ship the rules, and skip the
# merge entirely. Only an older CLI still takes the merge path.
if kit_rules_supported; then
    if [ "${MODE}" = "apply" ]; then
        log "CLAUDE.md: moving kit sections into rules/ (one-time)..."
        kit_migrate_claude_md
    else
        log "(dry-run: would move any kit sections out of CLAUDE.md into rules/)"
        python3 "${REPO_DIR}/scripts/migrate-claude-md-to-rules.py" \
            "${CLAUDE_HOME}/CLAUDE.md" \
            --manifest "${MANIFEST}" --dry-run 2>/dev/null || true
    fi
else
    warn "claude < ${KIT_RULES_MIN_VERSION}: ~/.claude/rules is not supported here."
    warn "  Falling back to merging CLAUDE.md. Upgrade the CLI to get rule files."
    kit_merge_claude_md_legacy
fi

# settings.json merge
log "settings.json merge..."
# Run in both modes: dry-run writes nothing but reports what the kit would
# reclaim, which is the one path where an upgrade replaces a value the user set.
if [ "${MODE}" = "apply" ]; then
    python3 "${MERGER_SETTINGS}" "${KIT_SETTINGS}" "${CLAUDE_HOME}/settings.json" \
        --policy "${POLICY}"
else
    python3 "${MERGER_SETTINGS}" "${KIT_SETTINGS}" "${CLAUDE_HOME}/settings.json" \
        --policy "${POLICY}" --dry-run
fi

# Reference docs. CLAUDE.md points at these by path, so refreshing it without
# them leaves dangling pointers — which is what happened when copy_docs lived
# only in install.sh: an upgraded machine got a CLAUDE.md citing a doc it did
# not have, and kept the previous release's copy of every other one.
if [ "${MODE}" = "apply" ]; then
    kit_copy_docs
    kit_copy_rules
else
    log "(dry-run: would refresh ${CLAUDE_HOME}/docs/ and ${CLAUDE_HOME}/rules/)"
fi

# Update kit cache + version marker
if [ "${MODE}" = "apply" ]; then
    kit_cache_snapshot
    kit_write_version_marker ""   # no rollback target on a forward upgrade
    kit_log_history upgrade "backup=${BK##*/}"
    log "Upgrade complete. Version marker updated."
fi

if [ "${MODE}" = "dry-run" ]; then
    log "(dry-run: no files written)"
fi
