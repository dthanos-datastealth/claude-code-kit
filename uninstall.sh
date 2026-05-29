#!/usr/bin/env bash
# claude-code-kit uninstaller — restores the latest backup of CLAUDE.md
# and settings.json. Idempotent: safe to run if no backups exist.
set -euo pipefail

CLAUDE_HOME="${HOME}/.claude"
BACKUP_ROOT="${CLAUDE_HOME}/backups"

log()  { printf '\033[1;34m[cck-uninstall]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[cck-uninstall]\033[0m %s\n' "$*" >&2; }

if [ ! -d "${BACKUP_ROOT}" ]; then
    log "Nothing to restore (no backups directory at ${BACKUP_ROOT})"
    exit 0
fi

# Find the most-recent backup directory (ISO timestamps sort lexicographically).
# shellcheck disable=SC2012  # safe: backup dir names are ISO-8601 timestamps, no special chars
latest=$(ls -1 "${BACKUP_ROOT}" 2>/dev/null | sort | tail -n1)
if [ -z "${latest}" ]; then
    log "Nothing to restore (backups directory is empty)"
    exit 0
fi

src="${BACKUP_ROOT}/${latest}"
log "Restoring from ${src}..."

for f in CLAUDE.md settings.json; do
    if [ -f "${src}/${f}" ]; then
        cp "${src}/${f}" "${CLAUDE_HOME}/${f}"
        log "  Restored ${f}"
    fi
done

# Clean up kit state files (version marker, cache, conflicts) — these are
# kit-specific bookkeeping that must not survive an uninstall, otherwise a
# future fresh install would see stale markers and get confused.
for f in .kit-version .kit-version.history.jsonl; do
    if [ -f "${CLAUDE_HOME}/${f}" ]; then
        rm -f "${CLAUDE_HOME}/${f}"
        log "  Removed ${f}"
    fi
done
for d in .kit-cache .kit-conflicts; do
    if [ -d "${CLAUDE_HOME}/${d}" ]; then
        rm -rf "${CLAUDE_HOME:?}/${d}"
        log "  Removed ${d}/"
    fi
done

log "Done. Plugins remain installed; remove via 'claude plugin uninstall <name>' if desired."
