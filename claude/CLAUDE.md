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

This is the unconditional discipline that runs around **every substantive change** the kit ships, regardless of which workflow (default, `/feature-dev`, or spec-kit) framed it. The plugin catalogue below describes the *tools*; this section describes the *rules they enforce*. The reasoning and the incidents behind the prohibitions are in `~/.claude/docs/verification-standards.md`.

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

The kit's `superpowers:requesting-code-review` skill, `feature-dev:code-reviewer` subagent, and `code-simplifier` plugin implement the V and O roles inside `superpowers:subagent-driven-development`'s built-in two-stage review; the V+O loop above sits **on top** of that, with one explicit difference: V+O verifies against **external authoritative sources**, not just against the local spec or the diff itself.

### Hard prohibitions for the quality loop

- Do not claim "tests pass" without a Berry span citing the actual test runner output.
- Do not skip V+O on the grounds that "the change is small" — small changes are exactly where unaudited drift accumulates.
- Do not invent answers when V flags a `[CONCERN]` — gather more evidence or escalate.
- 3-strike rule applies (see the Berry section below for the canonical statement): if a Berry audit fails three times on the same claim set, STOP and surface partial results. No silent looping.
- **Never verify a user-facing or protection feature with a synthetic proxy.** Driving your own element, reading back a value you set, dispatching an event straight to a handler, or treating a toast as proof all test a proxy you control. Drive the REAL widget and assert the GROUND TRUTH (for data protection: the outbound request carries zero raw values). If the harness cannot drive the real widget that is a BLOCKER — escalate, do not substitute.
- **A script can never confirm a visual result.** Any image, rasterised page or painted canvas must be viewed at legible resolution, every page, whole page. Re-OCR, pixel statistics and "0 leaked" counts choose what to look at; they are never confirmation. If a render has not been viewed, say so.
- **The O agent hunts redundant WORK, not just redundant code** — enumerate every expensive operation in the diff, trace each flow end to end, and state per call site whether it is cached+reused or recomputed. A report without that trace is itself a finding. Pair `optibot` with `code-simplifier` whenever a hot path is touched.

All three guard the same failure: a check that cannot observe the defect it is
meant to catch reports success, and ends the investigation. The exact forbidden
patterns, the failure mode behind each rule and the O agent's finding taxonomy
are in `~/.claude/docs/verification-standards.md` — read it before arguing that
one of them does not apply.

---

## MANDATORY: TRACKER.md + Task tool — the collaboration substrate

The quality loop above does not run on agent memory or chat scrollback. It runs on **two coupled artifacts**:

1. **Claude Code `Task` tool** — `TaskCreate` / `TaskUpdate` / `TaskList` / `TaskGet` for live, machine-readable task state every agent reads and writes.
2. **`docs/TRACKER.md`** (per project) — the durable Markdown record of what happened, what's in flight, what's open, what V/O produced. Single source of truth for any human or future agent reviewing the project.

Full reference doc: `~/.claude/docs/tracker-system.md` (installed by `install.sh`). What follows is the agent-side rule set Claude reads every session.

### Phase Start Protocol (coordinator)

Before starting any new phase, the coordinator MUST:

1. **`EnterPlanMode`** and produce a detailed technical plan for the phase — discrete testable sub-tasks; every file to create or modify; TDD sequence (what fails first, what makes it pass); integration points; known risks.
2. **Get explicit user approval** of the plan.
3. **`ExitPlanMode`** only after approval.
4. **Execute against the plan** — every dev agent prompt must reference the plan and implement exactly what it specifies.

This is what keeps the discipline from sliding into ad-hoc development. The plan is the contract dev + V + O agents all measure against.

### Pre-Dispatch Protocol (coordinator)

Before dispatching any dev agent, the coordinator MUST create all three quality-loop tasks UPFRONT:

```
1. TaskCreate("Dev: Phase X — <description>")    → dev agent claims/works/completes
2. TaskCreate("Verification: Phase X")           → V agent claims/works/completes
3. TaskCreate("Optimization: Phase X")           → O agent claims/works/completes
```

All three exist in the tracker BEFORE dev is dispatched. This makes the quality loop visible and prevents skipping it — the tracker enforces the loop, not coordinator memory.

After dev completes: dispatch V agent → dispatch O agent → if findings exist → dispatch fix agents per finding → re-run V + O. Phase closes ONLY when V reports `VERIFICATION: PASS` and O reports `OPTIMIZATION: APPROVED` on the SAME code revision.

### What every agent MUST do (Dev, V, O, Fix — all of them)

