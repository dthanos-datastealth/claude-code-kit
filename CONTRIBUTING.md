# Contributing

PRs welcome. Open one against `main` — CI runs shellcheck, the scrubbing
lint, the tools-docs schema lint, and the pytest suite on ubuntu-latest.

## Drift-back-to-source workflow

When your personal `~/.claude/` drifts from this repo (you add a plugin,
change a rule), use `scripts/diff-against-live.sh` to see the delta, then:

1. Decide if the drift should propagate back to the kit (most rules) or
   stay personal (project-specific tweaks).
2. If propagating, edit the matching files under `claude/` or `docs/`.
3. Add a `CHANGELOG.md` entry under `[Unreleased]`.
4. Open a PR.

See `docs/workflow.md` for the development conventions this kit enforces.
