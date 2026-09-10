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

# ~/.claude/rules/ landed in Claude Code 2.0.64 (10 Dec 2025). Below that the
# directory is ignored entirely, so shipping rules there would drop every kit
# instruction without erroring — the kit would look installed and be inert.
# When we cannot prove support, fall back to the CLAUDE.md merge.
KIT_RULES_MIN_VERSION="2.0.64"

kit_rules_supported() {
    local have
    have="$(claude --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
    [ -n "${have}" ] || return 1
    # sort -V so 2.0.100 beats 2.0.64; a lexical compare gets that backwards.
    [ "$(printf '%s\n%s\n' "${KIT_RULES_MIN_VERSION}" "${have}" \
        | sort -V | head -1)" = "${KIT_RULES_MIN_VERSION}" ]
}

# Move the kit's sections out of the user's CLAUDE.md, once. Exit 3 from the
# migration means there was nothing kit-owned left, which is the steady state.
kit_migrate_claude_md() {
    local target="${CLAUDE_HOME}/CLAUDE.md"
    [ -f "${target}" ] || return 0
    local rc=0
    python3 "${REPO_DIR}/scripts/migrate-claude-md-to-rules.py" "${target}" \
        --manifest "${REPO_DIR}/claude/CLAUDE.md.manifest.json" || rc=$?
    case "${rc}" in
        0) log "  moved the kit's sections out of CLAUDE.md into rules/" ;;
        3) : ;;
        *) err "  migration failed (rc=${rc}); leaving CLAUDE.md alone"; return 1 ;;
    esac
}

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
