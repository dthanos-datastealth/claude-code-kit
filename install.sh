#!/usr/bin/env bash
# claude-code-kit installer — macOS + Linux.
# Idempotent. Reversible via uninstall.sh.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_HOME="${HOME}/.claude"

log()  { printf '\033[1;34m[cck]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[cck]\033[0m %s\n' "$*" >&2; }
err()  { printf '\033[1;31m[cck]\033[0m %s\n' "$*" >&2; }

require() {
    local tool="$1"
    if ! command -v "$tool" >/dev/null 2>&1; then
        err "missing prerequisite: $tool"
        err "  Install it before re-running. See docs/prereqs.md."
        exit 1
    fi
}

preflight() {
    log "Preflight: checking required tools..."
    require claude
    require git
    require gh
    require python3
    require uv
    log "Preflight: OK"
}

main() {
    preflight
    # Subsequent steps added in later tasks.
}

main "$@"
