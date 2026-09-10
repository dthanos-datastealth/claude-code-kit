# Code search order

## MANDATORY Code Search Order (Dual-Graph + LSP First)

For ANY code navigation, symbol lookup, or codebase exploration, use this order. **No exceptions.**

1. **Dual-graph MCP FIRST** — `graph_continue` BEFORE any file read, grep, or exploration.
   - If `needs_project=true`: call `graph_scan(project_root=<pwd>)` once.
   - Read every entry in `recommended_files` via `graph_read` — one call per file. Use `file::symbol` form when present (e.g. `src/auth.ts::handleLogin`) to get only that symbol's lines.
   - Obey `confidence` caps strictly:
     - `high` → stop, do not grep or explore further.
     - `medium`/`low` → up to `max_supplementary_greps` calls to `fallback_rg` then up to `max_supplementary_files` more `graph_read`s.
   - **One exception to the `high` stop: if every entry in `recommended_files` is a test file, keep looking.** A graph that has indexed the tests but not the implementation answers confidently with the wrong files, and the supplementary budget at `high` is zero — so obeying the cap literally means answering from tests and never reaching the code. Spend a supplementary call, or re-query naming the symbol you expect.
   - After edits, register them with `graph_register_edit` using `file::symbol` notation when the edit targets a specific function.
   - Log decisions/tasks/facts via `graph_add_memory` — NEVER write `context-store.json` directly.

2. **LSP SECOND** — for precise symbol intelligence when graph hints point to code:
   - `goToDefinition`, `findReferences`, `hover`, `documentSymbol`, `workspaceSymbol`, `goToImplementation`, `prepareCallHierarchy`, `incomingCalls`, `outgoingCalls`.
   - Prefer LSP over grep when searching for a symbol — it understands scope, imports, and types. Grep matches strings; LSP matches meaning.

3. **Structured file tools THIRD** — only after 1+2 are exhausted or explicitly insufficient. Where the harness provides them these are `Read`, `Grep`, `Glob` and `Edit`.

4. **Prefer structured tools over shell text-slinging.** `grep`/`find`/`cat`/`sed`/`awk` in Bash lose structure, and in the default permission mode they also prompt, which stalls autonomous work.

   **This is a preference, not an absolute, because the tools it names are not always present.** Claude Code's permission modes decide the tool surface: under `auto` mode `Grep` and `Glob` do not exist at all, and that mode's own instructions direct work through Bash. Tool availability is set before any rule file is read, so nothing here can conjure a missing tool.

   So: use the structured tools when they exist. When they do not, use the shell equivalents and say once that you are doing so and why. Do not stall, and do not pretend a tool is available that is not. What is **not** negotiable is step 1 — `graph_continue` first — which is the part of this order that carries the value and does not depend on which file tools the harness exposes.

**Red flags** (stop and reset to step 1):
- "Let me just grep for X first" → NO. `graph_continue` first.
- "I know where that file is" → Still call `graph_continue`; it may surface a better entry point and it records context.
- `graph_continue` + LSP + targeted `graph_read` should answer most questions with ZERO grep.

---

Anything in `~/.claude/rules/00-user-overrides.md` overrides this file. If the two disagree, follow the override and say which rule you are setting aside.
