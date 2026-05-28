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

## MANDATORY Quality Loop (TDD → Berry → V+O)

This is the unconditional discipline that runs around **every substantive change** the kit ships, regardless of which workflow (default, `/feature-dev`, or spec-kit) framed it. The plugin sections below describe the *tools*; this section describes the *rules they enforce*.

### TDD discipline (always; no exceptions for "small" changes)

- Write the **failing test first** (RED). Run it; confirm it fails for the *right reason* — not for missing imports, typos, or fixture gaps.
- Implement the minimum that makes the test pass (GREEN). Do not add unrequested features.
- REFACTOR only with the test green. If you can't keep it green during refactor, stop and split the refactor into smaller steps.
- **Lifecycle tests, not just function-centric ones.** For anything stateful (sessions, caches, queues, write paths), assert on the full create → use → close → reopen → cleanup cycle. Function-only tests miss the failures that matter.
- Skill: `superpowers:test-driven-development`.

### Berry verification (load-bearing — fails the build if skipped)

- Every claim a session ships with — "tests pass", "the bug is fixed", "the spec is complete", "the plan is sound" — must be backed by a Berry span. No exceptions.
- Test output is the canonical evidence form: capture it via `berry-search-and-learn` and cite it before any "tests pass" assertion.
- See the **Berry** plugin section below for the mandatory triggers, hard rules, `audit_trace_budget` API contract, and the OpenRouter backend configuration.

### V+O loop (after each substantive change to a tracked artifact)

After any code commit, doc change, or config change that affects behavior, run the two-agent **Verification + Optimization** loop against that same revision before declaring the change complete:

