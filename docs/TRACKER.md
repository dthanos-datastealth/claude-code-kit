# claude-code-kit TRACKER

> Per-project tracker per `~/.claude/docs/tracker-system.md`. Single source of
> truth for in-flight work, V/O findings, and iteration state.

## Last Updated: 2026-09-11 Iter-5 — IN PROGRESS

**Phase: mutation testing.** Chosen over the depth-changing rename bug
(V2-3), which stays open. Reasoning recorded because the trade-off is the
interesting part: the rename bug is latent by construction — it needs a
second `renamed_from` entry that also changes heading depth, in the legacy
`CLAUDE.md` merge path, which only runs below Claude Code 2.0.64. Three
conditions, none current, all under our control.

Mutation testing is not one bug. It is the only check that found two of the
bugs in Iter-4, and the only one that could have:

| Check | Verdict on `tests/test_kit_compute_path.py` |
|---|---|
| Suite green | passed |
| V+O round 1 | no finding |
| O's revert matrix | "covered" — reverting the file does fail tests |
| **Mutation** (append → prepend) | **214 passed, zero failures** |

The revert matrix and mutation disagree, and mutation is right: reverting a
whole file breaks enough that something fails, so the file looks covered,
while flipping one operator leaves everything green. That test was the
centrepiece of a BLOCKER fix, written while explicitly fixing unfalsifiable
tests, and reviewed by a V agent.

So the honest position before this phase: every fix has a test, and we cannot
say which of those tests would catch a regression. Two checked could not.
`docs/verification-standards.md` already says a check that cannot observe the
failure it is meant to catch reports success and ends the investigation — the
kit applies that to product code and has no way to apply it to its own tests.

| Aspect | State |
|---|---|
| Active phase | Iter-5: mutation testing harness, then V2-3 fixed mutation-first |
| Dev branch | `prerelease`, at `c779568` |
| Plan | `scripts/mutate.py` + `mutants.json` + a test asserting every listed mutant is killed |
| Quality Loop State | Dev complete; V+O not yet dispatched on this phase |
| Open conflicts | none |

### Iter-5 result

`scripts/mutate.py` + `scripts/mutants.json` (15 mutants) + `tests/test_mutants.py`
(7 catalogue-integrity tests). Wired into `.github/workflows/ci.yml` after the
suite, because a surviving mutant only means anything when the tests otherwise
pass. Documented in `docs/verification-standards.md` §5 and referenced from
rule 30.

**First run: 12/15 killed.** The three survivors are the useful part, and only
one was a weak test:

| Survivor | Cause | Resolution |
|---|---|---|
| `notion-port-defaults-to-local-scope` | **Genuinely weak test.** `test_registers_at_user_scope` asserted `"--scope user" in log`, which the three *remove* lines satisfy — so it passed with the add left at its default local scope | Assertion now targets the `mcp add` line specifically |
| `uninstall-ignores-kit-value` | **Mis-targeted mutant.** Named `tests/test_uninstall.py`; the covering tests live in `tests/test_rollback.py` | Mutant retargeted. Kept as a note that uninstall coverage is split across two files |
| `verify-install-accepts-missing-rules` | **Equivalent mutant.** Disabling the `is_dir()` check changed nothing observable — the kit-rule-prefix check immediately below catches the same condition and still exits 1 | Retargeted at the whole `expect == "rules"` branch |

After resolution: **15/15 killed**. Suite 225 passed / 1 skipped (226 total),
33.6s. Lints and shellcheck clean.

Worth recording that two of three survivors were problems with the *mutants*,
not the tests. That ratio is the argument for `tests/test_mutants.py`: a
catalogue that rots silently is the same failure one level up.

**Still open:** V2-3, the depth-changing rename bug. Next, and to be fixed
mutation-first — the mutant `merge-ignores-renamed-from` already exists and is
killed, so the new test can be checked against a depth-changing variant of it.

---

## 2026-09-10 Iter-4 — COMPLETE (pushed `5b48c1f`, `c779568`)

A clean-machine install and full end-to-end test pass of `prerelease` @
`4d08e48` (macOS 26.6.2 arm64, Claude Code 2.1.267) produced **30 findings**,
recorded in `INSTALL-FINDINGS.md` at the repo root with the evidence for each.
`install.sh` itself ran clean — 6/6 marketplaces, 22/22 plugins, no retries —
and the suite was 174 passed / 1 skipped with all five lints green. The
defects are in what surrounds the installer.

