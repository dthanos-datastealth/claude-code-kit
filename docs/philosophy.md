# Philosophy

This kit is opinionated. The rules below are not aesthetic preferences — each
one exists because its absence produced a specific, costly failure mode in
practice. If you adopt this kit, you are accepting these constraints in
exchange for the workflows the tools enforce. If a constraint feels wrong for
your situation, fork the kit and remove it; do not weaken it in place.

The six principles are listed in dependency order. Earlier principles are
preconditions for later ones — you cannot honour "minimum viable changes"
without first honouring "evidence before assertions," because without evidence
you cannot tell which changes are viable and which are speculative.

---

## 1. Evidence before assertions

**The rule:** Every factual claim that drives an action must be backed by an
observation. Reading source code is an observation. Running a test and
capturing its output is an observation. Quoting an authoritative document
fetched at the current version is an observation. Reasoning about what code
*probably* does, what an API *likely* returns, or what a flag *should* mean is
not an observation — it is speculation, and the kit treats it as a defect.

**Why this is first:** Most catastrophic agent failures begin with a confident
hypothesis stated as fact. The agent "knows" a function exists, "knows" a
config key is read at startup, "knows" a test is flaky. Each of those
assertions is cheap to make and expensive to unwind. By the time the
downstream change has been written, reviewed, committed, and merged, the
original speculation has compounded into structural damage that is harder to
fix than the original problem.

**How the kit enforces it:**

- The Berry plugin ([`docs/tools/berry.md`](tools/berry.md)) provides
  `audit_trace_budget`, an information-theoretic check that the spans of
  evidence you cited actually contain enough mutual information to support
  your claims. If the spans are weak, the audit fails and you must gather
  more — you cannot pass by rephrasing.
- The `superpowers:verification-before-completion` skill blocks
  completion claims until you have run the verification commands and pasted
  their output into the transcript.
- The dual-graph MCP ([`docs/tools/dual-graph-mcp.md`](tools/dual-graph-mcp.md))
  steers exploration toward authoritative symbol locations rather than
  pattern-matched guesses.

**Day-to-day discipline:**

- When the cause of a bug is unknown, gather evidence before proposing a fix.
  Hypothesis-first debugging is a smell. Observation-first debugging starts
  by reproducing the bug, capturing the failing output, and narrowing the
  diff with `git bisect` or equivalent.
- "I think" and "should" are warning words. Replace them with the actual
  observation or label the statement as an assumption that needs verification.
- When citing documentation, fetch the current version via Context7
  ([`docs/tools/context7.md`](tools/context7.md)). Cached knowledge from
  training data is not evidence — APIs change.

---

## 2. Test-driven development for any non-trivial change

**The rule:** Before writing implementation code for a feature or a bug fix,
write a failing test that captures the intended behaviour. The test must run
and fail for the right reason. Only then write the implementation that makes
it pass. Refactor with the test as a guardrail.

**Why TDD here:** Without a failing test, you have no objective signal that
the change you are about to make is necessary or that the change you made
actually solved the problem. Manual verification is unreliable: it tests what
you remembered to check, in the configuration you happened to be in. A test
that fails before and passes after is a falsifiable claim that the change did
something specific. Anything weaker is a story.

**What counts as non-trivial:**

- Any new function, method, class, or module beyond a one-line trivial helper.
- Any bug fix where the regression risk is non-zero.
- Any change to logic in a hot path.
- Any change to a public API.

**What is exempt:**

- Pure documentation edits.
- Formatting-only changes.
- Trivial rename refactors where a type system or LSP rename does the work.
- Throwaway exploration scripts you will delete in the same session.

**How the kit enforces it:**

- The `superpowers:test-driven-development` skill walks you through
  RED → GREEN → REFACTOR explicitly and refuses to proceed if the RED step
  is skipped or the test fails for the wrong reason.
- The `superpowers:verification-before-completion` skill closes the loop —
  it will demand you re-run the test and capture passing output before any
  "done" claim.
- Berry's `berry-search-and-learn` skill makes the actual test output a
  citable span, so the audit can verify the test really passed (and was the
  test you claim it was).

**Pitfalls:**

- Writing the implementation first and the test second is not TDD. It is a
  retrofit, and the test will almost always pass on the first run because it
  was shaped by the implementation. The point of RED is to prove the test
  can fail.
- Tests that exercise stubs or inline duplicate logic rather than the real
  module under test are not tests. They are reassuring fiction.
- A test suite that "passes locally" but you have not personally watched
  pass does not count. Capture the runner output.

---

## 3. Minimum viable changes

**The rule:** Make the smallest change that solves the problem stated in the
task. Do not refactor adjacent code, do not "while you're in there" rename
variables, do not add helpful comments, do not improve formatting, do not
delete dead code unless deletion is the task. Anything beyond the strict
scope of the task becomes a separate task with its own brainstorming,
planning, TDD cycle, and review.

