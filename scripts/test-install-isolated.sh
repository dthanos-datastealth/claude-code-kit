#!/usr/bin/env bash
# test-install-isolated.sh — run install.sh in an isolated $HOME and prove
# the real ~/.claude/ stayed untouched. Use this to dry-run the kit against
# the real `claude` CLI without clobbering your working config.
#
# Usage:
#   scripts/test-install-isolated.sh          # keep tempdir for inspection
#   scripts/test-install-isolated.sh --clean  # auto-clean tempdir on success
#   scripts/test-install-isolated.sh --help   # print this header
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_SH="${REPO_DIR}/install.sh"
REAL_CLAUDE_HOME="${HOME}/.claude"

CLEAN=0
for arg in "$@"; do
    case "$arg" in
        --clean) CLEAN=1 ;;
        -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
        *) echo "Unknown arg: $arg" >&2; exit 2 ;;
    esac
done

log()  { printf '\033[1;34m[cck-test]\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m[cck-test]\033[0m %s\n' "$*"; }
err()  { printf '\033[1;31m[cck-test]\033[0m %s\n' "$*" >&2; }

# Portable mtime: macOS uses stat -f, Linux uses stat -c.
# Returns the literal string "absent" when the file doesn't exist;
# leak-check below compares with == so "absent" == "absent" passes
# correctly when the user has no prior install.
file_mtime() {
    local f="$1"
    if [ ! -f "$f" ]; then
        echo "absent"
        return
    fi
    stat -f '%m' "$f" 2>/dev/null || stat -c '%Y' "$f"
}

REAL_CLAUDE_MD_BEFORE=$(file_mtime "${REAL_CLAUDE_HOME}/CLAUDE.md")
REAL_SETTINGS_BEFORE=$(file_mtime "${REAL_CLAUDE_HOME}/settings.json")
# ~/.claude.json is the MCP server config (sibling dot-file, NOT under
# ~/.claude/). HOME-override still isolates it, but track its mtime so
# this script's leak check catches a regression if a future kit change
# ever writes to that path outside of HOME-redirection.
REAL_CLAUDE_DOTJSON_BEFORE=$(file_mtime "${HOME}/.claude.json")
log "Captured real-HOME mtimes (will verify UNCHANGED after the test):"
log "  ~/.claude/CLAUDE.md     : ${REAL_CLAUDE_MD_BEFORE}"
log "  ~/.claude/settings.json : ${REAL_SETTINGS_BEFORE}"
log "  ~/.claude.json          : ${REAL_CLAUDE_DOTJSON_BEFORE}"

TEST_HOME=$(mktemp -d -t cck-test-XXXXXX)
log "Isolated HOME: ${TEST_HOME}"
log "Running install.sh in isolated HOME (real claude CLI, real plugin installs)..."

if HOME="${TEST_HOME}" "${INSTALL_SH}"; then
    ok "install.sh completed"
else
    rc=$?
    err "install.sh failed (exit ${rc})"
    err "  Tempdir kept at ${TEST_HOME} for diagnosis"
    exit "${rc}"
fi

log "Verifying isolated-HOME contents..."
for f in CLAUDE.md settings.json memory/MEMORY.md; do
    if [ -f "${TEST_HOME}/.claude/${f}" ]; then
        ok "  ${f} installed"
    else
        err "  ${f} MISSING"
        exit 1
    fi
done
if [ -d "${TEST_HOME}/.claude/docs/tools" ]; then
    ok "  docs/tools/ installed"
else
    err "  docs/tools/ MISSING"
    exit 1
fi

plugin_count=$(python3 -c "import json; d=json.load(open('${TEST_HOME}/.claude/settings.json')); print(len(d.get('enabledPlugins', {})))")
docs_count=$(find "${TEST_HOME}/.claude/docs/tools" -maxdepth 1 -type f -name '*.md' | wc -l | tr -d ' ')
ok "  ${plugin_count} plugins enabled; ${docs_count} per-tool docs shipped"

# Hardcoded-path lint: scan every installed plugin's .mcp.json for
# owner-specific absolute paths. Catches the failure mode where a
# plugin ships a .mcp.json that only works on the author's machine
# (e.g. /Users/<owner>/...). If any are found, the lint exits 1 and
# this test fails.
log "Scanning installed .mcp.json files for hardcoded owner-specific paths..."
if python3 "${REPO_DIR}/scripts/lint-mcp-hardcoded-paths.py" "${TEST_HOME}/.claude"; then
    ok "  No hardcoded paths in any installed plugin's .mcp.json"
else
    err "  Hardcoded-path lint failed (see output above)"
    err "  Tempdir kept at ${TEST_HOME} for diagnosis"
    exit 3
fi

log "Leak check: verifying real ~/.claude/ is untouched..."
REAL_CLAUDE_MD_AFTER=$(file_mtime "${REAL_CLAUDE_HOME}/CLAUDE.md")
REAL_SETTINGS_AFTER=$(file_mtime "${REAL_CLAUDE_HOME}/settings.json")
REAL_CLAUDE_DOTJSON_AFTER=$(file_mtime "${HOME}/.claude.json")
leak=0
if [ "${REAL_CLAUDE_MD_BEFORE}" != "${REAL_CLAUDE_MD_AFTER}" ]; then
    err "  LEAK: ~/.claude/CLAUDE.md mtime CHANGED (${REAL_CLAUDE_MD_BEFORE} -> ${REAL_CLAUDE_MD_AFTER})"
    leak=1
fi
if [ "${REAL_SETTINGS_BEFORE}" != "${REAL_SETTINGS_AFTER}" ]; then
    err "  LEAK: ~/.claude/settings.json mtime CHANGED (${REAL_SETTINGS_BEFORE} -> ${REAL_SETTINGS_AFTER})"
    leak=1
fi
if [ "${REAL_CLAUDE_DOTJSON_BEFORE}" != "${REAL_CLAUDE_DOTJSON_AFTER}" ]; then
    err "  LEAK: ~/.claude.json mtime CHANGED (${REAL_CLAUDE_DOTJSON_BEFORE} -> ${REAL_CLAUDE_DOTJSON_AFTER})"
    leak=1
fi
if [ "${leak}" -eq 1 ]; then
    err "ISOLATION FAILED — install.sh wrote to your real HOME. This is a kit bug; please file it."
    err "  Tempdir kept at ${TEST_HOME} for diagnosis"
    exit 2
fi
ok "  Real ~/.claude/CLAUDE.md, ~/.claude/settings.json, and ~/.claude.json mtimes UNCHANGED"

ok ""
ok "==============================================="
ok "ISOLATION TEST PASSED"
ok "  Isolated HOME : ${TEST_HOME}"
ok "  Plugins       : ${plugin_count}"
ok "  Per-tool docs : ${docs_count}"
ok "  Real HOME     : untouched"
ok "==============================================="

if [ "${CLEAN}" -eq 1 ]; then
    log "Cleaning up tempdir..."
    rm -rf "${TEST_HOME}"
    ok "  Removed ${TEST_HOME}"
else
    log "Tempdir kept for inspection (re-run with --clean to auto-remove):"
    log "  ls -la ${TEST_HOME}/.claude/"
    log "  HOME=${TEST_HOME} claude plugin list"
    log "  rm -rf ${TEST_HOME}     # clean up manually when done"
fi
