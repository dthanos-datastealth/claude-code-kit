# Method landscape

Six families, none pre-committed. Verdicts marked *prior* are expectations to
be tested by the harness, not conclusions. Sources in `bibliography.md`.

## A — Surrogate substitution with consistent pseudonyms

Replace each sensitive value with a category-preserving surrogate drawn from
the same distribution; keep the substitution consistent within a job via
format-preserving encryption so co-reference survives. Verdicts return keyed by
span id and the customer maps them back.

This is the direct formalization of the intended shape. Its engine already
exists: Presidio ships an Anonymizer/Deanonymizer pair with an entity map,
custom operators, and Faker-backed surrogates.

**Prior:** core for the R1 text path. Blocked alone for R2 by finding #1, and
for OCR by finding #4.

## B — Feature-vector abstraction

Send only derived structure — character-class shape, length, entropy, checksum
validity, delimiters, field metadata — and never the token.

**Prior:** strongest privacy, but likely too lossy exactly where an LLM beats a
regex. If semantic context is what justifies the agent, discarding it discards
the reason for the project. Worth measuring precisely to bound the tradeoff.

## C — TEE-hosted agent

Run the agent inside a hardware-attested enclave — Intel TDX or AMD SEV-SNP
with NVIDIA H100/H200 confidential-compute mode — and have the customer verify
remote attestation before releasing anything.

Measured overhead for LLM inference in H100 CC mode is under 7%, and lower as
model size grows. This is the only family that covers the OCR path, and the
only one whose guarantee does not degrade with sanitizer recall.

**Prior:** likely primary, pending A1. If `ai-cloud` already self-hosts vLLM,
this is "enable CC mode on hardware already operated, add attestation" rather
than new infrastructure.

## D — MPC, PSI, and differential privacy

Full LLM inference under secure multiparty computation is orders of magnitude
too slow to serve. Two narrower uses are sound:

- **PSI** for secret-set membership — "is this value in the customer's employee
  gazetteer?" — without either side revealing its set.
- **DP** for the *subsequent analysis* half of the ask: aggregate FP/FN rates
  across customers with a formal privacy budget.

**Prior:** selective use, not the substrate.

## E — Local model plus remote agent

A local model rewrites the request, a remote model reasons, a local module
reassembles the answer. Established in PAPILLON, Hide-and-Seek, and PP-TS.

**Prior:** this is the *mechanism* that implements family A, most likely driven
by `ai-cloud`'s own NER (A3).

## F — Fully homomorphic encryption

Compute directly on ciphertext.

**Prior:** reject on performance. Reported throughput for GPU LLM inference
under HE is roughly 0.2 tokens per second, with overheads to 10,000×. Benchmark
once to produce a defensible number, record it in an ADR, and stop relitigating.

## Working hypothesis

Layered **C + A + D**: TEE as the hardware-bounded floor and the only viable
OCR answer; surrogate substitution as defense-in-depth and data minimization;
PSI and DP for the narrow operations that are genuinely cryptographic in shape.

The harness exists to confirm or kill this. It is written down so that it can
be falsified, not so that it can be assumed.
