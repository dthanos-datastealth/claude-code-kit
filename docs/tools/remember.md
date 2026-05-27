# remember — session-state checkpointing across session boundaries

**What it does:**
The `remember` plugin installs a `/remember` skill that captures the
in-progress state of a working session — the current task, what was
just decided, what is half-finished, what to resume next — and
persists it in a form the next session can pick up cleanly. A typical
checkpoint records:

- the active task or feature being worked on (one sentence),
- the most recent decisions made during the session,
- the immediate next steps (what to do first when resuming),
- open questions or blockers waiting on user input,
- pointers to the files, branches, or commits relevant to the work.

It writes this state to a known location (such as the project's
`CONTEXT.md`) rather than into chat memory, so a fresh session in the
same repository can load it and continue without re-deriving context
from the transcript.

**Why it's in this kit:**
The kit's memory system (under
`~/.claude/projects/-Users-dthanos-repos/memory/`) is built for
durable, cross-project knowledge — user preferences, recurring
feedback, project goals, hard rules. It is intentionally not the
right place for transient, in-progress task state, which would
quickly clutter the durable memory and rot as tasks change.

`/remember` fills exactly that gap. It is the bridge between an
ephemeral chat transcript (which Claude will not see next session)
and the durable memory index (which is the wrong granularity for
"I was in the middle of refactoring `handleLogin` and the test I
just wrote is failing because of X"). Without it, every session
boundary forces re-derivation of context from git history, comments,
and guesswork; with it, the next session opens with the previous
session's working state already loaded.

This matters most for multi-session features, debugging investigations
that span days, and any work where stopping and resuming is the
common case rather than the exception.

**When you'd disable it:**
- Short, self-contained sessions where the task completes inside the
  session and there is nothing to resume.
- One-shot questions or read-only exploration where no state would
  accumulate worth carrying forward.
- Sessions whose entire output is a single commit or PR that closes
  the loop on its own — the commit message and diff already encode
  the relevant state.

Do not disable it for multi-session feature work, long-running
debugging sessions, or any task where you are likely to be
interrupted before finishing.

**Source:**
GitHub: <https://github.com/anthropics/claude-plugins-official>
Marketplace: `anthropics/claude-plugins-official`
Plugin name: `remember`

Install via the kit's `install.sh`, which registers the marketplace and
runs `claude plugin install remember@anthropics/claude-plugins-official`.

The skill is pure prompt content; it writes state to a local file via
Claude Code's existing file-access tools. No daemon, no external
service, no API key.

**Cost / footprint:**
- Disk: negligible — a single markdown skill file plus a small text
  checkpoint file per project (typically `CONTEXT.md`, kept under
  ~20 lines by convention).
- Memory / CPU: zero at idle. The skill is invoked on demand by the
  `Skill` tool, usually at the end of a session.
- Network: none. The checkpoint is written and read locally.
- Dependencies: none beyond the Claude Code CLI and write access to
  the project directory.

The token cost is bounded by the size of the checkpoint, which is
deliberately tiny. The asymmetry favors running it — a small one-time
write at session end prevents a much larger context-reconstruction
cost at the start of the next session.
