---
name: upgrade
description: Use when the user wants to upgrade an existing claude-code-kit installation. Runs scripts/upgrade.sh against the user's current ~/.claude/ in dry-run first, surfaces proposed diff + conflicts, prompts for confirmation, then applies. Preserves user-added plugins, marketplaces, env vars, and CLAUDE.md sections via the kit's intelligent merge (union-on-conflict for settings, heading-based 3-way for CLAUDE.md). Use when user says "upgrade the kit", "update claude-code-kit", "pull in new kit changes", or invokes /claude-code-kit:upgrade.
---

# claude-code-kit:upgrade

Intelligent upgrade of an existing claude-code-kit installation in `~/.claude/`.

## When to invoke

- User wants to pull in new kit changes (newer `claude/CLAUDE.md`, new
  marketplace entries, new docs) without losing their accumulated state.
- `~/.claude/.kit-version` exists (proves a prior install).

## When NOT to invoke

- Fresh installs — use `install.sh` directly (no `.kit-version` marker
  yet, no merge needed).
- Conflict files exist under `~/.claude/.kit-conflicts/` — must resolve
  those first (delete after manual merge).

## What it does

1. Calls `scripts/upgrade.sh --dry-run` to produce a proposed diff
2. Surfaces the diff in chat, including:
   - settings.json key changes (new plugins added, existing plugins
     preserved, env vars merged)
   - CLAUDE.md section changes (clean updates, user-modifications
     preserved, conflicts requiring choice)
3. Prompts the user to confirm:
   - `[y]` proceed with `--apply`
   - `[n]` abort, no changes
   - `[c]` proceed but only for CLAUDE.md (skip settings.json)
   - `[s]` proceed but only for settings.json (skip CLAUDE.md)
4. On `[y]`: invokes `scripts/upgrade.sh --apply`
5. Reports the result, including backup path for rollback

## Pre-flight checks

- `~/.claude.json` is never touched (MCPs, project history, oauthAccount
  preserved by design — the kit doesn't own that file).
- `~/.claude/memory/` is never touched.
- Backup is mandatory and happens BEFORE any write.

## How to call from chat

Run the script and present its output:

```bash
bash scripts/upgrade.sh --dry-run
```

Then read the output, summarize it for the user in chat, ask for
confirmation, and on `[y]` run:

```bash
bash scripts/upgrade.sh --apply
```

## Conflict handling

If the dry-run reports CONFLICT sections, present each diff side-by-side
and let the user choose per-section:
- `[k]` take kit's new version (their changes lost; backup preserved)
- `[y]` keep theirs (kit changes for that section not applied)
- `[m]` write side-by-side `.conflict.md` file and skip the section
- `[a]` abort entire upgrade

Refuse to `--apply` if any conflict files exist in
`~/.claude/.kit-conflicts/` — they must be deleted (resolved) first.
