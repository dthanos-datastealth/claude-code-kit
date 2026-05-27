# explanatory-output-style — ★ Insight blocks after code changes

**What it does:**
The `explanatory-output-style` plugin installs an output style that
appends short `★ Insight` blocks after code that Claude writes or
modifies. Each block calls out something educational about the change
that would otherwise stay implicit:

- **Why** a particular implementation choice was made (and what the
  alternatives were),
- **Trade-offs** the change is making — performance vs. clarity,
  flexibility vs. simplicity, generality vs. specificity,
- **Patterns** that are relevant to the surrounding codebase or
  ecosystem (idioms, conventions, gotchas),
- **Non-obvious decisions** — places where the obvious approach was
  rejected for a specific reason worth recording.

The blocks are intentionally short — a sentence or two, not a lecture
— and they sit alongside the code rather than inside it, so they do
not pollute the file or get committed.

**Why it's in this kit:**
Claude Code is used by humans, and a large fraction of its value is
in the implicit teaching that happens when the user reads the
generated code. Without explicit prompting, that teaching gets lost:
the code is correct, but the *reasoning* behind it stays in the
model's head. `★ Insight` blocks externalize that reasoning so the
user benefits from it.

This matters for two compounding reasons:

1. **Knowledge transfer.** The user learns the codebase, the language,
   and the patterns faster when each change comes with a one-sentence
   "here is why this shape, not the other one" attached. Over weeks,
   this is the difference between a tool that ships code and a tool
   that also makes the user better at the work.
2. **Self-reflection.** Generating an `★ Insight` forces the model to
   articulate the choice it just made, which exposes weak reasoning
   before it ships. A change that cannot be justified in a sentence
   is often a change worth re-examining.

The kit's global `CLAUDE.md` explicitly notes that the explanatory
style is active and instructs not to suppress it. This doc records
*why* it is active so future maintainers do not silently turn it off
because it adds output volume.

**When you'd disable it:**
- Pure batch-execution sessions — long task lists, scripted runs,
  CI-style workflows — where every extra paragraph of commentary is
  pure noise and there is no human reader who would benefit.
- Output-volume-sensitive contexts where the additional tokens of
  insight blocks meaningfully change the cost or latency profile
  (rare; the blocks are small).
- Sessions whose entire purpose is producing a clean artifact (a
  diff, a PR description, a single file) with no surrounding
  narrative.

Do not disable it for normal interactive development, for sessions
where someone is learning the codebase or the language, or any
context where the *reasoning* behind the code matters as much as the
code itself.

**Source:**
GitHub: <https://github.com/anthropics/claude-plugins-official>
Marketplace: `anthropics/claude-plugins-official`
Plugin name: `explanatory-output-style`

Install via the kit's `install.sh`, which registers the marketplace and
runs `claude plugin install explanatory-output-style@anthropics/claude-plugins-official`.

The plugin is pure prompt content — an output-style definition that
Claude Code loads automatically. No daemon, no external service, no
API key, no file modification of the user's repository.

**Cost / footprint:**
- Disk: negligible — a small output-style definition file.
- Memory / CPU: zero at idle. The style is applied at generation
  time, not as a separate runtime.
- Network: none after install.
- Dependencies: none beyond the Claude Code CLI.

The real cost is output tokens: each insight block adds a sentence or
two of generated text per code change. In normal interactive use the
overhead is small and the educational return is high; in pure batch
contexts the tradeoff inverts, which is exactly why a disable path
exists.
