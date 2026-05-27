# claude-md-management — CLAUDE.md auditing and session-learning capture

**What it does:**
The `claude-md-management` plugin installs two skills that keep the
project's and the user's CLAUDE.md files from rotting:

- `claude-md-management:claude-md-improver` — audits every CLAUDE.md
  reachable from the working tree (project + nested + user-level),
  evaluates them against a quality template, prints a per-file report,
  and applies targeted updates where the file is missing structure,
  has stale guidance, or contradicts itself.
- `claude-md-management:revise-claude-md` (reachable as
  `/revise-claude-md`) — runs at the end of a session, scans what was
  learned (new conventions, gotchas, patterns, recurring corrections),
  and proposes additions or edits to the appropriate CLAUDE.md so the
  next session inherits them.

Both skills bias toward minimal diffs and explicit before/after summaries
rather than rewriting whole files.

**Why it's in this kit:**
CLAUDE.md is the single most important context file the kit ships —
it is what makes the difference between Claude following the workflow
and ignoring it. Its weakness is that it only stays useful if it is
kept current; every project accumulates conventions, gotchas, and
hard-won lessons that, if not captured, will be re-learned (badly) in
the next session.

`/revise-claude-md` is the explicit final step of the workflow defined
in the global `CLAUDE.md` — "Document — `/revise-claude-md` to capture
learnings". Without it, that step is aspirational. With it, the loop
closes: each session that produced a real lesson hands the lesson
forward.

`claude-md-improver` is the periodic counterpart: it sweeps existing
CLAUDE.md files for quality issues (missing sections, contradictions,
duplication with the global file) and is the right tool when adopting
the kit on a project that already has a stale CLAUDE.md.

**When you'd disable it:**
- Sessions that surface no new conventions, gotchas, or corrections —
  running `/revise-claude-md` on those just churns the file.
- Repositories where CLAUDE.md is deliberately frozen (release branches,
  audit-locked codebases) and updates would defeat that intent.
- Read-only exploration sessions where the user is not making changes
  and nothing is being learned that needs to persist.

Do not disable it for sessions that involved real debugging, real
decisions, or repeated user corrections — those are exactly the
sessions where the kit's "capture learnings" guarantee matters most.

**Source:**
GitHub: <https://github.com/anthropics/claude-plugins-official>
Marketplace: `anthropics/claude-plugins-official`
Plugin name: `claude-md-management`

Install via the kit's `install.sh`, which registers the marketplace and
runs `claude plugin install claude-md-management@anthropics/claude-plugins-official`.

Both skills are pure prompt content; no daemon, no external service,
no API key.

**Cost / footprint:**
- Disk: negligible — two markdown skill files.
- Memory / CPU: zero at idle. Skills are invoked on demand by the
  `Skill` tool.
- Network: none. Both skills operate on local CLAUDE.md files via
  Claude Code's existing file-access tools.
- Dependencies: none beyond the Claude Code CLI and a checked-out
  repository.

The token cost is bounded by the size of the CLAUDE.md files under
review. The asymmetry favors running them — a small one-time cost per
session prevents a much larger cost later when context drifts and
Claude starts ignoring conventions because the file no longer reflects
how the team actually works.
