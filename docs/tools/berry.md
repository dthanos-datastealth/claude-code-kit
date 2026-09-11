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
The kit's rules in `~/.claude/rules/` rule is "evidence before assertions — verify before
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
- `berry-greenfield-prototyping` — prototypes still cite what they assume.
- `berry-inline-completion-guard` — inline completions checked before they land.
- `berry-objective-optimization` — a measurable objective driven as a loop of
  baseline, hypothesis, smallest experiment, measurement, keep-or-revert, with
  each retained change backed by a stored before-and-after.

Seven, one per workflow playbook. Until recently none of them loaded: they
shipped as flat `skills/<name>.md` files, and Claude Code discovers plugin
skills only at `skills/<name>/SKILL.md`. Nothing errored — they were simply
absent. If a Berry skill does not appear, check that layout first.

**MCP tools, 28 of them.** Spans and runs: `start_run`, `load_run`,
`add_span`, `add_file_span`, `extract_span`, `list_spans`, `get_span`,
`search_spans`, `distill_span`, `mark_span`, `query_evidence`,
`get_evidence_pack`, `get_deliverable`, `export_run_ledger`. Verification:
`audit_trace_budget`, `detect_hallucination`, and their server-resolved
`audit_trace_budget_run` / `detect_hallucination_run` variants, which read the
run's own ledger instead of taking spans inline — prefer those when a run is
open. Claim graph: `create_claim`, `get_claim`, `list_claims`, `mark_claim`,
`link_claim_evidence`, `list_claim_evidence`, `audit_claims`. Attempts:
`record_attempt`, `list_attempts`, `list_audits`.

Two signatures changed with the v2 sync and the old calls fail validation
rather than misbehaving quietly, which is the good outcome. `start_run` now
requires `problem_statement` and `deliverable` and returns the sids it assigned
to each. `audit_trace_budget` takes `steps` directly; there is no `trace`
wrapper. A run is now a SQLite ledger at `~/.berry/runs/<id>/run.sqlite` with
tables for spans, claims, evidence links, audits and attempts, so state
survives the session rather than living in memory.

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
  `/berry:berry-configure` after install to set or rotate the key —
  then add the model pin by hand, because that command does not write it
  (see below).

If the verifier endpoint is down, every Berry skill fails fast — that is by
design. The kit prefers a hard failure to a silently-skipped audit.

---

## Choosing the verifier model

**The verifier must expose token logprobs.** Berry scores a claim from the
probability distribution over the YES token, so it calls the API with
`logprobs` and `top_logprobs` set. A model that does not return them cannot run
the gate at all — `stage_ab.py` raises `"logprobs is None; call the API with
logprobs enabled"`.

This constraint, not price, is what decides the shortlist. Checked against
OpenRouter's per-endpoint `supported_parameters`:

| Model | logprobs | price in/out per M |
|---|---|---|
| `openai/gpt-4o-mini` | yes, all endpoints | $0.15 / $0.60 |
| `openai/gpt-4o` | yes | $2.50 / $10.00 |
| `openai/gpt-4.1-mini`, `gpt-4.1-nano` | **no** | — |
| `openai/gpt-5-mini` | **no** (nor `temperature`) | — |
| `anthropic/claude-haiku-4.5` | **no**, all four providers | — |

So the kit's default is deliberate rather than inherited: `openai/gpt-4o-mini`
is the cheapest model in the OpenAI family that can run this gate. Every
obvious upgrade is ineligible. Escalate to `openai/gpt-4o` for high-stakes
gates; it is the same family and keeps logprobs.

Roughly 147 of OpenRouter's ~423 models advertise logprobs, so alternatives do
exist. Two cautions if you go outside OpenAI. Eligibility is **per endpoint**,
not per model, so an unpinned model can route to a provider that lacks logprobs
and fail intermittently — pin the provider as well as the model. And verify
against the raw `/models/<id>/endpoints` response rather than a summary.

**Always pin `BERRY_VERIFIER_MODEL` explicitly.** Berry's fallback discovers a
model by taking the first entry from `GET /v1/models`. Against OpenRouter that
is an arbitrary model, most likely without logprobs.

**`/berry:berry-configure` does not write the pin.** Its OpenAI-compatible
branch — the one you take for OpenRouter — writes `OPENAI_API_KEY` and
`OPENAI_BASE_URL` only. Following it end to end therefore leaves the verifier
unpinned, which is the state the paragraph above warns about. After running
it, add both remaining keys to `~/.berry/mcp_env.json` yourself:

```jsonc
{
  "OPENAI_API_KEY": "<your-openrouter-key>",
  "OPENAI_BASE_URL": "https://openrouter.ai/api/v1",
  "BERRY_VERIFIER_BACKEND": "openai",
  "BERRY_VERIFIER_MODEL": "openai/gpt-4o-mini"
}
```

**Read `error` before you trust `flagged`.** When the verifier call fails,
Berry returns `{"flagged": true, "under_budget": true, "error": "...",
"details": []}`. It fails closed, which is right, but `flagged: true` reads
exactly like a genuine claim failure. A flagged result carrying an `error` key
is a broken verifier, not evidence against your claim.

**`flagged` also does not always mean the claim failed.** Check `status`
first. `empty_context` (the step named no `cites`) and `no_spans` (the span
was mis-shaped) both mean the verifier was never called at all — they are
call bugs, not verdicts, and they should not count toward the three-strike
rule. Only `not_entailed` and `contradicted` say anything about your
evidence.

**The two audit calls do not return the same detail.** `audit_trace_budget`
(inline spans) reports `status` plus posterior YES bounds against a `target`,
and nothing else. `audit_trace_budget_run` (server-resolved spans) also
returns `observed`, `required` and `budget_gap` **in bits** per step, the
prior as well as the posterior, and an `evidence_pack` carrying its own
`text_sha256` and the list of materialized sids. Measured side by side on the
same claims: the inline form gave a bare status; the run form gave
`observed 23.80–39.86 bits` against `required 22.33–37.58`.

The bits matter for reading a flag correctly. Zero observed bits with
`contradicted` means the span refutes the claim. Zero bits with
`not_entailed` means the span is simply silent on it. Same number, opposite
diagnosis, and only one of them means you were wrong.

To settle a model choice empirically, build a golden set of about twenty
claim-and-span pairs — ten you know are supported, ten you know are not — run
`audit_trace_budget` with each candidate, and rank on false negatives first,
friction second, cost third.
