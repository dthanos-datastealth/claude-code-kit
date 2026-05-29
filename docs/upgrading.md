# Upgrading claude-code-kit

For users adopting a newer version of the kit on top of an existing
`~/.claude/` that already has accumulated state — custom plugins,
custom marketplaces, custom env vars, hand-edited CLAUDE.md sections.

The kit's `install.sh` is **safe for fresh installs** but its default
merge logic REPLACES `enabledPlugins`, `extraKnownMarketplaces`, and
`effortLevel` keys, which would destroy user state on a live HOME.
This guide covers the **upgrade-safe path** introduced in the
`claude-code-kit` plugin.

## TL;DR

```bash
# From an existing install (~/.claude/.kit-version present):
/claude-code-kit:upgrade          # in Claude Code session
# OR
bash scripts/upgrade.sh --dry-run # preview
bash scripts/upgrade.sh --apply   # commit
```

The upgrade tool preserves your custom plugins, marketplaces, env
vars, and any CLAUDE.md section the kit doesn't own (per the manifest
in `claude/CLAUDE.md.manifest.json`).

## When to use this vs `install.sh`

| Scenario | Use |
|---|---|
| Brand-new machine, no `~/.claude/` setup | `bash install.sh` |
| Existing `~/.claude/` from kit's earlier install | `/claude-code-kit:upgrade` (or `bash scripts/upgrade.sh --apply`) |
| Existing `~/.claude/` from manual setup (no kit history) | `/claude-code-kit:upgrade` — detects absence of `.kit-version` and delegates to install.sh |

The presence of `~/.claude/.kit-version` is the upgrade-tool's signal
that intelligent merge is needed. `install.sh` writes this marker on
every install.

## Merge semantics

### `settings.json` (per `scripts/merge-policy.json`)

| Key | Strategy | Conflict winner |
|---|---|---|
| `env` | UNION (dicts merged) | User |
| `enabledPlugins` | UNION (dicts merged) | User |
| `extraKnownMarketplaces` | UNION (dicts merged) | User |
| `effortLevel` | Scalar; user-wins-if-set | User if explicitly set, else kit |
| All other top-level keys | Preserve user verbatim | n/a (kit doesn't touch) |

Concrete: if you've enabled `sourcegraph@claude-plugins-official` and the
kit doesn't ship it, the upgrade preserves it. Same for any custom
marketplace, any custom env var.

### `CLAUDE.md` (per `claude/CLAUDE.md.manifest.json`)

The manifest declares which top-level (`##`) and sub-section (`###`)
headings the kit owns. Heading-based 3-way merge per section:

| live == kit_previous | live == kit_new | kit_previous == kit_new | Action |
|---|---|---|---|
| YES | * | * | Take `kit_new` (clean upgrade) |
| NO | YES | * | No-op |
| NO | NO | YES | Keep `live` (user modified; kit didn't) |
| NO | NO | NO | **CONFLICT** — surface to user |

Sections NOT in the manifest (e.g., your custom `### Sourcegraph`
block) are preserved verbatim.

### Conflict UX

If a 3-way conflict surfaces during `:upgrade`, you'll be prompted
per-section:

```
CONFLICT: section "## MANDATORY Code Search Order"
  Choose: [k] take kit_new  [y] keep yours  [m] write conflict file + skip  [a] abort
```

- `[k]` accepts the kit's new version (your customization lost; backup
  available for rollback)
- `[y]` keeps your version (kit changes for that section not applied)
- `[m]` writes a side-by-side `.conflict.md` file to
  `~/.claude/.kit-conflicts/` for manual reconcile; upgrade refuses to
  re-run until you delete the conflict file
- `[a]` aborts the whole upgrade (no backup created, no changes written)

## Rollback

Three layers of revert:

1. **Inline rollback** during conflict UX — `[a]` aborts, no writes.
2. **`/claude-code-kit:rollback`** — restores any specific timestamped
   backup from `~/.claude/backups/`. Useful when the last upgrade
   broke something and you want to revert without removing the kit
   entirely.
3. **`bash uninstall.sh`** — nuclear option. Restores the most recent
   backup AND removes all kit-installed docs + `.kit-version` +
   `.kit-cache` + `.kit-conflicts`. Use to leave the kit completely.

## Status + drift detection

```bash
/claude-code-kit:status           # in chat
# OR
bash scripts/upgrade.sh --status  # CLI
```

Reports:
- Installed kit version (from `.kit-version`)
- Unresolved conflicts in `.kit-conflicts/`
- Available backups for rollback
- Version history from `.kit-version.history.jsonl`

## Common patterns

### "I've never run install.sh; can I still upgrade?"
Yes — the upgrade tool detects the absence of `.kit-version` and
delegates to `install.sh` (clean install path). You'll get the same
result as a fresh install.

### "I want to skip the kit's CLAUDE.md and only merge settings.json"
Run the merger directly:
```bash
python3 scripts/intelligent_settings_merge.py \
    claude/settings.json ~/.claude/settings.json \
    --policy scripts/merge-policy.json
```

### "An upgrade ago, I edited the Quality Loop section and now I get conflicts every upgrade"
Either: (a) take the kit's new version once via `[k]` and let your
edit go; (b) keep your version via `[y]` every upgrade and accept
that the kit's improvements to that section won't reach you; (c)
move your custom content into a NEW section with a heading not in
the manifest (e.g., `## My Custom Quality Loop Notes`) — that
section is preserved verbatim across upgrades and never conflicts.

## Files this guide references

- `claude/CLAUDE.md.manifest.json` — list of kit-owned section headings
- `scripts/merge-policy.json` — per-key settings.json merge policy
- `scripts/intelligent_settings_merge.py` — settings.json merger
- `scripts/intelligent_claude_md_merge.py` — CLAUDE.md merger
- `scripts/upgrade.sh` — orchestrator
- `plugins/claude-code-kit/skills/{upgrade,rollback,status}.md` — slash
  command skills
- `uninstall.sh` — nuclear option (also cleans up `.kit-*` state files
  introduced by the upgrade tool)
