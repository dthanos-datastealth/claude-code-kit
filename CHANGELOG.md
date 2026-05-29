# Changelog

All notable changes to this kit are documented here.
Format: Keep a Changelog. Versioning: `vYYYY.MM.DD` when `install.sh`
contract changes; untagged for CLAUDE.md/docs edits.

## [Unreleased]
### Added
- **Doc-sync pass to propagate tracker discipline + recent fixes across
  every affected doc** (one commit, no behavior change):
  - **`docs/philosophy.md`** — new Principle 7 "Tracker as collaboration
    substrate" (between Principle 6 and "How the principles compose").
    Intro line + composition section updated from "six principles" to
    "seven principles".
  - **`docs/workflow.md`** — tracker dispatch folded into Step 2 (Plan)
    as "Tracker dispatch (Pre-Dispatch Protocol)" subsection and into
    Step 6 (Verify) as "Tracker-coordinated V+O dispatch" subsection.
    Cross-references `docs/tracker-system.md` for the full schema.
  - **`docs/corporate-tls.md`** — new section 0 "What the kit ships by
    default" documenting `UV_NATIVE_TLS=1` (what it fixes, what it
    doesn't, when it's not enough, the merge-layering contract). Closes
    the gap where the canonical TLS doc didn't mention the kit's actual
    mitigation that was already shipping in `claude/settings.json`.
  - **`README.md` Mermaid #2 (agentic dev process)** — added `track`
    node ("docs/TRACKER.md: coordinator opens row per planned Dev / V /
    O Task before dispatch") between `bgate1` and `worktree`, and
    `trackclose` node ("close rows, log V/O verdicts, file findings as
    new rows") between `simplify` and `finish`.
  - **`README.md` Mermaid #3 (quality loop)** — added `track` node
    ("Pre-Dispatch Protocol: coordinator opens TRACKER.md row per
    Dev / V / O Task") between `bgate` and `vo`; updated V and O node
    labels to include "updates own row · files findings as new rows";
    updated `done` terminal to "close TRACKER rows"; added
    `[WIRE-PATH MISS]` to the V verdict edge label.
  - **`README.md` Quality Loop prose** — added 4th bullet "Tracker as
    substrate" explaining Pre-Dispatch Protocol, agent-updates-own-row,
    findings-as-new-rows, coordinator-does-not-write-to-agents-rows;
    augmented existing V+O bullet with `[WIRE-PATH MISS]` BLOCKING
    finding and dual-graph + LSP redundancy check.
- **README — "If npx-based MCPs show ✘ failed on first launch, restart
  once" subsection** in §"Required setup after `install.sh`". Documents
  the cold-start race where prewarmed npm cache is healthy but Claude
  Code's sticky-failed MCP state from the first session needs a single
  session restart to recover. Surfaced when an isolated-HOME smoke test
  showed `claude mcp list` returning all npx-MCPs connected while the
  interactive session's MCP panel showed them failed — proving cache
  was warm and only the session state needed reload.
- **README — "Launching `claude` interactively in the isolated HOME"
  subsection** in §"Testing the kit in parallel". Documents the
  Keychain-vs-HOME scope mismatch that causes `/login` from a fresh
  `$HOME` to trigger a Keychain authorization prompt and a post-OAuth
  handshake failure that can leave both the test and real sessions
  broken. Ships the verified-working `claude setup-token` +
  `CLAUDE_CODE_OAUTH_TOKEN` env-var recipe with `read -s` for
  leak-safe paste, an `auth status` verification step, and a
  `claude auth logout` rotation recipe for the case where the
  long-lived token leaks. Empirically tested end-to-end in an
  isolated HOME against `claude auth status` and `claude mcp list`.

### Changed
- **README "Launching `claude` interactively" recipe rewritten.**
  Replaces the `cp ~/.claude.json` recipe with `claude setup-token` +
  `CLAUDE_CODE_OAUTH_TOKEN` env var; the copy populates display
  metadata but does not authenticate API calls (Keychain is
  source-of-truth, HOME-dependent). Also retracts the
  `security delete-generic-password "Claude Code-credentials"` cleanup
  step — those unsuffixed entries are MCP OAuth state caches, not
  Anthropic credentials.

### Fixed
- **README staleness in two places** caught during the post-iteration
  test pass: intro paragraph said "21 curated plugins from 4
  marketplaces" but the actual count is 5 (added `optimal-ai`
  marketplace earlier when `optibot` was repointed to its real
  upstream); Mermaid architecture label said "34 pytest cases" but
  the actual count is 36 (added 2 new cases for the kit-default env
  merge layering when `UV_NATIVE_TLS=1` landed).

### Added
- **TRACKER.md + Task tool discipline at the kit level.** Captures the
  user's real workflow: per-project `docs/TRACKER.md` (Last Updated +
  per-iteration aspect tables + Quality Loop State + V/O Findings
  Tracker + Open issues) coupled with the `Task` tool that agents update
  themselves. Every adopter inherits the same schema and dispatch
  protocols.
  - **`docs/tracker-system.md`** (NEW) — full schema, dispatch protocols,
    V/O agent protocols (Steps 0 + A–G), hard rules, plan-vs-tracker
    distinction. Shipped to `~/.claude/docs/` via `install.sh copy_docs`.
  - **`claude/CLAUDE.md` MANDATORY section** between Quality Loop and
    Installed Plugins: Phase Start Protocol (EnterPlanMode → approval
    → execute), Pre-Dispatch Protocol (coordinator creates Dev + V + O
    tasks upfront), agent procedures, coordinator prohibitions, full
    Verification Steps 0 + A–G (Step 0 = PRD Requirement Mapping;
    Step G = `[WIRE-PATH MISS]` hot-path check, BLOCKING), Optimization
    Protocol (dual-graph + LSP redundancy check), tracker hard rules.
  - **`install.sh TOP_LEVEL_DOCS`** + **`tests/test_install_docs.py`**
    + **README** ("Tracker discipline" row + layout listing + Mermaid).

### Changed
- **Settings merge contract: kit env defaults now layer UNDER user env
  overrides** (user always wins on conflict). Previously the user's env
  block was preserved byte-for-byte and any kit-side env was ignored;
  now the kit can ship broadly-needed defaults that fill in only the
  keys the user hasn't set themselves.
- **Kit ships `UV_NATIVE_TLS=1` as its first env default.** Required
  for uvx-based MCP servers (Berry) to start successfully behind
  corporate TLS-intercepting proxies (Cloudflare, Zscaler, Netskope, Palo Alto,
  Cisco). Without it, `uvx` uses its bundled rustls cert store which
  doesn't include corporate CA certs; with it, `uvx` uses the OS
  native TLS stack (macOS Keychain / Linux system CA bundle) which
  typically does. Surfaced when an isolated-HOME smoke test against
  the real `claude` CLI showed Berry's `uvx` failing with
  `Failed to fetch https://pypi.org/simple/openai/: invalid peer
  certificate: UnknownIssuer`. New README section "Corporate TLS
  handling" documents the kit's stance: ships UV_NATIVE_TLS=1,
  documents SSL_CERT_FILE/etc. for users who need an explicit cert
  path, never bakes absolute cert paths into plugin .mcp.json files.
  Three new pytest cases in `test_install_merge_settings.py` cover
  the new merge layering (user wins on conflict; kit default fills in
  missing keys; fresh-install env contains UV_NATIVE_TLS=1).

### Added
- **`scripts/lint-mcp-hardcoded-paths.py`** — scans every installed
  plugin's `.mcp.json` for owner-specific absolute paths (`/Users/<x>`,
  `/home/<x>`, `/var/folders/<x>`, `C:\Users\<x>`). Catches the failure
  mode where a plugin ships an MCP config that only works on the
  plugin author's machine — exactly what bit the kit when Berry's
  cached `.mcp.json` had `/Users/<owner>/.claude/certs/corporate-ca-bundle.pem`
  baked in. Wired into `scripts/test-install-isolated.sh` (which has
  a populated cache to scan against) as a fail-loudly step. Has an
  ALLOWED_SUBSTRINGS list for legitimate template placeholders
  (`${HOME}`, `${CLAUDE_PLUGIN_ROOT}`, doc examples like `/Users/example`,
  `/home/alice`).
