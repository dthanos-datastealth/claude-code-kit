# claude-code-kit TRACKER

> Per-project tracker per `~/.claude/docs/tracker-system.md`. Single source of
> truth for in-flight work, V/O findings, and iteration state.

## Last Updated: 2026-09-04 Iter-3 — IN PROGRESS

| Aspect | State |
|---|---|
| Active phase | Iter-3 PR-A: deployment-report defects + prerelease channel |
| Plan | Kept outside this repo (rev 8; Berry run 8f9226272b97fcdf, spans S0–S10, 0 flagged) — see note below |
| Dev branch | `prerelease` |
| Quality Loop State | dev done (111/111 GREEN, all lints clean); V+O pending on this revision |
| Open conflicts | none |

### Iter-3 note: the plan is deliberately not committed here

The convention is that plans live in `docs/plans/`. This one does not, and the
reason is worth recording rather than silently working around: this repository
is public, `scripts/lint-scrubbing.py` exists to keep company and customer
names out of it, and the plan's enterprise-distribution sections name the
private internal marketplace and the organisation repeatedly — five hits from
the scrubbing lint. Scrubbing those sections would remove the part of the plan
that carries the actual decisions.

So the plan stays outside the repo and this tracker carries the findings and
their disposition, which is what a reader here needs. If a plan of this kind
should be version-controlled in future, the private marketplace repository is
the right home for it, not the public kit.

### Iter-3 origin

A deployment onto one Mac plus three EC2 boxes produced a report of six
defects. Review of that report found two more (F5b, F7) and corrected the
premise of one (F6). Seven review rounds ran against the plan before execution;
the last was a workflow (five verification lenses, adversarial refutation,
three optimization lenses, completeness critic) returning 128 findings, of
which 15 were blockers. Each blocker was re-verified by hand against the raw
documentation and the repositories: five held, two did not.

### Iter-3 PR-A findings and disposition

| ID | Finding | Disposition |
|---|---|---|
| F1 | Dual-graph MCP documented but never named; `claude mcp add` recipe took an unobtainable path | FIXED — prereqs.md §10 names `graperoot`, states the tool contract, discloses the supply-chain profile; locator rule added to lint-tools-docs.py |
| F2 | `missing prerequisite: claude` while the binary is on disk but off PATH | FIXED — require() searches common install dirs and prints the path plus the export remedy; `hash -r` deliberately not suggested |
| F3 | philosophy.md claimed the dual-graph MCP "is registered automatically" | FIXED — bullet corrected and separated from the pre-configured LSPs; guarded by tests/test_docs_consistency.py, verified non-vacuous against the shipped text |
| F4 | Berry `.mcp.json` pins `/opt/homebrew/bin/uvx`; the kit lint could not see it | FIXED kit-side — command-field rule in lint-mcp-hardcoded-paths.py; upstream half is PR-B |
| F5b | The kit's own four plugin skills were flat files and had never loaded | FIXED — moved to `skills/<name>/SKILL.md`, plugin version bumped, tests repointed; scripts/lint-plugin-skill-layout.py added, RED against the real plugin before the move |
| F7 | Template shipped `effortLevel: max`, which the key does not accept | FIXED — `xhigh`; the assertion that hard-pinned `max` now reads the template; four README statements corrected |
| K9 | Release channel was implicit in three places | FIXED — derived from the settings template; self-check fails a promote that does not flip the refs |

### Iter-3 corrections to the plan itself, recorded

Two blockers the review produced did not survive hand-verification, and the
mistakes are recorded because both were mine, not the reviewers':

- An earlier revision asserted that Organization settings › Plugins does not
  reach the CLI. That treated the admin article's omission of the CLI as a
  denial; `plugin-marketplaces.md` documents org distribution as a Claude Code
  mechanism. The question of whether org-distributed plugins load in a terminal
  session is genuinely unanswered by the docs and is now an empirical step.
- The same revision quoted a sentence stating managed `enabledPlugins` cannot
  install plugins. That sentence exists in no Claude Code document; it came
  from a page-summarizing fetch. The real, verbatim constraint is narrower.

Load-bearing documentation claims are now taken from the raw
`code.claude.com/docs/en/<page>.md` and quoted with a line number.

## Iter-2 — CLOSED (2026-05-29)

