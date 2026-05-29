# Workflow

This is the 10-step development loop the kit enforces for any non-trivial
task. The loop is the same one declared in `claude/CLAUDE.md` under
"Workflow Order" — this document is the long-form version with the
per-step rationale, the skip conditions, the common pitfalls, and the exact
slash command to run.

Read this end-to-end once. After that, the slash commands in each step are
enough; the prose here is a reference for when something feels off.

A note on feature work specifically: for any new feature, prefer
`/feature-dev` ([`docs/tools/feature-dev.md`](tools/feature-dev.md)). It
runs phases 1–7 of a structured workflow — discovery, codebase exploration,
clarifying questions, architecture design, implementation, quality review,
summary — and subsumes most of the loop below. The 10-step loop here is
the canonical reference for everything else: bug fixes, refactors, ad-hoc
tasks, anything that does not warrant the full feature-dev ceremony.

---

## Step 1: Brainstorm

**Slash command:** `/superpowers:brainstorming`

**What it does:** Explores user intent, requirements, and design space
before any code is touched. The skill walks through the problem, asks
clarifying questions, and produces a shared understanding of what success
looks like.

**Why it is first:** Most failed changes were failed before the first line
of code, because the agent and the user had different mental models of the
task. Brainstorming is cheap; rework is expensive. Five minutes of
clarification at the start saves an hour of "wait, that's not what I asked
for" at the end.

**When to skip:**

- The task is genuinely trivial — a typo fix, a formatting change, a
  one-line config tweak.
- The request is unambiguous, scoped, and the success criterion is
  self-evident.
- You are mid-loop on a task you have already brainstormed and the current
  sub-step does not change the design.

**Common pitfalls:**

- Skipping because "I already know what they want." Verify the assumption
  by stating it back to the user and waiting for confirmation. If they
  correct you, you needed the step.
- Treating brainstorming as a one-shot. If the conversation surfaces a
  new constraint, restart the brainstorm with the new constraint in scope.
- Producing a brainstorm output that is just a restatement of the request.
  The deliverable is a set of decisions about scope, approach, and
  trade-offs — not a paraphrase.

---

## Step 2: Plan and Berry-verify

**Slash commands:** `/superpowers:writing-plans` then the
`berry-plan-and-execute` skill from the Berry plugin
([`docs/tools/berry.md`](tools/berry.md)).

**What it does:** Breaks the work into 2–5 minute tasks with explicit
file lists, expected outputs, and verification commands. Berry then audits
the plan: every step's claims must be backed by spans of evidence sufficient
to pass `audit_trace_budget` before execution is approved.

**Why both:** A plan without verification is a wish list. A plan that has
passed a Berry audit is a wish list that the verifier could not poke holes
in. The audit catches the most common planning failure — steps that depend
on assumed APIs, assumed file paths, or assumed behaviours that turn out
not to exist when you go to execute them.

**When to skip:**

- The task is genuinely trivial (same threshold as brainstorming).
- You are inside an existing plan executing the next step; do not re-plan
  per step.

**When to keep:**

- Any multi-file change.
- Any change that touches a hot path.
- Any change where the failure mode of getting it wrong is non-trivial to
  unwind.

**Common pitfalls:**

- Writing a plan that is too coarse. "Implement the feature" is not a
  step; "add the `Foo.bar` method, write the test, run the test" is.
- Skipping the Berry audit because the plan "looks fine." The whole point
  of the audit is to test claims that look fine. Run it.
- Treating an audit failure as an audit problem. The audit failed because
  the spans did not support the claims. Add stronger spans or weaken the
  claims; do not bypass the audit.
- Mis-shaped span parameters. Berry's `audit_trace_budget` expects
  `{"sid": "<id>", "text": "<content>"}`. The other shape
  (`{"<id>": "<content>"}`) parses but silently produces zero observed
  bits, which looks like an evidence problem but is actually a parameter
  problem. Check the keys first when a strong span fails the audit.

**Tracker dispatch (Pre-Dispatch Protocol):** Once the plan passes
Berry, open a `docs/TRACKER.md` row for the iteration and one row per
Dev / V / O `Task` you will dispatch. Do this **upfront, before any
dispatch fires**, so the parallel agents share a coordination
substrate from the moment they start. The full schema (Last Updated +
Earlier · per-iteration aspect tables · Quality Loop State · V/O
Findings Tracker · Open issues) and the rationale for opening rows
before dispatch live in [`docs/tracker-system.md`](tracker-system.md).
The hard rule: coordinators do **not** edit other agents' rows on
their behalf — each agent updates its own row state, and findings
surface as **new rows**, not as edits to existing ones.

