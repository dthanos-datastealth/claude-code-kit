# Installed tools

## Installed Plugins & When to Use Them

Every plugin, MCP and skill below has a depth-reference in
`~/.claude/docs/tools/`, installed by `install.sh`, following a strict
five-section schema: *What it does · Why it's in this kit · When you'd disable
it · Source · Cost / footprint*. The table names the file where it is not simply the tool's own name. **Read the depth-reference** before invoking a
tool whose cost you can't recall, when asked "what does X do?" or "should I
disable X?", when behaviour surprises you (the "when you'd disable it" section
lists the wrong-tool cases), or when you need the upstream source.

`~/.claude/docs/` also holds `philosophy.md` (why each rule exists),
`workflow.md` (the 10-step recipe), `verification-standards.md` (what counts as
evidence), `prereqs.md` (per-OS install commands), `corporate-tls.md` and
`memory-system.md`. If that directory is missing or thinner than the plugin
list, re-run `install.sh` — `kit_copy_docs` populates it.

| Tool | Reach for it when |
|---|---|
| **superpowers** | The backbone. Invoke `/superpowers:using-superpowers` at the start of any conversation. Brainstorm → plan → worktree → TDD → verify → review → finish. |
| **feature-dev** | **Mandatory for new features.** Any "add/build/create/implement". Seven phases; never skip phase 3 (clarifying questions) or the approval gate before phase 5. |
| **gopls / typescript / jdtls LSP** (`lsp-gopls.md`, `lsp-typescript.md`, `jdtls-lsp.md`) | Automatic in matching files. Needs the binary on `$PATH`; jdtls also needs JDK 21+. |
| **playwright** (`playwright-mcp.md`) · **chrome-devtools-mcp** | Browser automation and E2E. Drop to chrome-devtools for CDP-level work: LCP traces, memory snapshots, network conditions. |
| **context7** · **microsoft-docs** | Live library docs. Use whenever an external API is involved rather than trusting recall; microsoft-docs for anything .NET/Azure/M365. |
| **code-simplifier** (`/simplify`) · **optibot** | The O role. Simplifier targets clarity, optibot targets speed and cost — pair them on hot paths. |
| **security-guidance** (`/security-review`) | Before merging anything touching auth, input parsing, uploads, secrets, network or DB. |
| **frontend-design** | Production-grade UI. Never generic fonts or purple gradients. |
| **notion** | Capture decisions, turn specs into tasks, meeting prep. |
| **huggingface-skills** | Any ML-engineering task touching the Hub. |
| **claude-md-management** | `/revise-claude-md` at the end of a session that discovered new patterns. |
| **remember** (`/remember`) | Session end with work mid-flight. |
| **claude-code-kit** | This kit's own plugin. `/claude-code-kit:status` reports the installed channel, version and commit; `:upgrade` and `:rollback` drive the upgrade scripts; `:fix-notion-mcp-port` repairs the Notion re-auth port. |
| **andrej-karpathy-skills** | Always on. Reduces overcomplication and unstated assumptions. |
| **caveman** | Opt-in terse output when token cost dominates. Never overrides the mandatory rules above — it compresses how work is reported, not whether it meets the gates. |
| **spec-kit** | Optional spec-first alternative for greenfield or multi-contributor work. The full playbook, including where this kit is stricter than upstream, is in `~/.claude/docs/tools/spec-kit.md`. Do not run it and `/feature-dev` for the same feature. |

### Berry (Evidence Verification) — MANDATORY

Berry is an MCP-backed hallucination detection system installed via the `berry@berry-marketplace` plugin. It exposes MCP tools (`start_run`, `add_span`, `add_file_span`, `audit_trace_budget`, `detect_hallucination`, etc.) and seven workflow skills that encode when and how to call them.

**Skills are the entry points. MCP tools are what the skills call internally.**

#### Mandatory triggers — no exceptions

| Situation | Use this skill | Verification gate |
|-----------|---------------|-------------------|
| Writing or reviewing any plan | `berry-plan-and-execute` | Every plan step must pass `audit_trace_budget` before execution is approved |
| Any RCA or debugging session | `berry-rca-fix-agent` | ROOT_CAUSE must pass before writing a fix; FIX_VERIFIED must pass before closing |
| Claiming tests pass or work is complete | `berry-search-and-learn` | Capture actual test output as a Berry span; cite it in the completion claim |
| Generating boilerplate, config, migrations, docs | `berry-generate-boilerplate` | Design intent trace must pass `audit_trace_budget` before delivering the artifact |

#### Hard rules

- **No facts without citations.** Every factual claim must end with a Berry span citation `[S0]`, `[S1]` etc. If you cannot cite it, it is an **Assumption** — label it as such, never present it as fact.
- **Verification must pass before proceeding.** If `audit_trace_budget` flags claims, gather more evidence and re-run. Do not move forward with unresolved failures.
- **3-strike rule.** If `audit_trace_budget` fails 3 consecutive times on the same claim set: STOP, surface what passed and what flagged with reasons, and wait for user guidance. Do not silently loop or drop failures.
- **Test output is evidence.** Always capture real test runner output as a Berry span via `add_span`. Never claim tests pass without a span that cites the actual output.
- **RCA root cause must be verified before implementing a fix.** No exceptions.

