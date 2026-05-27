# andrej-karpathy-skills — behavioral heuristics for common LLM coding failures

**What it does:**
The `andrej-karpathy-skills` plugin installs a set of behavioral
guidelines distilled from Andrej Karpathy's observations about how
LLMs typically fail at coding tasks. The headline skill,
`andrej-karpathy-skills:karpathy-guidelines`, is loaded automatically
when writing, reviewing, or refactoring code, and steers the model
away from the failure modes that bite LLMs most often:

- **Overcomplication** — proposing speculative abstractions, premature
  generality, or new infrastructure when a smaller, surgical change
  would do.
- **Unsurfaced assumptions** — silently assuming a function exists, a
  field is non-null, a service returns the expected shape, or a
  library behaves a certain way, instead of stating the assumption
  and verifying it.
- **Sprawling diffs** — touching files and functions beyond the actual
  scope of the change, dragging in formatting fixes, "while I'm here"
  refactors, and unrelated cleanups.
- **Weak success criteria** — claiming a change is done without
  defining what "done" means in a verifiable way, or without naming
  the specific command, output, or behavior that would prove it.
- **Plausible-but-wrong code** — code that reads correctly but
  doesn't match the actual API, version, or codebase conventions.

The skill pushes for surgical changes, explicit assumption-surfacing,
and verifiable success criteria before code is written.

**Why it's in this kit:**
The kit's other workflow tools — superpowers, feature-dev, Berry,
the dual-graph MCP — enforce **process discipline** (brainstorm first,
plan first, TDD first, cite evidence, verify before claiming done).
The Karpathy guidelines enforce **content discipline** on the code
itself once you are inside that process: keep it small, name your
assumptions, define what success looks like.

The two layers are complementary. Superpowers makes sure you go
through the right phases; Karpathy guidelines make sure that inside
each phase, the model's natural tendency to over-build, over-assume,
and under-specify gets pushed back on. Either layer alone leaves a
real gap — workflow without content heuristics still ships sprawling
diffs; content heuristics without workflow ship surgical code that
was never verified.

The skill is also a useful counterweight to the kit's emphasis on
ceremony: it actively pushes for minimum-viable-change and against
gold-plating, which is the right complement to a workflow-heavy
environment.

**When you'd disable it:**
Effectively never. The skill is low-cost — a single set of guidelines
loaded on demand — and its advice is broadly applicable to almost any
coding task. There is no realistic session in which "make smaller,
more surgical changes; state your assumptions; define success
criteria" is bad advice.

If you genuinely want sprawling exploratory edits (rare, but possible
during throwaway prototyping), you can simply ignore the skill's
suggestions on that session without disabling the plugin.

**Source:**
GitHub: <https://github.com/multica-ai/andrej-karpathy-skills>
Marketplace: `multica-ai/andrej-karpathy-skills`
Plugin name: `andrej-karpathy-skills`

Install via the kit's `install.sh`, which registers the
`multica-ai/andrej-karpathy-skills` marketplace and runs
`claude plugin install andrej-karpathy-skills@multica-ai/andrej-karpathy-skills`.

The skill is pure prompt content; no daemon, no external service,
no API key.

**Cost / footprint:**
- Disk: negligible — a small set of markdown skill files.
- Memory / CPU: zero at idle. Skills are loaded on demand by the
  `Skill` tool and only consume tokens while active.
- Network: none after install.
- Dependencies: none beyond the Claude Code CLI.

The token cost is small per invocation and pays for itself the first
time it stops a speculative refactor, a hidden-assumption bug, or a
"done" claim without a verification step.
