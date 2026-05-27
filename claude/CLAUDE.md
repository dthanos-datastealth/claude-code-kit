# Global Claude Code Configuration

## Core Principles
- Be concise and direct. Lead with the answer, skip preamble.
- Minimum viable changes — don't refactor, add comments, or improve things not asked.
- Evidence before assertions — verify before claiming anything works.
- **NEVER speculate about root causes and then act on the speculation.** All solutions MUST be based on definitive evidence from authoritative research OR directly observed evidence from testing. If the cause is unknown, gather evidence first — do not propose fixes based on hypotheses alone.
- No emojis unless explicitly requested.
- NEVER add `Co-Authored-By: Claude` or any Claude authorship line to git commits. Claude is never a commit author.

---

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

## Installed Plugins & When to Use Them

### Superpowers (Primary Workflow Engine)
The backbone for all serious development work. Always invoke `/superpowers:using-superpowers` at the start of any new conversation.

| Skill | When to Use |
|-------|------------|
| `superpowers:brainstorming` | BEFORE any creative work — features, components, new behavior |
| `superpowers:writing-plans` | BEFORE touching code on multi-step tasks |
| `superpowers:using-git-worktrees` | BEFORE feature work that needs isolation |
| `superpowers:test-driven-development` | BEFORE writing implementation code (RED → GREEN → REFACTOR) |
| `superpowers:systematic-debugging` | BEFORE proposing fixes for any bug or test failure |
| `superpowers:executing-plans` | When executing a written plan in a separate session |
| `superpowers:subagent-driven-development` | When plan has independent parallel tasks |
| `superpowers:dispatching-parallel-agents` | When 2+ independent tasks can run without shared state |
| `superpowers:verification-before-completion` | BEFORE claiming work is complete or tests pass |
| `superpowers:requesting-code-review` | After completing tasks or before merging |
| `superpowers:receiving-code-review` | When processing review feedback — verify before implementing |
| `superpowers:finishing-a-development-branch` | When implementation is done and tests pass |
| `superpowers:writing-skills` | When creating or editing skills |

### Feature Dev (`feature-dev:feature-dev` or `/feature-dev`) — MANDATORY FOR NEW FEATURES
**Always use this for any new feature implementation.** It runs a structured 7-phase workflow with specialized subagents.

| Phase | What Happens |
|-------|-------------|
| 1. Discovery | Clarifies requirements, confirms understanding |
| 2. Codebase Exploration | Launches parallel `code-explorer` agents to map architecture |
| 3. Clarifying Questions | **Asks all ambiguities before designing** — never skips this |
| 4. Architecture Design | Parallel `code-architect` agents present approaches + trade-offs |
| 5. Implementation | Builds only after explicit user approval |
| 6. Quality Review | Parallel `code-reviewer` agents check simplicity, bugs, conventions |
| 7. Summary | Documents decisions and next steps |

**Mandatory triggers:** Any time the user says "add", "build", "create", "implement", or "new feature".
**Do NOT skip phases** — especially Phase 3 (clarifying questions) and the approval gate before Phase 5.

### Language Servers (LSP) — Active Automatically
These provide code intelligence (go-to-definition, find references, error checking) and are active when working in the relevant files. No manual invocation needed.

- **gopls-lsp** — Go files (`.go`). Requires: `go install golang.org/x/tools/gopls@latest`
- **typescript-lsp** — TypeScript/JavaScript files (`.ts`, `.tsx`, `.js`, `.jsx`, `.mts`, `.mjs`). Requires: `npm install -g typescript-language-server typescript`

If LSP features aren't working, verify the server binaries are installed and on `$PATH`.

### Playwright (Browser Automation)
MCP server for browser automation and E2E testing. Use for:
- Writing and running end-to-end tests
- Automating browser interactions (form fills, clicks, screenshots)
- Testing web UIs without manual intervention

### Context7 (Live Documentation)
MCP that fetches up-to-date, version-specific library docs directly from source. Use it when:
- Working with any external library or framework
- Claude's knowledge about an API might be stale
- Need accurate code examples for a specific version

### Code Simplifier (`/simplify`)
Reviews changed code for reuse, quality, and efficiency. Invoke after completing an implementation to clean up what was changed.

### Frontend Design (`superpowers:frontend-design` or `/frontend-design`)
Generates production-grade, distinctive UI — avoids generic AI aesthetics. Use for:
- Building web components, pages, or full interfaces
- When design quality matters (not throwaway prototypes)
- **Never use** generic fonts (Inter, Arial, Roboto) or purple gradients

### Claude MD Management
Two tools for keeping CLAUDE.md files accurate:
- `claude-md-management:claude-md-improver` — Audit and improve any CLAUDE.md
- `/revise-claude-md` — Capture session learnings at end of session

Use `/revise-claude-md` at the end of any session where new patterns, gotchas, or conventions were discovered.

### Notion Integration
Full Notion workspace access via MCP. Key slash commands:
- `/Notion:search` — Search workspace
- `/Notion:create-task` — Create task with defaults
- `/Notion:tasks:build <url>` — Build implementation task from a Notion page
- `/Notion:tasks:plan <url>` — Create plan from a Notion page
- `/Notion:tasks:explain-diff` — Document a code change in Notion

Use for: capturing decisions, meeting prep, turning specs into tasks, knowledge documentation.

