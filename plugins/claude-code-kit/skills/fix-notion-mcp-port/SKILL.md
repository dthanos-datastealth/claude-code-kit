---
name: fix-notion-mcp-port
description: Use when the user reports the Notion MCP fails to authenticate because of "Invalid redirect_uri" error, or when their Notion workspace has member-install allow-list enabled and the admin can't approve a random callback port. Runs scripts/fix-notion-mcp-port.sh which re-registers the Notion MCP with a pinned callback port (default 51234, configurable), then prints the exact URL the Notion admin must allow-list. Documents the GH Issue #55067 caveat (re-auth may break). Use when user says "Notion auth broken", "Notion OAuth failing", "enterprise Notion blocking install", "fix Notion port", or invokes /claude-code-kit:fix-notion-mcp-port.
---

# claude-code-kit:fix-notion-mcp-port

Pin the Notion MCP OAuth callback port so enterprise Notion workspaces
with member-install allow-list can approve a stable redirect_uri.

## When to invoke

- User reports Notion MCP failing with `Invalid redirect_uri` errors
- User's workspace has member-install allow-list enabled (admin must
  approve integrations + their redirect URIs)
- User cannot complete OAuth flow because port changes each attempt

## What it does

1. Runs `plugins/claude-code-kit/scripts/fix-notion-mcp-port.sh [port]`
2. Captures the script output (admin URL + workflow instructions)
3. Presents the admin URL to the user so they can forward it to their
   Notion workspace admin
4. Surfaces the Issue #55067 caveat (re-auth may break; re-run script
   to fix)

## Port selection

- If user provides a specific port: use it
- If `CLAUDE_NOTION_PORT` env var set: use it
- Otherwise: default 51234

## Team consideration

For a team rolling this out, USE THE SAME PORT across all developers so
the admin only needs to allow-list one URL. Document the port in the
team's internal runbook (e.g., `.team-notion-port` file or shared doc).

## Background

The kit's bundled Notion plugin
(`~/.claude/plugins/cache/claude-plugins-official/notion/0.1.0/.mcp.json`)
ships without a callbackPort. Claude Code's default behavior is to pick
a random localhost port per OAuth attempt. Notion validates redirect_uri
against an exact allowlist (no wildcards), so random ports always
reject. Pinning the port via `claude mcp add --callback-port` lets the
admin allow-list a stable URL.

Full reference: `docs/notion-mcp-pinning.md`.

## Caveat

GitHub Issue anthropics/claude-code#55067 (OPEN as of plan time): even
with the port pinned at registration, Claude Code may use a random port
during re-authentication. The workaround is to re-run this script
whenever the integration breaks (it's idempotent — safe to re-run).
