#!/usr/bin/env bash
# Shared reference-doc install. Sourced by install.sh AND scripts/upgrade.sh.
#
# These docs are the kit's own reference material, not user files: CLAUDE.md
# points at them by path, so a machine whose CLAUDE.md is current and whose
# docs are not has dangling pointers. They are copied wholesale, on install and
# on upgrade alike. Anything you want to keep across upgrades belongs somewhere
# other than ~/.claude/docs/.
#
# Requires the caller to have defined REPO_DIR, CLAUDE_HOME and log().

TOP_LEVEL_DOCS=(
    "philosophy.md"
    "workflow.md"
    "verification-standards.md"
    "prereqs.md"
    "corporate-tls.md"
    "memory-system.md"
    "tracker-system.md"
)

kit_copy_docs() {
    log "Copying kit reference docs into ${CLAUDE_HOME}/docs/..."
    local dst="${CLAUDE_HOME}/docs"
    mkdir -p "${dst}/tools"

    # Top-level guides (skip silently if any are missing from the kit)
    local f
    for f in "${TOP_LEVEL_DOCS[@]}"; do
        if [ -f "${REPO_DIR}/docs/${f}" ]; then
            cp "${REPO_DIR}/docs/${f}" "${dst}/${f}"
        fi
    done

    # Per-tool rationale docs (explicit glob, fails loudly if missing)
    cp "${REPO_DIR}/docs/tools/"*.md "${dst}/tools/"
    log "  Reference docs copied: ${#TOP_LEVEL_DOCS[@]} top-level + tools/"
}
