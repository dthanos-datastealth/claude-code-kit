# Tracker and task protocol

## MANDATORY: TRACKER.md + Task tool — the collaboration substrate

The quality loop above does not run on agent memory or chat scrollback. It runs on **two coupled artifacts**:

1. **Claude Code `Task` tool** — `TaskCreate` / `TaskUpdate` / `TaskList` / `TaskGet` for live, machine-readable task state every agent reads and writes.
2. **`docs/TRACKER.md`** (per project) — the durable Markdown record of what happened, what's in flight, what's open, what V/O produced. Single source of truth for any human or future agent reviewing the project.

> **The `Task` tools are opt-in on current Claude Code releases and model families**, and are enabled by `CLAUDE_CODE_ENABLE_TODO_TOOLS=1`. (Which versions and models default them off has moved between releases — check the tools reference for your CLI rather than trusting a version number written here.) `install.sh` writes that into your `settings.json` `env` block. Observed on a live upgrade: the Task tools appeared in the same session the file was saved, without a restart — Claude Code applies changed `env` values on save. If they do not appear, restart before concluding anything is wrong. And if `TaskCreate` is genuinely unavailable, say so once and run the protocol on `docs/TRACKER.md` alone; the tracker is the durable half and carries the state either way.

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

### When to write to the tracker — the trigger list

"Keep it current" has not proven to be an instruction anyone follows, including
Claude: the common failure is doing the work, then writing the tracker up in one
batch at the end, which loses exactly the intermediate state the file exists to
hold. If the session dies mid-way, a batched tracker records nothing.

So it is a trigger list, not a standard. **Write to `docs/TRACKER.md` immediately
on each of these, before starting the next thing:**

| Trigger | What goes in |
|---|---|
| Plan approved | The iteration row, the plan's location, the Berry run id for the plan gate |
| A phase completes | Its Quality Loop State row — what shipped, the suite total, the lint result |
| A V or O agent reports | Its verdict verbatim, and one row per finding with a disposition |
| A finding is closed | That row moves to CLOSED, naming the fix |
| A finding is deliberately not fixed | That row says OPEN and why — an unrecorded decision is indistinguishable from an oversight |
| Any gate fails | What failed, with the output, before attempting the fix |
| Work is handed back to the user | Everything above, current as of that moment |

The test for whether you have done this: **if the session ended right now, could
someone else pick up the work from the tracker alone?** If the answer needs
anything from the chat scrollback, the tracker is behind.

A finding you closed in the same turn you found it still gets a row. The row is
the record that it was found, not just that it was fixed — and "we already
checked that" is worth more to the next reader than a clean file.

### Hard rules around the tracker

- **`docs/TRACKER.md` must never be more than one step out of date.** Anything not in the tracker is unknown to anyone who didn't run the session.
- **Phase/iteration labels (`Iter-46`, `Phase 29`, etc.) belong in tracker / commit messages / PR descriptions / plan files — NEVER in source code comments, log strings, test assertion messages, or error strings.** Code is self-contained + functionally descriptive.
- **`Task` tool and `docs/TRACKER.md` are kept in lockstep.** Every `TaskUpdate` pairs with a `docs/TRACKER.md` edit in the same logical step.
- **Findings become tasks.** A finding logged only in chat is a comment, not a finding. Every V/O finding materializes as a `TaskCreate` AND appears in the Findings Tracker table in `docs/TRACKER.md`.

---

Anything in `~/.claude/rules/00-user-overrides.md` overrides this file. If the two disagree, follow the override and say which rule you are setting aside.