- **V — Verification agent.** Dispatched to verify the change against **authoritative external sources** (upstream READMEs, official docs, the kit's own spec/plan, vendor API references). Its job is to catch correctness drift between the change and reality. Output: `[OK]` / `[CONCERN]` / `[BLOCKER]` per check, with citations.
- **O — Optimization agent.** Dispatched in parallel to find simplification / clarity / consistency wins on the same revision. Output: `[trivial]` / `[worth-considering]` / `[worth-fixing]` per finding.
- Verdicts of either agent block "done" — if V flags a `[CONCERN]` or `[BLOCKER]`, fix it before moving on; if O flags `[worth-fixing]`, apply the fix in a follow-up commit before the next substantive change lands.
- Run V and O **in parallel** (independent reviews of the same state). Use `subagent_type: general-purpose` for V (it needs WebFetch + Read), `subagent_type: code-simplifier:code-simplifier` for O.

The kit's `requesting-code-review`, `code-quality-reviewer`, and `code-simplifier` plugins implement the V and O roles inside `superpowers:subagent-driven-development`'s built-in two-stage review; the V+O loop above sits **on top** of that, with one explicit difference: V+O verifies against **external authoritative sources**, not just against the local spec or the diff itself.

### Hard prohibitions for the quality loop

- Do not claim "tests pass" without a Berry span citing the actual test runner output.
- Do not skip V+O on the grounds that "the change is small" — small changes are exactly where unaudited drift accumulates.
- Do not invent answers when V flags a `[CONCERN]` — gather more evidence or escalate.
- 3-strike rule: if a Berry audit fails three consecutive times on the same claim set, STOP and surface the partial results. Do not silently loop.

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
- **jdtls-lsp** — Java files (`.java`). Requires the `jdtls` launcher on `$PATH` plus a **JDK 21+** runtime (upstream Eclipse JDT.LS minimum). macOS install: `brew install openjdk@21 jdtls`.

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

### Chrome DevTools MCP (`chrome-devtools-mcp`)
Low-level Chrome DevTools Protocol access — performance traces, network inspection, console capture, accessibility audits, memory snapshots. Use when Playwright's higher-level API is insufficient (LCP debugging, memory leak hunts, real-network-condition emulation). Requires Chrome/Chromium with `--remote-debugging-port` enabled.

### Microsoft Docs (`microsoft-docs`)
MCP for searching and fetching from Microsoft Learn (Azure, .NET, M365, Windows, Bicep, etc.). Use whenever code touches a Microsoft SDK or API — catches hallucinated `.NET` methods and confirms current signatures. Three sub-tools: `microsoft_docs_search` (breadth), `microsoft_code_sample_search` (working snippets), `microsoft_docs_fetch` (full pages).

### Hugging Face Skills (`huggingface-skills`)
A bundle of 12+ skills for Hugging Face Hub workflows: model selection by benchmark (`huggingface-best`), local inference (`huggingface-local-models` via llama.cpp), training (sentence-transformers, vision, LLM via TRL/Unsloth on HF Jobs), datasets (`huggingface-datasets`), papers (`huggingface-papers`), Gradio (`huggingface-gradio`), Trackio, ZeroGPU, and the `hf` CLI. Use for any ML-engineering task that touches the Hub. Some skills need `hf` CLI + a Hugging Face API token.

### Security Guidance (`/security-review`)
Security-aware code review skill that scans pending changes for OWASP-top-10-class issues. Use before merge on any code that handles auth, input parsing, file uploads, secrets, network calls, or DB queries. Complements (not replaces) the general code-review skill.

### Optibot (`optibot`)
Optimization-focused review skill — targets performance, allocations, complexity. Pairs with `code-simplifier`: simplifier targets *clarity*, optibot targets *speed/cost*. Use after profiling has identified a hot path, or when shipping code into a known throughput / latency budget. Skip for prototypes where perf isn't a concern yet.

### Remember (`/remember`)
Session-state checkpointing skill. Persists transient task state across session boundaries — bridges the auto-memory system's gap for in-progress work that isn't a "memory" yet but needs to survive a session restart. Use at session end when work is mid-flight; the next session can `/remember` to resume.

### Andrej Karpathy Skills (`andrej-karpathy-skills`)
Behavioral guidelines (Karpathy-style) for reducing common LLM coding failure modes — overcomplication, surface assumptions, weak success criteria, missing error-class definitions. Low cost, broadly applicable; the kit leaves it on by default. Complements superpowers' workflow discipline with content-specific heuristics.

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

The `observed_bits` value is the KL divergence between P(YES | span in context) and P(YES | span redacted). If the verifier cannot read your span (wrong key names), both probabilities collapse to near-zero, so `observed_bits = 0` and the verification fails with "insufficient bits" regardless of how good your evidence actually is. When you see 0 or near-0 bits on a span you believe is genuine, check the key names first.

#### Verifier backend

OpenRouter-hosted `openai/gpt-4o-mini` via Berry's OpenAI-compatible client. Two files configure this — `~/.berry/mcp_env.json` is **load-bearing** (Berry's MCP launcher reads these env vars at startup); `~/.berry/config.json` is what the `berry-configure` skill writes for its own bookkeeping. Keep them in sync.

```jsonc
// ~/.berry/mcp_env.json — LOAD-BEARING: read by the MCP launcher
{
  "OPENAI_API_KEY": "<your-openrouter-key>",
  "OPENAI_BASE_URL": "https://openrouter.ai/api/v1",
  "BERRY_VERIFIER_BACKEND": "openai",
  "BERRY_VERIFIER_MODEL": "openai/gpt-4o-mini"
}

// ~/.berry/config.json — written by berry-configure; informational
{
  "verifier": {
    "backend": "openai",
    "model": "openai/gpt-4o-mini",
    "base_url": "https://openrouter.ai/api/v1",
    "api_key": "<your-openrouter-key>"
  }
}
```

If verification calls start failing, first check that the OpenRouter key is still valid (`curl -H "Authorization: Bearer $KEY" https://openrouter.ai/api/v1/models | head`), then check OpenRouter status. A self-hosted llama.cpp backend remains an option for offline / air-gapped work — see Berry's upstream docs for the alternative config.

---

### Spec-Kit (`specify` CLI) — optional spec-driven alternative

