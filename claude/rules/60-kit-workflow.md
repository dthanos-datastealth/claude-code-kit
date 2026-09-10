# Workflow, output style, memory

## Workflow Order (For Any Non-Trivial Task)

**For new features → use `/feature-dev` (handles phases 1–7 automatically)**

**For bugs, refactors, or tasks without `/feature-dev`:**
1. **Brainstorm** — `/superpowers:brainstorming` to explore intent and design
2. **Plan** — `/superpowers:writing-plans` to break into 2-5 min tasks → **use `berry-plan-and-execute` skill to verify the plan before executing**
3. **Isolate** — `/superpowers:using-git-worktrees` for a clean branch
4. **TDD** — `/superpowers:test-driven-development` (write failing test first)
5. **Build** — Implement, using Context7 for current library docs
6. **Verify** — `/superpowers:verification-before-completion` + **`berry-search-and-learn` with actual test output as spans** — verification must pass before claiming done
7. **Review** — `/superpowers:requesting-code-review`
8. **Simplify** — `/simplify` to clean up changed code
9. **Finish** — `/superpowers:finishing-a-development-branch`
10. **Document** — `/revise-claude-md` to capture learnings

---

## Explanatory Output Style
The `explanatory-output-style` plugin installs a SessionStart hook that adds
`★ Insight` blocks after code. Depth-reference:
`~/.claude/docs/tools/explanatory-output-style.md`. These explain:
- Why specific implementation choices were made
- Patterns and trade-offs relevant to this codebase
- Non-obvious decisions

This is educational context — do not suppress it.

---

## Memory System
Persistent memory lives at `~/.claude/projects/<your-project-encoded>/memory/`. Save memories for:
- User preferences and role context
- Feedback / corrections (most important — prevents repeating mistakes)
- Project goals and constraints
- External system references (Notion DBs, internal wikis, dashboards)

**Do NOT save** to memory: code patterns, git history, debugging solutions, or anything derivable from the codebase.

> Note: Claude Code encodes your project directory path as a dash-separated string under `~/.claude/projects/`. For a project at `/home/alice/repos`, the encoded form is `-home-alice-repos`. The auto-memory hook resolves this for you.

---

Anything in `~/.claude/rules/00-user-overrides.md` overrides this file. If the two disagree, follow the override and say which rule you are setting aside.