| Aspect | State |
|---|---|
| Active phase | Iter-4: fix all 30 install findings |
| Plan | `~/.claude/plans/nested-marinating-stardust.md` (approved) |
| Plan Berry gate | run `e479d16648ca4486` first pass 3/7 flagged; second pass **0 flagged, 4/4 passed, 8 verifier calls**, `openai/gpt-4o-mini` |
| Dev branch | `prerelease` |
| Quality Loop State | Dev complete (all 6 phases); V and O both reported; blockers and worth-fixing items closed. Re-run of V+O waived by the user. |
| Suite | 216 passed, 1 skipped (217 total; baseline was 174) |
| Lints | 6 lint scripts + shellcheck, all exit 0 |
| End to end | `test-install-isolated.sh` PASSES including its leak check; `test-upgrade-isolated.sh` PASSES |
| Berry gates | plan `e479d16648ca4486`; completion `1b9ccf17b77d0b26` (5/5); e2e `b57a2318a05e9217` (7/7) |
| Open conflicts | none |

### Iter-4 round 2 — evidence-only V+O against `5b48c1f`

Re-dispatched under a stricter bar: every finding must be EXECUTED (a command
and its literal output) or CITED (an authoritative source fetched that run).
Anything that could not meet it was to be dropped rather than reported.

**V: `VERIFICATION: PASS`** — both prior blockers proven fixed by execution,
each with a control run showing the reproduction still detects the original
defect. Three new CONCERNs, all with a failing command attached.

| ID | Severity | Finding | Status |
|---|---|---|---|
| V2-1 | CONCERN | `uninstall.sh` deleted user-set `PATH` / `CLAUDE_CODE_ENABLE_TODO_TOOLS` on key presence alone, destroying the exact values `install.sh` refuses to overwrite. Demonstrated: seeded `{"CLAUDE_CODE_ENABLE_TODO_TOOLS":"0","PATH":"/my/own/path"}`, install left them alone, uninstall emptied the file to `{}` | CLOSED — compares against `kit_compute_path` and the kit's `"1"`; non-matching values are kept and reported. `tests/test_uninstall.py` RED first |
| V2-2 | CONCERN | `scripts/_kit_env.sh:39` forked `dirname` at **source time**, so on a PATH lacking it `KIT_RUNTIME_ENV_KEYS_FILE` silently resolved to `$PWD` and `kit_write_runtime_env` aborted the install without writing settings.json. Contradicted the file's own stated pure-shell invariant. Reachable from a Homebrew-only PATH that passes preflight | CLOSED — parameter expansion; reproduction now resolves correctly under `PATH=/bin` |
| V2-3 | CONCERN | `renamed_target` does not handle a rename whose heading **depth** changes: the stale section is kept and the new one appended at end of file — the outcome `renamed_from` exists to prevent. Not triggered by the shipped manifest (its only rename is depth 4→4) | OPEN |
| V2-4 | note | Local `shellcheck` is 0.11.0; `ci.yml` pins 0.10.0, undercutting that file's stated rationale that a local run is authoritative | OPEN |

V also confirmed by citation: uv's deprecation of `UV_NATIVE_TLS`, TypeScript
7.0.2 shipping no `lib/tsserver.js` (and `versionProvider.ts` loading exactly
that path), Homebrew `python@3.12` **not** being keg-only while `openjdk` is,
`claude mcp` scope precedence, and the `CLAUDE_CODE_ENABLE_TODO_TOOLS` gate.

**Process finding, recorded against myself:** this tracker was updated in a
batch at the end of the previous round rather than per step, which rule 40
forbids and which V flagged as a CONCERN. Reinforced in the rule with an
explicit trigger list rather than stronger wording.

**O: `OPTIMIZATION: CHANGES-RECOMMENDED`** — three `worth-fixing`, every one
proved by mutation or A/B measurement rather than inspection. O also ran a
revert matrix (each changed file restored to `4d08e48`, suite rerun) showing
every behavioural fix in the diff is covered by at least one test; the two
gaps below were only findable by mutation, which is why the first review
missed them.

