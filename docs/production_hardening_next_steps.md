# Production hardening — current gates

This document records the correctness gates for moving ResearchOS from research infrastructure toward production-grade evidence.

## 1. Runtime Evidence Certification — IMPLEMENTED / HARDENED

The production trust boundary is now:

`Dataset → Experiment → Run → Result`

`researchos.evidence.runtime_certification.certify_runtime()` fails closed unless a Dataset evidence parent exists. When the actual `ResearchDataset` is supplied, the Dataset envelope is emitted first and becomes the deterministic parent of the Experiment artifact. Run and Result artifacts are then emitted in dependency order and the complete chain is verified before certification is returned.

Artifact identity is deterministic under Evidence Envelope scheme 2. `created_at` is observational telemetry and is excluded from artifact and lineage hashes. `EvidenceRepository` is append-only: identical artifacts are idempotent, conflicting rewrites are rejected, parent closure is required, and lineage closure is verified.

Emission failure is therefore not converted into an uncertified successful result: certification raises immediately and no `RuntimeCertification` object is returned.

## 2. Synthetic-data certification gate — IMPLEMENTED / HARDENED

Runtime certification rejects datasets classified as `synthetic`, `demo`, `mock`, or `fixture`, and rejects the same classifications when present in the Experiment dataset configuration. The rejection occurs before any evidence artifact is written.

Engineering fixtures remain valid for ordinary unit tests; they are not valid scientific evidence.

## 3. Dataset identity — EXISTING IDENTITY SURFACES CONSOLIDATED AT EVIDENCE BOUNDARY

`HistoricalDataset` exposes both:

- `dataset_content_hash`: identity derived only from record hashes;
- `dataset_hash`: deterministic dataset identity including dataset metadata/version.

The Evidence Envelope provides the immutable artifact identity for the exact frozen `ResearchDataset` payload. Runtime certification uses that Dataset evidence artifact as the lineage parent rather than accepting an unverified free-form dataset version.

No timestamp is included in the artifact hash.

## 4. Real chronological Walk-Forward OOS — PARTIALLY IMPLEMENTED / REMAINING GATE

The repository already contains a real chronological C++ `BacktestEngine::run_walk_forward` implementation with disjoint test windows and next-bar-open execution. The Market Memory OOS validator also supports chronological train/validation/test partitions, train-only fitting callbacks, purge days, embargo days, and realized-label boundary checks.

However, the production certification contract is **not yet marked fully complete** because the C++ SignalFn walk-forward API does not itself expose a train-only parameter-fitting callback or an explicit label-horizon purge/embargo contract. A fitted strategy must not be certified as fitted OOS until that boundary is explicit.

Therefore:

- chronological OOS: available;
- next-bar-open execution: available;
- train/test temporal separation: available;
- train-only fitting contract for fitted strategies: still required;
- explicit purge/embargo tied to maximum outcome horizon at the certification boundary: still required.

## 5. Calibrated Probability — CAPABILITY EXISTS, PRODUCTION INTEGRATION REMAINS GATED

ResearchOS already contains deterministic calibration primitives, including isotonic and Platt calibration and outcome-grounded calibration reporting. Calibration must be fit on data disjoint from the model-fitting sample; it must never consume future outcomes. This is especially important for time-ordered research, where random cross-validation can leak temporal information.

The Phase 5.2 result contract already records calibration diagnostics, but the current Phase 5.2 pipeline still reports the raw empirical/multivariate probabilities and their calibration diagnostics rather than replacing the production probability surface with a separately fitted chronological calibrator.

The next production step is therefore a train-only / earlier-OOS calibration stage followed by a later-OOS evaluation and baseline comparison. Until that stage is complete, calibrated probabilities remain unavailable as certified decision evidence.

## 6. Scientific readiness gate

The canonical Phase 5.2 report remains fail-closed on the real production dataset. Current production data has 1,181 usable aligned samples against the 1,200 train+validation requirement, so the experiment remains `BLOCKED` rather than manufacturing rows or relaxing the evidence contract.

**Safety invariant:**

> No predictive intelligence without validated historical evidence.

A green software CI run is not equivalent to scientific readiness. Both must be reported separately.
