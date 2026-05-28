# berry — MCP-backed evidence verifier and hallucination detector

**What it does:**
Berry installs an MCP server plus a set of workflow skills that enforce
evidence-before-assertions. The MCP exposes tools for recording verifiable
spans of evidence (`add_span`, `add_file_span`), auditing whether a set of
claims is sufficiently supported by those spans (`audit_trace_budget`), and
running per-claim hallucination probes (`detect_hallucination`). The verifier
backend is any OpenAI-compatible chat-completions endpoint; the kit defaults
to OpenRouter-hosted `openai/gpt-4o-mini`, with a self-hosted llama.cpp
endpoint as an offline alternative.

**Why it's in this kit:**
The kit's `CLAUDE.md` rule is "evidence before assertions — verify before
claiming anything works." Berry is what turns that rule from a slogan into a
machine-checkable gate. Every plan step, RCA conclusion, test-pass claim, and
generated-artifact handoff routes through a Berry skill that requires spans
with citations and a passing budget audit. If the verifier cannot find enough
mutual information between your spans and your claims, the audit fails and you
have to gather more evidence — not rephrase the claim.

Skills installed:
- `berry-plan-and-execute` — every plan step audited before execution.
- `berry-rca-fix-agent` — ROOT_CAUSE verified before any fix; FIX_VERIFIED
  before closing.
- `berry-search-and-learn` — actual test output captured as a span before any
  "tests pass" claim.
- `berry-generate-boilerplate` — design intent verified before delivering
  generated code, configs, migrations, or docs.
- Two more workflow skills covering review and triage flows.

MCP tools: `start_run`, `load_run`, `add_span`, `add_file_span`, `list_spans`,
`get_span`, `search_spans`, `distill_span`, `audit_trace_budget`,
`detect_hallucination`, `get_deliverable`.

**When you'd disable it:**
- Read-only exploration sessions where you are not writing code or claiming
  completion of anything.
- Brief sandbox scripts you will throw away in the same session.
- Environments where the verifier endpoint is unreachable (no OpenRouter
  key, no self-hosted backend) and you do not want Berry skills attempting
  to call a dead endpoint.

Do not disable it when you are: closing a bug, declaring tests green, finishing
a plan step, or shipping any artifact a human or another agent will rely on.

**Source:**
GitHub (Claude-Code-packaged): <https://github.com/dthanos-datastealth/hallbayes>
Marketplace: `dthanos-datastealth/hallbayes`
Plugin name: `berry`
Upstream source (Python core, no Claude packaging): <https://github.com/leochlon/hallbayes>

The kit points at `dthanos-datastealth/hallbayes` rather than upstream
because upstream is the raw hallbayes Python project — it ships the
verifier source but NOT the Claude Code marketplace scaffolding
(`.claude-plugin/marketplace.json`, `commands/`, `skills/`, `.mcp.json`)
that `claude plugin marketplace add` needs. The fork adds that
scaffolding and is the only currently-published path to install Berry
as a Claude Code plugin.

Install via the kit's `install.sh`, which registers the marketplace and runs
`claude plugin install berry@berry-marketplace`.

**Cost / footprint:**
- Disk: the plugin itself is small (~5 MB). The default OpenRouter backend
  adds no disk footprint at all.
- Memory: negligible for the OpenRouter path (the verifier is remote). For
  the optional self-hosted llama.cpp alternative (Qwen3-Coder-30B-A3B in
  8-bit KV), budget ~18 GB on disk and ~16 GB RAM steady-state.
- Network: each `audit_trace_budget` / `detect_hallucination` call hits
  OpenRouter. Per-call cost is `openai/gpt-4o-mini` pricing × the spans +
  claims context size — typically fractions of a cent per audit (a
  10K-token prompt + 500-token response is ~0.18¢ at current rates).
- OpenRouter caveats: free-tier accounts have strict per-minute rate
  limits that will throttle Berry audits at any non-trivial pace. For
  sustained use, add a small credit balance to your OpenRouter account
  to unlock the paid-tier rate limits. Watch for `429` responses in
  Berry's logs as the signal to upgrade.
- Dependencies: an OpenRouter API key (free tier works for low volumes) OR
  any OpenAI-compatible server reachable from your machine.
- Configuration: `~/.berry/config.json` selects the backend; `~/.berry/mcp_env.json`
  carries the env vars (`OPENAI_API_KEY`, `OPENAI_BASE_URL`,
  `BERRY_VERIFIER_MODEL`) into the MCP process. Run
  `/berry:berry-configure` after install to set or rotate the key.

If the verifier endpoint is down, every Berry skill fails fast — that is by
design. The kit prefers a hard failure to a silently-skipped audit.
