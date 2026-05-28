# The TRACKER.md System — How Agents Collaborate

The kit's quality discipline (TDD → Berry → V+O) does not run on agent memory
or chat scrollback. It runs on **two coupled artifacts**:

1. **The Claude Code `Task` tool** — live, machine-readable task state
   (`TaskCreate` / `TaskUpdate` / `TaskList` / `TaskGet`) that every agent
   reads and writes during a session.
2. **`docs/TRACKER.md` per project** — a human-readable, durable
   write-once-per-step Markdown document that records what happened, what's
   in flight, what's open, and what the quality loop has produced.

Together they form the kit's **collaboration substrate**. Agents claim work
from the Task tool, work on it, surface findings as new tasks, and update
`docs/TRACKER.md` so any human (or any future agent) can read one file and
see the full state of a multi-iteration feature without replaying the chat
history.

This document defines the schema, the discipline, and the mandatory hooks
between the Task tool, `docs/TRACKER.md`, and the agent dispatch protocol.

---

## Why two layers

The Task tool is great for in-session ownership and status, but it doesn't
survive arbitrarily across sessions cleanly and isn't readable by humans
inspecting the repo without running the CLI. `docs/TRACKER.md` is great for
human review, code review, and post-hoc auditing but lacks the per-event
granularity needed for live multi-agent coordination.

Use both. Each layer covers what the other can't:

| Layer | Role | When updated |
|---|---|---|
| `Task` tool (`TaskCreate`/`TaskUpdate`) | Live ownership + status | Whenever an agent starts, finishes, or surfaces a finding |
| `docs/TRACKER.md` | Durable record + cross-iteration view | Whenever a task moves, a finding lands, an iteration closes |

The rule the kit enforces: **whenever you call `TaskUpdate`, also update
`docs/TRACKER.md` in the same logical step**. They are kept in lockstep.

---

## `docs/TRACKER.md` schema

Every project that uses the kit's discipline ships a `docs/TRACKER.md` in
its repo root. The file is the single source of truth for any human or
agent reviewing project progress. It must never be more than one step out
of date.

### 1. Document header

```markdown
# <Project> — Agentic Development Tracker (<branch-or-context>)

**Last Updated:** <YYYY-MM-DD> — <one-paragraph cumulative summary of the latest iteration>

**Earlier:** <YYYY-MM-DD> — <previous iteration summary>

**Earlier:** <YYYY-MM-DD> — <iteration before that>
```

The "Last Updated" line is the most important line in the file — it's what
a reader reads first to understand current state. Update it on every
substantive change; demote the previous "Last Updated" to a new "Earlier"
line.

The cumulative summary should cover what shipped, what was tested, what was
verified, what was deferred, and (when applicable) link to the per-iteration
deep-dive document under `docs/iter<N>-*.md`.

### 2. Per-iteration sections

Below the header, each iteration gets its own section in reverse-chronological
order:

```markdown
## <YYYY-MM-DD> Iter-<N> — <one-line subject>

<paragraph or bulleted summary of what this iteration delivered>

| Aspect | Detail |
|---|---|
| User directive | "<exact user phrasing that scoped this iteration>" |
| Root cause | <one-paragraph technical explanation> |
| Fix | <implementation summary with file:line references> |
| New tests | <count + names + invariants pinned> |
| Test sweep | <command + result, e.g. "16/16 packages GREEN at `go test ./... -count=1`"> |
| Lint | <command + result> |
| Visual verification | <if applicable; file paths + page numbers + visible evidence> |
| Berry gate | <run id + claims/flagged> |
| Temporal labels | <whether any iter-NN labels were scrubbed from code> |

### Quality Loop State — Iter-<N>

| Stage | Status | Findings | Notes |
|---|---|---|---|
| Dev | ✅ Complete | — | <commit ref> |
| Verification | ✅ PASS | <N> | <list any findings + which became fix tasks> |
| Optimization | ✅ APPROVED | <N> | <same> |
| Berry | ✅ <X>/<X> | 0 flagged | <run id> |
```

### 3. Quality Loop State table

Each iteration ends with a **Quality Loop State** table that records the
state of each gate on the SAME code revision:

