# Memory System

The kit ships with an auto-memory hook that gives Claude Code a persistent,
per-project store of high-signal context — user preferences, prior
corrections, project decisions, and pointers to external systems — that
survives across conversations. This document explains what the hook does,
where the memory lives, what the four memory types are, what belongs in
the store (and what does not), and how to maintain it.

The store complements but does not replace `CLAUDE.md`. `CLAUDE.md` is
directive prose loaded at the top of every conversation; the memory store
is structured per-project state that the auto-memory hook surfaces when it
matters.

---

## 1. What the auto-memory hook does

The hook is declared in `claude/CLAUDE.md` under the "Memory System"
section and installed into `~/.claude/CLAUDE.md` by `install.sh`. At
session start it locates the per-project memory directory, reads the
`MEMORY.md` index, and makes the index entries available as context for
the conversation. As the session proceeds, the hook prompts Claude to
write new memories when it sees patterns worth persisting — corrections
from the user, decisions worth keeping, references to external systems
that come up.

The hook does not write memories without intent. It surfaces *candidates*
for memorisation; the actual write is a deliberate action (either by
Claude, prompted by the hook, or by you via a slash command). This keeps
the store small enough to be useful and prevents it from degenerating
into a session transcript.

---

## 2. Where memories live

The store is rooted at:

```
~/.claude/projects/<encoded-cwd>/memory/
```

with two file types inside:

- `MEMORY.md` — the index. One line per memory, with a stable name and a
  one-sentence summary. This file is what the hook reads at session
  start.
- Per-memory files (`user_<name>.md`, `feedback_<name>.md`,
  `project_<name>.md`, `reference_<name>.md`) — the full content of each
  memory, addressed by name from the index.

The directory is plain files on disk. Inspect it with `ls`, edit it with
your editor, version-control it if you want to share state between
machines, ignore it from your dotfiles if you do not.

---

## 3. How Claude Code encodes the cwd path

Claude Code derives the `<encoded-cwd>` segment from your project's
absolute path by replacing every forward slash (`/`) with a dash (`-`).

| Project absolute path     | Encoded form              |
|---------------------------|---------------------------|
| `/home/alice/repos`       | `-home-alice-repos`       |
| `/home/alice/repos/work`  | `-home-alice-repos-work`  |
| `/opt/code/api`           | `-opt-code-api`           |

So a project at `/home/alice/repos/work` has its memory at
`~/.claude/projects/-home-alice-repos-work/memory/`. The auto-memory
hook resolves the encoding for you; you only need to know the convention
when you want to inspect or back up the directory by hand.

The encoding is per-project, not per-session. A new clone at the same
path uses the same memory store. A move to a different path produces a
new (empty) store at the new path — copy the directory across if you
want continuity.

---

## 4. The four memory types

The store recognises four types. Each type captures a different class of
context, and the choice of type determines how the auto-memory hook
weighs the entry when surfacing context.

### 4.1 `user` — role, preferences, knowledge

Captures stable facts about the person Claude is working with. Examples:

- "Prefers concise, evidence-first responses; no preamble."
- "Reviews PRs in chunks of 10 files max."
- "Works in Go and TypeScript primarily; Python only for tooling."

Write a `user` memory when the user states a preference that will
recur, or when you discover a working habit that should shape future
sessions.

### 4.2 `feedback` — corrections and successes (read-first priority)

The highest-priority type. Captures corrections the user has given you
that should not need to be given again, and patterns that have worked
notably well. Examples:

- "Always use built-in `Read`/`Edit` tools for files, never `cat`/`sed`."
- "Never add `Co-Authored-By: Claude` to commits."
- "Run the linter before claiming any task complete."

Write a `feedback` memory immediately after the user corrects you. The
goal is to prevent the same correction in the next session — the cost
of writing it now is small; the cost of being corrected twice for the
same thing is larger.

### 4.3 `project` — ongoing work, decisions, deadlines

Captures the state of work in progress: decisions taken, options
rejected, deadlines committed to, current focus. Examples:

- "Migration to v2 schema scheduled before end of quarter."
- "Decision: use server-side rendering for the public site; SPA for
  the dashboard."
- "Currently focused on the authentication subsystem; expansion on
  hold."

Write a `project` memory at decision points. Update it (or delete and
rewrite) when the decision is revisited.

### 4.4 `reference` — pointers to external systems

Captures stable handles into external systems the project depends on:
specific Notion database IDs, Sourcegraph endpoints, internal wiki
URLs, account names that recur. Examples:

- "Tasks database in Notion: <database-id>."
- "Internal Sourcegraph: <hostname>; primary repos under `code/`."
- "Issue tracker for vendor X: <project-url>."

Write a `reference` memory when an external pointer is one Claude will
need to use repeatedly. Do not write one for a one-off lookup; that is
session-scoped, not project-scoped.

---

## 5. The `MEMORY.md` index format

`MEMORY.md` is the entry point the auto-memory hook reads. It is
organised by type and uses one line per memory, with the memory name in
brackets, the file path, and a one-sentence summary.

Skeleton:

