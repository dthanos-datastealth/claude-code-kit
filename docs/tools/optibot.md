# optibot — performance-focused review pass

**What it does:**
The `optibot` plugin installs an optimization-focused review skill that
inspects recently-changed code for performance issues the general
review pass tends to skip. It targets:

- algorithmic complexity — accidental O(n²) loops, repeated work that
  could be hoisted or memoized, unnecessary recursion,
- allocation patterns — hot-path heap allocations, large temporary
  buffers, string-concatenation hot spots, unnecessary copies,
- data-structure choices — list scans where a set or map would be
  O(1), repeated dictionary lookups that could be local bindings,
- I/O and concurrency — synchronous calls inside loops, N+1 queries,
  missed batching opportunities, lock contention surfaces,
- runtime-specific footguns — language- or framework-level patterns
  known to be slow (boxing, reflection, dynamic dispatch in tight
  loops, ORM lazy-load cascades).

It produces a structured report with each finding tied to a specific
location and a concrete fix recommendation rather than a generic
"consider performance" note.

**Why it's in this kit:**
The kit already runs `code-simplifier` as a post-implementation pass,
but simplifier targets clarity and reuse — it does not flag a clean,
idiomatic function that happens to be quadratic. Performance is a
separate axis of review, with separate failure modes, and it warrants
its own pass.

`optibot` pairs with `code-simplifier` deliberately: simplifier first
removes complexity and dead paths so optibot is reviewing the code
that will actually ship, then optibot looks at speed and cost on that
final shape. Splitting the two passes keeps each focused and keeps
their suggestions from contradicting each other.

It also acts as a cheap second opinion before merging changes that
touch hot paths — request paths, batch jobs, data pipelines — where
a single algorithmic mistake is much more expensive to fix
post-merge than to catch in review.

**When you'd disable it:**
- Early-stage prototypes where performance is not yet a concern and
  optimization suggestions would just push toward premature work.
- Glue code, configuration, scripts, and one-off utilities where the
  runtime budget is irrelevant.
- Docs-only or comment-only changes — there is nothing for optibot
  to review.
- Trivial single-line fixes where running an optimization pass is
  pure overhead.

Do not disable it for changes on a documented hot path, anything
touching loops over user-scale data, database access patterns, or
new code that will be called per-request or per-event.

**Source:**
GitHub: <https://github.com/anthropics/claude-plugins-official>
Marketplace: `anthropics/claude-plugins-official`
Plugin name: `optibot`

Install via the kit's `install.sh`, which registers the marketplace and
runs `claude plugin install optibot@anthropics/claude-plugins-official`.

The skill is pure prompt content; it operates on the working tree via
Claude Code's existing file-access tools. No profiler, no external
service, no API key.

**Cost / footprint:**
- Disk: negligible — a single markdown skill file.
- Memory / CPU: zero at idle. The skill is invoked on demand by the
  `Skill` tool and only consumes tokens while it runs.
- Network: none. The review runs entirely against the local diff.
- Dependencies: none beyond the Claude Code CLI and a working
  repository state (a diff to review).

The token cost is bounded by the size of the diff under review.
Skipping it on prototypes and glue code is cheap; running it on
hot-path changes typically pays for itself the first time it catches
a quadratic loop before production traffic does.