| ID | Severity | Finding | Status |
|---|---|---|---|
| O2-1 | worth-fixing | The harness change symlinked the **real** `npx` into the isolated PATH, so every isolated install performed live npm downloads. A/B on the same tree: **351s vs 25s**, 138 network fetches, ~177 MB per throwaway HOME, **6.89 GB** peak under `tests/.tmp` | CLOSED — `node`/`npx` are now always stubs. Measured after: **33.6s** |
| O2-2 | worth-fixing | `tests/test_kit_compute_path.py` **passed against the exact prepend regression it is named for**. `git` is processed before `python3` in `KIT_RUNTIME_TOOLS`, so python3's own prepend restored `early` to the front and the output was byte-identical | CLOSED — shadowing stub changed to `npx` (processed after python3). Verified: 2 fail under mutation, 6 pass on real code |
| O2-3 | worth-fixing | `test_install_succeeds_with_no_npx` asserted nothing — its `A or B` was satisfied by the pre-warm branch, and deleting the guard it named left all 3 tests green | CLOSED — replaced with a test that npx absence **stops** the install, plus a positive control |
| O2-4 | worth-considering | `prewarm_npx_mcps`'s missing-npx guard became unreachable once preflight required npx | CLOSED — guard removed; an unreachable guard documents a fallback that cannot happen |

O measured and explicitly **did not file**: `kit_compute_path` at 6.3 ms/call;
122 process spawns per install with none redundant; settings.json read 2×
written 2× per install at ~15 ms interpreter startup each. Recorded here so
the numbers exist without becoming findings.

**Correction against myself:** I initially disputed O2-2 from a manual
reproduction that appeared to show both stub layouts detecting the prepend.
My reproduction was wrong — it had a leftover `npx` stub from a second layout,
which masked the effect. Running the actual test against the mutated function
settled it: 6 passed. O was right; the reasoning I used to doubt it was not
evidence.

### Iter-4 round 2 — Berry validation via the MCP, file-backed

Berry's MCP reconnected after a restart, so the round-2 fixes were validated
through the documented path rather than the stdio workaround used earlier:
`start_run` → `add_file_span` (server reads the file, pins to `sha256`) →
`audit_trace_budget_run(require_citations: true)`.

Run `7fa0b483b98dc03e`, spans S2–S5 and S7, all file-backed with
`file_sha256 == worktree_file_sha256`.

| Claim | Status | Posterior | Observed bits |
|---|---|---|---|
| `combined="${combined}:${dir}"` places dir after | `passed` | 1.000 | 23.80–39.86 |
| appends `/usr/bin` and `/bin` | `passed` | 0.99999 | 22.18–39.86 |
| uninstall deletes a runtime key only on value match | `passed` | 0.9989 | 24.48–39.80 |
| ordering test stubs `npx` in the shadowing dir | `passed` | 0.99995 | 25.79–39.86 |
| first statement of `prewarm_npx_mcps` is a `log` call | `passed` | 0.9997 | 24.87–39.85 |
| **false control:** dir is prepended | `contradicted` | 1.3e-10 | ~0 |
| **false control:** `combined="${dir}:${combined}"` | `contradicted` | 2.8e-10 | ~0 |

Two false controls against the same spans as their true counterparts, both
contradicted. A rubber-stamping verifier passes both halves of such a pair;
this one did not.

**Span hygiene lesson, and it cost two audit rounds.** The true "appends"
claim first scored **0.562** (`not_entailed`) because the cited span ran from
line 73 and therefore included the comment explaining that *an earlier version
prepended*. The verifier saw both behaviours described in its evidence and
declined to entail either. Narrowing the span to lines 74–89 — code, no
comment — scored the identical claim at **1.000**. A comment documenting a
fixed bug poisons the span for claims about current behaviour. Added to
`50-kit-plugins.md`.

**Correction to the kit, and to my earlier correction.** I had written into
`claude/CLAUDE.md` and `docs/tools/berry.md` that "there is no `observed_bits`
field". That is true of the inline `audit_trace_budget` and false of
`audit_trace_budget_run`, which returns `observed`, `required` and
`budget_gap` in bits plus prior and posterior. The user's override said bits
were the signal; I contradicted it from incomplete measurement of only one of
the two calls. Both documents corrected.

### Iter-4 Quality Loop State

| Stage | Status | Findings | Notes |
|---|---|---|---|
| Dev | Complete | — | 31 findings fixed across 6 phases |
| Verification | Reported `VERIFICATION: FAIL`, findings closed | 2 BLOCKER, 3 SHALLOW TEST, 4 TEST MISSING, 6 CONCERN | All blockers and shallow tests fixed; see below |
| Optimization | Reported `OPTIMIZATION: CHANGES-RECOMMENDED`, worth-fixing closed | 3 worth-fixing, 14 worth-considering, 11 trivial | 3 worth-fixing + 3 worth-considering applied |
| Berry | 3 gates, 0 flagged after evidence correction | — | Flagged 4 claims across the session before passing |

### Iter-4 V/O findings and disposition

