# Changelog

All notable changes to this kit are documented here.
Format: Keep a Changelog. Versioning: `vYYYY.MM.DD` when `install.sh`
contract changes; untagged for CLAUDE.md/docs edits.

## [Unreleased]
### Added
- **`scripts/test-install-isolated.sh`** — parallel-test the kit
  against the real `claude` CLI without clobbering your real
  `~/.claude/`. Pattern: capture mtimes of `~/.claude/CLAUDE.md` and
  `~/.claude/settings.json` BEFORE, run `HOME=<tempdir> ./install.sh`,
  assert isolated artifacts landed correctly (CLAUDE.md, settings.json,
  MEMORY.md, docs/tools/, plugin count), then re-capture real mtimes
  and **fail loudly if either changed** — so the script actively proves
  no leak, not just hopes. Useful any time you change `install.sh`,
  the plugin set, or docs-shipping logic and want to confirm the kit
  installs cleanly without touching your working setup. Documented
  with a new "Testing the kit in parallel" section in the README;
  also listed in the layout tree under `scripts/`.
- **`install.sh copy_docs` step** ships kit reference docs to
  `~/.claude/docs/` (top-level: `philosophy.md`, `workflow.md`,
  `prereqs.md`, `corporate-tls.md`, `memory-system.md`; plus
  `tools/<name>.md` for all 23 plugins/MCPs/skills). Previously
  these only existed in the cloned kit repo, with no stable path
  Claude Code sessions could reference. New `claude/CLAUDE.md`
  paragraph in "Installed Plugins" tells Claude exactly when to
  consult `~/.claude/docs/tools/<name>.md` (cost recall, "should I
  disable X" questions, unexpected behavior, source URL lookup).
  Three new pytest cases (`test_install_docs.py`) verify the copy
  works and stays in sync with the kit repo's `docs/tools/` count.
  install.sh `main()` step order is now:
  preflight → backup → copy_templates → **copy_docs** →
  merge_settings → install_memory_index → register_marketplaces →
  install_plugins.
- **MANDATORY Quality Loop section** at the top of `claude/CLAUDE.md`
  (between Code Search Order and Installed Plugins). Codifies the
  TDD → Berry → V+O discipline the kit actually runs:
  - TDD with mandatory lifecycle tests (not just function-centric);
    RED must fail for the right reason.
  - Berry verification on every completion claim, with test output
    as the canonical evidence form.
  - V+O loop: dispatch a Verification agent (verifies against
    authoritative external sources) and an Optimization agent
    (finds simplification / consistency wins) in parallel against
    each substantive change.
  - Hard prohibitions: no "tests pass" without a Berry span,
    no skipping V+O on small changes, no inventing answers when
    V flags a concern, 3-strike rule.
  Previously the V+O pattern lived only as an auto-memory feedback
  entry; promoting it to CLAUDE.md makes it a load-bearing rule
  every session reads at start.
- `jdtls-lsp` plugin (wraps Eclipse JDT.LS) and `docs/tools/jdtls-lsp.md`
  rationale doc. Java is now a first-class LSP target alongside Go and
  TypeScript. Plugin count 19 → 20; official-marketplace count 17 → 18.
  Requires JDK 21+ (upstream Eclipse JDT.LS minimum) and the `jdtls`
  launcher on `$PATH`. New dedicated prereqs section 9 in `docs/prereqs.md`.
- Spec-kit (`specify` CLI) coverage: new `## Spec-Kit` section in
  `claude/CLAUDE.md` positions it as an optional spec-driven alternative
  to the default brainstorm → plan → TDD flow; new
  `docs/tools/spec-kit.md` rationale doc (5-section schema); new
  prereqs section 12 in `docs/prereqs.md` documenting `uv tool install
  specify-cli ...` (pinned to `v0.8.16`) and the per-project
  `specify init --here --integration claude` setup.
- Spec-kit agent playbook in `claude/CLAUDE.md`: explicit 9-step
  procedure telling Claude HOW to drive `/speckit-*` skills on the
  user's behalf, grounded in SDD best practices, with `[upstream]`
  vs `[kit policy]` labels distinguishing official spec-kit behavior
  from this kit's stricter overlays. Includes a `/feature-dev` vs
  spec-kit disambiguation rule and hard prohibitions (no Implement
  without Constitution, no bypassing Berry, no inventing spec answers).
  Berry rules stack on top of every spec-kit step.
- `caveman` skill coverage (token-savings terse-output mode): new
  `## Caveman` section in `claude/CLAUDE.md`, new `docs/tools/caveman.md`
  rationale doc, new prereqs section 13 with the manual install path
  (`gh repo clone JuliusBrussee/caveman ~/.claude/skills/caveman`).
  Skill is opt-in per session.

### Changed
- **Caveman now installs automatically** via the kit's `install.sh`
  instead of requiring a manual `gh repo clone` step. Verification
  agent caught that the previously-documented install path was not
  the upstream-recommended one: caveman IS a Claude Code plugin
  (`caveman@caveman`, marketplace `JuliusBrussee/caveman`), and
  upstream's INSTALL.md specifies `claude plugin marketplace add
  JuliusBrussee/caveman && claude plugin install caveman@caveman`
  as the canonical install for Claude Code. Kit now:
  - Adds `caveman` marketplace + `caveman@caveman` enabled plugin
    to `claude/settings.json` (plugin count 20 → 21; marketplace
    count 3 → 4).
  - Adds `JuliusBrussee/caveman` to `install.sh`'s `MARKETPLACES`
    array so it registers automatically.
  - Renames `tests/test_install_marketplaces.py::test_registers_three_marketplaces`
    → `test_registers_four_marketplaces` with the new assertion.
  - Updates `tests/test_install_plugins.py` EXPECTED_PLUGINS to
    include `caveman@caveman` and `tests/test_install_merge_settings.py`
    to assert `len(plugins) == 21`.
  - Drops the manual "Step 5: install caveman" row from the
    README's Required-setup post-install table (now auto).
  - Rewrites the Caveman section in `claude/CLAUDE.md`,
    `docs/tools/caveman.md`, and `docs/prereqs.md` section 13 to
    reflect the plugin-marketplace install path. Also bumps the
    upstream-claimed token savings 65% → 75% (per current upstream
    README). Mentions the four upstream modes (`lite`/`full`/`ultra`/
    `wenyan`) and points at the upstream one-liner for users who
    want extras (caveman-shrink MCP middleware, statusline badge).
- Berry verifier backend default is now OpenRouter-hosted `openai/gpt-4o-mini`
  instead of self-hosted llama.cpp + Qwen3-Coder-30B-A3B. Configured via
  `~/.berry/config.json` and `~/.berry/mcp_env.json`. The llama.cpp path
  remains supported for offline / air-gapped use. Updated:
  `claude/CLAUDE.md` (Verifier backend section; clarifies that env vars
  in `mcp_env.json` are the load-bearing config, with `~/.berry/config.json`
  shown for what `berry-configure` writes), `docs/tools/berry.md`
  (cost/footprint + setup + OpenRouter rate-limit/free-tier caveat),
  `docs/prereqs.md` (section 11 install + verification recipe).

### Removed
- `sourcegraph` plugin and `docs/tools/sourcegraph.md` — not used in this
  kit's workflow (dual-graph + LSP already cover the in-repo navigation
  case; Sourcegraph adds a hosted-service dependency we don't need).

### Fixed
- **Stale "22 per-tool docs" / "20 plugins" / "3 marketplaces" counts**
  across the README (11 occurrences), Mermaid architecture diagram,
  and the layout section. New counts: **23 per-tool docs, 21 plugins,
  4 marketplaces** (caveman added; this is the source of the bump).
- **Typo `code-quality-reviewer` → `code-reviewer`** in `claude/CLAUDE.md`
  (Quality Loop section's reference to the kit's review-subagent
  stack). The correct plugin is `feature-dev:code-reviewer`.
- **jdtls install command tightened**: `brew install openjdk@21 jdtls`
  was redundant because Homebrew's `jdtls` formula pulls a current
  JDK as a dependency. Now recommends `brew install jdtls` by
  default, with the `openjdk@21` pin as the optional fallback for
  users who need a specific JDK on `$PATH` for other reasons.
  Updated in `claude/CLAUDE.md` LSP section and README step 4c.
- **3-strike rule consolidated to canonical statement in the Berry
  section**; the Quality Loop section now references it instead of
  re-stating, eliminating the in-file duplication the optimization
  agent flagged.
- **Reframed README "What to do after install.sh" → "Required setup
  after install.sh".** Previous wording marked Berry config, dual-graph
  MCP, LSP binaries, caveman, and spec-kit init as `(Optional)`,
  which contradicted the CLAUDE.md mandates (Berry hard gate;
  dual-graph FIRST in code-search order; LSPs SECOND; bash grep
  forbidden). New section structures them as: one-time required
  steps in order (restart → Berry config → dual-graph → LSPs →
  caveman), then per-project (spec-kit init when adopting spec-driven),
  then per-session (caveman invocation). Also adds a verification
  block (`claude plugin list`, `which gopls ...`, etc.) so the user
  can confirm the wiring is complete. The reason install.sh doesn't
  do these itself stays the same (supply-chain risk; foundational
  tools have their own update cadence), but the framing no longer
  understates that they're load-bearing.
- README workflow Mermaid diagram now uses GitHub-safe syntax
  (rectangles instead of parallelograms, no `<br/>` inside edge labels)
  so GitHub's Mermaid renderer can parse it.
- `jdtls-lsp` JDK floor corrected from "17+" to "21+" in
  `docs/tools/jdtls-lsp.md` and `README.md` — upstream Eclipse JDT.LS
  requires Java 21 minimum. Empirical cost/footprint numbers in the
  rationale doc are now labelled as observed-in-this-kit's-usage
  rather than asserted as upstream-published benchmarks.
- Spec-kit playbook: removed factual misattribution of "2–5 minute task
  granularity" to spec-kit (it's actually from `superpowers:writing-plans`).
  Relabelled stricter-than-upstream rules (Constitution gate, Analyze
  mandatory, update-spec-first-on-intent-change) as `[kit policy]` to be
  honest about which steps go beyond official spec-kit guidance.
- Spec-kit pin bumped `v0.8.15` → `v0.8.16` (released same day; minor
  staleness fix).

### Security
- Purged `docs/superpowers/` (internal design spec + implementation plan)
  from git history via `git filter-branch` and force-pushed `main`. Those
  files were accidentally committed in `81972a2` and contained owner
  paths plus the scrubbing-rules table that enumerates company names.
  Now also `.gitignore`d so future commits cannot accidentally include
  them.

## [v2026.05.27] — 2026-05-27
### Added
- Initial repo skeleton.
- Source snapshot taken: ~/.claude/CLAUDE.md (~lines: 210), ~/.claude/settings.json (20 plugins).
- Phase A complete: install.sh + scrubbed CLAUDE.md + settings.json + MEMORY.md template + full pytest harness.
- Phase B complete: 21 per-tool docs (schema-linted), philosophy, workflow, prereqs, corporate-TLS, memory-system guides.
- CI workflow added (.github/workflows/ci.yml: shellcheck + lints + pytest on ubuntu-latest).
- Manual smoke test (running install.sh end-to-end against the real `claude` CLI on a fresh HOME) is DEFERRED — to be performed by the human owner. See README.md "Quick install" for the procedure.
