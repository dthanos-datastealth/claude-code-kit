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
The kit's rules in `~/.claude/rules/` makes graph-first navigation mandatory. Grep matches
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
NOT bundled with this kit — an external prerequisite you install and register
yourself. The reference implementation is the `graperoot` package on PyPI
(<https://pypi.org/project/graperoot/>), whose repository is
<https://github.com/kunal12203/Codex-CLI-Compact>; it provides the
`mcp-graph-server` binary the registration points at. Any MCP server exposing
the same tool contract works just as well. `install.sh` neither installs nor
registers it. [`docs/prereqs.md`](../prereqs.md) section 10 owns the recipe, the
tool contract, and the supply-chain profile you should read before adopting it
— including that the engine is proprietary and closed-source, self-updates
without asking, and emits telemetry by default.

If it is absent, `CLAUDE.md` still instructs Claude to call the graph tools,
those calls fail, and exploration falls back to grep — more tokens, and the
kit's intended workflow broken.

**Cost / footprint:**
- Disk: ~50 MB index per medium-sized repository, stored under a project-local
  cache directory.
- Memory: one Python process per active project, typically a few hundred MB
  depending on repo size.
- CPU: a one-time `graph_scan` is the only heavy operation; subsequent
  `graph_continue` and `graph_read` calls are cheap lookups.
- Network: **indexing and queries are local, but the tool is not silent.**
  Upstream documents a version check, a heartbeat carrying a machine id and
  platform, a one-time feedback prompt, anonymous crash reports, and a launcher
  that checks for updates on every run and applies them without asking, from
  its own distribution channel. `graperoot --no-telemetry` and
  `graperoot --no-auto-update` are the documented opt-outs; confirm they exist
  in `graperoot --help` on the version you installed. Your code is not
  uploaded; the process is not offline either.
- Dependencies: a working Python runtime. The engine ships as compiled
  per-interpreter wheels, so check `pip download --only-binary=:all: graperoot`
  covers your interpreter and OS before relying on the PyPI install path.