| Stage | What it asserts | Pass criteria |
|---|---|---|
| Dev | Implementation complete + tests pass | Dev agent shows actual test output |
| Verification (V) | PRD compliance + test authenticity + wire-path | V agent verdict = `VERIFICATION: PASS` on the SAME revision the dev agent shipped |
| Optimization (O) | Lint clean + redundancy check + best-practice sweep | O agent verdict = `OPTIMIZATION: APPROVED` on the SAME revision |
| Berry | Evidence claims pass `audit_trace_budget` | All non-trivial claims under budget |

A phase closes ONLY when V and O both report on the same revision. If V
finds something, the fix lands as a new task, then V and O re-run on the
new revision. The table records the FINAL pass.

### 4. V/O Findings Tracker (when applicable)

For iterations with significant findings, add an explicit findings table:

```markdown
### V/O Findings Tracker — Iter-<N>

| ID | Agent | Severity | Finding | Status | Fix commit |
|---|---|---|---|---|---|
| V-N1 | V | BLOCKING | `[WIRE-PATH MISS]` `SynthesiseStampFindings` has no caller in request hot path | ✅ CLOSED | `abc123` |
| O-N1 | O | HIGH | `[REDUNDANT FUNCTION]` `clampRect` duplicates `clampToBounds` | ✅ CLOSED | `def456` |
| V-N2 | V | LOW | `[SHALLOW TEST]` test only asserts mock response shape | 🔧 IN PROGRESS | — |
```

Severities: `BLOCKING` (must fix before phase closes), `HIGH`,
`MEDIUM`, `LOW`. Use the V/O agents' actual finding tags
(`[WIRE-PATH MISS]`, `[STUB TEST]`, `[REDUNDANT FUNCTION]`, etc.) verbatim
so a reader can grep across trackers.

### 5. Open issues / Refined open follow-ups

End each iteration section with explicit open items:

```markdown
### Open issues — Iter-<N> (deferred)

- **<one-line subject>** — <why deferred, what evidence triggered it, what
  the closure criteria are, which iteration they're scheduled into>
```

Anything that surfaced this iteration but isn't fixed THIS iteration goes
here. The next iteration's "Last Updated" header should reference whether
the open items were closed or carried.

---

## How agents collaborate via Task tool + tracker

### The dispatch protocol (coordinator does this BEFORE any dev agent)

The coordinator (the human or the top-level Claude session that orchestrates
sub-agents) MUST create all three quality-loop tasks **upfront** before
dispatching the dev agent:

```
1. TaskCreate("Dev: Phase X — <description>")           → dev agent will claim + work + complete
2. TaskCreate("Verification: Phase X")                  → V agent will claim + work + complete
3. TaskCreate("Optimization: Phase X")                  → O agent will claim + work + complete
```

All three exist in the tracker before the dev agent is dispatched. This
makes the quality loop visible and PREVENTS skipping it — the tracker
enforces the loop, not the coordinator's memory.

### What every agent MUST do at the start of work

```
1. TaskList                          # find your assigned task
2. TaskUpdate(taskId, in_progress)   # claim it
3. Read docs/TRACKER.md              # understand current phase state
4. Read the relevant plan section    # under ~/.claude/plans/ or docs/plans/
5. Do the work
```

### What every agent MUST do during work

Whenever the agent produces a finding (V agent finds a [REQUIREMENT GAP],
O agent finds a [REDUNDANT FUNCTION], etc.):

```
TaskCreate("Fix V-N1: <finding summary>")
```

Each finding = one new task. Findings are NOT logged in chat and then
hoped-to-be-actioned — they enter the tracker as concrete units of work.

### What every agent MUST do at the end of work

```
1. TaskUpdate(taskId, completed)
2. Update docs/TRACKER.md:
   - If you closed a finding: update the V/O Findings Tracker row
   - If you completed a stage: update the Quality Loop State row
   - If you completed an iteration: append a new "## YYYY-MM-DD Iter-N" section
3. If new follow-up items surfaced: append to "Open issues" of the current section
```

### What the coordinator MUST NOT do

