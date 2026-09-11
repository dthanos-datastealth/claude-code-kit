# The mandatory quality loop

## MANDATORY Quality Loop (TDD → Berry → V+O)

This is the unconditional discipline that runs around **every substantive change** the kit ships, regardless of which workflow (default, `/feature-dev`, or spec-kit) framed it. `50-kit-plugins.md` describes the *tools*; this section describes the *rules they enforce*. The reasoning and the incidents behind the prohibitions are in `~/.claude/docs/verification-standards.md`.

### TDD discipline (always; no exceptions for "small" changes)

- Write the **failing test first** (RED). Run it; confirm it fails for the *right reason* — not for missing imports, typos, or fixture gaps.
- Implement the minimum that makes the test pass (GREEN). Do not add unrequested features.
- REFACTOR only with the test green. If you can't keep it green during refactor, stop and split the refactor into smaller steps.
- **Lifecycle tests, not just function-centric ones.** For anything stateful (sessions, caches, queues, write paths), assert on the full create → use → close → reopen → cleanup cycle. Function-only tests miss the failures that matter.
- **Prove the test can fail before trusting it.** RED-before-GREEN is the cheap version of this and it is not always enough: a test can fail at first for the wrong reason and then pass forever regardless of the code. When a test exists to guard a specific defect, break that defect on purpose and confirm the test notices. In this repo that is `python3 scripts/mutate.py run <id>`; elsewhere it is reverting the one line and rerunning. Measured here: two tests written to cover two specific bugs passed against those exact bugs, and neither the suite, a code review, nor reverting the whole file found it.
- **Capture RED and GREEN as Berry spans, not just the final run.** "The test failed first, for the right reason" is a claim like any other, and it is the one that distinguishes TDD from a retrofit — a test written after the code almost always passes on its first run. Take the failing output as one span and the passing output as another, cite both, and the audit can check that the same test moved from failing to passing. A single end-of-work GREEN span cannot show that, and it is exactly what a retrofit produces.
- Skill: `superpowers:test-driven-development`.

### Berry verification (load-bearing — fails the build if skipped)

- Every claim a session ships with — "tests pass", "the bug is fixed", "the spec is complete", "the plan is sound" — must be backed by a Berry span. No exceptions.
- Test output is the canonical evidence form: capture it via `berry-search-and-learn` and cite it before any "tests pass" assertion.
- See `50-kit-plugins.md` for the mandatory triggers, hard rules, `audit_trace_budget` API contract, and the OpenRouter backend configuration.

### V+O loop (after each substantive change to a tracked artifact)

After any code commit, doc change, or config change that affects behavior, run the two-agent **Verification + Optimization** loop against that same revision before declaring the change complete:

- **V — Verification agent.** Dispatched to verify the change against **authoritative external sources** (upstream READMEs, official docs, the kit's own spec/plan, vendor API references). Its job is to catch correctness drift between the change and reality. Output: `[OK]` / `[CONCERN]` / `[BLOCKER]` per check, with citations. **Test coverage is part of V's remit, not a separate concern** — Steps E and F of the Verification Agent Protocol in `40-kit-tracker.md` require mapping every changed behaviour to a test and confirming each one passes non-vacuously. A change whose tests would pass against the unfixed code is a `[SHALLOW TEST]` finding, and a behaviour with no test at all is `[TEST MISSING]`.
- **O — Optimization agent.** Dispatched in parallel to find simplification / clarity / consistency wins on the same revision. Output: `[trivial]` / `[worth-considering]` / `[worth-fixing]` per finding.
- Verdicts of either agent block "done" — if V flags a `[CONCERN]` or `[BLOCKER]`, fix it before moving on; if O flags `[worth-fixing]`, apply the fix in a follow-up commit before the next substantive change lands.
- Run V and O **in parallel** (independent reviews of the same state). Use `subagent_type: general-purpose` for V (it needs WebFetch + Read), `subagent_type: code-simplifier:code-simplifier` for O.

The kit's `superpowers:requesting-code-review` skill, `feature-dev:code-reviewer` subagent, and `code-simplifier` plugin implement the V and O roles inside `superpowers:subagent-driven-development`'s built-in two-stage review; the V+O loop above sits **on top** of that, with one explicit difference: V+O verifies against **external authoritative sources**, not just against the local spec or the diff itself.

### Hard prohibitions for the quality loop

- Do not claim "tests pass" without a Berry span citing the actual test runner output.
- Do not skip V+O on the grounds that "the change is small" — small changes are exactly where unaudited drift accumulates.
- Do not invent answers when V flags a `[CONCERN]` — gather more evidence or escalate.
- 3-strike rule applies (see `50-kit-plugins.md` for the canonical statement): if a Berry audit fails three times on the same claim set, STOP and surface partial results. No silent looping.
- **Never verify a user-facing or protection feature with a synthetic proxy.** Driving your own element, reading back a value you set, dispatching an event straight to a handler, or treating a toast as proof all test a proxy you control. Drive the REAL widget and assert the GROUND TRUTH (for data protection: the outbound request carries zero raw values). If the harness cannot drive the real widget that is a BLOCKER — escalate, do not substitute.
- **A script can never confirm a visual result.** Any image, rasterised page or painted canvas must be viewed at legible resolution, every page, whole page. Re-OCR, pixel statistics and "0 leaked" counts choose what to look at; they are never confirmation. If a render has not been viewed, say so.
- **The O agent hunts redundant WORK, not just redundant code** — enumerate every expensive operation in the diff, trace each flow end to end, and state per call site whether it is cached+reused or recomputed. A report without that trace is itself a finding. Pair `optibot` with `code-simplifier` whenever a hot path is touched.

All three guard the same failure: a check that cannot observe the defect it is
meant to catch reports success, and ends the investigation. The exact forbidden
patterns, the failure mode behind each rule and the O agent's finding taxonomy
are in `~/.claude/docs/verification-standards.md` — read it before arguing that
one of them does not apply.

---

Anything in `~/.claude/rules/00-user-overrides.md` overrides this file. If the two disagree, follow the override and say which rule you are setting aside.
