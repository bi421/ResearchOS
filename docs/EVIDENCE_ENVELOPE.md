# XAUUSD M1 Evidence Envelope

## Purpose

The Evidence Envelope is the reproducibility boundary for the real XAUUSD M1 research chain. It binds the exact bytes of the raw dataset, source event/outcome artifact, walk-forward result, and independent audit to the contract, parameters, code commit, and runtime fingerprint.

It is an integrity and lineage mechanism. **It is not evidence of predictive edge, profitability, calibrated live probability, or trading validity.**

## Proof chain

```text
raw CSV bytes
    -> dataset SHA-256
    -> source event/outcome artifact SHA-256
    -> frozen XAUUSD M1 contract
    -> walk-forward parameters
    -> result artifact SHA-256
    -> independent source-to-result audit
    -> evidence envelope hash
```

The envelope refuses to build when any link is inconsistent.

## Required bindings

- raw CSV SHA-256 must equal the dataset identity declared by the source artifact;
- result dataset identity must equal the raw CSV SHA-256;
- result source-artifact SHA-256 must equal the supplied source artifact bytes;
- source and result contracts must be identical and use the frozen XAUUSD/M1 `hit_threshold_1d` contract;
- the walk-forward result must declare the leakage embargo and no validation-label fitting;
- the independent audit must be `PASS` and must bind both source and result hashes;
- code commit is recorded explicitly;
- canonical contract and parameter hashes are recorded;
- Python implementation/version and platform are recorded;
- the complete envelope receives its own deterministic SHA-256.

## CLI

```powershell
python scripts/create_xauusd_m1_evidence_envelope.py `
  --raw-csv data/mt5/xauusd/XAUUSD_M1_2021_2025_MT5.csv `
  --source-artifact artifacts/xauusd_m1_real.json `
  --result-artifact artifacts/xauusd_m1_walkforward.json `
  --audit-artifact artifacts/xauusd_m1_source_to_result_audit.json `
  --code-commit 156bea8f99f7c0c0222becd65f197f48bb5e28a3 `
  --output artifacts/xauusd_m1_evidence_envelope.json
```

The exact local artifact paths may differ; no default or synthetic fallback is provided.

## Scientific boundary

A passing envelope establishes that the referenced artifacts form a consistent, auditable lineage at the time of creation. It does not establish that the probability model predicts future XAUUSD outcomes better than a baseline. That question requires subsequent out-of-sample statistical evaluation, negative controls, uncertainty intervals, and protection against multiple-testing/data-snooping effects.
