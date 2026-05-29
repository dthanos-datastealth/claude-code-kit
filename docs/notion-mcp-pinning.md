# Notion MCP port-pinning for enterprise workspaces

The kit's bundled Notion MCP plugin (`notion@claude-plugins-official`)
uses Claude Code's HTTP OAuth flow, which by default picks a
**random localhost callback port** per authentication attempt. Some
enterprise Notion workspaces (those with member-install allow-list
enabled) require the admin to pre-approve a specific redirect URI.
A random port can't be allow-listed.

This guide documents the workaround the kit ships:
`plugins/claude-code-kit/scripts/fix-notion-mcp-port.sh`.

## TL;DR

```bash
# Pin Notion's OAuth callback to a stable port (default 51234):
bash plugins/claude-code-kit/scripts/fix-notion-mcp-port.sh
# OR via slash command in Claude Code:
/claude-code-kit:fix-notion-mcp-port
```

The script prints the admin allow-list URL
(`http://localhost:51234/callback`) — forward it to your Notion
workspace admin, who adds it to the OAuth client's allowed
redirect_uri list. Restart Claude Code, complete `/mcp` auth, done.

## Why this is needed

Two upstream factors collide:

1. **Notion validates `redirect_uri` against an exact pre-registered
   allowlist** — no wildcards, no port flexibility, no DCR fallback
   for the hosted Notion MCP server. Reference:
   [Claude Code Issue #52961](https://github.com/anthropics/claude-code/issues/52961).
   Failing request shows `"Invalid redirect_uri for OAuth client"`.

2. **Claude Code's default OAuth callback uses a random port per
   attempt**, picked from the OS's available range. Reference:
   [docs.code.claude.com on MCP OAuth](https://code.claude.com/docs/en/mcp).

Enterprise Notion workspaces with member-install restrictions reject
the random port because it isn't in the allowlist. The user sees
"As a member, you can't install localhost to <workspace>. Ask a
workspace admin to add this to the allow list."

## The workaround

Claude Code supports a documented `--callback-port` flag at
`claude mcp add` time that pins the port. The kit's
`fix-notion-mcp-port.sh` automates the re-registration:

1. Removes the existing `notion` MCP server registration (if any)
2. Re-adds it with `--transport http --callback-port <port>`
3. Prints the exact admin allow-list URL + admin workflow

## Picking a port

Order of precedence:
1. First positional arg to the script (e.g., `... fix-notion-mcp-port.sh 8080`)
2. `CLAUDE_NOTION_PORT` env var
3. Default: **51234** (kit-default; chosen for low-collision probability)

For teams: pick one port and standardize. The admin only needs to
allow-list one URL across the whole team.

## Per-HOME implication

`claude mcp add` writes the config to the **per-HOME** `~/.claude.json`
(scoped to the current project path). Each developer needs to run
the script once per HOME. Same port across the team minimizes admin
allow-list burden.

## CAVEAT: Issue #55067 — re-auth may break the pin

GitHub Issue [anthropics/claude-code#55067](https://github.com/anthropics/claude-code/issues/55067)
(OPEN as of plan time): when Claude Code re-authenticates an HTTP MCP
server after token expiry, it generates a **random localhost port**
instead of honoring the configured `callbackPort` from
`~/.claude.json`. This means:

- Initial setup via this script → works
- ~1 hour later (Notion access token expires) → re-auth attempt uses
  random port → Notion rejects → integration breaks

**Workaround:** re-run `fix-notion-mcp-port.sh`. The script is
idempotent (safe to re-run as often as needed). For now, expect to
re-pin periodically until Anthropic fixes #55067 upstream.

The kit cannot fix this from outside — it's a Claude Code bug. The
script is the best mitigation available.

## End-to-end recipe (user + admin)

### User (developer)

```bash
# 1. Re-register with pinned port
bash plugins/claude-code-kit/scripts/fix-notion-mcp-port.sh

# 2. Copy the admin allow-list URL from the script's output
# (looks like:  http://localhost:51234/callback)

# 3. Send the URL to the Notion workspace admin

# 4. Wait for admin confirmation, then in Claude Code:
/mcp
# Complete the Notion OAuth browser flow

# 5. Verify in Claude Code:
claude mcp list | grep notion
# Expect: notion: https://mcp.notion.com/mcp (HTTP) - ✓ Connected
```

### Admin (Notion workspace owner)

1. Notion → **Settings** → **Integrations** → **Approved connections**
2. Approve the Notion MCP connection for member-install
3. Contact Notion support to add the redirect_uri the developer sent
   (e.g., `http://localhost:51234/callback`) to the OAuth client's
   allowlist
4. Confirm with the developer to proceed with Step 4 above

## Related kit docs

- `docs/corporate-tls.md` — sibling enterprise concern (TLS-intercepting
  proxies for Berry MCP)
- `docs/upgrading.md` — uses the same `plugins/claude-code-kit/` plugin
  scaffold that hosts this script
