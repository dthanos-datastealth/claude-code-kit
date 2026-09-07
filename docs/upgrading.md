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

The upgrade tool preserves your custom plugins, the marketplaces you added, env
vars, and any CLAUDE.md section the kit doesn't own (per the manifest
in `claude/CLAUDE.md.manifest.json`). The one exception is a marketplace the
kit itself ships that you repointed at your own fork: that declaration is
restored, because it carries the release channel. See
[Merge semantics](#merge-semantics).

## When to use this vs `install.sh`

| Scenario | Use |
|---|---|
| Brand-new machine, no `~/.claude/` setup | `bash install.sh` |
| Existing `~/.claude/` from kit's earlier install | `/claude-code-kit:upgrade` (or `bash scripts/upgrade.sh --apply`) |
| Existing `~/.claude/` from manual setup (no kit history) | `/claude-code-kit:upgrade` — detects absence of `.kit-version` and delegates to install.sh |

The presence of `~/.claude/.kit-version` is the upgrade-tool's signal
that intelligent merge is needed. `install.sh` writes this marker on
every install.

## Release channels: testing before stable

Every change lands on the `prerelease` branch first. The two channels are the
same marketplaces at a different `ref`, so switching channel means re-pointing
the marketplace registrations — the marketplace *names* never change, and a
second `marketplace add` under an existing name replaces it.

`scripts/upgrade.sh` deliberately does **not** register marketplaces or install
plugins (it merges settings and CLAUDE.md), so switching branch and re-running
it does not move you between channels. Do both halves:

```sh
# Existing machine: stable -> prerelease
git switch prerelease
bash scripts/upgrade.sh --apply        # FIRST: settings + CLAUDE.md half

export CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1
claude plugin marketplace add dthanos-datastealth/claude-code-kit@prerelease
claude plugin marketplace add dthanos-datastealth/hallbayes@prerelease
# then, in a Claude Code session:  /plugin update
```

Three details in that snippet are load-bearing, and getting any of them wrong
fails the add:

- **Run `scripts/upgrade.sh` before the marketplace adds, not after.** The add
  is checked against what `~/.claude/settings.json` declares for that name, and
  `upgrade.sh` is what writes the new `ref` there. Run the adds first and both
  are refused, because settings still declares the marketplace without a ref.
  Verified end to end: install from `main`, then follow this recipe in each
  order.

- **Use the `owner/repo@ref` shorthand, not a `https://…/repo.git#ref` URL.**
  `claude/settings.json` declares each marketplace as a `github` source, and
  Claude Code refuses an add whose source *kind* differs from the declaration
  for that name — `Cannot add marketplace "berry-marketplace": its network
  source differs from the one declared for it in settings`. The shorthand is
  the matching kind.
- **Export `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` first.** The shorthand otherwise
  clones over SSH (`Cloning via SSH: git@github.com:…`), which fails on a box
  with no key loaded. `install.sh` exports this for you; a manual add does not.

```sh
# Brand-new machine, straight onto the channel
git clone -b prerelease https://github.com/dthanos-datastealth/claude-code-kit.git
cd claude-code-kit && ./install.sh
```

```sh
# Back to stable
git switch main
bash scripts/upgrade.sh --apply        # again, settings half first

export CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1
claude plugin marketplace add dthanos-datastealth/claude-code-kit@main
claude plugin marketplace add dthanos-datastealth/hallbayes@main
# then:  /plugin update
```

`/claude-code-kit:status` reports which channel and commit the current install
came from, so you can confirm the switch took effect. Promoting a channel is a
pull request from `prerelease` to `main` that flips the `ref` values and the
plugin versions; a test in the suite fails until they are flipped, so a promote
cannot silently leave stable users pointed at the prerelease channel.

### When the upgrade stops instead of proceeding

`scripts/upgrade.sh` runs the CLAUDE.md merge non-interactively. If you edited a
section the kit owns and the kit also changed it, that is a conflict, and with
no terminal to prompt on the merge exits non-zero and the upgrade aborts with
your file untouched. Nothing is written and nothing is lost.

This surface grew deliberately. The kit now declares every section it ships,
including the subsections of the mandatory protocols, because a section it did
not declare was silently kept at your old version — which is how a release's new
rules reached nobody who upgraded. The cost is that an edit inside one of those
subsections now blocks the upgrade rather than being quietly preserved.

To get past it, either run the merge where it can prompt you
(`python3 scripts/intelligent-claude-md-merge.py claude/CLAUDE.md ~/.claude/CLAUDE.md --prev <cached>`),
or move your own material into a section of your own — any heading the kit has
never shipped is yours and is preserved verbatim, forever.

## Merge semantics

### `settings.json` (per `scripts/merge-policy.json`)

| Key | Strategy | Conflict winner |
|---|---|---|
| `env` | UNION (dicts merged) | User |
| `enabledPlugins` | UNION (dicts merged) | User |
| `extraKnownMarketplaces` | UNION (dicts merged) | **Kit** |
| `effortLevel` | Scalar; user-wins-if-set | User if explicitly set, else kit |
| All other top-level keys | Preserve user verbatim | n/a (kit doesn't touch) |

Concrete: if you've enabled a plugin the kit doesn't ship, the upgrade preserves
it. Same for any custom env var, and for any marketplace you added under a name
the kit does not use.

**Marketplaces are the one place the kit wins, and it is deliberate.** A
marketplace entry carries the release channel as a `ref`. If your older copy won,
the ref could never change, and `claude plugin marketplace add owner/repo@ref` is
refused whenever it disagrees with what settings declares for that name — so the
channel would be unreachable for everyone already installed. The union still
protects marketplaces you added. What it does not protect is a *kit* marketplace
you repointed at your own fork: that declaration is restored on upgrade. To hold
a fork, register it under a name of your own.

The kit ships `effortLevel: xhigh`. The persisted key accepts `low`, `medium`,
`high` and `xhigh` only — `max` is a per-session level you select with `/effort`,
and an invalid value here is dropped with a validation error when the key is
delivered through managed settings.

### `CLAUDE.md` (per `claude/CLAUDE.md.manifest.json`)

The manifest declares every heading the kit owns, at any depth — `##`, `###`
and `####` alike. Depth matters: a `###` entry does not cover a `####` beneath
it, so each nested heading needs its own entry. A heading the manifest does not
list is yours: preserved verbatim, forever, and never replaced by a kit version.

Heading-based 3-way merge per section:

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
python3 scripts/intelligent-settings-merge.py \
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
- `scripts/intelligent-settings-merge.py` — settings.json merger
- `scripts/intelligent-claude-md-merge.py` — CLAUDE.md merger
- `scripts/upgrade.sh` — orchestrator
- `plugins/claude-code-kit/skills/{upgrade,rollback,status}/SKILL.md` — slash
  command skills
- `uninstall.sh` — nuclear option (also cleans up `.kit-*` state files
  introduced by the upgrade tool)
