# ResearchOS XAUUSD M1 Research Baseline Freeze

**Baseline date:** 2026-09-10  
**Baseline commit:** `0978ead574b1f7053abb31a0eafcf67970b681fe`  
**Repository:** `bi421/ResearchOS`  
**Protected branch:** `main`  
**CI:** GitHub Actions run `#430` (`34387912986`) — **GREEN**

## 1. Freeze decision

This document freezes the current XAUUSD M1 research foundation as the reference baseline. Future work must not silently alter the frozen scientific surfaces.

A post-freeze change is allowed only when it is a demonstrated defect or an explicitly approved extension, and must follow:

`detect → classify → prove → isolated fix → regression test → CI → merge → re-baseline`

## 2. Frozen scientific contract

- Instrument: `XAUUSD`
- Timeframe: `M1`
- Primary outcome contract: `hit_threshold_1d`
- Research scope: historical/research only
- No broker execution
- No autonomous trading
- No predictive-edge, profitability, or live-probability claim without separate validation
- Deterministic execution and provenance are required

## 3. Frozen pipeline stages

`DATA → VALIDATION → STRUCTURED DATA → MARKET MEMORY → QUANTITATIVE ANALYSIS → MARKET CONTEXT → RESEARCH → EXPERIMENT → EVALUATION → EVIDENCE → INTELLIGENCE → FUTURE LEARNING → PROBABILITY`

The currently validated M1 research path includes:

1. deterministic event/outcome extraction;
2. direction-aware forward outcome semantics;
3. leakage-safe chronological walk-forward probability;
4. independent source-to-result audit;
5. evidence envelope/provenance binding;
6. label-shuffle structural negative control;
7. future-leakage negative control;
8. OOS isotonic calibration with independent audit.

## 4. Frozen audit invariants

- Source artifacts are SHA-256 bound.
- Result artifacts are SHA-256 bound.
- Source/result contract identity must match.
- Event IDs are unique where required.
- Training observations precede validation in time.
- Forward outcomes cannot be used before their realization time.
- Validation windows cannot overlap/reuse OOS events.
- Calibration uses only earlier eligible OOS observations.
- Calibration requires minimum prior observations and both outcome classes.
- Tampered result/source bindings fail closed.
- Negative controls are expected to detect deliberate violations.

## 5. Current CI verification

Run `#430` on baseline commit `0978ead574b1f7053abb31a0eafcf67970b681fe` completed successfully for:

- Python Tests (3.10)
- Python Tests (3.11)
- Python Tests (3.14)
- Quant Engine (C++ / nanobind)
- Coverage

No CI artifact is treated as scientific evidence merely because CI is green. CI establishes software/regression status only.

## 6. Dataset identity boundary

The real XAUUSD M1 MT5 dataset is maintained as a local research input rather than a Git-tracked artifact. The latest local audit reported **1,764,176 rows** with columns:

`time, open, high, low, close, tick_volume, spread, real_volume`

The exact raw CSV SHA-256 must be recorded from the local dataset/audit manifest before a dataset-specific evidence result is promoted. It is intentionally **not guessed or fabricated in this baseline document**.

## 7. Scientific limitations

This baseline proves research-pipeline integrity and auditability, not market predictability. In particular:

- OOS raw probability is not evidence of trading edge.
- OOS calibration is not evidence of profitability.
- Negative controls validate failure detection, not economic validity.
- A green CI run does not validate the market hypothesis.
- Any future probability/edge claim requires a separate, outcome-grounded validation protocol.

## 8. Protected surfaces

Unless a demonstrated defect is found, the following are frozen:

- walk-forward arithmetic and temporal rules;
- outcome-direction semantics;
- source-to-result audit logic;
- evidence-envelope identity/hash scheme;
- negative-control semantics;
- calibration training-membership rules;
- C++ numerical implementation and backend certification;
- broker/execution boundary.

## 9. Re-baselining rule

Any legitimate scientific or integrity correction after this freeze must create a new isolated change, add or update a regression/negative-control test as appropriate, pass the full CI matrix, and produce a new baseline document/identifier. The old baseline remains historically immutable.