---

## Step 3: Isolate

**Slash command:** `/superpowers:using-git-worktrees`

**What it does:** Creates an isolated git worktree (or equivalent
sandbox) so that the in-progress change does not contaminate the main
workspace. The skill picks the right mechanism for your repo — native
worktree, a separate clone, or a topic branch — and sets it up.

**Why isolation:** Multi-file changes in progress are unsafe to mix with
unrelated edits. An isolated worktree means: you can run tests without
worrying about half-finished changes elsewhere; you can abandon the work
cleanly if the approach turns out to be wrong; you can switch contexts
without losing the in-progress state.

**When to skip:**

- Single-file changes that you can hold in your head and revert in one
  command.
- Documentation-only edits.
- You are already inside an isolated worktree for this task.

**Common pitfalls:**

- Skipping because "I'll just commit often." Frequent commits help, but
  they do not provide the workspace separation that lets you reproduce
  test runs cleanly.
- Creating a new worktree when one already exists for the same task. The
  skill checks for an existing worktree first; trust the check.
- Forgetting to come back. After the work is merged, clean up the
  worktree. Step 9 (Finish) handles this when used.

---

## Step 4: Test-driven development

**Slash command:** `/superpowers:test-driven-development`

**What it does:** Walks through RED → GREEN → REFACTOR explicitly. You
write a failing test first, watch it fail for the right reason, then
write the implementation that makes it pass, then refactor with the test
as a guardrail.

**Why TDD here:** A failing test is the only objective signal that the
change you are about to make is necessary and that the change you made
actually solved the problem. Manual verification tests what you remembered
to check, in the configuration you happened to be in. A test that fails
before and passes after is a falsifiable claim that the change did
something specific.

**When to skip:**

- Pure documentation edits.
- Formatting-only changes.
- Trivial rename refactors handled by an LSP rename.
- Throwaway exploration scripts you will delete in the same session.

**When not to skip even though it is tempting:**

- Bug fixes. A bug without a regression test is a bug waiting to come
  back.
- "Small" feature additions. Small features have edge cases too.
- Internal helpers. They get called, often in unexpected ways; test the
  contract.

**Common pitfalls:**

- Writing the implementation first and the test second. That is a
  retrofit, and the test will almost always pass on the first run because
  it was shaped by the implementation. The point of RED is to prove the
  test can fail.
- Tests that exercise stubs or inline duplicate logic rather than the
  real module under test. They produce green output without exercising
  the code path the change actually modified.
- Watching the test pass and not investigating why it took less time
  than expected. RED that passes is a sign the test is not actually
  exercising the new code.
- Skipping the REFACTOR step because GREEN feels like done. GREEN with
  the seams visible is a smell; the test exists so you can clean up
  safely.

---

## Step 5: Build

**Slash command:** none — this is the implementation work itself.
Pair with Context7 ([`docs/tools/context7.md`](tools/context7.md)) for
current library docs and the dual-graph MCP
([`docs/tools/dual-graph-mcp.md`](tools/dual-graph-mcp.md)) for
navigation.

**What it does:** Write the code that makes the failing test pass. Stay
inside the scope the plan declared. Use the dual graph and LSP to find
symbols and references; use Context7 to verify library APIs at the
current version.

**Why pair with Context7:** Library APIs change. Cached knowledge from
training data is not evidence — it is a memory of how the API used to
look. Context7 fetches the docs at the current version, which is the
only version your code is going to run against.

**When to skip:** Never — this is the actual work. But if you find
yourself building beyond what the test demands, stop and add another
test for the new behaviour (return to step 4) rather than expanding the
implementation freehand.

**Common pitfalls:**

- Scope creep. The test demands one behaviour; the implementation adds
  three. The two extras are unverified work and they belong in their
  own task.
- Building from cached library knowledge instead of Context7-current
  docs. The function you remember may have been renamed, the parameter
  you remember may now be required, the return type you remember may
  have grown a field.
- Grepping for symbols when the dual graph or LSP would answer
  precisely. See [`docs/philosophy.md`](philosophy.md) §4.
- Implementing more than the test needs because "I'm already in here."
  See [`docs/philosophy.md`](philosophy.md) §3 — minimum viable changes.

---

## Step 6: Verify

**Slash commands:** `/superpowers:verification-before-completion` plus
the `berry-search-and-learn` skill from Berry.

