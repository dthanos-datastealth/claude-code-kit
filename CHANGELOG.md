# Changelog

All notable changes to this kit are documented here.
Format: Keep a Changelog. Versioning: `vYYYY.MM.DD` when `install.sh`
contract changes; untagged for CLAUDE.md/docs edits.

## [Unreleased]
### Removed
- `sourcegraph` plugin and `docs/tools/sourcegraph.md` — not used in this kit's workflow (dual-graph + LSP already cover the in-repo navigation case; Sourcegraph adds a hosted-service dependency we don't need). Plugin count drops 20 → 19; official-marketplace count 18 → 17.

## [v2026.05.27] — 2026-05-27
### Added
- Initial repo skeleton.
- Source snapshot taken: ~/.claude/CLAUDE.md (~lines: 210), ~/.claude/settings.json (20 plugins).
- Phase A complete: install.sh + scrubbed CLAUDE.md + settings.json + MEMORY.md template + full pytest harness.
- Phase B complete: 21 per-tool docs (schema-linted), philosophy, workflow, prereqs, corporate-TLS, memory-system guides.
- CI workflow added (.github/workflows/ci.yml: shellcheck + lints + pytest on ubuntu-latest).
- Manual smoke test (running install.sh end-to-end against the real `claude` CLI on a fresh HOME) is DEFERRED — to be performed by the human owner. See README.md "Quick install" for the procedure.
