# superpowers — workflow-discipline plugin for serious development

**What it does:**
Superpowers is a plugin that installs a suite of workflow skills which force Claude
through the disciplined cycle of brainstorming, planning, test-driven development,
systematic debugging, verification before completion, and code review. Each skill
is a structured prompt template the model invokes via the `Skill` tool, gating
itself before it touches code.

**Why it's in this kit:**
This kit's `CLAUDE.md` mandates that every non-trivial task pass through
brainstorm → plan → TDD → verify. Superpowers is the concrete machinery that
encodes those phases; without it, the workflow rules in `CLAUDE.md` have nothing
to enforce them. It is the spine that other plugins (Berry, feature-dev,
dual-graph) plug into — they assume the brainstorm/plan/TDD/verify cadence
exists. Skipping it produces the failure mode this kit was built to prevent:
speculative changes shipped without evidence.

Key skills installed:
- `superpowers:brainstorming` — explore intent and design before any creative work.
- `superpowers:writing-plans` — break work into 2–5 minute tasks before coding.
- `superpowers:test-driven-development` — RED → GREEN → REFACTOR enforcement.
- `superpowers:systematic-debugging` — required before proposing any bug fix.
- `superpowers:verification-before-completion` — gather evidence before claiming done.
- `superpowers:requesting-code-review` and `superpowers:receiving-code-review`.
- `superpowers:using-git-worktrees` — isolate feature work in its own tree.
- `superpowers:executing-plans` and `superpowers:subagent-driven-development`.
- `superpowers:finishing-a-development-branch` — merge/PR/cleanup decisions.

**When you'd disable it:**
- Throwaway one-line edits where the ceremony of a plan + TDD cycle costs more
  than the change itself (typo fixes, comment tweaks, single-line config changes).
- Pure exploration sessions where you are reading, not writing.
- Environments where the user is driving every step manually and does not want
  Claude to suggest workflow gates.

Never disable for production code changes, multi-file refactors, new features,
bug fixes that touch business logic, or anything that will be merged to a shared
branch. The whole point of the kit is to make those changes verifiable.

**Source:**
GitHub: <https://github.com/anthropics/claude-plugins-official>
Marketplace: `anthropics/claude-plugins-official`
Plugin name: `superpowers`

Install via the kit's `install.sh`, which registers the marketplace and runs
`claude plugin install superpowers@anthropics/claude-plugins-official`.

**Cost / footprint:**
- Disk: negligible — the plugin is a directory of markdown skill prompts.
- Memory / CPU: zero runtime cost. Skills are loaded on demand by the
  `Skill` tool and add only their prompt text to the active context window.
- Network: none after install.
- Dependencies: none beyond the Claude Code CLI itself.

The only real cost is context tokens consumed when a skill is invoked, which is
intentional — those tokens buy you the workflow discipline that keeps later
work cheaper and safer.