**What it does:** Runs the verification commands, captures the actual
output, and gates any "done" claim on a passing audit of that output.
Test output is captured as a Berry span via `add_span`; the audit
verifies the span actually contains the passing output and that the
output corresponds to the test you claim ran.

**Why both skills:** `verification-before-completion` blocks the
completion claim until verification has been run. `berry-search-and-learn`
makes the test output a citable span, which means the audit can verify
the test really passed (and was the test you claim it was).

**When to skip:** Never. Skipping verification is how broken changes
ship.

**Common pitfalls:**

- Claiming green based on a partial test run. If you ran the unit
  tests, do not claim the integration tests pass. Run the full relevant
  suite.
- Pasting an old test output as if it were the current run. The audit
  can catch this if the spans are honest; do not invite it to fail.
- Treating warnings as ignorable. Warnings often become errors a version
  later. If the change introduced a warning, decide explicitly to ignore
  it (and document why) or fix it.
- Three-strike audit failures. If `audit_trace_budget` flags the same
  claim set three times, stop and surface the failure. Do not silently
  loop. Either the evidence is genuinely insufficient (gather more) or
  the verifier is mis-configured (check span keys first — see step 2's
  span-shape note).
- Linter not run. The kit's standard is: linter green before claiming
  any task complete. Go: `go vet` + `golangci-lint`. TypeScript:
  `eslint`. Other languages: whatever the project uses.

**Tracker-coordinated V+O dispatch:** Verification and Optimization
agents run as parallel `Task` dispatches against the rows opened in
Step 2's Pre-Dispatch Protocol. Each agent claims its row by updating
its own row state (in-progress → done), follows the Verification
Steps 0 + A–G (including the `[WIRE-PATH MISS]` hot-path check, which
is BLOCKING) or the Optimization Protocol (dual-graph + LSP redundancy
check), then files **findings as new rows** in the V/O Findings
Tracker — never as edits to other rows. The coordinator that
dispatched them does not write to their rows. Full protocols and
examples in [`docs/tracker-system.md`](tracker-system.md).

---

## Step 7: Review

**Slash command:** `/superpowers:requesting-code-review`

**What it does:** Surfaces the diff for review against the kit's
quality criteria — simplicity, correctness, test coverage, adherence
to project conventions, absence of drive-by changes, evidence backing
non-obvious decisions.

**Why request review even in a solo session:** The review skill is a
structured pass over the change against a checklist you would otherwise
have to remember. It catches the classes of issue that are easy to
notice when looking at the diff cold and hard to notice when you wrote
it line by line.

**When to skip:**

- Pure documentation edits where the diff is trivially correct on
  inspection.
- Trivial changes (typo fix, single-line config tweak) where the
  review would not produce useful signal.

**When to keep:**

- Any multi-file change.
- Anything touching public APIs.
- Anything touching authentication, authorisation, or data handling.
- Any change you are unsure about.

**Common pitfalls:**

- Skipping because "I just wrote it and it looks fine." The whole point
  of review is to surface what is not visible to the writer.
- Treating review feedback as adversarial. If a reviewer is asking, the
  question itself is information about how the change reads to someone
  who did not write it.
- Accepting review feedback without verification. The
  `superpowers:receiving-code-review` skill exists specifically to
  prevent performative agreement — verify suggestions before
  implementing them, especially if the feedback seems technically
  questionable.

---

## Step 8: Simplify

**Slash command:** `/simplify`
([`docs/tools/code-simplifier.md`](tools/code-simplifier.md))

**What it does:** Reviews the changed code for reuse opportunities,
quality issues, and efficiency improvements, then fixes what it finds.
The pass is scoped to the diff — it does not refactor unrelated code.

**Why a separate step:** During implementation, the focus is on
correctness. Simplification asks different questions: is there a
helper that already does this? Is this loop doing in three lines what
a built-in does in one? Is this struct field used? The questions are
hard to ask while building and easy to ask once GREEN is reached.

**When to skip:**

- Pure documentation edits.
- The change is already minimal and obviously cannot be reduced
  further.

**Common pitfalls:**

- Letting `/simplify` expand the scope of the change. The skill is
  scoped to the diff; if it suggests refactoring unrelated code, treat
  that as a follow-up task.
- Accepting simplifications that hurt readability. "Shorter" is not the
  same as "simpler." If the one-liner is harder to read than the
  three-line version, keep the three-line version.
