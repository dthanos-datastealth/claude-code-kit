# code-simplifier — post-implementation cleanup pass

**What it does:**
The `code-simplifier` plugin installs a `/simplify` skill that reviews
recently-changed code for opportunities to remove complexity, reuse
existing helpers, and improve clarity. It runs against the working
diff — not the whole repository — and flags:
- premature abstractions introduced by the change,
- duplicate logic that could collapse into an existing helper,
- dead branches and unreachable code,
- redundant state, parameters, or layers of indirection,
- straightforward efficiency wins (allocations, repeated work).

Where it finds real issues it proposes (or applies) targeted fixes,
keeping the diff minimal.

**Why it's in this kit:**
The kit's workflow ends every meaningful change with an explicit
"Simplify" step (step 8 in `CLAUDE.md`). The reason is that even
disciplined TDD cycles tend to leave a tail of small over-engineering —
an interface introduced for a single caller, a helper that wraps one
line, a leftover parameter from a refactor. Catching those at the end
of the cycle is much cheaper than catching them in a future review or
during a later refactor, and `/simplify` is the concrete tool that
turns that workflow rule into action.

It pairs naturally with `optibot` (performance-focused review) — the
simplifier targets clarity and reuse, optibot targets speed and cost.

**When you'd disable it:**
- Single-line fixes, typo corrections, or tiny config tweaks where
  there is nothing meaningful to simplify.
- Generated code (migrations, schemas, vendored files) where the
  "complexity" is intentional and the tool would propose unhelpful
  changes.
- Sessions where the user explicitly wants to preserve a verbose-but-
  readable style and does not want suggested collapses.

Do not disable it for any non-trivial implementation. The whole point
is to make the last pass before code review remove obvious cruft so
human reviewers can focus on substantive concerns.

**Source:**
GitHub: <https://github.com/anthropics/claude-plugins-official>
Marketplace: `anthropics/claude-plugins-official`
Plugin name: `code-simplifier`

Install via the kit's `install.sh`, which registers the marketplace and
runs `claude plugin install code-simplifier@anthropics/claude-plugins-official`.

The skill is pure prompt content; no daemon, no external service.

**Cost / footprint:**
- Disk: negligible — a single markdown skill file.
- Memory / CPU: zero at idle. The skill is loaded on demand by the
  `Skill` tool and only consumes tokens while it runs.
- Network: none. It reads the working diff locally via Claude Code's
  existing file-access tools.
- Dependencies: none beyond the Claude Code CLI and a working
  repository state (a diff to review).

The token cost is bounded by the size of the diff under review.
Skipping it on small fixes is cheap; running it on substantive changes
typically pays for itself in the size of the diff it removes.