- **`install.sh prewarm_npx_mcps` step** — runs `npx -y <pkg> --version`
  in parallel for the three npx-based MCP packages shipped via the
  kit's plugins (`@playwright/mcp@latest`, `chrome-devtools-mcp@latest`,
  `@upstash/context7-mcp`). Populates the npm cache during install so
  those MCPs don't show `✘ failed` on first Claude Code launch while
  npm downloads in the background. Soft-fail: if `npx` isn't on PATH
  the step prints a warning and skips; install.sh still succeeds.
  Two new pytest cases (`test_install_prewarm.py`) cover the
  step's ordering and the no-npx graceful-skip path.
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
- **`optibot` now installs from `Optimal-AI/optibot-skill` (marketplace
  name `optimal-ai`)** instead of `claude-plugins-official`. Optibot
  was removed from the upstream `anthropics/claude-plugins-official`
  marketplace.json at some point and is now maintained at its own
  marketplace; the kit's settings still referenced the old location.
  Fresh installs failed at `claude plugin install optibot@claude-plugins-official`
  with "Plugin not found in marketplace". Updated:
  `claude/settings.json` (added `optimal-ai` marketplace, changed
  enabledPlugins entry), `install.sh` MARKETPLACES array (4→5),
  `tests/test_install_marketplaces.py` (renamed test, 4→5 asserted),
  `tests/test_install_plugins.py` (EXPECTED_PLUGINS), `docs/tools/optibot.md`,
  `README.md` plugin table + Mermaid + layout (4→5 marketplaces).
- **New `scripts/lint-plugin-marketplaces.py` guard** wired into CI.
  Fetches each declared marketplace's authoritative `.claude-plugin/
  marketplace.json` via `gh api` and asserts every enabled plugin
  appears in its declared marketplace's plugin list. Would have caught
  optibot's drift the moment it happened — the pytest harness can't
  catch this class of bug because the fake `claude` CLI returns 0 for
  any plugin install regardless of whether the marketplace actually
  publishes that plugin. CI step `Verify every plugin resolves against
  its upstream marketplace` runs this on every push/PR.
- **Berry marketplace points back to `dthanos-datastealth/hallbayes`**
  (the Claude-Code-packaged fork) instead of `leochlon/hallbayes`
  (the raw Python upstream). The upstream repo doesn't ship a
  `.claude-plugin/marketplace.json` or any of the Claude Code
  scaffolding (`commands/`, `skills/`, `.mcp.json`); only the fork
  carries that. Surfaced when an isolated-HOME smoke test against
  the real `claude` CLI failed at marketplace registration with
  "Marketplace file not found at .../leochlon-hallbayes/.claude-plugin/
  marketplace.json". The kit's CI pytest harness uses a mock
  `claude` CLI that always returns 0 for `plugin marketplace add`,
  so this failure mode couldn't surface there. Fork is also publicly
  accessible, so kit distribution is unchanged. Updated:
  `claude/settings.json`, `install.sh` MARKETPLACES array,
  `tests/test_install_marketplaces.py`,
  `tests/test_install_merge_settings.py`, `docs/tools/berry.md`
  (now documents the fork-vs-upstream split explicitly),
  `README.md` plugin table.
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