- Skipping because GREEN feels like done. GREEN with the seams visible
  is the input to this step, not an alternative to it.

---

## Step 9: Finish

**Slash command:** `/superpowers:finishing-a-development-branch`

**What it does:** Presents the structured options for completing the
development branch — merge to main, open a PR, or clean up — and walks
through the chosen path. Handles worktree teardown if step 3 was used.

**Why a separate step:** "How do I land this?" is a different question
from "is this ready?" The answer depends on the team's branching
strategy, the change's risk profile, whether CI must run before merge,
and whether the change needs human review beyond the agentic review in
step 7. The skill prompts the questions explicitly so the decision is
deliberate.

**When to skip:**

- The change was committed directly to a feature branch that will be
  merged via a separate process (e.g. a release manager handles it).
- You are not yet done — the change is checkpoint-level, not
  branch-level.

**Common pitfalls:**

- Force-pushing to main without explicit confirmation. The kit's git
  safety protocol forbids this; the skill enforces it.
- Closing the branch without cleaning up the worktree from step 3.
  Leftover worktrees accumulate and confuse the next session.
- Opening a PR without a summary that explains the why. The diff shows
  the what; the PR description carries the rationale that is otherwise
  lost.

---

## Step 10: Document

**Slash command:** `/revise-claude-md` or
`claude-md-management:revise-claude-md`
([`docs/tools/claude-md-management.md`](tools/claude-md-management.md))

**What it does:** Audits the session for new patterns, gotchas,
conventions, or corrections that should be captured in `CLAUDE.md`
(project or global). Proposes targeted edits and applies them.

**Why end-of-session:** The cost of writing a CLAUDE.md update right
now is small. The cost of rediscovering the same pattern three sessions
later is large. The session you just finished is the cheapest moment to
capture what it taught you.

**What to capture:**

- A non-obvious gotcha you tripped over and resolved.
- A pattern that worked well and should be repeated.
- A correction the user gave you that should not need to be given
  again.
- A new convention the project has adopted.

**What not to capture:**

- One-off facts derivable from the codebase.
- Session-specific debugging logs (those go in the auto-memory system,
  not CLAUDE.md — see [`docs/memory-system.md`](memory-system.md)).
- Anything the next session can reconstruct from `git log` in under a
  minute.

**When to skip:**

- The session did not surface anything new — same patterns, same
  conventions, smooth execution.
- The session was scoped to a single trivial change.

**Common pitfalls:**

- Treating CLAUDE.md as a journal. It is a directive document — every
  line should change the next session's behaviour. If a line does not
  change behaviour, it is noise.
- Writing the update too verbose. A pithy one-line rule beats a
  paragraph of explanation. The rule fits in context every session;
  the explanation does not.
- Updating CLAUDE.md mid-session for things that are still in flux. Wait
  until the pattern stabilises; otherwise you will revise the rule
  three times in one day.

---

## The loop in one paragraph

Brainstorm the intent, plan and Berry-verify the plan, isolate in a
worktree, write a failing test, build the minimal code to pass it with
Context7 for current docs, verify with captured test output as a Berry
span, request review, simplify the diff, finish the branch with a
considered merge strategy, then document what the session taught you.
Ten steps, each with a slash command, most with a clear skip condition.
The cadence is the kit; the kit is the cadence.

---

## When the loop feels heavy

The loop is intentionally fuller than is comfortable for small changes.
For changes that genuinely warrant only a subset, use the skip
conditions to drop steps — but be honest about it. The most common
self-deception is "this is a small change so I will skip planning and
TDD," followed by a multi-hour debugging session caused by an
assumption the plan would have caught. The skip conditions exist;
inflating "trivial" to dodge the discipline does not.

If you find yourself wanting to skip more than two steps, the right
question is not "which step do I skip next?" — it is "is this task
actually trivial, or am I being optimistic about my own care?"

---

## Further reading

- [`docs/philosophy.md`](philosophy.md) — the principles the loop
  operationalises.
- [`docs/tools/superpowers.md`](tools/superpowers.md) — the
  workflow-discipline plugin that owns most of the slash commands here.
- [`docs/tools/berry.md`](tools/berry.md) — the evidence-verification
  gate referenced in steps 2 and 6.
- [`docs/tools/feature-dev.md`](tools/feature-dev.md) — the structured
  multi-phase feature workflow that subsumes most of this loop for new
  features.
- [`docs/memory-system.md`](memory-system.md) — the auto-memory system
  invoked by `/revise-claude-md` and complementary captures.
