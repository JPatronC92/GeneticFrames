# SECURITY MODEL & AUDITABILITY SPECIFICATION

## 1. Threat Model & Trust Assumptions
GeneticFrames addresses key adversarial scenarios:

### 1.1 Generation Front-running / Outcome Prediction
* **Attack**: An agent or miner predicts the random seed to only mint high-tier assets (e.g. Genesis/Epic).
* **Mitigation**: The protocol incorporates client-provided salt + epoch entropy + sequential nonce in a cryptographic commitment scheme. The outcome cannot be known before the transaction commitment is confirmed.

### 1.2 Retroactive Modification
* **Attack**: An attacker attempts to change the organism, biological sequence, or traits of an already issued frame.
* **Mitigation**: Every frame's identity is locked with a canonical SHA-256 manifest hash stored at minting time. Verification checks match the computed digest against the immutable record.

### 1.3 Double-Spending & Replay Attacks
* **Attack**: An agent attempts to spend the same 1 GF multiple times or replay generation calls.
* **Mitigation**: Monotonic account nonces and atomic database transactions ensure strict state consistency.

---

## 2. Independent Verifier Contract

Any node or agent can run the verification script without trusting the GeneticFrames server:

1. Fetch raw sequence from public NCBI/RefSeq using the manifest `accession`.
2. Compute `SHA-256(canonicalize_dna(sequence))` and assert equality with `manifest.sequence.sha256`.
3. Apply `FragmentPolicy(length, mode)` and assert `SHA-256(fragment) == manifest.fragment.sha256`.
4. Execute `GFDP v2.0.0(fragment)` and assert `SHA-256(generated_svg) == manifest.artifact.svg_sha256`.
5. Compute canonical manifest JSON and assert `SHA-256(manifest) == manifest.manifest_sha256`.
