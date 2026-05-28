# caveman — terse-output mode for token and context savings

**What it does:**
[`caveman`](https://github.com/JuliusBrussee/caveman) is a Claude Code
skill (delivered as a single `SKILL.md` rather than a marketplace
plugin) that switches the agent's reply style to a heavily condensed
"caveman" voice — short sentences, no filler, minimal markdown,
no preamble. Upstream measures the result at roughly **65% fewer
output tokens** versus the agent's default register. The skill is
opt-in per session, not always-on.

**Why it's in this kit:**
Output tokens dominate session cost on long working runs (bulk
refactors, large doc generation, mass code review). The kit's
default register is verbose by design — it pairs answers with
reasoning, citations, and `★ Insight` blocks when
`explanatory-output-style` is active. That register is the right
choice for teaching and design work but the wrong choice for
high-throughput execution. Caveman gives the user a way to flip
into a compression mode for the specific sessions where output
length is the constraint, without re-tuning prompts or disabling
other skills.

**When you'd disable it:**
- Sessions whose primary deliverable is *explanation* — debugging
  walkthroughs, teaching, architecture deep-dives. Compression
  destroys the reasoning chain.
- Code-review sessions where the user will read feedback carefully
  and act on nuance.
- Any session running under `explanatory-output-style` (the
  `★ Insight` regime conflicts with caveman's no-filler rule —
  pick one).
- Per-message — caveman is session-scoped, so to drop it just clear
  the session or start a fresh one.

**Source:**
GitHub: <https://github.com/JuliusBrussee/caveman>
Distribution: cloned directly into the user's global Claude Code
skills directory (`~/.claude/skills/caveman/`). Not packaged for
the official Anthropic plugin marketplace, so `install.sh` does NOT
install it — the kit documents the manual install in
[`docs/prereqs.md`](../prereqs.md) section 13.

Install command (one-time):
```sh
gh repo clone JuliusBrussee/caveman ~/.claude/skills/caveman
```
Restart Claude Code afterward so the skill is discovered. To use it,
invoke `/caveman` (or the skill name the upstream `SKILL.md` exposes
in its frontmatter) — it modifies the output style for the rest of
the session.

**Cost / footprint:**
- Disk: ~50 KB (single markdown skill file).
- Memory / CPU: zero at rest. Skills are markdown files the agent
  reads on invocation; no background process.
- Network: none after the one-time `gh repo clone`.
- Dependencies: none beyond Claude Code itself and `gh` for the
  install command.
- Operational cost: **paid back immediately** in output-token
  savings on any session where it's invoked. The 65% figure is the
  upstream's measurement; actual savings vary by task shape but
  consistently positive on long sessions.

**Hard rule (kit overlay):** caveman never overrides the kit's
mandatory rules. Berry verification, evidence-before-assertions,
the MANDATORY code-search order, and the spec-kit / Berry hard
prohibitions all still apply. Caveman compresses *how* the agent
reports its work, not *whether* the work meets the kit's quality
gates.
