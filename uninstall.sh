#!/usr/bin/env bash
# claude-code-kit uninstaller — restores the latest backup of CLAUDE.md
# and settings.json. Idempotent: safe to run if no backups exist.
set -euo pipefail

CLAUDE_HOME="${HOME}/.claude"
BACKUP_ROOT="${CLAUDE_HOME}/backups"

log()  { printf '\033[1;34m[cck-uninstall]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[cck-uninstall]\033[0m %s\n' "$*" >&2; }

# Restoring is conditional on there being a backup; removing what the kit
# installed is not. An install onto a clean machine makes no backup at all, and
# an early exit here used to mean such a machine could never be uninstalled —
# the rules, docs and state files all stayed.
src=""
if [ -d "${BACKUP_ROOT}" ]; then
    # Most-recent backup directory (ISO timestamps sort lexicographically).
    # shellcheck disable=SC2012  # safe: names are ISO-8601 timestamps
    latest=$(ls -1 "${BACKUP_ROOT}" 2>/dev/null | sort | tail -n1)
    [ -n "${latest}" ] && src="${BACKUP_ROOT}/${latest}"
fi

if [ -n "${src}" ]; then
    log "Restoring from ${src}..."
else
    log "No backup to restore from; removing what the kit installed."
fi

for f in CLAUDE.md settings.json; do
    if [ -n "${src}" ] && [ -f "${src}/${f}" ]; then
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

# The kit's rule files and reference docs are the kit's, so leaving the kit
# means removing them — otherwise every future session keeps loading kit rules
# from a kit that is no longer installed. 00-user-overrides.md is yours and
# stays, along with anything else you put in rules/.
if [ -d "${CLAUDE_HOME}/rules" ]; then
    removed=0
    for f in "${CLAUDE_HOME}/rules/"*-kit-*.md; do
        [ -e "${f}" ] || continue
        rm -f "${f}"
        removed=$((removed + 1))
    done
    if [ "${removed}" -gt 0 ]; then
        log "  Removed ${removed} kit rule file(s) from rules/"
    fi
    # Only if nothing of yours is left in there.
    if rmdir "${CLAUDE_HOME}/rules" 2>/dev/null; then
        log "  Removed empty rules/"
    fi
fi

if [ -d "${CLAUDE_HOME}/docs" ]; then
    rm -rf "${CLAUDE_HOME:?}/docs"
    log "  Removed docs/"
fi

log "Done. Plugins remain installed; remove via 'claude plugin uninstall <name>' if desired."
