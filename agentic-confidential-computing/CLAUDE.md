# Agentic Confidential Computing — project rules

This project adopts `claude-code-kit`'s discipline in full. The rules live here
so they bind every session, not just the one that created the repo.

## Core

- Evidence before assertions. Never speculate a root cause and act on it.
- Minimum viable changes. No unrequested refactors, comments, or features.
- No emojis. No Claude authorship trailer in commits.
- Code navigation order: dual-graph MCP, then LSP, then grep.

## Nothing about ai-cloud is a fact without a citation

`docs/ai-cloud-audit.md` holds the gating questions A1–A7. Any statement about
`ai-cloud`'s behavior must carry a `file:line` reference recorded in that
document. Until A1, A3 and A4 are answered, no architecture decision is final —
the design branches on them.

## Nothing is built that already exists

Order of preference: `ai-cloud`, then mature open source, then new code. See
`docs/research/oss-inventory.md`. Writing new code where a listed option exists
requires an ADR explaining why both prior options were rejected. Check
maintenance status before adopting — CrypTen is the cautionary case.

## Per-phase protocol

1. **Phase Start.** `EnterPlanMode`, write a plan with discrete testable
   sub-tasks, every file touched, the TDD sequence, integration points and
   risks. Get explicit user approval. Then `ExitPlanMode`.
2. **Pre-Dispatch.** Create all three quality-loop tasks before any dev work:
   `Dev: Phase X`, `Verification: Phase X`, `Optimization: Phase X`.
3. **TDD.** Failing test first, confirmed failing *for the right reason*.
   Minimum code to green. Refactor only while green. Lifecycle tests for
   anything stateful.
4. **V + O in parallel on the same revision.** V verifies against authoritative
   external sources: Step 0 requirement mapping, then Steps A–G including the
   blocking `[WIRE-PATH MISS]` check that every new exported symbol has
   non-test callers. O runs the linter sweep, the redundancy and duplication
   check, and the best-practice sweep.
5. **Phase closes only when V reports `VERIFICATION: PASS` and O reports
   `OPTIMIZATION: APPROVED` on the same revision.**

Every V/O finding becomes a task *and* a row in the Findings Tracker. A finding
logged only in chat is a comment, not a finding.

## Tracker

`docs/TRACKER.md` is never more than one step out of date, and is kept in
lockstep with the Task tool — every task transition pairs with an edit there.

Phase and iteration labels (`Iter-4`, `Phase 2`) belong in the tracker, commit
messages and plans. **Never** in source comments, log strings, test assertion
messages, or error strings. Code is self-contained and functionally
descriptive.

## Harness invariants

These encode the project's findings; breaking one silently invalidates the
results.

- The protected payload is the only object that crosses the trust boundary.
  Attacks score against it alone. A `ReidentificationMap` must never be
  embedded in a payload.
- Leakage is scored against `ground_truth_spans`, never against the detector's
  `spans` — otherwise a detector's blind spots hide leaks from the measurement.
- `plaintext_baseline` is the positive control and must keep failing the leak
  check. `naive_sanitize` is the negative control and must keep failing R2-FN.
  If either starts passing, the measurement broke, not the finding.
- No real customer data in this repository, ever.
