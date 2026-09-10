# Code search order

## MANDATORY Code Search Order (Dual-Graph + LSP First)

For ANY code navigation, symbol lookup, or codebase exploration, use this order. **No exceptions.**

1. **Dual-graph MCP FIRST** — `graph_continue` BEFORE any file read, grep, or exploration.
   - If `needs_project=true`: call `graph_scan(project_root=<pwd>)` once.
   - Read every entry in `recommended_files` via `graph_read` — one call per file. Use `file::symbol` form when present (e.g. `src/auth.ts::handleLogin`) to get only that symbol's lines.
   - Obey `confidence` caps strictly:
     - `high` → stop, do not grep or explore further.
     - `medium`/`low` → up to `max_supplementary_greps` calls to `fallback_rg` then up to `max_supplementary_files` more `graph_read`s.
   - After edits, register them with `graph_register_edit` using `file::symbol` notation when the edit targets a specific function.
   - Log decisions/tasks/facts via `graph_add_memory` — NEVER write `context-store.json` directly.

2. **LSP SECOND** — for precise symbol intelligence when graph hints point to code:
   - `goToDefinition`, `findReferences`, `hover`, `documentSymbol`, `workspaceSymbol`, `goToImplementation`, `prepareCallHierarchy`, `incomingCalls`, `outgoingCalls`.
   - Prefer LSP over grep when searching for a symbol — it understands scope, imports, and types. Grep matches strings; LSP matches meaning.

3. **Built-in Read/Grep/Glob THIRD** — only after 1+2 are exhausted or explicitly insufficient.

4. **Bash grep/find/cat/sed/awk — FORBIDDEN.** Never. They require permission, stall autonomous work, and lose structure. Use `Grep`/`Glob`/`Read`/`Edit` tools instead.

**Red flags** (stop and reset to step 1):
- "Let me just grep for X first" → NO. `graph_continue` first.
- "I know where that file is" → Still call `graph_continue`; it may surface a better entry point and it records context.
- `graph_continue` + LSP + targeted `graph_read` should answer most questions with ZERO grep.

---

Anything in `~/.claude/rules/00-user-overrides.md` overrides this file. If the two disagree, follow the override and say which rule you are setting aside.