### Sourcegraph (Code Search)
MCP for searching large codebases, finding references, navigating symbols. Use when:
- Working across repos or unfamiliar codebases
- Finding where a symbol is defined or used
- Searching commit history or diffs
- `/sourcegraph:sg-search` — Natural language or keyword search
- `/sourcegraph:sg-file` — Fetch and summarize a specific file

### Berry (Evidence Verification) — MANDATORY

Berry is an MCP-backed hallucination detection system installed via the `berry@berry-marketplace` plugin. It exposes MCP tools (`start_run`, `add_span`, `add_file_span`, `audit_trace_budget`, `detect_hallucination`, etc.) and six workflow skills that encode when and how to call them.

**Skills are the entry points. MCP tools are what the skills call internally.**

#### Mandatory triggers — no exceptions

| Situation | Use this skill | Verification gate |
|-----------|---------------|-------------------|
| Writing or reviewing any plan | `berry-plan-and-execute` | Every plan step must pass `audit_trace_budget` before execution is approved |
| Any RCA or debugging session | `berry-rca-fix-agent` | ROOT_CAUSE must pass before writing a fix; FIX_VERIFIED must pass before closing |
| Claiming tests pass or work is complete | `berry-search-and-learn` | Capture actual test output as a Berry span; cite it in the completion claim |
| Generating boilerplate, config, migrations, docs | `berry-generate-boilerplate` | Design intent trace must pass `audit_trace_budget` before delivering the artifact |

#### Hard rules

- **No facts without citations.** Every factual claim must end with a Berry span citation `[S0]`, `[S1]` etc. If you cannot cite it, it is an **Assumption** — label it as such, never present it as fact.
- **Verification must pass before proceeding.** If `audit_trace_budget` flags claims, gather more evidence and re-run. Do not move forward with unresolved failures.
- **3-strike rule.** If `audit_trace_budget` fails 3 consecutive times on the same claim set: STOP, surface what passed and what flagged with reasons, and wait for user guidance. Do not silently loop or drop failures.
- **Test output is evidence.** Always capture real test runner output as a Berry span via `add_span`. Never claim tests pass without a span that cites the actual output.
- **RCA root cause must be verified before implementing a fix.** No exceptions.

#### `audit_trace_budget` API usage (CRITICAL — wrong format = always 0 bits)

The `spans` parameter must use `{"sid": "<id>", "text": "<content>"}` format. **Do NOT use `{"<id>": "<content>"}` — that silently produces 0 observed bits every time.**

```python
# CORRECT — Berry source uses getattr(s, "sid") and getattr(s, "text")
spans=[{"sid": "S0", "text": "actual test output content here"}]

# WRONG — sid and text attributes not found, P(YES|post) ≈ P(YES|prior) ≈ 0
spans=[{"S0": "actual test output content here"}]
```

The `observed_bits` value is the KL divergence between P(YES | span in context) and P(YES | span redacted). If the verifier cannot read your span (wrong key names), both probabilities are near-zero and `observed_bits = 0`, causing the verification to fail with "insufficient bits" regardless of how good your evidence is. When you see 0 or near-0 bits on a span you believe is genuine, check the key names first.

#### Verifier backend

Local llama-server at `http://127.0.0.1:8080/v1` (Qwen3-Coder-30B-A3B, KV cache 8-bit, autostart via launchd). If Berry's verifier is unreachable: `launchctl load ~/Library/LaunchAgents/com.llamacpp.server.plist`

---

## Workflow Order (For Any Non-Trivial Task)

**For new features → use `/feature-dev` (handles phases 1–7 automatically)**

**For bugs, refactors, or tasks without `/feature-dev`:**
1. **Brainstorm** — `/superpowers:brainstorming` to explore intent and design
2. **Plan** — `/superpowers:writing-plans` to break into 2-5 min tasks → **use `berry-plan-and-execute` skill to verify the plan before executing**
3. **Isolate** — `/superpowers:using-git-worktrees` for a clean branch
4. **TDD** — `/superpowers:test-driven-development` (write failing test first)
5. **Build** — Implement, using Context7 for current library docs
6. **Verify** — `/superpowers:verification-before-completion` + **`berry-search-and-learn` with actual test output as spans** — verification must pass before claiming done
7. **Review** — `/superpowers:requesting-code-review`
8. **Simplify** — `/simplify` to clean up changed code
9. **Finish** — `/superpowers:finishing-a-development-branch`
10. **Document** — `/revise-claude-md` to capture learnings

---

## Explanatory Output Style
A SessionStart hook is active that adds `★ Insight` blocks after code. These explain:
- Why specific implementation choices were made
- Patterns and trade-offs relevant to this codebase
- Non-obvious decisions

This is educational context — do not suppress it.

---

## Memory System
Persistent memory lives at `~/.claude/projects/<your-project-encoded>/memory/`. Save memories for:
- User preferences and role context
- Feedback / corrections (most important — prevents repeating mistakes)
- Project goals and constraints
- External system references (Notion DBs, Sourcegraph endpoints)

**Do NOT save** to memory: code patterns, git history, debugging solutions, or anything derivable from the codebase.

> Note: Claude Code encodes your project directory path as a dash-separated string under `~/.claude/projects/`. For a project at `/home/alice/repos`, the encoded form is `-home-alice-repos`. The auto-memory hook resolves this for you.
