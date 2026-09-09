# XAUUSD M1 OOS calibration

`run_xauusd_m1_oos_calibration.py` is a post-walk-forward calibration stage. It does not replace the raw probability estimator.

## Invariants

- The source and walk-forward result contract must be exactly `XAUUSD / M1 / hit_threshold_1d`.
- The supplied source artifact SHA-256 must match the result's declared source SHA-256.
- Every prediction must resolve to the source event with identical timestamp and realized label.
- Calibration for an OOS prediction uses only earlier OOS predictions whose `realized_end_1d` is strictly before the current prediction timestamp.
- At least 10 prior calibration observations and both outcome classes are required; otherwise the stage fails closed.
- The current validation label is never used to fit its own calibration.
- No future outcome is used.

## Scientific boundary

The output is an out-of-sample calibration artifact. It does not establish predictive edge, profitability, trading validity, or live probability validity.