| Aspect | State |
|---|---|
| Active phase | (none — Iter-2 closed; all Iter-1 deferred items resolved) |
| Last completed phase | Iter-2: A7 (lint-merge-policy + test-upgrade-isolated + CI wire) + _atomic.py helper consolidation + kebab-case rename |
| Plan | `~/.claude/plans/effervescent-spinning-bumblebee.md` (Berry-verified Iter-1 run_id 5b359944a9ff9741) |
| Dev branch | `main` |
| Quality Loop State | CLOSED — V=PASS (1 doc-only concern resolved) + O=worth-fixing (all 10 items addressed); tests=84/84 GREEN |
| Open conflicts | none |

### Iter-2 quality loop (final)

| Stage | Status |
|---|---|
| Kebab-case rename + ref updates | done — 77/77 still GREEN after rename |
| scripts/_atomic.py helper consolidation | done — both mergers import via sys.path |
| scripts/lint-merge-policy.py + 7 test cases | done — 84/84 GREEN |
| scripts/test-upgrade-isolated.sh | done — shellcheck clean, mirrors test-install-isolated.sh pattern |
| .github/workflows/ci.yml wire-up | done — lint-merge-policy step added; both isolated tests documented as local-only |
| V (Verification agent) | done — PASS with 1 doc-only CONCERN (CHANGELOG snake_case refs) |
| O (Optimization agent) | done — worth-fixing (10 items, all `worth-fixing` addressed; `worth-considering` deferred) |
| Fix-cycle for V+O findings | done — V concern + all 10 O findings closed in same revision |
| Iteration close | done |

### V/O findings (Iter-2)

| ID | Source | Severity | File:line | Finding | Status |
|---|---|---|---|---|---|
| V-1 | V Step F | CONCERN doc-only | CHANGELOG.md:19,22,82 | snake_case refs after rename | FIXED (kebab-case) |
| O-1 | O | worth-fixing | CHANGELOG.md:19,22,82 | same as V-1 | FIXED |
| O-2 | O | worth-fixing | README.md:36 (Mermaid inventory) | missing lint-merge-policy + test-upgrade-isolated | FIXED |
| O-3 | O | worth-fixing | README.md §"Testing the kit in parallel" | new test-upgrade-isolated.sh not mentioned | FIXED (added sibling note) |
| O-4 | O | worth-fixing | tests/test_intelligent_claude_md_merge.py:5,9 | unused json + pytest imports | FIXED (deleted) |
| O-5 | O | worth-fixing | tests/test_lint_merge_policy.py:10 | unused KIT_POLICY constant | FIXED (deleted) |
| O-6 | O | worth-fixing | tests/test_lint_merge_policy.py:59 | redundant .replace half of assertion | FIXED (simplified) |
| O-7 | O | worth-fixing | scripts/intelligent-claude-md-merge.py:194 | `elif x == "a" or x == "b"` non-idiomatic | FIXED (in tuple) |
| O-8 | O | worth-considering | scripts/_atomic.py:40 | atomic_write_json prefix `.settings-` not generic | FIXED (`.cck-`) |
| O-9 | O | worth-considering | scripts/intelligent-settings-merge.py:51 | dead `default` var | FIXED (deleted) |
| O-10 | O | worth-considering (pre-existing) | scripts/upgrade.sh:130-132 | orphaned `.before` snapshot cp | FIXED (deleted) |

### Open issues (carry to next iteration)

- Berry audit on Iter-2 pytest output (deferred from Iter-2 close due to no new external behavior claims; would re-validate the same "all tests pass" claim from Iter-1).
- Python atomic_write helper consolidation: DONE this iteration (was a worth-considering deferred item from Iter-1).
- A7: DONE this iteration.
- snake_case → kebab-case rename: DONE this iteration.
- Issue #55067 upstream — kit cannot fix; documented in docs/notion-mcp-pinning.md.

---

## Last Updated: 2026-05-29 Iter-1 — CLOSED

| Aspect | State |
|---|---|
| Active phase | (none — Iter-1 closed) |
| Last completed phase | Iter-1: intelligent upgrade tooling + Notion port-pinning |
| Plan | `~/.claude/plans/effervescent-spinning-bumblebee.md` (Berry-verified run_id 5b359944a9ff9741) |
| Dev branch | `main` (direct; small kit, no PR workflow yet) |
| Quality Loop State | CLOSED — V=CONCERN (deferred A7 only), O=worth-fixing (all addressed), tests=77/77 GREEN |
| Open conflicts | none |

### Quality Loop State (Iter-1, final)

