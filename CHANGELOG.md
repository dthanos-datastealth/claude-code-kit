# Changelog

All notable changes to this kit are documented here.
Format: Keep a Changelog. Versioning: `vYYYY.MM.DD` when `install.sh`
contract changes; untagged for CLAUDE.md/docs edits.

## [Unreleased]
### Added
- Spec-kit (`specify` CLI) coverage: new `## Spec-Kit` section in
  `claude/CLAUDE.md` positions it as an optional spec-driven alternative
  to the default brainstorm → plan → TDD flow; new
  `docs/tools/spec-kit.md` rationale doc (5-section schema); new
  prereqs section 11 in `docs/prereqs.md` documenting `uv tool install
  specify-cli ...` (pinned to `v0.8.15`) and the per-project
  `specify init --here --integration claude` setup.
- Spec-kit agent playbook in `claude/CLAUDE.md`: explicit 9-step
  procedure telling Claude HOW to drive `/speckit-*` skills on the
  user's behalf, grounded in SDD best practices (Constitution before
  first spec; spec = WHAT/WHY, plan = HOW; Clarify when ambiguous;
  Analyze before Implement; update spec first when intent changes).
  Includes hard prohibitions (no Implement without Constitution, no
  bypassing Berry, no inventing spec answers). Berry rules stack on
  top of every spec-kit step.

### Changed
- Berry verifier backend default is now OpenRouter-hosted `openai/gpt-4o-mini`
  instead of self-hosted llama.cpp + Qwen3-Coder-30B-A3B. Configured via
  `~/.berry/config.json` and `~/.berry/mcp_env.json`. The llama.cpp path
  remains supported for offline / air-gapped use. Updated:
  `claude/CLAUDE.md` (Verifier backend section), `docs/tools/berry.md`
  (cost/footprint + setup), `docs/prereqs.md` (section 10 install +
  verification recipe).

### Added
- `jdtls-lsp` plugin (wraps Eclipse JDT.LS) and `docs/tools/jdtls-lsp.md`
  rationale doc. Java is now a first-class LSP target alongside Go and
  TypeScript. Plugin count 19 → 20; official-marketplace count 17 → 18.
  Requires JDK 17+ and the `jdtls` launcher on `$PATH`.

### Removed
- `sourcegraph` plugin and `docs/tools/sourcegraph.md` — not used in this kit's workflow (dual-graph + LSP already cover the in-repo navigation case; Sourcegraph adds a hosted-service dependency we don't need).

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
