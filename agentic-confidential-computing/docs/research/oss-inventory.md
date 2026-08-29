# Build vs. reuse inventory

Order of preference: **`ai-cloud` first, mature open source second, new code
last.** Writing new code requires an ADR explaining why both prior options were
rejected.

| Need | First choice | External fallback | Notes |
|---|---|---|---|
| Deterministic PII / security-data detection | `ai-cloud` detector set (A2) | — | Defines the R2 input contract |
| LLM / vLLM classification | `ai-cloud` (A1) | — | Gating for the TEE decision |
| OCR | `ai-cloud` (A4) | — | Gating for finding #4 |
| NER for local over-masking | `ai-cloud` NER, if recall suffices (A3) | GLiNER (`urchade/GLiNER`, `knowledgator/gliner-pii-*`), spaCy | GLiNER is zero-shot, CPU-friendly, 60+ PII categories, with a documented Presidio integration |
| Anonymize + de-anonymize with entity map | — | **Microsoft Presidio** | Already ships the Anonymizer/Deanonymizer pair, custom operators, Faker surrogates. This *is* family A's engine — do not reimplement |
| Surrogate generation | — | Faker; Presidio AHDS surrogate operator | Per-job entity map gives the co-reference consistency family A needs |
| Format-preserving encryption | — | `fpe` crate (Rust, FF1); `ff3` (Python, FF3-1) | NIST SP 800-38G. No hand-rolled crypto, ever |
| Attestation verification | — | Veraison (`rust-ear`, `rust-cmw`); Confidential Containers Trustee; Fraunhofer-AISEC `cmc` | Trustee covers TDX, SGX, SEV-SNP, ARM CCA, Hygon CSV. Ours is a thin verifier *client* |
| MPC | — | MP-SPDZ, MOTION, HPMPC, SecretFlow-SPU | **CrypTen is deprecated — do not adopt.** HPMPC executes MP-SPDZ bytecode, so the compiler choice stays portable |
| PSI | — | OpenMined/PSI | ECDH + Bloom filter; C++/Go/JS/Python/Rust bindings, matching the polyglot layout |
| Differential privacy | — | OpenDP, IBM diffprivlib, Google differential-privacy | For cross-customer FP/FN aggregates |
| FHE (benchmark, then likely reject) | — | OpenFHE, TenSEAL, Zama Concrete | Enough to produce a real number for the ADR |
| Datasets | `ai-cloud` corpus (A6) | TAB, ai4privacy, PII-Bench, REDACT | No customer data in the repo |

## Written here, and only this

The method-under-test interface, the four attack implementations, the metrics
triple, the dataset adapters, the span and verdict schemas (derived from A2,
not invented), and the thin attestation-verifier client.

## Maintenance status is part of the decision

CrypTen's deprecation is the cautionary case: a well-known library, widely
cited, no longer developed. Every entry above carries a maintenance check
before adoption, recorded in the adopting ADR.
