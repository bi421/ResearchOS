# Production hardening — next steps

This document records the next correctness gates after execution-timing hardening.

## 1. Real walk-forward OOS

Issue #10. The existing `run_walk_forward()` guard must remain `NotImplemented` until a genuine chronological implementation exists. A valid implementation must keep training and test windows temporally disjoint, purge/embargo at least the maximum outcome horizon, execute signals at the following bar open, and record deterministic train/test provenance.

## 2. Dependence-aware inference

Issue #11. Bonferroni controls family-wise error for multiple hypotheses; it does not remove dependence caused by overlapping labels. Inference must either model this dependence or use an explicitly dependence-aware resampling method, with assumptions reported in evidence provenance.

## 3. Dataset identity

Issue #12. Evidence provenance must bind to the actual validated dataset content identity. `dataset_content_hash`, `dataset_hash`, and `dataset_version` must not create ambiguous or contradictory identities.

## Current safety invariant

**No predictive intelligence without validated historical evidence.**

The repository must not claim out-of-sample validation while the walk-forward engine is only a guard, and it must not certify evidence from synthetic/demo/mock/fixture data.
