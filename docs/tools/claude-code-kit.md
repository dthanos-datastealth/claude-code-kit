# claude-code-kit — self-published plugin shipping the kit's own upgrade/rollback/status/fix-notion-mcp-port skills

**What it does:**
Bundles four slash-command skills that operate on the kit's own
installation under `~/.claude/`. `/claude-code-kit:upgrade` runs the
intelligent merge (preserves user state, surfaces 3-way conflicts);
`/claude-code-kit:rollback` restores a specific timestamped backup
(soft alternative to `uninstall.sh`); `/claude-code-kit:status`
reports installed version, drift, unresolved conflicts, and
available backups; `/claude-code-kit:fix-notion-mcp-port` re-registers
the bundled Notion MCP with a pinned OAuth callback port (workaround
for enterprise Notion workspaces with member-install allow-list).
The plugin owns no MCP servers — only skills + supporting scripts.

**Why it's in this kit:**
Without it, every adopter who runs `install.sh` on top of an existing
`~/.claude/` loses their custom `enabledPlugins`,
`extraKnownMarketplaces`, and any hand-edited CLAUDE.md sections
(because the kit's original `merge-settings.py` REPLACED rather than
UNIONed those keys). The upgrade tool fixes that destructively-merge
gap and ships it as a first-class skill so adopters get a single
canonical path (`/claude-code-kit:upgrade`) instead of having to
remember a Python one-liner.

**When you'd disable it:**
If you're using the kit on a brand-new machine and don't anticipate
ever upgrading from a divergent state, you can skip enabling this
plugin (`enabledPlugins["claude-code-kit@claude-code-kit"] = false`)
— the upgrade skills won't load but `install.sh`, `uninstall.sh`,
and the underlying `scripts/upgrade.sh` continue to work. Also
disable if you specifically don't want the Notion port-pinning
workaround surfaced (e.g., your Notion workspace doesn't have
member-install restrictions and the random-port flow works fine).

**Source:**
Self-published from this repo: `dthanos-datastealth/claude-code-kit`
marketplace, plugin path `plugins/claude-code-kit/`. Skill files at
`plugins/claude-code-kit/skills/{upgrade,rollback,status,fix-notion-mcp-port}.md`,
script at `plugins/claude-code-kit/scripts/fix-notion-mcp-port.sh`,
underlying mergers at `scripts/intelligent-settings-merge.py` and
`scripts/intelligent-claude-md-merge.py`.

**Cost / footprint:**
Negligible. Four markdown skill files (~3 KB each, loaded on demand
by Claude Code's Skill resolver), one bash script (~80 lines), and
the orchestrator at `scripts/upgrade.sh` (~140 lines). No persistent
process, no MCP server, no network calls beyond the underlying
`claude mcp add` / `git` invocations that the skills shell out to.
Adds 1 marketplace + 1 plugin to the kit's install count (6
marketplaces / 22 plugins total). On-disk: `~/.claude/.kit-version`
(~200 B), `~/.claude/.kit-cache/CLAUDE.md` (~20 KB snapshot of the
kit's CLAUDE.md at last install — used for 3-way merge on next
upgrade), and append-only `~/.claude/.kit-version.history.jsonl`
(one line per install/upgrade/rollback event).
