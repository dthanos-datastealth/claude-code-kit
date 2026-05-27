#!/usr/bin/env bash
# Report drift between this kit's `claude/` content and the live `~/.claude/`.
# Exit 0 if no drift, 1 if any drift detected.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_HOME="${HOME}/.claude"

echo "=== CLAUDE.md diff ==="
if [ -f "${CLAUDE_HOME}/CLAUDE.md" ]; then
    if diff -u "${REPO_DIR}/claude/CLAUDE.md" "${CLAUDE_HOME}/CLAUDE.md"; then
        echo "(no diff)"
        claude_md_drift=0
    else
        claude_md_drift=1
    fi
else
    echo "(live ~/.claude/CLAUDE.md does not exist)"
    claude_md_drift=1
fi

echo
echo "=== settings.json structural delta ==="
if [ -f "${CLAUDE_HOME}/settings.json" ]; then
    if python3 "${REPO_DIR}/scripts/diff-settings.py" \
        "${REPO_DIR}/claude/settings.json" \
        "${CLAUDE_HOME}/settings.json"; then
        settings_drift=0
    else
        settings_drift=1
    fi
else
    echo "(live ~/.claude/settings.json does not exist)"
    settings_drift=1
fi

if [ "${claude_md_drift}" -eq 0 ] && [ "${settings_drift}" -eq 0 ]; then
    exit 0
else
    exit 1
fi