[GitHub `spec-kit`](https://github.com/github/spec-kit) is a CLI (`specify`) that installs a set of `/speckit-*` agent skills into a project's `.claude/skills/` directory and scaffolds a `.specify/` working area. It gives you a more formal spec-first workflow than the kit's default brainstorm → plan → TDD path: a project Constitution at the top, then per-feature Specify → Clarify → Plan → Tasks → Analyze → Implement.

**When to use spec-kit instead of `/superpowers:brainstorming` + `/superpowers:writing-plans`:**
- New greenfield project where a written Constitution + governance is the bigger win than fast iteration.
- Multi-contributor work where the specs/plans need to be artifacts other people read.
- Any feature where stakeholder review of `spec.md` will happen before implementation starts.

**When to stick with the default workflow:**
- Bugfixes, refactors, single-session changes — spec-kit's ceremony overhead doesn't pay back at small scale.
- Anything that's already mid-flight in a `/feature-dev` run.

**Setup (per project, one-time):**
```sh
specify init --here --integration claude   # writes .claude/skills/speckit-* + .specify/
```

After init, the slash commands appear after a Claude Code restart:
- `/speckit-constitution` — project principles (run first, once)
- `/speckit-specify` — feature spec from a natural-language description
- `/speckit-clarify` (optional) — drive out ambiguities before planning
- `/speckit-plan` — tech stack + implementation plan
- `/speckit-tasks` — actionable task list
- `/speckit-analyze` (optional) — cross-artifact consistency check
- `/speckit-implement` — execute all tasks

Berry verification stacks on top of every spec-kit step — the playbook below specifies exactly where (Step 8). The hard prohibitions also forbid bypassing Berry by switching modes.

#### How Claude drives spec-kit on the user's behalf (SDD playbook)

When the user asks for something that fits a spec-driven flow (new feature, greenfield project, multi-step work that will outlive this session), follow this playbook **before** writing any code:

In each step below, behavior labelled **[upstream]** matches the official spec-kit workflow as documented in <https://github.com/github/spec-kit>; behavior labelled **[kit policy]** is stricter than upstream and reflects this kit's discipline. Both layers apply when working in a project that has adopted this kit.

**1. Detect the project's spec-kit state.** Check if `.specify/` exists at the project root.
- **Exists** → existing spec-kit project; check `.specify/memory/constitution.md` to see if the Constitution is filled in. If not, the user is mid-setup; offer to run `/speckit-constitution`.
- **Does not exist** → ask the user before running `specify init --here --integration claude`. Initialization writes files into their project, so it needs explicit consent — but once consented, do it via the shell yourself; do not ask the user to run the command. After init, the `/speckit-*` slash commands may not register until the agent re-discovers skills (in most agents this requires a session restart). **Stop and ask the user to restart** rather than guessing — invoking a skill that hasn't loaded yet wastes a turn.

**2. Constitution before first spec [kit policy — stricter than upstream].** If `.specify/memory/constitution.md` is empty or placeholder-only, this kit requires you to run `/speckit-constitution` first (or ask the user to) before any `/speckit-specify`. Upstream's `speckit-implement` skill only requires the Constitution to exist *if present*, but skipping it leaves `/speckit-analyze` with no consistency baseline to check against — which is exactly the gate the kit relies on.

**3. Spec describes WHAT and WHY, not HOW [upstream].** In `/speckit-specify`, focus on user goals, acceptance criteria, and constraints. Do not name a tech stack, framework, or library — those belong in `/speckit-plan`. Upstream is explicit: *"Be as explicit as possible about what you are trying to build and why. Do not focus on the tech stack at this point."* If the user describes the request in tech-stack terms ("build a React app with..."), separate the WHAT from the HOW: capture WHAT in spec, defer HOW to plan.

**4. Clarify when ambiguous [upstream — strongly recommended].** After `/speckit-specify`, scan the produced `spec.md` for open questions, vague requirements, or unstated assumptions. If you find any, run `/speckit-clarify` before proceeding. **Do not invent answers** — clarify gets the user to commit to a single interpretation. The cost of one clarification round is far smaller than the cost of implementing the wrong interpretation.

**5. Plan establishes the HOW [upstream].** Run `/speckit-plan` with the chosen tech stack and architectural decisions. Cite the relevant `docs/tools/*.md` entries for any plugin/MCP/LSP the plan depends on.

**6. Tasks decompose the plan [upstream].** Run `/speckit-tasks` to generate an actionable task list. Upstream organizes tasks by phase and user story, with the rule that each task should be independently testable; upstream does NOT impose a minute bound. The kit's separate `superpowers:writing-plans` discipline does enforce 2–5 minute task granularity, so when you are working in *spec-kit mode* and the upstream output produces coarser tasks, decompose them further before handing off to `/speckit-implement` — the TDD step downstream is easier when tasks are bite-sized.

**7. Analyze before implementing [kit policy — stricter than upstream].** Run `/speckit-analyze` after `/speckit-tasks`. Upstream documents Analyze as *optional*; this kit treats it as mandatory because cross-artifact drift (Constitution ↔ spec ↔ plan ↔ tasks) is the most common spec-driven failure mode, and analyze catches it for the cost of one query.

**8. Implement under Berry [kit overlay].** Run `/speckit-implement` to execute the task list. Spec-kit itself has no verification overlay; this kit adds one: every step routes through `berry-plan-and-execute` per the Berry hard rules — no shortcuts. Test output is always captured as a Berry span (`berry-search-and-learn`) before any "tests pass" claim.

**9. Update spec when intent changes [kit policy — derived from SDD principles].** If the user changes their mind mid-implementation, **update the spec first** (re-run `/speckit-specify` or edit `spec.md` directly), then re-run `/speckit-analyze` to surface what else needs to change. Upstream does not document this explicitly, but the principle is fundamental to spec-driven development — once implementation is allowed to drift from spec, the spec stops being a source of truth and becomes a lie that grows over time.

**Hard prohibitions for spec-driven mode (this kit):**
- Do not start implementation before the spec is approved by the user.
- Do not skip `/speckit-analyze` because "the plan looks fine to me."
- Do not run `/speckit-implement` if the Constitution is empty (kit-policy gate).
- Do not invent answers to spec ambiguities — always `/speckit-clarify`.
- Do not bypass Berry gates by switching to spec-driven mode; both layers stack.

**Relationship to `/feature-dev`:** the global guidance "use `/feature-dev` for any new feature" assumes you have NOT opted into spec-kit for the project. When `.specify/` exists, **use spec-kit for new features instead of `/feature-dev`** — they cover the same ground (spec → plan → implement) but spec-kit produces durable on-disk artifacts (`spec.md`, `plan.md`, `tasks.md`) that survive across sessions, while `/feature-dev`'s subagent outputs are session-scoped. Do not run both for the same feature.

If spec-kit isn't initialized and the user's request is small (bugfix, refactor, single-session task), use the default brainstorm → plan → TDD flow instead. Spec-kit overhead does not pay back at small scope.

---

### Caveman — terse-output mode for token/context savings

[`caveman`](https://github.com/JuliusBrussee/caveman) is a Claude Code skill (not a marketplace plugin) that makes the agent reply in radically condensed prose — short sentences, no filler, minimal markdown. Upstream measures the saving at roughly 65% fewer output tokens. The skill is opt-in per session, not always-on.

**When to invoke caveman:**
- Long working sessions where output tokens dominate cost (e.g. bulk refactors, large doc generation).
- High-throughput review/triage where you want answers, not explanations.
- When context is filling up and you need the agent to compress what it says without losing what it does.

**When NOT to invoke caveman:**
- Explanatory work where reasoning matters (debugging walkthroughs, teaching, design exploration).
- Code review feedback that the user will read carefully — terse output loses nuance.
- Any session under the `explanatory-output-style` plugin's `★ Insight` regime (the two styles conflict).

**Install (one-time):**
```sh
gh repo clone JuliusBrussee/caveman ~/.claude/skills/caveman
```
After a Claude Code restart, the skill is available globally. To use it in a session, invoke the skill explicitly (e.g. `/caveman`) — it modifies the agent's output style for the rest of that session until cleared.

**Hard rule:** caveman never overrides the kit's mandatory rules. Berry verification, evidence-before-assertions, the MANDATORY code-search order, and the spec-kit / Berry hard prohibitions all still apply — caveman compresses *how* the agent reports work, not *whether* the work meets the kit's quality gates.

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
- External system references (Notion DBs, internal wikis, dashboards)

**Do NOT save** to memory: code patterns, git history, debugging solutions, or anything derivable from the codebase.

> Note: Claude Code encodes your project directory path as a dash-separated string under `~/.claude/projects/`. For a project at `/home/alice/repos`, the encoded form is `-home-alice-repos`. The auto-memory hook resolves this for you.
