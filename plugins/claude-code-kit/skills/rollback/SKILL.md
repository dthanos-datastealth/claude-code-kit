---
name: rollback
description: Use when the user wants to revert a specific claude-code-kit upgrade by restoring a particular timestamped backup. Different from uninstall.sh (which is the nuclear option that restores only the most recent backup + removes all kit-installed docs). Lists backups under ~/.claude/backups/, prompts user to pick one, restores CLAUDE.md + settings.json from that specific backup. Use when user says "rollback the kit upgrade", "revert to last week's state", "undo the last kit upgrade", or invokes /claude-code-kit:rollback.
---

# claude-code-kit:rollback

Soft restore from a specific timestamped backup.

## When to invoke

- User reports the last kit upgrade broke something.
- User wants to revert to a known-good state without removing the kit entirely.

## When NOT to invoke

- User wants the kit completely gone from the machine — that's
  `uninstall.sh`, not this skill.
- No backups exist (`~/.claude/backups/` empty) — surface the gap and stop.

## What it does

1. Lists backups under `~/.claude/backups/` (each named with an ISO
   timestamp).
2. Prompts the user to select one.
3. Calls `scripts/upgrade.sh --rollback <backup-id>` which:
   - Validates the backup exists and contains the expected files
   - Restores `CLAUDE.md` + `settings.json` from that backup
   - Updates `~/.claude/.kit-version` to the version recorded in the backup
   - Appends a `rollback` event to `~/.claude/.kit-version.history.jsonl`

## Differences from `uninstall.sh`

| Aspect | `/claude-code-kit:rollback` | `uninstall.sh` |
|---|---|---|
| Scope | Reverts to a specific backup | Nuclear: removes everything kit-installed |
| Backup picked | User chooses any backup | Always most recent backup |
| Docs left in place? | Yes (untouched) | No (removes `~/.claude/docs/`) |
| `.kit-version` after | Updated to backup's version | Removed |

## How to call from chat

```bash
ls ~/.claude/backups/
```

Present the list, ask which to restore, then resolve the checkout from the
install marker — `scripts/upgrade.sh` lives there, not in this plugin, and a
slash command runs in whatever project the user is in:

```bash
KIT="$(python3 -c "import json,pathlib;print(json.loads((pathlib.Path.home()/'.claude'/'.kit-version').read_text()).get('repo_dir',''))")"
bash "${KIT:?kit checkout not recorded — ask where the kit was cloned}/scripts/upgrade.sh" --rollback <chosen-backup-id>
```

A backup taken by a current install also carries `rules/`, so the rollback
restores the kit's instruction files as well as `settings.json`.
