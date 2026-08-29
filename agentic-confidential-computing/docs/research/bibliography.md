# Bibliography

Every factual claim in `docs/` resolves to an entry here. Entries are grouped
by the claim they support.

## Confidential computing for agentic AI

- *When Agents Handle Secrets: A Survey of Confidential Computing for Agentic
  AI* — arXiv 2605.03213
- *AgenTEE: Confidential LLM Agent Execution on Edge Devices* — arXiv 2604.18231
- *Two-Way Confidential VMs (2cVM): Collaborative Confidential Computing for
  Mutually Distrustful Parties* — arXiv 2606.10615
- *EnclaveX: End-to-End Confidential AI with CPU/GPU TEEs* — arXiv 2606.31408
- cMCP — Confidential MCP gateway, hardware-attested MCP tool-call policy:
  <https://github.com/agentrust-io/cmcp>

## TEE performance (the <7% claim)

- *Confidential Computing on nVIDIA Hopper GPUs: A Performance Benchmark Study*
  — arXiv 2409.03992
- *Confidential LLM Inference: Performance and Cost Across CPU and GPU TEEs* —
  arXiv 2509.18886
- *Characterization of GPU TEE Overheads in Distributed Data Parallel ML
  Training* — arXiv 2501.11771

## Attestation

- Veraison — standards-based remote attestation; Rust `rust-ear`, `rust-cmw`:
  <https://github.com/veraison>
- Confidential Containers Trustee — Attestation Service + Key Broker Service
- Fraunhofer-AISEC `cmc`: <https://github.com/Fraunhofer-AISEC/cmc>
- *SNPGuard: Remote Attestation of SEV-SNP VMs Using Open Source Tools* — arXiv
  2406.01186

## Sanitization, surrogates, and local/remote splits

- *PAPILLON: Privacy Preservation from Internet-based and Local Language Model
  Ensembles* — NAACL 2025 / arXiv 2410.17127
- *SurrogateShield: Beyond Redaction for High-Utility, Privacy-Preserving LLM
  Interactions* — arXiv 2606.29567
- *Casper: Prompt Sanitization for Protecting User Privacy in Web-Based LLMs* —
  arXiv 2408.07004
- *Minim: Privacy-Aware Minimal View for Agents via Trusted Local Sanitization*
  — arXiv 2606.13949
- *LLM-Redactor: An Empirical Evaluation of Eight Techniques for
  Privacy-Preserving LLM Requests* — arXiv 2604.12064
- Microsoft Presidio — analyzer, anonymizer, deanonymizer:
  <https://github.com/microsoft/presidio>

## Leakage measurement

- *How do we measure privacy in text? A survey of text anonymization metrics* —
  arXiv 2512.01109
- *LLM Anonymization Against Agentic Re-Identification* — arXiv 2605.30848
- *Evaluating the disclosure risk of anonymized documents via a machine
  learning-based re-identification attack* — Data Mining and Knowledge
  Discovery, 2024
- *The Double-edged Sword of LLM-based Data Reconstruction* — arXiv 2508.18976

## Datasets

- *The Text Anonymization Benchmark (TAB)* — arXiv 2202.00443
- ai4privacy `pii-masking-300k`, `openpii-1m` — Hugging Face
- *PII-Bench: Evaluating Query-Aware Privacy Protection Systems* — ACL 2026 /
  arXiv 2502.18545
- *REDACT: A Systematically Controlled Multilingual Benchmark for Personal
  Information Detection* — arXiv 2606.19881

## MPC, PSI, DP, FHE

- *Benchmarking Secure Multiparty Computation Frameworks for Real-World
  Workloads* — IACR ePrint 2026/183
- *A Pragmatic Comparison of Cryptographic Computation Technologies for Machine
  Learning* — arXiv 2605.04858 (source for CrypTen's deprecation and the HE
  performance figures)
- MP-SPDZ, MOTION, HPMPC, SecretFlow-SPU
- OpenMined/PSI: <https://github.com/OpenMined/PSI>
- OpenDP, IBM diffprivlib

## NER

- GLiNER: <https://github.com/urchade/GLiNER>
- *GLiNER2-PII: A Multilingual Model for Personally Identifiable Information
  Extraction* — arXiv 2605.09973
- `knowledgator/gliner-pii-{edge,small,base,large}-v1.0` — Hugging Face