**At start of work:**
```
1. TaskList                         # find the assigned task
2. TaskUpdate(taskId, in_progress)  # claim it
3. Read docs/TRACKER.md             # understand current phase state
4. Read the relevant plan section
5. Do the work
```

**During work — for every finding produced:**
```
TaskCreate("Fix V-N1: <finding summary>")
```
Each finding = one new task. Findings are NOT logged only in chat and hoped-to-be-actioned — they enter the tracker as concrete units of work.

**At end of work:**
```
1. TaskUpdate(taskId, completed)
2. Update docs/TRACKER.md:
   - Closed a finding → update the V/O Findings Tracker row
   - Completed a stage → update the Quality Loop State row
   - Completed an iteration → append a new "## YYYY-MM-DD Iter-N" section
3. If new follow-up items surfaced → append to the section's "Open issues"
```

### Coordinator hard prohibitions

- **Coordinators do not update the tracker on behalf of agents.** If an agent finished work without calling `TaskUpdate` or editing `docs/TRACKER.md`, that's evidence the agent didn't have the task context it needed. Fix the agent's prompt — do NOT paper over the missing context by patching the tracker yourself.
- **No phase closes without V + O on the same revision.** If V finds something, the fix lands as a new task, V and O re-run on the new revision, then the phase closes.

### Verification Agent Protocol (mandatory)

Skipping any step is a verification failure.

- **Step 0 — PRD Requirement Mapping.** For each requirement in the task spec (PRD, plan, or explicit acceptance criteria), trace it to a specific file:line in the implementation. If a requirement has no corresponding code, that is a `[REQUIREMENT GAP]` finding — file it as a task and surface it before proceeding to Step A. Skip this step ONLY when the task has no PRD-style requirements to map (e.g., a docs-only change).
- **Step A — Identify the real target function.** Read the implementation; note every exported symbol and its signature.
- **Step B — Trace the test's call path.** Confirm tests import the real module, use the real exported symbol, with the real package import path (not a test double).
- **Step C — Verify input → output tracing.** Does the assertion test the REAL function's REAL output, or a mock response independent of the real code path? Mock-only assertions are `[SHALLOW TEST]`.
- **Step D — Check for stub/duplicate anti-patterns.** Local function with the same logic, test-only wrapper, or different file compiled = `[STUB TEST]`.
- **Step E — Behavioral coverage gap check.** Map tests to requirements; flag uncovered branches (errors, edges, negatives) as `[TEST MISSING]` with file:line.
- **Step F — Test result validity.** Run tests with verbose output. Confirm every test passes (not skipped), assertions are real, nothing passes vacuously.
- **Step G — Hot-path call-site verification (`[WIRE-PATH MISS]`).** For every new exported helper / setter / primitive in the diff: grep/LSP-search for callers. Callers must include the request handler, a `main.go` startup block, or an existing pipeline-pass file. **If the only callers are TEST files, that is a `[WIRE-PATH MISS]` finding and is BLOCKING.** Tests prove the primitive works in isolation; they do NOT prove the pipeline uses it.

For every finding the V agent produces, call `TaskCreate`. On its own task, call `TaskUpdate(status="completed")` at the end. Do NOT mark the development task complete — that is the coordinator's job after all findings close.

### Optimization Agent Protocol

- **Linter sweep:** project's linter on changed code only; 0 NEW issues required. Pre-existing issues in unrelated files = flag-don't-fix.
- **Mandatory redundancy + duplication check (dual-graph driven):** for every new function/struct/regex/helper/test fixture in the diff: (1) call `graph_continue` with the new symbol name and surrounding terms; (2) `workspaceSymbol` + `findReferences` via LSP to confirm; (3) flag `[REDUNDANT FUNCTION]` if equivalent behavior already exists; `[REDUNDANT CODE PATH]` if logic re-implements another path; `[REDUNDANT TEST]` if invariant already covered by an existing test. The O agent's report MUST show evidence of the dual-graph + LSP search (which symbols, what returned). An O report lacking this evidence is itself a finding.
- **Mandatory redundant-WORK hunt (first-class — same severity as redundant code):** redundancy is not only duplicated code, it is code that re-executes work an earlier step already did. Enumerate every expensive operation in the diff with `file:line` (network/RPC, LLM or backend classify, DB query, OCR, crypto, file parse, `context.sync()`, any cross-process `await`); trace each flow end to end (`scan → preview → save`); and state per call site whether it is **cached+reused** or **recomputed**. Flag `[REDUNDANT EXPENSIVE CALL]` (blocking), `[UNCACHED RECOMPUTATION]`, `[HOT-PATH N+1 / SYNC-IN-LOOP]` (quantify N), `[REDUNDANT ROUND-TRIP]`, `[RE-INCURRED BLOCKING WAIT]`. A report without the per-call-site trace is itself a finding. When the diff touches a hot path, run `optibot` **in addition to** `code-simplifier` — clarity-only review misses these. Taxonomy and the worked example: `~/.claude/docs/verification-standards.md`.
- **Best-practice sweep on changed code:** allocation patterns, naming, comment quality (no temporal/phase labels — those belong in TRACKER.md), idiomatic error wrapping.
- **Tracker updates:** `TaskCreate` for every finding; `TaskUpdate(status="completed")` on own task. Verdict: `APPROVED` or `CHANGES-RECOMMENDED`. Phase closes only when V says PASS AND O says APPROVED on the SAME revision.

