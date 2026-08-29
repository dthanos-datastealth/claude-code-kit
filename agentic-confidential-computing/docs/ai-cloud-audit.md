# ai-cloud audit — gating questions

`dthanos-datastealth/ai-cloud` (branch `feature/experimental`) already carries
LLM and vLLM classification, a large set of conventional deterministic PII and
security-critical-data detectors, OCR, and NER. This project retrofits a
confidentiality boundary around that stack rather than building a new one.

> **Nothing below is verified.** Repository access has not been granted, so
> every row is an open question. No statement about `ai-cloud` may be promoted
> to a finding without a `file:line` citation recorded here.

## Access blocker

| Attempt | Result |
|---|---|
| `add_repo` (×4) | `requires approval` — never granted |
| `mcp__github__list_branches` | `Access denied: not configured for this session` |
| `git ls-remote` | `could not read Username` — no credentials |

Unblocking needs the `add_repo` approval, and confirmation of the exact branch
name (`feature/experimental` vs. the literal `feature/experimentional`).

## Questions

| # | Question | What it decides | Status |
|---|---|---|---|
| **A1** | Is inference self-hosted vLLM, a third-party API, or both? Which models, which hardware? | **Gating.** Self-hosted vLLM makes the TEE path cheap — enable CC mode on GPUs already operated. A third-party API puts the model provider outside the trust boundary and forces the client-side transform to carry full weight | open |
| **A2** | Detector inventory: rule types, entity coverage, output schema, confidence semantics | This *is* the R2 subject. Its output schema becomes `proto/`'s span and verdict contract rather than something invented here | open |
| **A3** | **NER recall, per entity type** | **Gating.** Decides finding #2. High recall means it can serve as the client-side over-masking sanitizer; low recall means augmenting it or letting the TEE carry the risk | open |
| **A4** | OCR shape: image in, text out, with or without coordinates? Are images retained? | **Gating.** Decides whether the OCR path admits any client-side transform (finding #4) | open |
| **A5** | Where data physically rests and for how long — queues, caches, KV cache, logs, vector stores | Retention is often the real leak, not inference. Agent memory and KV caches are named high-value targets in the literature | open |
| **A6** | Existing evaluation assets — labelled data, FP/FN metrics, regression suites | If a labelled corpus exists, the harness scores against real data instead of public datasets alone | open |
| **A7** | Language, framework, package boundaries, test setup, CI | Decides whether this repo consumes `ai-cloud` as a library, a service, or a vendored subset | open |

## Reuse rule

`ai-cloud` outranks every external library. Nothing is reintroduced from open
source that already exists there and works. Where a component exists but its
quality is unknown — the NER, A3 — the harness measures it before deciding to
keep, augment, or replace it. Measurement, not assumption.
