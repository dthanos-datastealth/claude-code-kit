# claude-code-kit

Opinionated bootstrap kit for replicating a complete Claude Code development
setup on a clean macOS or Linux machine.

## What you get

- A scrubbed `~/.claude/CLAUDE.md` enforcing the kit's workflow philosophy
  (TDD-first, evidence-before-assertions, dual-graph + LSP + Read code-search
  order, Berry verification mandatory).
- 19 plugins from 3 marketplaces, installed and enabled automatically:
  - `anthropics/claude-plugins-official` (17 plugins)
  - `leochlon/hallbayes` (Berry verifier)
  - `multica-ai/andrej-karpathy-skills`
- A memory-system index ready for the auto-memory hook.
- A `settings.json` with `effortLevel: max` merged in (your existing `env`
  block is preserved untouched).
- Per-tool rationale documentation under `docs/tools/` — one file per
  plugin, MCP, or skill, explaining what it does and why it's here.

## Quick install

```bash
gh repo clone <owner>/claude-code-kit
cd claude-code-kit
./install.sh
```

Then restart Claude Code.

## Prereqs

You must have these on `$PATH` before running `install.sh`:

- `claude` (Claude Code CLI)
- `git`
- `gh` (authenticated: `gh auth login`)
- `python3` (>= 3.11)
- `uv`

The installer **does not** install these for you. See `docs/prereqs.md`.

## What install.sh does (and does not do)

Does:
1. Preflight-check required tools on PATH.
2. Back up existing `~/.claude/CLAUDE.md` and `~/.claude/settings.json` to
   `~/.claude/backups/<timestamp>/`.
3. Copy `claude/CLAUDE.md` to `~/.claude/CLAUDE.md`.
4. Merge `claude/settings.json` into `~/.claude/settings.json`, preserving
   your existing `env` block byte-for-byte.
5. Install `claude/memory/MEMORY.md` at `~/.claude/memory/MEMORY.md` (only
   if you don't already have one — never overwrites).
6. Register the three plugin marketplaces.
7. Install all 19 plugins.

Does NOT:
- Install `uv`, `gh`, `ripgrep`, `jq`, LSP servers, MCP backend binaries,
  or the Berry verifier LLM backend.
- Touch corporate CA certificate configuration.
- Modify your shell rc files (`.zshrc`, `.bashrc`).
- Write to anything outside `~/.claude/`.

## Reverting

```bash
./uninstall.sh
```

Restores the most recent backup. Idempotent.

## Layout

- `claude/` — files copied or merged into `~/.claude/`.
- `docs/` — philosophy, workflow, per-tool rationale, memory system, optional
  corporate-TLS guide.
- `install.sh` / `uninstall.sh` / `scripts/` — installation logic.
- `tests/` — pytest suite that runs install.sh against an isolated HOME.

See `docs/philosophy.md` for the workflow this kit assumes you want to adopt.
