# frontend-design — distinctive, production-grade UI generation

**What it does:**
The `frontend-design` plugin installs a single skill
(`frontend-design:frontend-design`, also reachable as `/frontend-design`)
that generates frontend code — web components, pages, full interfaces —
with a strong bias toward distinctive, polished output. The skill is
explicitly designed to avoid the generic "AI aesthetic" that LLMs drift
into by default: no Inter / Arial / Roboto as the only typography
choice, no purple gradients as the default decorative move, no
shadcn-clone layouts shipped as finished work.

It steers toward production-grade choices: deliberate typography pairs,
intentional spacing systems, considered color palettes, and component
patterns that look like a designer touched them rather than the first
thing a model could autocomplete.

**Why it's in this kit:**
Frontend work is one of the places where "good enough to render" and
"actually shippable" are the widest apart. Without active steering,
Claude reliably produces UIs that all look like the same Tailwind
demo — and the cost of that drift is usually paid silently by the human
having to redo the work. The `frontend-design` skill encodes the design
heuristics that prevent the drift in the first place, so the first pass
is closer to something a real product team would merge.

The skill is also a useful prompt-design pattern in its own right: it
demonstrates how to add quality-direction to a generative skill without
locking it into a single style.

**When you'd disable it:**
- Pure backend, CLI, library, infrastructure, or data-engineering work
  with no rendered UI surface.
- Throwaway internal tools where the visual quality genuinely does not
  matter and any HTML that exposes the data is sufficient.
- Sessions where the team has its own design system that Claude should
  follow verbatim — in that case provide the system as context and skip
  the generative-design heuristics.

Do not disable it when building anything user-facing, anything that
will be screenshotted for stakeholders, or any prototype where design
quality affects whether the idea reads as serious.

**Source:**
GitHub: <https://github.com/anthropics/claude-plugins-official>
Marketplace: `anthropics/claude-plugins-official`
Plugin name: `frontend-design`

Install via the kit's `install.sh`, which registers the marketplace and
runs `claude plugin install frontend-design@anthropics/claude-plugins-official`.

The skill is pure prompt content — no external services, no API keys,
no runtime daemon.

**Cost / footprint:**
- Disk: negligible — a single markdown skill file.
- Memory / CPU: zero at idle. The skill prompt adds tokens to the
  active context only when invoked.
- Network: none. The skill ships its design guidance inline; it does
  not fetch external references at runtime.
- Dependencies: none beyond the Claude Code CLI. Whatever frontend
  framework, build tool, or runtime the user is already on remains
  unchanged.

The only cost is the context-token budget of the skill itself when
loaded, which is a deliberately small price for first-pass UI that
doesn't have to be redone by hand.