| ID | Agent | Severity | Finding | Status |
|---|---|---|---|---|
| V-1 | V | BLOCKER | `kit_compute_path` PREPENDED resolved dirs; `git` at `/usr/bin` hoisted `/usr/bin` above `python@3.12/libexec/bin`, so the persisted PATH resolved `python3` to 3.9 — reintroducing #1/#13 permanently | CLOSED — appends now, `/usr/bin:/bin` floor added, pure shell (the old version died on an impoverished PATH because it forked `dirname`). `tests/test_kit_compute_path.py`, 6 cases |
| V-2 | V | BLOCKER | `claude mcp remove --scope user` stopped removing a pre-existing **local**-scoped `notion`, which outranks user scope and silently shadows the pin | CLOSED — every scope cleared before the add; test asserts all three |
| V-3 | V | SHALLOW TEST | `test_preflight_accepts_a_python3_at_or_above_the_floor` could not fail (disjunction always true) | CLOSED — asserts `returncode == 0` and absence of "too old" |
| V-4 | V | SHALLOW TEST | Two `test_install_env_path` cases measured the harness, not the code | CLOSED — properties moved to unit tests against controlled PATHs |
| V-5 | V | TEST MISSING | No coverage of multi-directory PATH composition — the configuration that produced V-1 | CLOSED |
| V-6 | V | TEST MISSING | dry-run delta, uninstall rules-restore, `permissions`/`statusLine` preservation | CLOSED — 5 new cases |
| V-7 | V | CONCERN | "keg-only" is the wrong mechanism for `python@3.12` (`keg_only: false`; only unversioned names diverted) | CLOSED — wording corrected |
| V-8 | V | CONCERN | Version claim `2.1.233` for the Task-tool opt-in not supported by current docs | CLOSED — version number removed, reader pointed at their own tools reference |
| V-9 | V | CONCERN | TRACKER stale | CLOSED — this section |
| V-10 | V | CONCERN | Kit pins `typescript@5`; upstream now pins `@6`, which also ships `tsserver.js` | OPEN — `@5` is the conservative pin and is verified working here; revisit |
| O-1 | O | worth-fixing | Prereq list duplicated between `install.sh` and `KIT_RUNTIME_TOOLS` | CLOSED — preflight derives from the array |
| O-2 | O | worth-fixing | Runtime env key list in four places | CLOSED — `scripts/kit-runtime-env-keys.txt` is the single source; consistency test added |
| O-3 | O | worth-fixing | `reinstall_over_existing` duplicated `run_install`'s child-process contract | CLOSED — `_exec_install` extracted |
| O-4 | O | worth-fixing | `test_install_env_path` ran six installs (41s) for one install's worth of assertions | CLOSED — module fixture, ~13s |
| O-5 | O | worth-considering | uninstall restored six kit rule files then deleted them three lines later | CLOSED — restore moved after deletion, copies only surviving files |
| O-6 | O | worth-considering | `test_fix_notion_port` assertion loosened until the *add* line satisfied it | CLOSED |
| O-7 | O | worth-considering | Two interpreter starts in `kit_compute_path` | CLOSED as a side effect of V-1 — now pure shell |
| O-8 | O | various | Remaining worth-considering / trivial items: shared `kit_restore_rules`, settings.json read twice per run, harness recomputes counts, duplicated incident narratives in comments, `verify-install.py` hardcoded rule prefixes, unreachable `npx` guard | OPEN — recorded, not blocking |

### Iter-4 origin

Three root causes account for most of the 30:

1. **The rules migration was left half-done.** `install.sh` stopped writing
   `CLAUDE.md` and began writing `~/.claude/rules/`, but the isolation
   harness, `kit_backup_files` and `uninstall.sh` were never updated. The
   harness now fails on every run — and fails *before* its leak check, which
   is the only thing it exists to prove. The kit's own instructions have no
   revert path at all.
2. **Checks that cannot observe what they claim to check.** `--status`
   reports drift it never computes. The README's `jdtls --help` check exits 0
   on a machine with no JVM. `tsc --version` passes while the TypeScript LSP
   is dead. This is precisely the failure mode
   `docs/verification-standards.md` was written against, committed four times
   in the kit's own tooling.
3. **Prerequisites declared but not enforced, or documented wrongly.** Node
   is a hard runtime dependency of four enabled plugins and appears in no
   prereq list and no preflight check; `brew install python@3.12` and
   `npm install -g typescript` both produce installs that fail their own
   documented verification.

