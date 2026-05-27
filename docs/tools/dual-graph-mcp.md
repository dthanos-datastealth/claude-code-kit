# dual-graph-mcp — symbol + dependency graph navigator over MCP

**What it does:**
The dual-graph MCP server is a project-local code navigator that maintains two
parallel graphs of a repository — a symbol graph (functions, classes, hooks)
and a dependency graph (imports, call relationships) — and exposes them
through MCP tools Claude can call before touching files. The headline tool,
`graph_continue`, returns a structured suggestion of which files (or specific
`file::symbol` slices) are most likely relevant to the current turn, along
with a confidence level that caps how much supplementary exploration is
allowed.

Tools exposed:
- `graph_continue` — entry point; returns `recommended_files`, `confidence`,
  and supplementary caps. Must be called before any file read or grep.
- `graph_scan` — one-time scan of a project root to build/refresh the graph.
- `graph_read` — read a file or a `file::symbol` slice (e.g.
  `src/auth.ts::handleLogin`) — returns only the symbol's lines.
- `graph_register_edit` — record an edit against the graph after a change,
  using `file::symbol` notation when the edit targets a specific function.
- `graph_add_memory` — append a typed memory entry (decision, task, next,
  fact, blocker) to the project's context store.
- `fallback_rg` — a constrained ripgrep escape hatch used only when
  `confidence` is medium or low and graph hints proved insufficient.

**Why it's in this kit:**
The kit's `CLAUDE.md` makes graph-first navigation mandatory. Grep matches
strings; the graph matches scope. A `graph_read("src/auth.ts::handleLogin")`
call returns just that function's lines — not the file, not the imports, not
unrelated symbols — which is orders of magnitude cheaper in context than the
grep-then-read pattern. The structured `confidence` field also keeps Claude
from sprawling into broad exploration when a high-confidence answer already
exists. And because `graph_add_memory` writes through the same server,
decisions and tasks accumulate in a single place rather than scattered across
ad-hoc files.

**When you'd disable it:**
- Projects with fewer than five files — `graph_continue` returns `skip=true`
  automatically in that case, so disabling is rarely necessary, but you can
  skip installation entirely for one-file scripts.
- Environments where you cannot run a long-lived Python process per project
  (locked-down CI containers, for example).
- Sessions whose entire purpose is to demonstrate or audit grep/find behavior
  itself.

Disable for nothing else. Even on small changes the graph saves enough context
to pay for itself many times over.

**Source:**
NOT bundled with this kit — the dual-graph MCP server is an external
prerequisite. Install it separately following its upstream documentation, then
register it with the Claude Code CLI via `claude mcp add` so the graph tools
appear in the MCP namespace. The kit's `CLAUDE.md` assumes it is installed and
will instruct Claude to call its tools; if absent, those calls fail and Claude
falls back to grep-based exploration (which costs more in tokens and breaks
the kit's intended workflow).

**Cost / footprint:**
- Disk: ~50 MB index per medium-sized repository, stored under a project-local
  cache directory.
- Memory: one Python process per active project, typically a few hundred MB
  depending on repo size.
- CPU: a one-time `graph_scan` is the only heavy operation; subsequent
  `graph_continue` and `graph_read` calls are cheap lookups.
- Network: none — the server runs entirely on the local machine.
- Dependencies: a working Python runtime and whatever the upstream
  installation instructions specify (typically tree-sitter parsers for the
  languages you want indexed).