**Why this matters:** Drive-by changes inflate diffs, dilute the review
signal, increase merge risk, and silently introduce regressions in code paths
the original task did not touch. The reviewer expected to evaluate one change
is now evaluating four, and the bug introduced by change #3 ships because
attention was on change #1.

**How the kit enforces it:**

- The `/simplify` slash command ([`docs/tools/code-simplifier.md`](tools/code-simplifier.md))
  runs after implementation and reviews the diff for opportunities to remove
  code that did not need to be added in the first place.
- Code review skills check for diff bloat and flag changes that touch files
  unrelated to the task.

**Day-to-day discipline:**

- If you find a bug or smell adjacent to your work, file a follow-up task.
  Do not fix it in the same change.
- If a refactor would make your task easier, do the refactor as a separate,
  reviewed change first, then return to the original task with the cleaner
  ground.
- Resist the urge to add explanatory comments to code you did not write.
  If you needed the comment to understand it, the original code is the
  problem and that is a separate task.

---

## 4. Dual-graph and LSP before grep

**The rule:** When you need to find a symbol, navigate a codebase, or
understand how a function is used, call the dual-graph MCP first
(`graph_continue` and `graph_read`), then the language server's structured
queries (`goToDefinition`, `findReferences`, `documentSymbol`), then — only
if the prior tools were genuinely insufficient — fall back to grep. Bash
`grep`, `find`, `cat`, `sed`, and `awk` are forbidden as a first move.

**Why precision matters:** Grep matches strings. The dual graph and LSP
match meaning. A grep for `handleLogin` returns every file containing those
characters, including comments, strings, unrelated identifiers in unrelated
languages, and old logs. A `graph_read("src/auth.ts::handleLogin")` returns
exactly that function's lines. A `findReferences` query returns the call
sites the type system can prove are call sites, not strings that happen to
look like them. Working from imprecise matches is a primary source of
speculation, which violates principle #1.

**Why this is also about token economics:** Reading whole files to find one
symbol burns context that you will need later for the actual implementation.
A focused `file::symbol` slice is often less than 5% the size of the
surrounding file, and the dual graph's `confidence` field caps how much
additional exploration is even allowed. Discipline here is what keeps long
sessions from collapsing under their own context weight.

**How the kit enforces it:**

- `claude/CLAUDE.md` declares the search order mandatory.
- The dual-graph MCP ([`docs/tools/dual-graph-mcp.md`](tools/dual-graph-mcp.md))
  is registered automatically and exposed via `graph_continue`, which
  returns a structured suggestion before the agent has a chance to grep.
- The Go and TypeScript LSPs ([`docs/tools/lsp-gopls.md`](tools/lsp-gopls.md),
  [`docs/tools/lsp-typescript.md`](tools/lsp-typescript.md)) are
  pre-configured so that structured queries are available without per-project
  setup.

**Pitfalls:**

- "Let me just grep for it first" is the most common violation. It feels
  fast but produces noisy matches and biases follow-up reading toward
  whatever the first hit was.
- "I already know where that file is" still requires `graph_continue` —
  it may surface a better entry point and it records context for the next
  turn.
- Reading a 2000-line file to find a 20-line function is a failure mode the
  dual graph specifically exists to prevent.

---

## 5. Berry verification as a hard gate

**The rule:** Plan steps, root-cause analyses, test-pass claims, and
generated artifacts route through a Berry skill that requires evidence spans
with citations and a passing `audit_trace_budget` audit. If the audit fails
three times on the same claim set, stop and surface the failure to the user.
Do not silently loop, do not drop failing claims, do not paper over an
audit miss by rewording the conclusion.

**Why a hard gate:** Soft suggestions get skipped under deadline pressure.
A hard gate refuses to advance the work until evidence exists, which is the
only way the discipline survives the conditions under which evidence is most
likely to be invented. If verification only ran when the agent felt like
running it, verification would never run.

**The mechanics:**

- Every factual claim ends with a span citation (`[S0]`, `[S1]`, etc.).
- Claims without spans are labelled as assumptions.
- `audit_trace_budget` computes the KL divergence between
  P(YES | span in context) and P(YES | span redacted) — the "observed bits"
  the span contributes to the claim. Weak spans produce near-zero bits and
  fail the audit. Strong spans produce many bits and pass.
- Test output is captured as a span via `add_span` before any "tests pass"
  claim. The audit verifies the span actually contains the passing output.

**Why three strikes:** Repeated audit failures on the same claim set indicate
either a real lack of evidence (the agent should stop and gather more, with
human guidance) or a verifier configuration problem (the spans are well-formed
but the verifier cannot read them). Either way, looping past the third
failure wastes time and erodes trust. Stop, surface, ask.

**How the kit enforces it:**

