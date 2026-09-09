# M1 pipeline status

Implemented on `fix/m1-outcome-contract`:

- deterministic XAUUSD M1 SMA20/100 crossover extraction
- explicit immutable M1 outcome contract
- direction-aware forward outcome integration test
- scientific boundary: no predictive-edge claim before real OOS validation
- scientific boundary: no synthetic/mock fallback

Next gate:

REAL MT5 XAUUSD M1 2021-2025 -> integrity audit -> event extraction -> forward outcomes -> leakage audit -> walk-forward OOS -> calibration -> evidence report.