### Hard rules around the tracker

- **`docs/TRACKER.md` must never be more than one step out of date.** Anything not in the tracker is unknown to anyone who didn't run the session.
- **Phase/iteration labels (`Iter-46`, `Phase 29`, etc.) belong in tracker / commit messages / PR descriptions / plan files — NEVER in source code comments, log strings, test assertion messages, or error strings.** Code is self-contained + functionally descriptive.
- **`Task` tool and `docs/TRACKER.md` are kept in lockstep.** Every `TaskUpdate` pairs with a `docs/TRACKER.md` edit in the same logical step.
- **Findings become tasks.** A finding logged only in chat is a comment, not a finding. Every V/O finding materializes as a `TaskCreate` AND appears in the Findings Tracker table in `docs/TRACKER.md`.

---

## Installed Plugins & When to Use Them

Every plugin, MCP and skill below has a depth-reference in
`~/.claude/docs/tools/`, installed by `install.sh`, following a strict
five-section schema: *What it does · Why it's in this kit · When you'd disable
it · Source · Cost / footprint*. The table names the file where it is not simply the tool's own name. **Read the depth-reference** before invoking a
tool whose cost you can't recall, when asked "what does X do?" or "should I
disable X?", when behaviour surprises you (the "when you'd disable it" section
lists the wrong-tool cases), or when you need the upstream source.

`~/.claude/docs/` also holds `philosophy.md` (why each rule exists),
`workflow.md` (the 10-step recipe), `verification-standards.md` (what counts as
evidence), `prereqs.md` (per-OS install commands), `corporate-tls.md` and
`memory-system.md`. If that directory is missing or thinner than the plugin
list, re-run `install.sh` — `kit_copy_docs` populates it.

| Tool | Reach for it when |
|---|---|
| **superpowers** | The backbone. Invoke `/superpowers:using-superpowers` at the start of any conversation. Brainstorm → plan → worktree → TDD → verify → review → finish. |
| **feature-dev** | **Mandatory for new features.** Any "add/build/create/implement". Seven phases; never skip phase 3 (clarifying questions) or the approval gate before phase 5. |
| **gopls / typescript / jdtls LSP** (`lsp-gopls.md`, `lsp-typescript.md`, `jdtls-lsp.md`) | Automatic in matching files. Needs the binary on `$PATH`; jdtls also needs JDK 21+. |
| **playwright** (`playwright-mcp.md`) · **chrome-devtools-mcp** | Browser automation and E2E. Drop to chrome-devtools for CDP-level work: LCP traces, memory snapshots, network conditions. |
| **context7** · **microsoft-docs** | Live library docs. Use whenever an external API is involved rather than trusting recall; microsoft-docs for anything .NET/Azure/M365. |
| **code-simplifier** (`/simplify`) · **optibot** | The O role. Simplifier targets clarity, optibot targets speed and cost — pair them on hot paths. |
| **security-guidance** (`/security-review`) | Before merging anything touching auth, input parsing, uploads, secrets, network or DB. |
| **frontend-design** | Production-grade UI. Never generic fonts or purple gradients. |
| **notion** | Capture decisions, turn specs into tasks, meeting prep. |
| **huggingface-skills** | Any ML-engineering task touching the Hub. |
| **claude-md-management** | `/revise-claude-md` at the end of a session that discovered new patterns. |
| **remember** (`/remember`) | Session end with work mid-flight. |
| **claude-code-kit** | This kit's own plugin. `/claude-code-kit:status` reports the installed channel, version and commit; `:upgrade` and `:rollback` drive the upgrade scripts; `:fix-notion-mcp-port` repairs the Notion re-auth port. |
| **andrej-karpathy-skills** | Always on. Reduces overcomplication and unstated assumptions. |
| **caveman** | Opt-in terse output when token cost dominates. Never overrides the mandatory rules above — it compresses how work is reported, not whether it meets the gates. |
| **spec-kit** | Optional spec-first alternative for greenfield or multi-contributor work. The full playbook, including where this kit is stricter than upstream, is in `~/.claude/docs/tools/spec-kit.md`. Do not run it and `/feature-dev` for the same feature. |

