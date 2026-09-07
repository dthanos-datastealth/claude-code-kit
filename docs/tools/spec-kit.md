# spec-kit — spec-driven development workflow via the `specify` CLI

**What it does:**
GitHub's [`spec-kit`](https://github.com/github/spec-kit) is a CLI
(`specify`) that scaffolds a spec-driven development workflow into any
project. Running `specify init --here --integration claude` installs
one agent skill per `/speckit-*` command into `.claude/skills/` — ten
core commands upstream — and creates a
`.specify/` directory with templates, scripts, and a Constitution
slot. The skills drive a Constitution → Specify → (Clarify) → Plan →
Tasks → (Analyze) → Implement loop, with `.specify/` as the on-disk
working area for every artifact the loop produces.

**Why it's in this kit:**
The kit's default flow (`/superpowers:brainstorming` →
`/superpowers:writing-plans` → TDD) is fast and conversational — good
for single-developer work where the plan lives in chat and the artifact
that matters is the diff. Spec-kit is the alternative for situations
where you need durable, reviewable artifacts: greenfield projects, work
that crosses team boundaries, or features where stakeholders read the
`spec.md` before implementation lands. Both flows enforce the same
verification layer (Berry stays mandatory either way), so adopting
spec-kit doesn't weaken the kit's evidence-first stance — it just
replaces the spec/plan ceremony with a more formal one.

**When you'd disable it:**
- You don't need it for bugfixes, refactors, small dependency bumps,
  or single-session changes — the ceremony cost doesn't pay back.
- A feature already mid-flight in a `/feature-dev` run should not be
  retrofitted with spec-kit; finish the current flow first.
- Solo prototyping where the spec is in your head and will stay there.
- Projects that already have a different spec system (RFCs, ADRs, etc.)
  and you don't want two parallel spec layers.

