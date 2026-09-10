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
# kit_rules_supported: the harness must expect the same artifact install.sh
# just wrote, and that depends on the CLI version.
# shellcheck source=scripts/_kit_rules.sh
. "${REPO_DIR}/scripts/_kit_rules.sh"
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
# ~/.claude.json is a sibling dot-file, NOT under ~/.claude/. `claude mcp add`
# writes its `mcpServers` key, so a kit change could leak in here — but the
# file also holds the CLI's own session state (caches, counters, tips history,
# `pluginUsage`), which a Claude Code session running right now rewrites every
# few seconds. Measured: with no install running at all, the whole-file digest
# and `pluginUsage` both change inside 70 seconds while `mcpServers` holds
# still. So the file's mtime says nothing about whether install.sh touched it,
# and keying on it fails this harness for anyone running it from inside a live
# session. Digest `mcpServers` alone: it is the only key an install writes.
dotjson_mcp_servers() {
    python3 - "$1" <<'PY'
import hashlib, json, sys
try:
    with open(sys.argv[1], encoding="utf-8") as fh:
        d = json.load(fh)
except (OSError, ValueError):
    print("absent")
    raise SystemExit(0)
print(hashlib.sha256(
    json.dumps(d.get("mcpServers", {}), sort_keys=True, separators=(",", ":")).encode()
).hexdigest())
PY
}
REAL_CLAUDE_DOTJSON_BEFORE=$(dotjson_mcp_servers "${HOME}/.claude.json")
log "Captured real-HOME state (will verify UNCHANGED after the test):"
log "  ~/.claude/CLAUDE.md     : ${REAL_CLAUDE_MD_BEFORE}"
log "  ~/.claude/settings.json : ${REAL_SETTINGS_BEFORE}"
log "  ~/.claude.json          : mcpServers ${REAL_CLAUDE_DOTJSON_BEFORE:0:12}"

TEST_HOME=$(mktemp -d -t cck-test-XXXXXX)
# Every early exit below used to abandon the isolated HOME — measured at
# 961 MB, once per run, and the harness failed on every run. Keep it on
# failure only when it is worth inspecting, and say where it is.
cleanup() {
    local rc=$?
    if [ "${rc}" -ne 0 ]; then
        err "  Tempdir kept for diagnosis: ${TEST_HOME}"
        err "  Remove it with: rm -rf ${TEST_HOME}"
    elif [ "${CLEAN}" -eq 1 ]; then
        rm -rf "${TEST_HOME}"
    fi
}
trap cleanup EXIT
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
# Which instruction artifact to expect depends on the CLI this install ran
# against: rules/ from Claude Code 2.0.64 on, the CLAUDE.md template below it.
# Asserting CLAUDE.md unconditionally is what made this harness fail on every
# run against a current CLI — and fail here, before the leak check below.
if kit_rules_supported; then
    expect_flag="--expect-rules"
else
    expect_flag="--expect-claude-md"
fi
if python3 "${REPO_DIR}/scripts/verify-install.py" "${TEST_HOME}/.claude" "${expect_flag}"; then
    ok "  every expected artifact present (${expect_flag#--expect-})"
else
    err "  isolated HOME is missing expected artifacts (see above)"
    exit 1
fi

plugin_count=$(python3 -c "import json; d=json.load(open('${TEST_HOME}/.claude/settings.json')); print(len(d.get('enabledPlugins', {})))")
docs_count=$(find "${TEST_HOME}/.claude/docs/tools" -maxdepth 1 -type f -name '*.md' | wc -l | tr -d ' ')

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

# Skill-layout lint: a plugin whose skills are flat skills/<name>.md files
# instead of skills/<name>/SKILL.md ships skills Claude Code never discovers —
# silently, with no error. Only a populated cache can reveal this, which is why
# it runs here rather than in CI.
log "Scanning installed plugins for undiscoverable skill layouts..."
if python3 "${REPO_DIR}/scripts/lint-plugin-skill-layout.py" "${TEST_HOME}/.claude"; then
    ok "  Every installed plugin skill is at a discoverable path"
else
    err "  Skill-layout lint failed (see output above)"
    err "  Tempdir kept at ${TEST_HOME} for diagnosis"
    exit 4
fi

log "Leak check: verifying real ~/.claude/ is untouched..."
REAL_CLAUDE_MD_AFTER=$(file_mtime "${REAL_CLAUDE_HOME}/CLAUDE.md")
REAL_SETTINGS_AFTER=$(file_mtime "${REAL_CLAUDE_HOME}/settings.json")
REAL_CLAUDE_DOTJSON_AFTER=$(dotjson_mcp_servers "${HOME}/.claude.json")
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
    err "  LEAK: ~/.claude.json mcpServers CHANGED"
    err "        (${REAL_CLAUDE_DOTJSON_BEFORE} -> ${REAL_CLAUDE_DOTJSON_AFTER})"
    leak=1
fi
if [ "${leak}" -eq 1 ]; then
    err "ISOLATION FAILED — install.sh wrote to your real HOME. This is a kit bug; please file it."
    err "  Tempdir kept at ${TEST_HOME} for diagnosis"
    exit 2
fi
ok "  Real ~/.claude/CLAUDE.md + settings.json mtimes and ~/.claude.json mcpServers UNCHANGED"

ok ""
ok "==============================================="
ok "ISOLATION TEST PASSED"
ok "  Isolated HOME : ${TEST_HOME}"
ok "  Plugins       : ${plugin_count}"
ok "  Per-tool docs : ${docs_count}"
ok "  Real HOME     : untouched"
ok "==============================================="

# Removal on success is the EXIT trap's job, so that a failure anywhere above
# is cleaned up the same way rather than leaking the tempdir.
if [ "${CLEAN}" -eq 1 ]; then
    log "Cleaning up tempdir on exit..."
else
    log "Tempdir kept for inspection (re-run with --clean to auto-remove):"
    log "  ls -la ${TEST_HOME}/.claude/"
    log "  HOME=${TEST_HOME} claude plugin list"
    log "  rm -rf ${TEST_HOME}     # clean up manually when done"
fi
