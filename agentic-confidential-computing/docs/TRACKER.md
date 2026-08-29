# Agentic Confidential Computing — Agentic Development Tracker (main)

Durable record of what happened, what is in flight, and what is open. Kept in
lockstep with the Task tool: every task transition pairs with an edit here.

## Iter-1 — Phase 0 bootstrap

Scaffolded the repository, encoded the development process, and stood up the
evaluation harness far enough to reproduce the false-negative paradox as a
test. Research documents are written from public sources only.

### Quality Loop State — Iter-1

| Stage | Status | Revision | Notes |
|---|---|---|---|
| Dev | complete | Phase 0 | Harness + docs scaffold |
| Verification | pending | Phase 0 | Berry gates unavailable this session — see Constraints |
| Optimization | pending | Phase 0 | — |

### V/O Findings Tracker — Iter-1

| ID | Source | Finding | Status |
|---|---|---|---|
| — | — | None recorded yet | — |

### Evidence — Iter-1

`python -m pytest -q` at Phase 0 revision:

```
...s....                                                                 [100%]
SKIPPED [1] tests/test_method_contract.py:45: plaintext_baseline declares it leaks
7 passed, 1 skipped in 0.02s
```

The skip is deliberate: `plaintext_baseline` declares that it leaks, and
`test_leak_check_has_teeth` asserts the leak check catches it — so the skip
cannot hide a broken check.

### Open issues — Iter-1 (deferred)

- **BLOCKER: `ai-cloud` is unreadable.** `add_repo` returned "requires
  approval" on four attempts; the GitHub MCP is scoped to `claude-code-kit`
  only; `git ls-remote` has no credentials. Phase 1 cannot start.
- **BLOCKER: the new repository does not exist.** `create_repository` against
  the `dthanos-datastealth` org returns 404 — the app cannot create repos
  there. This tree currently lives only on local disk.
- Berry and dual-graph MCPs are not connected in this environment, so the
  `audit_trace_budget` gate and dual-graph redundancy check could not run.
  Evidence is captured inline instead and labelled as such.
- Commit attribution: the kit forbids a Claude authorship trailer; this
  session's harness instructs the opposite. Following the kit.
