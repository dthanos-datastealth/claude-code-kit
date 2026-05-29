---
name: status
description: Use when the user wants to check the current state of their claude-code-kit installation. Reports installed version, drift between live ~/.claude/ files and the recorded SHAs, any unresolved conflicts in ~/.claude/.kit-conflicts/, and lists available backups. Useful before running upgrade (to know what will change) and for troubleshooting. Use when user says "what kit version do I have", "is my kit up to date", "show kit status", "are there conflicts", or invokes /claude-code-kit:status.
---

# claude-code-kit:status

Report install state, drift, and unresolved conflicts.

## When to invoke

- Before running `:upgrade` to understand what's installed and what
  would change.
- After an aborted upgrade, to see lingering conflicts.
- For routine "what version am I on" checks.

## What it reports

- Installed kit version (from `~/.claude/.kit-version`)
- Whether live `CLAUDE.md` and `settings.json` SHA matches the recorded
  SHA (drift detection — user has manually edited a kit-owned file)
- Unresolved conflicts in `~/.claude/.kit-conflicts/`
- Available backups under `~/.claude/backups/`
- Version history from `~/.claude/.kit-version.history.jsonl`

## How to call from chat

```bash
bash scripts/upgrade.sh --status
```

Present the output to the user, calling out:
- Drift (if any) — proactively offer `:upgrade` to reconcile
- Unresolved conflicts (if any) — block `:upgrade` until resolved
- Recent backups — useful for `:rollback` selection