- The Berry plugin and its workflow skills ([`docs/tools/berry.md`](tools/berry.md))
  are mandatory triggers for plan execution, RCA, test verification, and
  artifact generation.
- The `claude/CLAUDE.md` hard rules section makes the three-strike rule
  explicit, with API-format gotchas documented (the silent
  `{"<id>": "<text>"}` vs. correct `{"sid": "<id>", "text": "<text>"}` trap).

**Pitfalls:**

- Wrong span key shape (`{"S0": "..."}`) silently produces zero observed
  bits and looks like an evidence problem when it is actually a parameter
  shape problem. The verifier cannot read your span, so neither probability
  changes, so the divergence is zero, so the audit fails. Check the keys
  first.
- A passing audit with low total bits is a warning, not a victory. Gather
  stronger spans before proceeding.
- Disabling Berry "just for this one step" is the path back to speculative
  work. Disable it only for genuinely read-only sessions or throwaway
  sandbox scripts.

---

## 6. Explanatory output style

**The rule:** When the agent writes code, it follows the code with an
`Insight` block that explains the non-obvious choices, the trade-offs
considered, and the patterns the code adheres to. The point is to teach the
reader, not to flatter the writer.

**Why this is in the kit:** Code that ships without explanation accumulates
into a system no one understands six weeks later, including the person who
wrote it. The cost of writing a three-line `Insight` block at the moment of
the change is much smaller than the cost of an archaeologist reconstructing
the intent later. And the act of explaining the choice surfaces unjustified
decisions while they are still cheap to revisit — if you cannot articulate
why a function takes a `context.Context` as the first parameter, you have
not actually decided to add it; you have copied a pattern.

**What an Insight block contains:**

- The choice the code embodies (e.g., "this returns early on the empty case
  rather than threading the result through the loop").
- The alternative considered (e.g., "the loop-with-flag variant").
- The reason for the choice (e.g., "the early return is what the caller's
  retry budget assumes; threading would require updating three call sites").
- Any non-obvious trade-off the reader should know about.

**What an Insight block is not:**

- A restatement of what the code does at the line level. The code already
  says that.
- A defensive justification. If the choice needs defending, it needs
  redesigning.
- Marketing prose. The reader does not need to be sold on the change; they
  need to understand it.

**How the kit enforces it:**

- The explanatory-output-style configuration
  ([`docs/tools/explanatory-output-style.md`](tools/explanatory-output-style.md))
  is installed by `install.sh` and applied via a `SessionStart` hook so that
  the model produces Insight blocks without per-turn reminders.
- The style is treated as educational context, not as noise to be
  suppressed.

---

## How the principles compose

The six principles are a chain. Evidence-before-assertions gives you the
ground truth that TDD turns into a falsifiable claim. TDD's small, scoped
changes are what makes minimum-viable-changes possible. The dual-graph and
LSP discipline is how you gather evidence without burning the context budget
you need for the implementation. Berry is the mechanism that prevents the
prior principles from being skipped under pressure. And the explanatory
output style is how the discipline propagates — to the next session, to the
next reviewer, to the next maintainer.

Remove any one link and the chain weakens. Remove two and the kit is no
longer doing the work it was built to do. If you find yourself in a session
where you have skipped two of the six, stop and reset: this is the failure
mode the kit was assembled to prevent.

---

## What this kit is not

To prevent the kit from being mistaken for something it is not:

- **It is not a productivity multiplier in the "make Claude do more, faster"
  sense.** The discipline it enforces is, in the short term, slower than
  unconstrained work. The payoff is in fewer rollbacks, fewer regressions,
  and fewer "wait, why did we do it this way" archaeology sessions.
- **It is not a substitute for thinking.** The skills walk you through the
  process; you still have to do the work. Berry verifies evidence; it does
  not produce it. The dual graph suggests files; it does not understand the
  business logic.
- **It is not a fixed set of tools.** Each per-tool doc in `docs/tools/`
  spells out when to disable that tool. The kit's defaults are opinionated,
  but the configuration is yours.
- **It is not a guarantee.** A passing Berry audit means the evidence
  supports the claim, not that the claim is correct in a deeper sense. A
  passing test means the code does what the test says, not what you meant.
  The kit reduces classes of error; it does not eliminate error.

---

## Further reading

- [`docs/workflow.md`](workflow.md) — the 10-step development loop that
  operationalises the principles above.
- [`docs/tools/superpowers.md`](tools/superpowers.md) — the workflow-discipline
  skills.
- [`docs/tools/berry.md`](tools/berry.md) — the evidence-verification gate.
- [`docs/tools/dual-graph-mcp.md`](tools/dual-graph-mcp.md) — graph-first
  code navigation.
- [`docs/tools/feature-dev.md`](tools/feature-dev.md) — the structured
  multi-phase feature workflow.
