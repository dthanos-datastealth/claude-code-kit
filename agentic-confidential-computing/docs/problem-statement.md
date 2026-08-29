# Problem statement

## Requests

**R1 — Classification.** A customer submits records or data spans. For each
span the agent returns whether it is PII and of what type.

**R2 — Verdict adjudication.** The customer's deterministic detector has
already produced a verdict. The customer submits that verdict together with the
original data and surrounding metadata as context. The agent returns whether
the verdict was a true positive, a false positive, or a false negative. The
results feed detector tuning.

R2 is the harder request and the one that shapes the architecture: it is
defined by needing the original context, and its value is concentrated in
exactly the cases the detector got wrong.

## Constraint

The agent, the infrastructure it runs on, and any model provider behind it must
not observe confidential values. The intended shape: transform the data so it
can be analysed without being revealed, then let a client-side transform turn
the agent's answer into a verdict about the real data.

## Actors

| Actor | Holds | Trusted with |
|---|---|---|
| Customer | Original records, the re-identification map, detector verdicts | Everything — this is the data owner |
| DataStealth control plane | Job orchestration, results keyed to surrogate ids | Metadata and surrogate-space verdicts only |
| Agent runtime | The protected payload | Only what the payload discloses |
| Model provider | Prompts and completions | **Depends on A1.** Self-hosted vLLM keeps this inside DataStealth; a third-party API makes it a separate untrusted party |

The trust boundary sits between the customer and everything to its right. What
crosses it is exactly one object — `ProtectedPayload` in `eval/harness/method.py`
— which is why the harness scores attacks against that object alone.

## What "the customer-side transform gives the final answer" means concretely

The agent never learns the mapping. It receives spans identified by surrogate
ids and returns verdicts keyed by those same surrogate ids. The customer holds
the `ReidentificationMap` and applies it locally to recover verdicts about real
spans. The verdict transfers because adjudication is a judgement about a
*category*, not about a *value* — whether a name is "John Smith" or "Aisha
Okonkwo" does not change that it is a person name.

That equivalence is the load-bearing assumption of the whole surrogate
approach, and it is exactly what the harness must measure rather than assume:
where context carries the signal, a surrogate can destroy it.

## Non-goals

Production implementation, TEE procurement and deployment, the customer-side
SDK, changes to `ai-cloud` itself, and the detector-tuning loop that consumes
R2 output.
