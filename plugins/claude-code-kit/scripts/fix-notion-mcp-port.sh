#!/usr/bin/env bash
# fix-notion-mcp-port.sh — re-register the Notion MCP with a pinned OAuth
# callback port so enterprise Notion workspaces (with member-install
# allow-list enabled) can approve a stable redirect_uri.
#
# Usage:
#   plugins/claude-code-kit/scripts/fix-notion-mcp-port.sh [port]
#
# Port selection (in order):
#   1. Explicit positional arg ($1)
#   2. CLAUDE_NOTION_PORT env var
#   3. Default 51234
#
# Per-HOME: writes via `claude mcp add` which targets the current HOME's
# ~/.claude.json. If the team uses multiple HOMEs, run once per HOME with
# the SAME port so the admin only needs to allow-list one URL.
#
# CAVEAT — GitHub Issue anthropics/claude-code#55067 (OPEN at time of
# writing): re-authentication after token expiry may ignore the configured
# callbackPort and request a random port instead. If the integration
# breaks after a while, re-run this script.

set -euo pipefail

B='\033[1;34m'; Y='\033[1;33m'; R='\033[1;31m'; N='\033[0m'
log() { printf "${B}[fix-notion-mcp-port]${N} %s\n" "$*"; }
warn() { printf "${Y}[fix-notion-mcp-port]${N} %s\n" "$*" >&2; }
err()  { printf "${R}[fix-notion-mcp-port]${N} %s\n" "$*" >&2; }

PORT="${1:-${CLAUDE_NOTION_PORT:-51234}}"
NOTION_MCP_URL="https://mcp.notion.com/mcp"

# Validate port
if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1024 ] || [ "$PORT" -gt 65535 ]; then
    err "invalid port: $PORT (must be integer 1024-65535)"
    exit 2
fi

# Validate claude CLI
if ! command -v claude >/dev/null 2>&1; then
    err "claude CLI not on PATH"
    exit 2
fi

log "Removing existing 'notion' MCP server (if any)..."
claude mcp remove notion 2>/dev/null || true

log "Registering Notion MCP with --callback-port ${PORT}..."
claude mcp add --transport http --callback-port "$PORT" notion "$NOTION_MCP_URL"

cat <<EOF

  Notion MCP registered with pinned callback port.

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Next step: ask your Notion workspace admin to allow-list this URL: │
  │                                                                     │
  │      http://localhost:${PORT}/callback                              │
  │                                                                     │
  │  Admin path (Notion):                                               │
  │    Settings → Integrations → Approved connections                   │
  │    → Approve the Notion MCP connection                              │
  │    → Contact Notion support to add the redirect_uri above to the    │
  │      OAuth client's allowlist (if workspace member-install is       │
  │      restricted).                                                   │
  └─────────────────────────────────────────────────────────────────────┘

  Then in Claude Code:
    1. Restart the session
    2. Run /mcp and complete the Notion OAuth flow

  ┌─────────────────────────────────────────────────────────────────────┐
  │  CAVEAT: GitHub Issue anthropics/claude-code#55067 (OPEN)           │
  │                                                                     │
  │  Re-auth after token expiry may ignore the pinned port and use a    │
  │  random port. If the integration breaks after a while, re-run this  │
  │  script (no state to clean up — it's idempotent).                   │
  └─────────────────────────────────────────────────────────────────────┘

  Team note: every developer who needs Notion access must run this script
  once per HOME, using the SAME port (default 51234, configurable via
  CLAUDE_NOTION_PORT env var or first positional arg).

EOF
