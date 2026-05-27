# feature-dev — 7-phase feature workflow with parallel subagents

**What it does:**
Feature-dev installs a single `feature-dev:feature-dev` skill (also reachable
as `/feature-dev`) that runs a structured seven-phase workflow whenever Claude
is asked to add a new feature. Phases 2, 4, and 6 dispatch parallel subagents
(`code-explorer`, `code-architect`, `code-reviewer`) so that exploration,
design alternatives, and quality review all happen against fresh context
windows rather than the main thread.

Phases:
1. Discovery — clarify what the user actually wants.
2. Codebase Exploration — parallel `code-explorer` agents map the relevant
   architecture and existing patterns.
3. Clarifying Questions — every ambiguity is asked before design starts.
4. Architecture Design — parallel `code-architect` agents present competing
   approaches with trade-offs.
5. Implementation — only after explicit user approval.
6. Quality Review — parallel `code-reviewer` agents check simplicity, bugs,
   and convention adherence.
7. Summary — decisions and next steps captured for handoff.

**Why it's in this kit:**
The kit's `CLAUDE.md` mandates that any time the user says "add", "build",
"create", "implement", or "new feature", Claude must route through this
workflow. The Phase-3 clarifying-questions gate is the differentiator —
ordinary brainstorming skills will happily start designing on incomplete
requirements; feature-dev refuses to. The parallel-subagent phases also
preserve the main context window by offloading exploration and design work
to fresh threads whose conclusions come back as compact summaries. Skipping
phases — especially the approval gate before Phase 5 — is the most common way
features arrive misaligned with the user's actual intent.

**When you'd disable it:**
- Pure bug fixes — use `superpowers:systematic-debugging` plus
  `superpowers:test-driven-development` instead.
- Refactors that do not change behavior — use
  `superpowers:brainstorming` to scope, then TDD to execute.
- Tiny additive changes (one function in an existing file, no architectural
  decisions) where the seven-phase ceremony would dominate the actual work.
- Sessions where the user is explicitly prototyping and wants to skip the
  approval gate.

Do not disable it when the change introduces a new module, a new external
integration, a new user-facing surface, or any design decision that other
parts of the codebase will be forced to live with.

**Source:**
GitHub: <https://github.com/anthropics/claude-plugins-official>
Marketplace: `anthropics/claude-plugins-official`
Plugin name: `feature-dev`

Install via the kit's `install.sh`, which registers the marketplace and runs
`claude plugin install feature-dev@anthropics/claude-plugins-official`.

**Cost / footprint:**
- Disk: negligible — the plugin is markdown skill and subagent prompt files.
- Memory / CPU: zero direct runtime cost. The real cost is in the parallel
  subagent calls during Phases 2, 4, and 6 — each is a separate Claude
  invocation with its own context budget.
- Network: none beyond the underlying Claude API calls those subagents make.
- Dependencies: none beyond the Claude Code CLI.

The token cost is intentional: paying for parallel exploration and design
review up front is cheaper than paying for an unwanted feature in code review
later.