```markdown
# Memory Index

## Feedback (read first)
- [name](./feedback_name.md) — one sentence summary, under 20 words.

## User
- [name](./user_name.md) — one sentence summary.

## Project
- [name](./project_name.md) — one sentence summary.

## Reference
- [name](./reference_name.md) — one sentence summary.
```

The index obeys a hard 200-line cap. If it grows beyond 200 lines, the
hook truncates rather than loading the overflow — which silently
degrades the context. Keep entries short, prune ruthlessly, and split
long-running projects into more specific names rather than longer
summaries.

A reasonable index has on the order of 20–60 entries. If you find
yourself near 100, the store is collecting too much; revisit principle
6 below.

---

## 6. What NOT to save

The store is for context that is hard or impossible to reconstruct from
the codebase. Do not save:

- **Code patterns derivable from the codebase** — a `grep`, an LSP
  query, or a `graph_continue` call surfaces them faster than memory
  retrieval.
- **Git history** — `git log` is the canonical source; mirroring it
  in memory is duplication that goes stale.
- **Debugging recipes for solved bugs** — once the bug is fixed and
  the regression test is in place, the test is the memory. Keep the
  store for *unsolved* gotchas or for class-level lessons.
- **Session-scoped state** — what you happen to be working on at this
  exact moment is not project state; it is conversation state, and it
  belongs in the conversation.
- **Transcripts of long discussions** — extract the decision, not the
  argument. The store records what you decided, not how you got there.
- **API tokens, passwords, or any credential** — the store is a plain
  directory on disk; treat it as you would a project README.

A useful heuristic: if you can reconstruct the fact in under a minute
from the codebase, git history, or a fresh `graph_continue`, do not
save it. If the fact required a correction from the user, took
significant exploration to discover, or is an external reference you
will need repeatedly, save it.

---

## 7. How to update or remove a memory

The store is plain files; edit them directly.

To update:

1. Open the memory file (`feedback_<name>.md`, etc.) in your editor.
2. Rewrite the content; keep the file's tone and length similar.
3. Update the corresponding line in `MEMORY.md` if the summary
   changed.

To remove:

1. Delete the memory file.
2. Remove its line from `MEMORY.md`.

Removal is not destructive in the file-history sense — if the store is
version-controlled, the previous content lives in git. If you remove
something and decide later it was useful, recover it from history; do
not let "I might need it again" prevent you from pruning.

A periodic prune (every few weeks of active use) keeps the store at a
useful size. Entries that have not been surfaced in months are good
prune candidates — if you have not needed them, the auto-memory hook
has not needed them either.

---

## 8. Cross-linking with `[[name]]` markers

When one memory references another, use double-bracket notation:

```markdown
The team's review cadence — see [[feedback_review_chunks]] — caps
reviewable diffs at 10 files. Larger changes are split per
[[project_split_strategy]].
```

The brackets are a convention the hook understands; they signal that the
referenced memory should be considered together with the referencing
one when surfacing context. Use them when:

- A `feedback` entry depends on context from a `project` entry.
- A `reference` entry is consumed by multiple `project` entries.
- A `user` preference is repeatedly intertwined with a `feedback`
  correction.

Do not use `[[…]]` for general prose links — those are normal markdown.
Reserve the double-bracket form for genuine cross-memory references the
hook should follow.

---

## 9. Inspecting the store

Useful commands for a quick audit:

```sh
# List all memories for the current project
ls ~/.claude/projects/$(pwd | tr '/' '-')/memory/

# Show the index
cat ~/.claude/projects/$(pwd | tr '/' '-')/memory/MEMORY.md

# Count entries
ls ~/.claude/projects/$(pwd | tr '/' '-')/memory/ | wc -l
```

If the directory does not exist, the auto-memory hook has not been
triggered yet for this project. It will create the directory the first
time a memory is written.

---

## 10. Relationship to `CLAUDE.md` and the dual-graph context store

Three persistent stores can look similar at first glance. They have
distinct roles:

| Store                                  | Scope                | Role                                                                              |
|----------------------------------------|----------------------|-----------------------------------------------------------------------------------|
| `~/.claude/CLAUDE.md`                  | Global, all projects | Directive prose. Behaviour-shaping rules loaded at every session start.           |
| `~/.claude/projects/<enc>/memory/`     | Per-project          | Structured context store. The subject of this doc.                                |
| Dual-graph MCP context store           | Per-project          | Decisions/tasks/facts/blockers written via `graph_add_memory`, surfaced by graph. |

Rules of thumb:

- A rule that should apply across every project lives in `CLAUDE.md`.
- A project-specific fact that needs to outlive the current session
  lives in the memory store described here.
- A graph-anchored decision tied to a specific file or symbol lives in
  the dual-graph context store via `graph_add_memory`.

When in doubt, default to the memory store described here; it is the
most easily inspected and pruned of the three.

---

## Further reading

- [`docs/workflow.md`](workflow.md) — the 10-step development loop;
  step 10 (Document) overlaps with what gets captured here.
- [`docs/tools/claude-md-management.md`](tools/claude-md-management.md)
  — the `/revise-claude-md` slash command that handles the
  `CLAUDE.md`-shaped half of the same job.
- [`docs/tools/dual-graph-mcp.md`](tools/dual-graph-mcp.md) — the
  `graph_add_memory` tool for graph-anchored notes.
