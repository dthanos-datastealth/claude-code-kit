# Threat model

## Assets

| Asset | Why it matters |
|---|---|
| Confidential span values | The thing the customer is paying not to disclose |
| The re-identification map | Inverts every surrogate at once; strictly more valuable than any single payload |
| Detector rules and thresholds | Customer security posture; discloses what they can and cannot catch |
| Aggregate FP/FN rates | Cross-customer, these describe where detection is weak |
| Retained artifacts | Queues, caches, KV cache, logs, vector stores (A5) — frequently the real leak |

## Adversaries

| Adversary | Capability | In scope |
|---|---|---|
| Curious operator | Reads infrastructure the agent runs on: memory, logs, storage | Yes — this is the core case |
| Model provider | Sees prompts and completions | Depends on A1 |
| Compromised agent runtime | Arbitrary code in the analysis path | Yes — motivates hardware isolation |
| Malicious customer | Submits crafted records to probe other tenants or extract detector internals | Yes |
| Network observer | Sees traffic in transit | Yes, but TLS-solved; not the interesting case |
| Nation-state with hardware attack capability | Physical die attacks, side channels against TEEs | Out of scope; recorded, not defended |

## Boundaries

One object crosses the trust boundary: the protected payload. Everything the
adversary knows is derived from it, so the harness scores every attack against
that object and nothing else. This is enforced by construction — the
`ReidentificationMap` is a separate return value that no method may embed in the
payload.

## Failure modes specific to this problem

- **False-negative disclosure.** Sanitizing from detector output leaks the
  misses. Measured by `eval/attacks/disclosure.py`; reproduced in
  `tests/test_false_negative_leak.py`.
- **Co-reference leakage.** Consistent pseudonyms preserve the fact that a
  value recurs, which adjudication needs and which also enables linkage.
- **Context inference.** The surrounding text can identify a person even with
  the name removed — the failure mode the Text Anonymization Benchmark was
  built to expose.
- **Structural leakage.** Length, character class, and checksum validity are
  precisely the features that make a span classifiable, and precisely what a
  reconstruction attack exploits.
- **Retention.** Data protected in flight and at rest in the agent, then
  written to a log or KV cache in the clear.

## Explicit non-defence

Perfect confidentiality is not on offer. Any representation rich enough to
support adjudication carries information about the data. The deliverable is a
measured, contractible bound — a number a customer's security review can
argue with — not a claim of zero knowledge.