#### `audit_trace_budget` API usage (CRITICAL — a step without `cites` verifies nothing)

Two things have to be right, and getting either wrong produces a `flagged` result that looks exactly like a failed claim.

**1. Every step must cite the spans that support it.** `context_mode` defaults to `"cited"`, which selects only the spans a step names in `cites`. A step with no `cites` gets an empty context, the verifier is never called, and the result comes back flagged.

**2. Spans use `{"sid": ..., "text": ...}`.** The other shape is rejected outright rather than scored.

```python
# CORRECT — the step cites S0, so S0 is in scope when the claim is scored
audit_trace_budget(
    steps=[{"claim": "The suite reports 174 passed and 1 skipped.", "cites": ["S0"]}],
    spans=[{"sid": "S0", "text": "<actual test runner output>"}],
)

# WRONG — no cites. status="empty_context", verifier_calls=0, flagged=true.
# Nothing was verified, and the result is indistinguishable from a real failure.
audit_trace_budget(
    steps=[{"claim": "..."}],
    spans=[{"sid": "S0", "text": "..."}],
)

# WRONG — span keyed by id. status="no_spans": "no spans were provided,
# so the claim cannot be verified".
spans=[{"S0": "<actual test runner output>"}]
```

Passing `context_mode="all"` is the alternative to `cites` when every span is relevant to every claim. Prefer `cites`: it is what makes a citation `[S0]` in your prose mean something checkable.

#### Reading the result

There is no `observed_bits` field. Each step returns a `status` and, where the verifier ran, posterior YES bounds against a `target` (default `0.95`):

| `status` | Meaning | What to do |
|---|---|---|
| `passed` | Posterior clears the target | Proceed; cite the span |
| `not_entailed` | Verifier ran; evidence does not reach the target | Strengthen the span, or narrow the claim to what the span actually shows |
| `contradicted` | Verifier ran; evidence points the other way | The claim is wrong. Do not reword it |
| `empty_context` | No span was in scope — **missing `cites`** | Fix the call, not the claim |
| `no_spans` | Span shape rejected | Fix the call, not the claim |

`empty_context` and `no_spans` mean the gate did not run. Treat them as build errors, not as evidence about your claim.

A claim that asserts more than its span shows will legitimately sit just under target — "the claude-code-kit suite reports 174 passed" scores lower than "the suite reports 174 passed" when the span is bare pytest output that never names the project. That is the gate working. Narrow the claim.

#### Verifier backend

OpenRouter-hosted `openai/gpt-4o-mini` via Berry's OpenAI-compatible client.

**Always pin `BERRY_VERIFIER_MODEL`.** The fallback takes the first model from
`GET /v1/models`, which on OpenRouter is arbitrary and probably lacks the token
logprobs Berry requires. A `flagged` result carrying an `error` key is a broken
verifier, not a failed claim — check `error` first. The model-choice rationale
and the logprobs eligibility table live in `~/.claude/docs/tools/berry.md`.

**The plugin's own `/berry:berry-configure` does not write this pin.** Its
OpenAI-compatible branch writes `OPENAI_API_KEY` and `OPENAI_BASE_URL` only, so
following it against OpenRouter leaves the verifier unpinned. Add
`BERRY_VERIFIER_BACKEND` and `BERRY_VERIFIER_MODEL` to `mcp_env.json` yourself
afterwards.

Two files configure this, and they hold different things.
`~/.berry/mcp_env.json` is **load-bearing**: the MCP launcher reads these env
vars at startup, and it is the only place credentials belong.
`~/.berry/config.json` holds permissions — `allowed_roots` (without which
`add_file_span` refuses to read anything), the `allow_*` flags, audit settings.
Do not let an API key end up in `config.json`: nothing reads it there, and a
second copy is a second thing to rotate and to leak.

```jsonc
// ~/.berry/mcp_env.json — LOAD-BEARING: read by the MCP launcher
{
  "OPENAI_API_KEY": "<your-openrouter-key>",
  "OPENAI_BASE_URL": "https://openrouter.ai/api/v1",
  "BERRY_VERIFIER_BACKEND": "openai",
  "BERRY_VERIFIER_MODEL": "openai/gpt-4o-mini"
}

// ~/.berry/config.json — permissions, NOT credentials
{
  "allowed_roots": ["/path/to/your/repos"],
  "allow_write": false,
  "allow_exec": false,
  "allow_web": false,
  "enforce_verification": true,
  "audit_log_enabled": true
}
```

An earlier version of this example carried a `verifier` block with the API key
repeated here. That is what put a second plaintext copy on installed machines.
Only `mcp_env.json` is read for credentials; if your `config.json` still has an
`api_key`, delete that field — everything keeps working.

If verification calls start failing, first check that the OpenRouter key is still valid (`curl -H "Authorization: Bearer $KEY" https://openrouter.ai/api/v1/models | head`), then check OpenRouter status. A self-hosted llama.cpp backend remains an option for offline / air-gapped work — see Berry's upstream docs for the alternative config.

---

Anything in `~/.claude/rules/00-user-overrides.md` overrides this file. If the two disagree, follow the override and say which rule you are setting aside.
