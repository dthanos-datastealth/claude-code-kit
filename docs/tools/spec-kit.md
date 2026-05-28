# spec-kit — spec-driven development workflow via the `specify` CLI

**What it does:**
GitHub's [`spec-kit`](https://github.com/github/spec-kit) is a CLI
(`specify`) that scaffolds a spec-driven development workflow into any
project. Running `specify init --here --integration claude` installs
nine `/speckit-*` agent skills into `.claude/skills/` and creates a
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
