# Research Evidence Pipeline

## Production sequence

`REAL XAUUSD DATA -> VALIDATION -> WFO/OOS -> PURGE/EMBARGO -> DEPENDENCE-AWARE INFERENCE -> DATASET PROVENANCE -> E2E CERTIFICATION`

This pipeline is evidence-first. A predictive claim cannot become certified evidence unless the source is real, the dataset identity is bound to validated content, labels are temporally valid, OOS folds are causal, overlap/dependence is explicitly handled, and the final artifact preserves the complete provenance chain.

## Gates

1. **Real XAUUSD evidence**: source must be classified as real production data; synthetic/demo/mock/fixture sources are rejected for certification.
2. **WFO/OOS correctness**: train/context observations precede each OOS observation; OOS intervals are disjoint; signals execute at the following bar open; no full-sample fallback.
3. **Purge/embargo**: remove observations whose realized label window can cross the train/OOS boundary; purge is at least the maximum label horizon and must be derived from realized label boundaries where available.
4. **Dependence-aware statistics**: overlapping labels are measured and reported. Bonferroni controls family-wise error but does not remove serial/label dependence. Inferential claims require a dependence-aware method; otherwise results remain descriptive.
5. **Dataset provenance**: dataset content hash, dataset identity, record count, symbol/timeframe, validation result, methodology version, execution hash, and evidence digest must agree.
6. **Production E2E certification**: certification is written only after every gate passes. Rejection must occur before evidence artifacts or lineage edges are persisted.

## Current scope

The existing ResearchOS walk-forward API performs fixed-signal chronological OOS evaluation because `SignalFn` has no train-only fit callback. This is valid for causal evaluation of a fixed rule, but it is not parameter-fitting WFO. Model-fitting WFO must introduce an explicit train-only API boundary before being claimed as such.

## XAUUSD target

The primary production evidence target is the validated MT5 XAUUSD dataset covering 2021-2025. The evidence runner must consume the validated dataset boundary rather than bypassing it with an arbitrary raw dataframe.