**Coordinators do not update the tracker on behalf of agents.** If an agent
finished work without calling `TaskUpdate` or without editing `docs/TRACKER.md`,
that's evidence the agent didn't have the task context it needed. The fix is
to amend the agent's prompt with the missing context. Do NOT compensate by
patching the tracker after the fact — that hides the prompt bug AND
breaks the tracker's "this is what the agent actually said it did" contract.

---

## Phase Start Protocol (coordinator)

Before starting any new phase, the coordinator MUST:

1. **`EnterPlanMode`** and produce a detailed technical plan:
   - Break the phase into discrete, testable sub-tasks
   - Identify every file to create or modify with its exact purpose
   - Define the TDD sequence: what fails first, what makes it pass
   - Identify integration points with existing code
   - Flag any known risks or technical constraints
2. **Get explicit user approval** of the plan
3. **`ExitPlanMode`** only after approval
4. **Execute against the plan** — every dev agent prompt must reference the
   plan and implement exactly what it specifies

This protocol is what keeps the kit's discipline from sliding into
ad-hoc development. The plan is the contract the dev agent + V agent + O
agent all measure against.

---

## Verification Agent Protocol

The Verification agent MUST perform ALL of the following. Skipping any step
is a verification failure.

### Step 0. PRD Requirement Mapping

For each requirement in the task spec (PRD document, plan section, or
explicit acceptance criteria from the coordinator), trace it to a specific
`file:line` in the implementation. If a requirement has no corresponding
code, that is a **`[REQUIREMENT GAP]` finding** — file it as a task and
surface it before proceeding to Step A.

Skip Step 0 only when the task has no PRD-style requirements to map (e.g.
a docs-only change). For implementation phases, the requirement-to-code
trace is the first thing V records — without it, Steps B–G are auditing
an implementation that may not even claim to do the right thing.

### A. Identify the real target function
Read the implementation file completely. Note every exported function/method
name and its exact signature (parameters, return types, error conditions).

### B. Trace the test's call path
For each test, find the exact line where the function under test is called.
Confirm the test imports the real module (not a re-implementation), uses
the real exported symbol name (not a local copy), and the package import
path matches the real package (not a test double).

### C. Verify input → output tracing
For each test:
- What specific inputs are passed?
- What does the REAL implementation do with those inputs?
- Does the assertion test the REAL output of the real function, or a mock
  response independent of the real code path?

A test that only verifies a mock response (e.g., `page.route()` returning
hardcoded JSON) is a `[SHALLOW TEST]` finding unless its purpose is
explicitly HTTP integration testing.

### D. Check for stub/duplicate anti-patterns
Flag as `[STUB TEST]` if:
- The test defines a local function with the same logic as the function
  under test
- The test imports a test-only wrapper instead of the real exported function
- The test compiles a different file than the implementation file

### E. Behavioral coverage gap check
Map all tests to requirements. Are there execution branches in the
implementation with no test coverage? Error paths, edge cases specified in
the PRD, negative paths? Flag each uncovered branch as `[TEST MISSING]`
with the specific branch location (file:line).

### F. Test result validity
Run the tests and capture full output (`-v` for Go, `--reporter=list` for
Playwright). Confirm:
- Every test passes (not skipped, not pending)
- Output contains actual assertion results
- No test passes vacuously (no empty tests, no tests with no assertions)

### G. Hot-path call-site verification (the wire-path check)
**This is the step that catches "tests pass but feature doesn't actually
run in production".** For every NEW exported helper / package-level setter
/ per-page closure / overlay primitive introduced in the diff:

1. Identify the symbol (e.g. `SynthesiseStampFindings`).
2. Grep / LSP-search the codebase for callers.
3. The set MUST include at least one of:
   - The request handler (the top-level entry point of the feature)
   - A package-level init / `cmd/server/main.go` startup block
   - An existing pipeline pass file
4. If the only callers are TEST files, that is a **`[WIRE-PATH MISS]`
   finding** and is **BLOCKING**. Tests prove the primitive *works*; they
   do not prove the pipeline *uses* it.
5. Require at least one test that calls the helper THROUGH the same
   surface the production handler uses (handler → helper). A pure-primitive
   unit test is necessary but NOT sufficient.

