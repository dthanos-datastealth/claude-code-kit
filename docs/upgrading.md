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
vars, and your `CLAUDE.md`, which the kit no longer writes at all — its
instructions live in `~/.claude/rules/` instead. The one exception is a marketplace the
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
plugins (it merges settings and installs rules), so switching branch and re-running
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

On a CLI older than 2.0.64 the kit falls back to merging `CLAUDE.md`, and that
merge runs non-interactively. If you edited a section the kit owns and the kit
also changed it, that is a conflict; with no terminal to prompt on, the merge
exits non-zero and the upgrade aborts with your file untouched. Nothing is
written and nothing is lost.

On a current CLI this cannot happen. The kit does not write `CLAUDE.md`, so
there is nothing to conflict with. Put your changes in
`~/.claude/rules/00-user-overrides.md` and they survive every upgrade.

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

### `CLAUDE.md` and `~/.claude/rules/`

The kit no longer writes your `CLAUDE.md`. Its instructions ship as files under
`~/.claude/rules/`, which Claude Code discovers and loads every session:

```
~/.claude/rules/
├── 00-user-overrides.md      yours; seeded once, never overwritten
├── 10-kit-core.md
├── 20-kit-code-search.md
├── 30-kit-quality-loop.md
├── 40-kit-tracker.md
├── 50-kit-plugins.md
└── 60-kit-workflow.md
```

Files there are discovered, not merged, so an upgrade is a copy. A kit rule file
you edit locally is replaced on the next upgrade, which is what it means for the
kit to own it. `00-user-overrides.md` is the exception: the kit writes it once,
when it is absent, and never again.

**Overrides are stated, not layered.** Load order cannot carry precedence here.
The memory docs are explicit that files are "concatenated into context rather
than overriding each other", and that when two rules contradict, Claude "may
pick one arbitrarily". So every kit rule file ends by naming
`00-user-overrides.md` as the file that wins. Put your changes there rather than
editing a kit file, and they survive every upgrade.

**Migration happens once.** The first upgrade on a CLI that supports rules moves
the kit's sections out of your `CLAUDE.md`, leaves your own sections exactly
where they were, and stamps a comment at the top saying where the kit's content
went. Preview it with `scripts/upgrade.sh --dry-run`, which lists every section
it would move and writes nothing.

**Version floor.** `~/.claude/rules/` arrived in Claude Code 2.0.64, December
2025. On an older CLI the directory is ignored, so the upgrade detects the
version, says so, and falls back to the previous merge behaviour rather than
installing rules that would never load.


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

### "I edited a kit section and my edits keep getting clobbered"

Stop editing kit files. Put the change in
`~/.claude/rules/00-user-overrides.md`, which the kit seeds once and never
writes again. Every kit rule file ends by saying that file wins, so an
instruction there beats the kit's without you having to defend an edit against
each upgrade.

If you edited kit sections before migrating, those edits are still in your
`CLAUDE.md`. Migration left them there rather than discarding them, but the
kit's fresh copy of the same rule now lives in `rules/` — so both load and they
may disagree. Move what you want to keep into the override file and delete the
rest.

## Files this guide references

- `claude/CLAUDE.md.manifest.json` — list of kit-owned section headings
- `scripts/merge-policy.json` — per-key settings.json merge policy
- `scripts/intelligent-settings-merge.py` — settings.json merger
- `scripts/intelligent-claude-md-merge.py` — legacy CLAUDE.md merger (pre-2.0.64 fallback)
- `scripts/migrate-claude-md-to-rules.py` — one-shot move of kit sections into rules/
- `scripts/_kit_rules.sh` — installs `claude/rules/` into `~/.claude/rules/`
- `scripts/upgrade.sh` — orchestrator
- `plugins/claude-code-kit/skills/{upgrade,rollback,status}/SKILL.md` — slash
  command skills
- `uninstall.sh` — nuclear option (also cleans up `.kit-*` state files
  introduced by the upgrade tool)
