# Real XAUUSD M1 research pipeline

The real-data path is intentionally separated into deterministic stages:

1. MT5 XAUUSD M1 raw data
2. Dataset integrity and canonical identity validation
3. M1 SMA20/100 event extraction using only information available at the event timestamp
4. Explicit directional forward outcome calculation
5. Label-window / event-window leakage checks
6. Chronological walk-forward evaluation
7. Out-of-sample raw probability
8. Calibration fitted only from prior observations
9. OOS calibration metrics and baseline comparison
10. Evidence emission with dataset and contract provenance

The current M1 event engine and outcome contract do **not** claim predictive edge.
A probability may be promoted to research evidence only after the complete
real-data, leakage-free, out-of-sample pipeline succeeds.

## Frozen first contract

- Asset: XAUUSD
- Bar timeframe: M1
- Event: SMA20/100 crossover
- Outcome price: close
- Default horizon: 1 calendar day
- Threshold: non-negative directional return threshold
- Direction: bullish/long and bearish/short are explicitly distinct
- Future endpoint: first available observation at or after the target timestamp
- No synthetic/mock fallback