**Source:**
Upstream: <https://github.com/github/spec-kit>.
CLI install: `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z`
(replace `vX.Y.Z` with the latest tag from the releases page; the
kit's `docs/prereqs.md` pins the version this kit was tested with).
Spec-kit is NOT a Claude Code plugin and is NOT installed by this
kit's `install.sh` — it is a separate CLI you install once globally,
then init per project.

**Cost / footprint:**
- Disk: the `specify` CLI itself is ~1 MB (Python). Each project
  initialized with `specify init` adds a `.specify/` directory
  (templates + scripts, ~200 KB) and one SKILL.md per `/speckit-*`
  command under `.claude/skills/speckit-*/` (~30 KB total).
- Memory / CPU: zero at rest — the skills are markdown files the
  Claude Code agent reads on invocation. No background process.
- Network: the `uv tool install` step clones the spec-kit repo from
  GitHub (one-time). Subsequent `specify init` runs are offline
  (templates are bundled in the CLI package).
- Dependencies: `uv` (already a kit prerequisite — see
  `docs/prereqs.md` section 5). Python 3.11+ (also already a
  prerequisite).
- Per-project setup: one `specify init --here --integration claude`
  command, then a Claude Code restart in that project directory for
  the slash commands to register.

---

## How Claude drives spec-kit on the user's behalf (SDD playbook)

When the user asks for something that fits a spec-driven flow (new feature, greenfield project, multi-step work that will outlive this session), follow this playbook **before** writing any code:

In each step below, behavior labelled **[upstream]** matches the official spec-kit workflow as documented in <https://github.com/github/spec-kit>; behavior labelled **[kit policy]** is stricter than upstream and reflects this kit's discipline. Both layers apply when working in a project that has adopted this kit.

**1. Detect the project's spec-kit state.** Check if `.specify/` exists at the project root.
- **Exists** → existing spec-kit project; check `.specify/memory/constitution.md` to see if the Constitution is filled in. If not, the user is mid-setup; offer to run `/speckit-constitution`.
- **Does not exist** → ask the user before running `specify init --here --integration claude`. Initialization writes files into their project, so it needs explicit consent — but once consented, do it via the shell yourself; do not ask the user to run the command. After init, the `/speckit-*` slash commands may not register until the agent re-discovers skills (in most agents this requires a session restart). **Stop and ask the user to restart** rather than guessing — invoking a skill that hasn't loaded yet wastes a turn.

**2. Constitution before first spec [kit policy — stricter than upstream].** If `.specify/memory/constitution.md` is empty or placeholder-only, this kit requires you to run `/speckit-constitution` first (or ask the user to) before any `/speckit-specify`. Upstream's `speckit-implement` skill only requires the Constitution to exist *if present*, but skipping it leaves `/speckit-analyze` with no consistency baseline to check against — which is exactly the gate the kit relies on.

**3. Spec describes WHAT and WHY, not HOW [upstream].** In `/speckit-specify`, focus on user goals, acceptance criteria, and constraints. Do not name a tech stack, framework, or library — those belong in `/speckit-plan`. Upstream is explicit: *"Be as explicit as possible about what you are trying to build and why. Do not focus on the tech stack at this point."* If the user describes the request in tech-stack terms ("build a React app with..."), separate the WHAT from the HOW: capture WHAT in spec, defer HOW to plan.

**4. Clarify when ambiguous [upstream — strongly recommended].** After `/speckit-specify`, scan the produced `spec.md` for open questions, vague requirements, or unstated assumptions. If you find any, run `/speckit-clarify` before proceeding. **Do not invent answers** — clarify gets the user to commit to a single interpretation. The cost of one clarification round is far smaller than the cost of implementing the wrong interpretation.

**5. Plan establishes the HOW [upstream].** Run `/speckit-plan` with the chosen tech stack and architectural decisions. Cite the relevant `docs/tools/*.md` entries for any plugin/MCP/LSP the plan depends on.

**6. Tasks decompose the plan [upstream].** Run `/speckit-tasks` to generate an actionable task list. Upstream organizes tasks by phase and user story, with the rule that each task should be independently testable; upstream does NOT impose a minute bound. The kit's separate `superpowers:writing-plans` discipline does enforce 2–5 minute task granularity, so when you are working in *spec-kit mode* and the upstream output produces coarser tasks, decompose them further before handing off to `/speckit-implement` — the TDD step downstream is easier when tasks are bite-sized.

**7. Analyze before implementing [kit policy — stricter than upstream].** Run `/speckit-analyze` after `/speckit-tasks`. Upstream documents Analyze as *optional*; this kit treats it as mandatory because cross-artifact drift (Constitution ↔ spec ↔ plan ↔ tasks) is the most common spec-driven failure mode, and analyze catches it for the cost of one query.

**8. Implement under Berry [kit overlay].** Run `/speckit-implement` to execute the task list. Spec-kit itself has no verification overlay; this kit adds one: every step routes through `berry-plan-and-execute` per the Berry hard rules — no shortcuts. Test output is always captured as a Berry span (`berry-search-and-learn`) before any "tests pass" claim.

**9. Update spec when intent changes [kit policy — derived from SDD principles].** If the user changes their mind mid-implementation, **update the spec first** (re-run `/speckit-specify` or edit `spec.md` directly), then re-run `/speckit-analyze` to surface what else needs to change. Upstream does not document this explicitly, but the principle is fundamental to spec-driven development — once implementation is allowed to drift from spec, the spec stops being a source of truth and becomes a lie that grows over time.

**Hard prohibitions for spec-driven mode (this kit):**
- Do not start implementation before the spec is approved by the user.
- Do not skip `/speckit-analyze` because "the plan looks fine to me."
- Do not run `/speckit-implement` if the Constitution is empty (kit-policy gate).
- Do not invent answers to spec ambiguities — always `/speckit-clarify`.
- Do not bypass Berry gates by switching to spec-driven mode; both layers stack.

**Relationship to `/feature-dev`:** the global guidance "use `/feature-dev` for any new feature" assumes you have NOT opted into spec-kit for the project. When `.specify/` exists, **use spec-kit for new features instead of `/feature-dev`** — they cover the same ground (spec → plan → implement) but spec-kit produces durable on-disk artifacts (`spec.md`, `plan.md`, `tasks.md`) that survive across sessions, while `/feature-dev`'s subagent outputs are session-scoped. Do not run both for the same feature.

If spec-kit isn't initialized and the user's request is small (bugfix, refactor, single-session task), use the default brainstorm → plan → TDD flow instead. Spec-kit overhead does not pay back at small scope.

---

### Setup, once per project

```sh
specify init --here --integration claude   # writes .claude/skills/speckit-* + .specify/
```

The commands appear after a Claude Code restart. Upstream documents ten core
commands: `constitution` (run first, once), `specify`, `clarify`, `plan`,
`tasks`, `taskstoissues`, `analyze`, `checklist`, `implement` and `converge`.
The playbook above uses the seven that carry the kit's gates; `checklist`,
`taskstoissues` and `converge` are optional and unchanged by kit policy.

**Check the separator before you type one.** Upstream's README shows the core
commands both as `/speckit.constitution` and as `/speckit-constitution`, and
the bundled bug and assess extensions use the hyphen form
(`/speckit-bug-fix`, `/speckit-assess-intake`). The form your project actually
has is whatever `specify init` wrote into `.claude/skills/` — list that
directory rather than guessing, because a wrong separator is a silent no-op.
