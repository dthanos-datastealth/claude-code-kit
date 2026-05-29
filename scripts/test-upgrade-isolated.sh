#!/usr/bin/env bash
# test-upgrade-isolated.sh — exercise scripts/upgrade.sh against an isolated
# $HOME that's been seeded with: (a) a fresh kit install + (b) user-side
# mutations (custom plugin, custom marketplace, custom env var, custom
# CLAUDE.md section outside the manifest). Asserts upgrade preserves the
# user state while still applying any kit changes.
#
# Differs from test-install-isolated.sh: that script tests the install path
# from empty HOME; this one tests the upgrade path from a populated HOME
# with user mutations.
#
# Usage:
#   scripts/test-upgrade-isolated.sh          # keep tempdir for inspection
#   scripts/test-upgrade-isolated.sh --clean  # auto-clean tempdir on success
#   scripts/test-upgrade-isolated.sh --help   # print this header
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_SH="${REPO_DIR}/install.sh"
UPGRADE_SH="${REPO_DIR}/scripts/upgrade.sh"
REAL_CLAUDE_HOME="${HOME}/.claude"

CLEAN=0
for arg in "$@"; do
    case "$arg" in
        --clean) CLEAN=1 ;;
        -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
        *) echo "Unknown arg: $arg" >&2; exit 2 ;;
    esac
done

log()  { printf '\033[1;34m[cck-upgrade-test]\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m[cck-upgrade-test]\033[0m %s\n' "$*"; }
err()  { printf '\033[1;31m[cck-upgrade-test]\033[0m %s\n' "$*" >&2; }

file_mtime() {
    local f="$1"
    if [ ! -f "$f" ]; then echo "absent"; return; fi
    stat -f '%m' "$f" 2>/dev/null || stat -c '%Y' "$f"
}

REAL_CLAUDE_MD_BEFORE=$(file_mtime "${REAL_CLAUDE_HOME}/CLAUDE.md")
REAL_SETTINGS_BEFORE=$(file_mtime "${REAL_CLAUDE_HOME}/settings.json")
REAL_CLAUDE_DOTJSON_BEFORE=$(file_mtime "${HOME}/.claude.json")
log "Captured real-HOME mtimes (will verify UNCHANGED after the test):"
log "  ~/.claude/CLAUDE.md     : ${REAL_CLAUDE_MD_BEFORE}"
log "  ~/.claude/settings.json : ${REAL_SETTINGS_BEFORE}"
log "  ~/.claude.json          : ${REAL_CLAUDE_DOTJSON_BEFORE}"

TEST_HOME="$(mktemp -d -t cck-upgrade-test-XXXXXX)"
log "Isolated HOME: ${TEST_HOME}"

# Step 1 — fresh install into isolated HOME
log "Step 1: fresh install via install.sh into isolated HOME..."
HOME="${TEST_HOME}" bash "${INSTALL_SH}" >/dev/null 2>&1 || { err "install.sh failed"; exit 1; }
ok "  install complete"

# Verify .kit-version was written
if [ ! -f "${TEST_HOME}/.claude/.kit-version" ]; then
    err "  install did not write .kit-version"
    exit 1
fi
ok "  .kit-version present"

# Step 2 — simulate user mutations
log "Step 2: simulate user mutations (custom plugin, custom marketplace, custom env, custom CLAUDE.md section)..."
python3 - <<PY
import json, os
p = "${TEST_HOME}/.claude/settings.json"
d = json.load(open(p))
# Custom plugin user has manually enabled (kit doesn't ship it)
d.setdefault("enabledPlugins", {})["my-team-custom@my-team-marketplace"] = True
# Custom marketplace (kit doesn't list it)
d.setdefault("extraKnownMarketplaces", {})["my-team-marketplace"] = {
    "source": {"source": "github", "repo": "my-org/my-team-marketplace"}
}
# Custom env var
d.setdefault("env", {})["MY_TEAM_VAR"] = "team-specific-value"
# Custom top-level key the kit doesn't know about
d["myInternalKey"] = {"foo": "bar"}
json.dump(d, open(p, "w"), indent=2)
PY
# Custom CLAUDE.md section (outside the manifest — heading "### My Team Custom Tool")
printf '\n### My Team Custom Tool\nThis section is user-added and outside the kit manifest.\nUpgrade must preserve it.\n' >> "${TEST_HOME}/.claude/CLAUDE.md"
ok "  user mutations applied"

