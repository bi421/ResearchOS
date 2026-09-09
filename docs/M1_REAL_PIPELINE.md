# XAUUSD M1 Real-Data Pipeline

This is the first narrow real-data Market Memory study surface.

## Frozen contract

- Instrument: XAUUSD
- Source: audited MT5 XAUUSD M1 data
- Event: SMA20/SMA100 crossover
- Event features: only information available at the event timestamp
- Outcome: direction-aware forward close return
- Default label: `hit_threshold_1d`
- Horizon: one calendar day, resolved to the first actual observation at or after the target timestamp
- Calibration: outcome-grounded and fitted only on prior observations
- Validation: chronological walk-forward / strict OOS

## Promotion gates

1. Raw dataset identity and integrity pass.
2. Event extraction is deterministic and leakage-safe.
3. Forward outcome endpoints are recorded explicitly.
4. Event and label windows do not leak across evaluation boundaries.
5. Predictions are generated strictly OOS.
6. Calibration uses only observations available before each OOS prediction.
7. Results are compared with an unconditional baseline.
8. Evidence is bound to dataset identity, event definition, outcome contract, and code version.

No synthetic/mock fallback is allowed. Passing the implementation tests does not establish predictive edge, trading profitability, or live validity.
