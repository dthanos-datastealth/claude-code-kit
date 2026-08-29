# Evaluation protocol

Every candidate implements `ProtectionMethod` and is scored on the same triple.
A method is not adopted on argument; it is adopted on these numbers.

## 1. Utility — loss against the plaintext ceiling

`PlaintextBaseline` runs the adjudication with no protection at all and fixes
the upper bound. Every other method is reported as a loss against it, never as
an absolute score, because an absolute score cannot distinguish "the transform
hurt" from "the task is hard".

Reported separately for:

- **R1** — classification accuracy per entity type
- **R2-FP** — correctly overturning a detector false positive
- **R2-FN** — correctly catching a detector miss (the hard case)
- **text path** vs. **OCR path** (finding #4)

## 2. Leakage — adversarial, not theoretical

Attacks run against the protected payload alone.

| Attack | Question |
|---|---|
| `disclosure` | Does a real value survive verbatim? The weakest adversary; anything it finds is disclosed under every threat model |
| `reconstruction` | Can an adversary rebuild the original text from the payload? |
| `re-identification` | Can an adversary name the subject from context alone? |
| `attribute-inference` | Can an adversary recover a sensitive attribute without recovering the value? |

Scored against `ground_truth_spans`, never against the detector's `spans`, so a
detector's blind spots cannot hide a leak from the measurement. The last three
use an LLM as the adversary, which is the realistic threat.

## 3. Cost

Latency, throughput, cost per thousand spans, and operational burden on the
customer: local GPU, local model, key management, CC-mode hardware.

## Datasets

| Dataset | Why |
|---|---|
| **TAB** (Text Anonymization Benchmark) | 1,268 European Court of Human Rights cases with span-level annotations, identifier type, and co-reference. Marks *which* spans must be masked to conceal identity — the best available fit for R2 |
| **ai4privacy** `pii-masking-300k` / `openpii-1m` | Breadth and multilingual coverage |
| **PII-Bench** | Query-aware protection evaluation |
| **REDACT** | Systematically controlled multilingual detection |
| `ai-cloud` internal corpus | Pending A6. If it exists, it is the most representative data available |

Synthetic fixtures cover shapes the public sets miss. **No real customer data
enters this repository.**

## Controls

Two methods exist to keep the harness honest:

- **`plaintext_baseline`** — the positive control for leakage. A check that
  cannot catch it cannot clear anything else. Asserted by
  `test_leak_check_has_teeth`.
- **`naive_sanitize`** — the negative control. It must fail R2-FN. If it ever
  passes, the measurement has broken, not the finding.