The Berry gate on the plan is worth recording as a worked example. The first
pass flagged 3 of 7 claims. The claims were right; the *spans* were the
problem — two carried `...` elisions the verifier could not rule a version
check out of, and one span mixed the TypeScript 7 defect with its
`typescript@5` fix. Replacing paraphrase with literal source and splitting the
compound claim moved all four to `passed`. Rewording would not have.

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
| K10a | `claude/CLAUDE.md` at 503 lines against the ~200-line guidance, and about to become non-excludable via managed `claudeMd` | FIXED — 341 lines. The 290-line plugin catalogue restated the 24 `docs/tools/*.md` depth references, so it is now a table saying when to reach for each tool; the Spec-Kit playbook moved whole into `docs/tools/spec-kit.md`; Berry's operational rules stay inline because they gate every session |
| K10b | The kit's three V+O verification standards existed only as assertions | FIXED — `docs/verification-standards.md` carries each with the failure mode it exists to catch; CLAUDE.md states each in one line and points there; shipped via `TOP_LEVEL_DOCS`, which the test now reads from `install.sh` rather than restating |
| F8 | Upgrade never removed a section the kit had dropped — the merger walked the user's file with no branch for a heading absent from the new template, so retired guidance survived forever beside its replacement | FIXED — unmodified sections are removed, user-edited ones go to the conflict path; manifest entries for retired headings are tombstones and documented as such, since the entry is what makes a section removable |
| F9 | Fresh installs registered no marketplace: the derived spec was a git URL while settings declares a `github` source, and the CLI refuses a kind mismatch | FIXED — `owner/repo` / `owner/repo@ref` shorthand, HTTPS preserved by `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1`. Found by the isolated harness against the real CLI; the unit test had only checked that each repo name appeared somewhere in the command, which both forms satisfy |
| F10 | Skill-layout lint false-positived on `caveman`'s `native-core.md`, a frontmatter-less prose fragment beside `compile.mjs` | FIXED — a skill opens with a `---` frontmatter block, as all six genuinely broken Berry skills did; that is now the discriminator |
| F11 | The isolation harness failed whenever a Claude Code session was running | FIXED — it compared `~/.claude.json` mtimes, but the CLI rewrites that file constantly. Measured with no install running: whole-file digest and `pluginUsage` both moved inside 70s while `mcpServers` held still. Now digests `mcpServers` alone |
| F12 | CI red on every run since 2026-08-07 on both `main` and `prerelease`; no gate was enforcing anything on merge | FIXED — two shellcheck findings (SC2119 bare call to an optional-arg function, SC2002 useless cat) that the runner's apt shellcheck emits and a newer local build does not. Fixed at source and verified against a downloaded v0.10.0, not just the local 0.11.0; CI now pins that version so a local run is authoritative. First green run: `3d7a540`, all 14 steps |
| F13 | Two concurrent pytest sessions in one checkout deleted each other's isolated HOMEs, producing six unrelated-looking failures | FIXED — every session shared one `tests/.tmp` and teardown rmtree'd the whole root. Each session now owns a subdirectory and removes only that. Observed live when a review agent ran the suite concurrently; reproduced deterministically before the fix (6 failures) and clean after (0) |
| V-1 | BLOCKER — an upgrade never delivered the release. 14 headings the kit ships were absent from the manifest, so the merger preserved the user's old copy of each: both agent protocols, all Berry operational rules, the TDD and V+O subsections. The three ported verification rules reached nobody who upgraded | FIXED — every heading listed; a clean upgrade now reproduces the template byte for byte, asserted with a diff on failure. Guard fails if any of the three sections loses its entry |
| V-2 | BLOCKER — depth-4 `#### How Claude drives spec-kit` orphaned on upgrade (31 lines), refiled under `### Berry`, because `matches_owned` compares depth exactly and the `### Spec-Kit` tombstone did not cover it | FIXED — tombstone at its own depth; covered by the byte-identity guard |
| V-3 | BLOCKER — the skill lint's frontmatter filter silently skipped misplaced skills. `skills.md:330` "All fields are optional"; `:338` `name` defaults to the directory name; `:339` `description` falls back to the first paragraph — so a skill loads with no frontmatter | FIXED — reports both kinds, fails only on the confident case, warns on the rest. Caveman's fragment no longer fails the gate; all six real Berry defects still do |
| V-4 | CONCERN — `claude-code-kit` and `explanatory-output-style` were enabled but named nowhere in CLAUDE.md | FIXED — both named; a test asserts every enabled plugin appears |
| V-5 | CONCERN — CLAUDE.md promised a depth-reference at `<name>.md`, false for playwright-mcp, lsp-gopls, lsp-typescript | FIXED — the table names the file where it differs; a test asserts every doc named in CLAUDE.md exists |
| V-6 | CONCERN — merger tests used a synthetic fixture that passed while the real shipped upgrade failed | FIXED — the real template pair is now exercised in both directions |
| V-7 | CONCERN — spec-kit.md said nine commands (upstream documents ten) and duplicated two sections the ported playbook already carried | FIXED — count corrected from the raw upstream README, duplicates removed, and the separator ambiguity (`/speckit.x` and `/speckit-x` both appear upstream) stated rather than guessed |
| V-8 | trivial — merger dropped the blank line after the H1, so output was never byte-identical | FIXED — a body of one empty line is no longer indistinguishable from no body |
| O-12 | worth-fixing — the README-count test spawned a nested pytest, re-collecting what the running session had just collected, and its session teardown deleted the outer run's fixtures | FIXED — in-process AST count, verified equal to collection (126 = 126) with a guard that fails if `parametrize` is ever introduced |
| O-13 | worth-fixing — `tests/test_install_docs.py` ran three identical installs (~2.4s) and read from all three | FIXED — one module-scoped install; module now 1.2s |
| O-14 | worth-fixing — tracker finding ID `F5` in a source comment, against the kit's own rule | FIXED |
| O-15 | worth-fixing — comment claimed 23 tool docs; 24 ship | FIXED — count dropped rather than restated |
| O-16 | worth-considering — dead `exempt` branch in the skill lint that could not fire for its stated purpose, and suppressed all findings for a plugin declaring `skills: ["skills"]` | FIXED — branch and its now-unused helper removed |
| F14 | The prerelease channel was unreachable for any existing install. The settings merge gave the user's copy priority for every marketplace including the kit's own, so a new `ref` never landed, and `claude plugin marketplace add owner/repo@ref` is then refused | FIXED — the kit's own marketplaces are authoritative, user-added ones untouched. The policy's stated rationale already said this; the implementation did the opposite |
| F15 | The documented channel-switch recipe had its two halves in the wrong order — `upgrade.sh` writes the ref that the marketplace add is validated against | FIXED — order corrected and the reason written next to the snippet. Both orders were run against a real install from `main` |
| F16 | An upgrade never refreshed `~/.claude/docs/`. `copy_docs` lived only in `install.sh`, so an upgraded machine had a CLAUDE.md citing `verification-standards.md` four times with no such file, and the previous release's copy of every other doc | FIXED — factored into `scripts/_kit_docs.sh`, called from both, following the `_kit_backup.sh` pattern. Three tests, one of which fails on any doc CLAUDE.md names that the upgrade does not install |
| F17 | Upgrade aborted on macOS whenever no cached previous template existed: under `set -u`, bash 3.2 treats `"${arr[@]}"` on an empty array as unbound | FIXED — portable `${arr[@]+"${arr[@]}"}` expansion |
| V-9 | BLOCKER (round 2) — both real-upgrade guards were vacuous. `git log -2 -- claude/CLAUDE.md` resolves mid-release to an earlier commit of the release being developed, so zero headings differed and the assertions asserted nothing | FIXED — replay from a committed fixture of the template stable users have; the fixture is rejected if it ever equals the current template. Proven against four seeded regressions |
| V-10 | BLOCKER (round 2) — one of those guards never ran at all: a rewritten copy sat above an older definition of the same name, so the older shadowed it and pytest said nothing | FIXED — a test fails on any duplicated test name in a module |
| V-11 | CONCERN — removing the skill lint's exemption wholesale turned a legal layout (`skills: ["./skills"]` with `skills/SKILL.md`) into a false positive | FIXED — exemption restored but narrowed to the declared directory's own SKILL.md, so declaring the root no longer silences every finding. Both directions tested |
| V-12 | CONCERN — the lint printed warnings and then an unqualified all-clear | FIXED |
| V-13 | CONCERN — the manifest's `parent` field is never read by the merger, so it reads as scoping that does not exist | FIXED by documenting it as descriptive, plus a test forbidding the ambiguity it appeared to prevent |
| V-14 | CONCERN — the non-interactive abort surface widened with the new ownership entries | DOCUMENTED in `docs/upgrading.md`: what aborts, why the surface grew, and that any heading the kit never shipped stays the user's forever |
| O-17 | worth-considering — the scratch-dir test asserted on conftest's source text, the proxy shape this kit's own standards forbid | FIXED — asserts teardown behaviour against a planted sibling session directory |
| O-18 | trivial — a killed session's scratch directory leaked and blocked cleanup permanently | FIXED — reaped at session start when its PID is gone |
| V-15 | CONCERN — the one lossy upgrade path was silent: a kit marketplace the user repointed at their own fork is restored with no signal, and `--dry-run` did not preview it | FIXED — the merger reports each entry it reclaims, naming the old and new value, and `upgrade.sh --dry-run` now runs the settings merge in preview mode so the report appears before anything is written |
| V-16 | trivial — the settings merger's `--help` still described `union_dict + user-wins` | FIXED |
| O-19 | worth-considering — `tests/test_upgrade_docs.py` spawned three identical upgrades | FIXED — module-scoped fixture; 1.93s to 0.57s |
| O-20 | trivial — the upgrading TL;DR said marketplaces are preserved, unqualified | FIXED — "the marketplaces you added", with the exception named and linked |
| O-21 | trivial — the policy/doc sync test skipped a policy key absent from the table instead of failing | FIXED — an undocumented key with a conflict winner now fails |
| O-22 | flag-don't-fix — 18 no-argument `run_install()` calls are roughly 25-35s of a 52s suite | DECLINED for this release, recorded as follow-up. Pre-existing, orthogonal to every defect here, and the safe fix is per-module fixtures verified read-only one module at a time, which is its own change. `test_install_docs` and `test_upgrade_docs` were done that way; the rest remain |
| O-23 | trivial — `scripts/_kit_docs.sh` vs `_kit_backup.sh` split | KEPT — both cohesive, sourced by the same two callers, 111 lines total. Revisit if a third file arrives carrying the same `REPO_DIR`/`CLAUDE_HOME`/`log()` preamble contract |
| V-17 | The reclaim note fired for entries the user never touched: an untouched user switching channel saw two "replaced" notes because the kit bumped its own ref, which is how the one note that means real loss gets tuned out. It also did not say what to do | FIXED — the two cases are told apart by where the entry points. Same target, the kit updated itself, quiet line. Different target, the user aimed it elsewhere and that is undone, loud line carrying the remedy. No new cached state needed |
| O-24 | worth-considering — `upgrade.sh --dry-run` gained a code path and nothing exercised that command, though it is the first one the docs tell a user to run | FIXED — smoke test asserts exit 0 and a byte-identical `~/.claude`, scoped past the interpreter's own bytecode cache. Proven non-vacuous by making dry-run write |
| O-25 | trivial — the kit-wins predicate was stated in two places, one deciding what to report and one deciding what to write | FIXED — one `kit_wins()` helper, since a disagreement would print a note that does not match the merge |
| O-26 | trivial — indentation residue from the fixture refactor | FIXED |
| OB-1 | optibot [RE-INCURRED BLOCKING WAIT] — the harness wrote a new fake `claude` executable per install, and macOS charges roughly 180ms the first time any newly created executable runs, nothing on re-exec. Paid 28 times | FIXED — the fake CLI takes its log path from `CCK_FAKE_CLAUDE_LOG`, so the script is identical every run, written once per process and symlinked; symlinks do not pay the tax. Measured tax independently at ~179ms per inode. Suite 33s to 27s |
| OB-2 | optibot — the per-session scratch dir made the suite parallel-safe for the first time, worth 3x, and nothing was taking it | FIXED — `pytest-xdist` and `-n auto` in CI. Verified independently: pre-diff tree at `-n 8` fails with FileNotFoundError on different tests each run; this tree passes 142 in 9.4s against 28.1s serial |
| OB-3 | optibot — three more modules could share an install fixture, worth about 6s serial | DECLINED for this release. Parallel execution already subsumes most of it, and the remaining benefit does not justify auditing three modules for mutation under release pressure. Recorded with O-22, which it overlaps |
| OB-4 | optibot — `merge-settings.py` is a shim that `os.execv`s the real merger, costing an extra interpreter per install, ~31ms | DEFERRED — the shim exists for third-party callers; changing `install.sh` to call the real script directly is safe but is a separate change with its own test |
| OB-5 | optibot — `lint-mcp-hardcoded-paths.py` parses the same text twice (1.1ms), and its `rglob` descends 61k files to find 18 | DECLINED on optibot's own reasoning: the parse is trivial, and pruning the walk is a semantic change about whether a vendored `.mcp.json` counts, not a perf edit |
| R-1 | The manifest-driven CLAUDE.md merge produced five defects in one release, two of them blockers, because a prose document was being reconciled through metadata a human keeps in sync by hand | REPLACED — the kit's instructions ship as owned files under `~/.claude/rules/`, which Claude Code discovers rather than merges. Upgrade is a copy. Manifest, tombstones, depth matching, conflict path and abort all removed from the normal path. Spec `docs/superpowers/specs/2026-09-10-claude-md-rules-migration-design.md`, plan `docs/superpowers/plans/2026-09-10-claude-md-rules-migration.md` |
| R-2 | Load order cannot express precedence: the docs say files are concatenated rather than overriding, and contradictions resolve arbitrarily | SOLVED by stating it — every kit rule ends by naming `00-user-overrides.md` as the file that wins. That file is seeded once and never written again; two tests pin both halves |
| R-3 | `parse_sections` split on any line starting with `#`, including comments inside fenced code blocks | FIXED — the parser tracks fences, as Claude Code's own import parser does. Latent for as long as sections were only preserved in place; the first real migration run left 19 lines of orphaned code-block debris |
| R-4 | Shipping rules on a CLI that ignores `~/.claude/rules/` would drop every kit instruction without erroring | GATED on Claude Code 2.0.64 with a `sort -V` compare, falling back to the merge and saying so. Tested at the floor, either side, an older major, a much newer release, and a CLI that reports no version |
| R-5 | Files on disk do not prove Claude Code loads them | PROVEN — an end-to-end test installs a rule carrying a unique canary and asserts a live `claude -p` session returns it. Skips explicitly when the CLI is absent or logged out; asserting a canary that was never installed fails it |