### Berry (Evidence Verification) — MANDATORY

Berry is an MCP-backed hallucination detection system installed via the `berry@berry-marketplace` plugin. It exposes MCP tools (`start_run`, `add_span`, `add_file_span`, `audit_trace_budget`, `detect_hallucination`, etc.) and seven workflow skills that encode when and how to call them.

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

#### `audit_trace_budget` API usage

**CRITICAL — a step without `cites` verifies nothing.** Two things have to be right, and getting either wrong produces a `flagged` result that looks exactly like a failed claim.

**1. Every step must cite the spans that support it.** `context_mode` defaults to `"cited"`, which selects only the spans a step names in `cites`. A step with no `cites` gets an empty context, the verifier is never called, and the result comes back flagged.

**2. Spans use `{"sid": ..., "text": ...}`.** The other shape is rejected rather than scored.

```python
# CORRECT — the step cites S0, so S0 is in scope when the claim is scored
audit_trace_budget(
    steps=[{"claim": "The suite reports 174 passed and 1 skipped.", "cites": ["S0"]}],
    spans=[{"sid": "S0", "text": "<actual test runner output>"}],
)

# WRONG — no cites. status="empty_context", verifier_calls=0, flagged=true.
audit_trace_budget(steps=[{"claim": "..."}], spans=[{"sid": "S0", "text": "..."}])

# WRONG — span keyed by id. status="no_spans".
spans=[{"S0": "<actual test runner output>"}]
```

Each step returns a `status` — `passed`, `not_entailed`, `contradicted`, `empty_context`, `no_spans` — and, where the verifier ran, posterior YES bounds against a `target` (default `0.95`). `empty_context` and `no_spans` mean the gate did not run: fix the call, not the claim.

`audit_trace_budget_run` additionally returns `observed`, `required` and `budget_gap` in bits per step, plus an `evidence_pack` with its own `text_sha256`. The inline `audit_trace_budget` does not — another reason to prefer the run-backed form.

#### Verifier backend

OpenRouter-hosted `openai/gpt-4o-mini` via Berry's OpenAI-compatible client.

**Always pin `BERRY_VERIFIER_MODEL`.** The fallback takes the first model from
`GET /v1/models`, which on OpenRouter is arbitrary and probably lacks the token
logprobs Berry requires. A `flagged` result carrying an `error` key is a broken
verifier, not a failed claim — check `error` first. The model-choice rationale
and the logprobs eligibility table live in `~/.claude/docs/tools/berry.md`.

Two files configure this, and they hold different things.
`~/.berry/mcp_env.json` is **load-bearing**: the MCP launcher reads these env
vars at startup, and it is the only place credentials belong.
`~/.berry/config.json` holds permissions — `allowed_roots` (without which
`add_file_span` refuses to read anything), the `allow_*` flags, audit settings.
Do not let an API key end up in `config.json`: nothing reads it there, and a
second copy is a second thing to rotate and to leak.

```jsonc
// ~/.berry/mcp_env.json — LOAD-BEARING: read by the MCP launcher
{
  "OPENAI_API_KEY": "<your-openrouter-key>",
  "OPENAI_BASE_URL": "https://openrouter.ai/api/v1",
  "BERRY_VERIFIER_BACKEND": "openai",
  "BERRY_VERIFIER_MODEL": "openai/gpt-4o-mini"
}

// ~/.berry/config.json — permissions, NOT credentials
{
  "allowed_roots": ["/path/to/your/repos"],
  "allow_write": false,
  "allow_exec": false,
  "allow_web": false,
  "enforce_verification": true,
  "audit_log_enabled": true
}
```

An earlier version of this example carried a `verifier` block with the API key
repeated here. That is what put a second plaintext copy on installed machines.
Only `mcp_env.json` is read for credentials; if your `config.json` still has an
`api_key`, delete that field — everything keeps working.

If verification calls start failing, first check that the OpenRouter key is still valid (`curl -H "Authorization: Bearer $KEY" https://openrouter.ai/api/v1/models | head`), then check OpenRouter status. A self-hosted llama.cpp backend remains an option for offline / air-gapped work — see Berry's upstream docs for the alternative config.

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
The `explanatory-output-style` plugin installs a SessionStart hook that adds
`★ Insight` blocks after code. Depth-reference:
`~/.claude/docs/tools/explanatory-output-style.md`. These explain:
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