# Step 3 — run upgrade.sh --dry-run
log "Step 3: run scripts/upgrade.sh --dry-run..."
HOME="${TEST_HOME}" bash "${UPGRADE_SH}" --dry-run >/dev/null 2>&1 || { err "upgrade --dry-run failed"; exit 1; }
ok "  dry-run complete (no changes written)"

# Verify dry-run didn't mutate anything
if ! grep -q "my-team-custom@my-team-marketplace" "${TEST_HOME}/.claude/settings.json"; then
    err "  dry-run mutated settings.json (custom plugin lost!)"
    exit 1
fi
ok "  dry-run preserved user state"

# Step 4 — run upgrade.sh --apply
log "Step 4: run scripts/upgrade.sh --apply..."
HOME="${TEST_HOME}" bash "${UPGRADE_SH}" --apply >/dev/null 2>&1 || { err "upgrade --apply failed"; exit 1; }
ok "  upgrade applied"

# Step 5 — assert user state preserved
log "Step 5: assert all 4 user mutations survived the upgrade..."
if ! python3 - <<PY
import json, sys
d = json.load(open("${TEST_HOME}/.claude/settings.json"))
errs = []
if d.get("enabledPlugins", {}).get("my-team-custom@my-team-marketplace") is not True:
    errs.append("custom plugin lost")
if "my-team-marketplace" not in d.get("extraKnownMarketplaces", {}):
    errs.append("custom marketplace lost")
if d.get("env", {}).get("MY_TEAM_VAR") != "team-specific-value":
    errs.append("custom env lost")
if d.get("myInternalKey") != {"foo": "bar"}:
    errs.append("custom top-level key lost")
if errs:
    print("USER-STATE LEAKS:", errs, file=sys.stderr)
    sys.exit(1)
PY
then err "  user state was destroyed by upgrade"; exit 1; fi
ok "  settings.json: all user state preserved"

# Check CLAUDE.md preserved the custom section
if ! grep -q "### My Team Custom Tool" "${TEST_HOME}/.claude/CLAUDE.md"; then
    err "  CLAUDE.md: user-added section was destroyed"
    exit 1
fi
ok "  CLAUDE.md: user-added section preserved"

# Step 6 — leak check (real HOME mtimes UNCHANGED)
log "Step 6: leak check — real ~/.claude/ must be untouched..."
REAL_CLAUDE_MD_AFTER=$(file_mtime "${REAL_CLAUDE_HOME}/CLAUDE.md")
REAL_SETTINGS_AFTER=$(file_mtime "${REAL_CLAUDE_HOME}/settings.json")
REAL_CLAUDE_DOTJSON_AFTER=$(file_mtime "${HOME}/.claude.json")
leaked=0
if [ "${REAL_CLAUDE_MD_AFTER}" != "${REAL_CLAUDE_MD_BEFORE}" ]; then
    err "  LEAK: ~/.claude/CLAUDE.md mtime changed (${REAL_CLAUDE_MD_BEFORE} → ${REAL_CLAUDE_MD_AFTER})"
    leaked=1
fi
if [ "${REAL_SETTINGS_AFTER}" != "${REAL_SETTINGS_BEFORE}" ]; then
    err "  LEAK: ~/.claude/settings.json mtime changed"
    leaked=1
fi
if [ "${REAL_CLAUDE_DOTJSON_AFTER}" != "${REAL_CLAUDE_DOTJSON_BEFORE}" ]; then
    err "  LEAK: ~/.claude.json mtime changed"
    leaked=1
fi
if [ "${leaked}" -ne 0 ]; then exit 2; fi
ok "  no leak — real ~/.claude/ untouched"

ok "ALL CHECKS PASSED"
log "Isolated HOME: ${TEST_HOME}"

if [ "${CLEAN}" -eq 1 ]; then
    rm -rf "${TEST_HOME}"
    log "Cleaned up tempdir."
else
    log "(Pass --clean to auto-remove on success.)"
fi