A `[WIRE-PATH MISS]` finding blocks phase closure. Do not approve a stage
that has one.

---

## Optimization Agent Protocol

### 1. Standard linter sweep
Run the project's linter (`go vet ./...` + `golangci-lint`, `eslint`, `ruff`,
etc.). 0 NEW issues required on changed code. Pre-existing issues in
unrelated files are out of scope; flag-don't-fix.

### 2. Mandatory redundancy + duplication check (dual-graph driven)

For every NEW function, struct, regex, helper, or test fixture introduced
in the diff:

1. **Use dual-graph MCP first.** Call `graph_continue` with the new symbol
   name and surrounding semantic terms. Read `recommended_files`.
2. **Use LSP to confirm**: `workspaceSymbol` for the new name;
   `findReferences` on similar existing helpers in the same package.
3. **Flag as `[REDUNDANT FUNCTION]`** if a function with equivalent
   behaviour already exists. Suggest the existing helper as the reuse target.
4. **Flag as `[REDUNDANT CODE PATH]`** if the new code re-implements logic
   another path already handles.
5. **Flag as `[REDUNDANT TEST]`** if the new test asserts an invariant
   already covered by an existing test that exercises the same surface.

The O agent's report MUST show evidence of the dual-graph + LSP search
(which symbols were checked, what the search returned). An O report that
lacks this evidence is itself a finding.

### 3. Best-practice sweep (changed code only)
- Allocation patterns, slice capacity hints, map sizing
- Naming consistency with neighbouring code
- Comment quality (no temporal/phase labels — those belong in TRACKER.md,
  not in code)
- Idiomatic error wrapping

### 4. Tracker updates
- `TaskCreate` for EVERY finding (each finding = one task)
- `TaskUpdate` on your own optimization task: `status="completed"`
- Verdict: `APPROVED` or `CHANGES-RECOMMENDED`. Both V and O must report
  PASS/APPROVED on the SAME revision before the phase closes.

---

## Hard rules around the tracker

- **`docs/TRACKER.md` is the single source of truth for human reviewers.**
  Anything not in the tracker is unknown to anyone who didn't run the
  session. The tracker must never be more than one step out of date.
- **Phase/iteration labels (`Iter-46`, `Phase 29`, etc.) belong in the
  tracker, commit messages, PR descriptions, and plan files — never in
  source code comments, log strings, test assertion messages, or error
  strings.** This is enforced by the kit's `feedback_no_temporal_labels_in_code`
  rule. Code must be self-contained + functionally descriptive.
- **The Task tool and `docs/TRACKER.md` are kept in lockstep.** Every
  `TaskUpdate` call should be paired with a `docs/TRACKER.md` edit in the
  same logical step.
- **Coordinators do not write to the tracker on behalf of agents.** If an
  agent didn't update the tracker, fix the agent's prompt — don't paper
  over the missing context.
- **Findings become tasks.** A finding logged only in chat is not a
  finding; it's a comment. Every finding from V or O must materialize as a
  `TaskCreate` call AND appear in the Findings Tracker table.

---

## What goes IN the tracker vs the plan

The kit's discipline produces two main written artifacts per non-trivial
piece of work: a **plan** (under `docs/plans/` or `~/.claude/plans/`) and
the **tracker** (`docs/TRACKER.md`). They serve different audiences and
have different lifecycles.

| Artifact | What | Audience | Lifecycle |
|---|---|---|---|
| Plan | The agreed approach to a phase BEFORE execution | Reviewer at plan-approval gate | Written once + immutable after approval (any plan change requires re-approval) |
| Tracker | What's happened, what's in-flight, what's open | Anyone joining the project mid-flight | Updated continuously |

If you find yourself wanting to put the same content in both, prefer the
plan for "what we're going to do" and the tracker for "what we actually did
+ what surfaced".

---

## See also

- [`docs/workflow.md`](workflow.md) — the 10-step development loop that
  the tracker discipline wraps around.
- [`docs/philosophy.md`](philosophy.md) — the kit's stance on
  evidence-before-assertions.
- The kit's `claude/CLAUDE.md` `## MANDATORY Quality Loop` section is the
  agent-side reference for these protocols; this document is the
  human-readable expansion.
