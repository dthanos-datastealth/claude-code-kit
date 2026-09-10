#!/usr/bin/env bash
# Shared rule-file install. Sourced by install.sh AND scripts/upgrade.sh.
#
# Claude Code discovers ~/.claude/rules/*.md rather than merging them, so the
# kit owns these files outright and replaces them wholesale. That is the point:
# the kit no longer writes prose into a file the user also writes, so there is
# nothing to reconcile and nothing to get wrong.
#
# The one exception is 00-user-overrides.md, which belongs to the user. It is
# seeded once if absent and never written again.
#
# Requires the caller to have defined REPO_DIR, CLAUDE_HOME and log().

KIT_OVERRIDES="00-user-overrides.md"

kit_copy_rules() {
    log "Installing kit rules into ${CLAUDE_HOME}/rules/..."
    local dst="${CLAUDE_HOME}/rules"
    mkdir -p "${dst}"

    local src name count=0
    for src in "${REPO_DIR}/claude/rules/"*.md; do
        name="$(basename "${src}")"
        if [ "${name}" = "${KIT_OVERRIDES}" ]; then
            if [ ! -f "${dst}/${name}" ]; then
                cp "${src}" "${dst}/${name}"
                log "  seeded ${name} (yours; the kit will not overwrite it)"
            fi
            continue
        fi
        cp "${src}" "${dst}/${name}"
        count=$((count + 1))
    done
    log "  ${count} kit rule file(s) installed"
}
