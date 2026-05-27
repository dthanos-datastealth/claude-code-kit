# berry — MCP-backed evidence verifier and hallucination detector

**What it does:**
Berry installs an MCP server plus a set of workflow skills that enforce
evidence-before-assertions. The MCP exposes tools for recording verifiable
spans of evidence (`add_span`, `add_file_span`), auditing whether a set of
claims is sufficiently supported by those spans (`audit_trace_budget`), and
running per-claim hallucination probes (`detect_hallucination`). The verifier
backend is a local OpenAI-compatible LLM that computes the information-theoretic
contribution each span makes to each claim.

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
- Environments where the local LLM backend is unavailable and you do not want
  Berry skills attempting to call a dead endpoint.

Do not disable it when you are: closing a bug, declaring tests green, finishing
a plan step, or shipping any artifact a human or another agent will rely on.

**Source:**
GitHub: <https://github.com/leochlon/hallbayes>
Marketplace: `leochlon/hallbayes`
Plugin name: `berry`

Install via the kit's `install.sh`, which registers the marketplace and runs
`claude plugin install berry@leochlon/hallbayes`.

**Cost / footprint:**
- Disk: the plugin itself is small (~5 MB), but the recommended verifier
  backend — Qwen3-Coder-30B-A3B served by llama.cpp — is roughly 18 GB on disk
  in its 8-bit-KV configuration.
- Memory: ~16 GB RAM steady-state for the llama-server process (more on
  longer contexts).
- Network: none in steady state; the verifier runs entirely locally at
  `http://127.0.0.1:8080/v1`.
- Dependencies: `llama.cpp` (or any OpenAI-compatible local server), the GGUF
  model weights, and one always-on process. On macOS the kit's recommended
  setup runs llama-server via a `launchctl`-managed plist so it auto-starts.
- One-time setup: configure the backend with `berry-configure` after install
  (`/berry:berry-configure`).

If the verifier endpoint is down, every Berry skill fails fast — that is by
design. The kit prefers a hard failure to a silently-skipped audit.
