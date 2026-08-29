# Agentic Confidential Computing

Research and reference architecture for **adjudicating sensitive data without
seeing it**.

## The problem

Customers send DataStealth records and data spans to be classified as PII. They
also send the verdict of their own deterministic detector, together with the
original data and metadata as context, and ask whether that verdict was a false
positive or a false negative so the detector can be tuned.

The agent doing that analysis must not observe the confidential values. The
intended shape: transform the data so it can be analysed without being revealed,
then let a client-side transform turn the agent's answer back into a verdict
about the real data.

- **R1 — Classification.** Spans in, PII labels out.
- **R2 — Verdict adjudication.** Detector verdict + original context in,
  false-positive / false-negative judgement out.

## Why this is hard

Four findings drive the work. They are stated up front so they can be tested
rather than rediscovered.

1. **The false-negative paradox.** Sanitizing the payload using the detector's
   own output masks what it found and leaves what it missed — so the false
   negatives, the entire point of R2, cross the boundary in the clear.
   `tests/test_false_negative_leak.py` reproduces this on every run.
2. **Sanitizer circularity.** If the client-side transform needs a model good
   enough to recognise PII before it can hide it, the customer has already
   solved the problem and does not need the agent.
3. **Leakage is a budget, not a boolean.** Any signal sufficient to judge "is
   this PII" is signal about the data. What is achievable is a quantified,
   contractible bound — measured by attack, not asserted.
4. **OCR breaks the transform story.** Surrogate substitution over pixels is a
   different and harder problem than over text. That path may admit no
   client-side transform at all.

## Status

Phase 0 (bootstrap) complete. Phase 1 — the `ai-cloud` audit — is **blocked on
repository access**; see `docs/ai-cloud-audit.md`. No architecture decision is
made until it closes, because the answers branch the design.

## Layout

| Path | What lives there |
|---|---|
| `docs/problem-statement.md` | R1/R2 formalized |
| `docs/threat-model.md` | Adversaries, assets, boundaries |
| `docs/ai-cloud-audit.md` | The gating questions about the existing stack |
| `docs/research/` | Method landscape, OSS inventory, bibliography |
| `docs/adr/` | One record per decision |
| `docs/evaluation-protocol.md` | How a method earns its place |
| `eval/` | The harness: methods, attacks, datasets, metrics |
| `crates/`, `packages/`, `proto/` | Rust, TypeScript, shared schemas |

## Running the harness

```sh
pip install pytest
python -m pytest
```