### Iter-3 PR-B findings and disposition (the Berry fork)

Tracked here rather than in the fork, because the fork is a third-party project
and this is where the deployment report's findings live. Fork branch
`prerelease`, verified against the tree a fresh `install.sh` actually pulls.

| ID | Finding | Disposition |
|---|---|---|
| F4 | `.mcp.json` pinned `/opt/homebrew/bin/uvx`, which cannot resolve on Linux | FIXED — `"command": "uvx"`, resolved from PATH. Confirmed in the installed copy after a fresh isolated install, not only in the repo |
| F5 | Six workflow skills shipped as flat `skills/<name>.md` and had never loaded on any install | FIXED — all at `skills/<name>/SKILL.md`, now seven (upstream v2 adds an objective-optimization workflow). The installed copy carries all seven; every MCP tool name the skills reference exists in the live 28-tool registry |
| F5c | `commands/berry-setup.md` had no frontmatter and never loaded | FIXED by deletion — its `claude plugin path` command does not exist. `berry-configure` is the surviving command and keeps credentials in one file |
| F6 | `ModuleNotFoundError: httpx` on a fresh install | FIXED — `httpx` declared as the `backends` extra and the Gemini/Vertex backends made lazy, so a missing extra is an instruction rather than a traceback. Reproduced live on pristine upstream first: the resolver takes mcp 2.2.0, which moved to httpx2 and no longer supplies `httpx` |
| Item 5 | Is `openai/gpt-4o-mini` the intended verifier? | CONFIRMED intended (owner). Documented in `docs/tools/berry.md` with the constraint that decides it: Berry scores from token logprobs, and most obvious upgrades do not expose them |
| — | Upstream v2.0.0 sync | Done by unrelated-histories merge, not force-push, so every box's background pull still fast-forwards. Native packaging upstream deleted was removed; `k8s_wrapper.py` deleted as fork-only dead code |

Verified on the shipping tree: 120 tests pass, `ruff check` and `ruff format
--check` clean, and `mypy --platform linux src` clean (the one macOS-only error
is upstream's own `sys.platform` chain and is not present on the platform
upstream's CI runs). A cold-cache `uvx --from . berry mcp` starts and
`create_server` returns a FastMCP instance exposing 28 tools.

An upstream fix is prepared but **not opened**: `mcp[cli]` unpinned and `httpx`
undeclared break `berry mcp` on a fresh install of `leochlon/hallbayes` today,
reproduced in a clean venv. The branch is local pending a decision, since
opening it is an outward-facing action on a third-party repository.

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
| O-1 | O scrubbing-lint | BLOCKER | plugins/claude-code-kit/skills/fix-notion-mcp-port.md:3 | a customer name in a user-facing string | FIXED | Replaced with a generic description |
| O-2 | O scrubbing-lint | BLOCKER | docs/TRACKER.md:11 | an absolute home-directory path | FIXED | Replaced with a `~`-relative path |
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