| Stage | Status | Notes |
|---|---|---|
| TDD cycles (40 new cases) | done | All RED→GREEN; 77 total tests pass |
| Berry audit on test outputs | done | run_id 5b359944a9ff9741 S9 — PASS (observed 28-40 bits vs required 23-33) |
| V (Verification agent) | done | Verdict: CONCERN — implementation correct + wire paths all live; only deferred-A7 (lint-merge-policy.py + test-upgrade-isolated.sh) noted as concern |
| O (Optimization agent) | done | Verdict: worth-fixing (9 items, 2 BLOCKER-class); see findings below |
| Fix-cycle for V+O findings | done | All 9 O-findings addressed; 2 BLOCKERs cleared, others as listed |
| Iteration close | done | V CONCERN treated as defer-OK (A7 = separate iteration); O worth-fixing all resolved |

### V/O Findings Tracker (Iter-1)

| ID | Source | Severity | File:line | Finding | Status | Resolution |
|---|---|---|---|---|---|---|
| V-1 | V Step 0 | concern | n/a | A7 not shipped (lint-merge-policy.py + test-upgrade-isolated.sh) | DEFERRED | Will ship in next iteration; pytest target globs the new tests automatically so coverage gate intact |
| V-2 | V (minor) | trivial | docs/TRACKER.md | Tracker stale (V/O verdicts row) | FIXED | This update closes that gap |
| O-1 | O scrubbing-lint | BLOCKER | plugins/claude-code-kit/skills/fix-notion-mcp-port.md:3 | "DataStealth Notion blocked me" string | FIXED | Replaced with "enterprise Notion blocking install" |
| O-2 | O scrubbing-lint | BLOCKER | docs/TRACKER.md:11 | /Users/dthanos/.claude/plans path | FIXED | Replaced with ~/.claude/plans |
| O-3 | O doc/code drift | worth-fixing | README.md (11+ places) | 21 plugins / 5 marketplaces / 23 docs / 36 tests stale | FIXED | All counts updated to 22 / 6 / 24 / 76 |
| O-4 | O doc/code drift | worth-fixing | claude/CLAUDE.md.manifest.json:3, scripts/merge-policy.json:3 | refs nonexistent scripts/intelligent-merge.py | FIXED | Updated to intelligent_claude_md_merge.py + intelligent_settings_merge.py |
| O-5 | O doc/code drift | worth-fixing | plugins/claude-code-kit/skills/rollback.md vs scripts/upgrade.sh | Skill claimed rollback updates .kit-version but script didn't | FIXED | Implemented .kit-version update in scripts/upgrade.sh rollback path; test_case_14b added |
| O-6 | O lint | worth-fixing | scripts/intelligent_claude_md_merge.py:121 | f-string without placeholders | FIXED | Removed f-prefix |
| O-7 | O lint | worth-fixing | scripts/intelligent_*.py atomic_write | try/except one-liners (SIM105) | FIXED | Replaced with contextlib.suppress(OSError) in both files |
| O-8 | O dead code | worth-fixing | scripts/intelligent_settings_merge.py:79-87 | apply_policy loop is no-op | FIXED | Deleted; comment notes future-extension hook |
| O-9 | O redundancy | worth-fixing | install.sh + scripts/upgrade.sh | backup + version-marker duplicated | FIXED | Consolidated into scripts/_kit_backup.sh (kit_backup_files, kit_write_version_marker, kit_cache_snapshot, kit_log_history); both sourced |
| O-10 | O (worth-considering) | worth-considering | snake_case vs kebab-case naming | Inconsistent scripts/ naming | DEFERRED | Rename would touch many imports; defer to follow-up iteration |
| O-11 | O (worth-considering) | worth-considering | scripts/intelligent_*.py atomic_write x2 | Same shape in two files | DEFERRED | Borderline per O's own report; only worth consolidating when 3rd site appears |

### Open issues (carry to next iteration)

- A7 (lint-merge-policy.py JSON-schema validator + scripts/test-upgrade-isolated.sh smoke gate) — wire into .github/workflows/ci.yml when shipped.
- Python atomic_write helper consolidation (worth-considering) — defer until 3rd site appears.
- snake_case → kebab-case rename of intelligent_*.py (worth-considering) — cosmetic; defer.
- Issue #55067 upstream (re-auth ignores callbackPort) — kit cannot fix; documented in docs/notion-mcp-pinning.md as caveat.

---

## Earlier

(No prior iterations recorded — TRACKER.md introduced in Iter-1.)
