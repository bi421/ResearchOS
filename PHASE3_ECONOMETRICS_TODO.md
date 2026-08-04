# Phase 3 — Econometrics Engine: Step Tracker

## Foundation
- [x] Create `macro_intelligence/econometrics/__init__.py`
- [x] Create `macro_intelligence/econometrics/models.py` (frozen result dataclasses)
- [x] Create `macro_intelligence/econometrics/matrix.py` (minimal matrix algebra: transpose, matmul, Gaussian elimination w/ pivoting, inversion)

## Regression (reuse canonical OLS; do NOT duplicate)
- [x] Create `macro_intelligence/econometrics/regression.py` — Multiple Linear, Polynomial, Logistic (Newton-Raphson, deterministic, bounded iterations, convergence report)

## Time-series / Hypothesis tests
- [x] Create `macro_intelligence/econometrics/autocorrelation.py` — ACF, PACF
- [x] Create `macro_intelligence/econometrics/stationarity.py` — ADF, KPSS
- [x] Create `macro_intelligence/econometrics/cointegration.py` — Engle-Granger
- [x] Create `macro_intelligence/econometrics/causality.py` — Granger Causality
- [x] Create `macro_intelligence/econometrics/vif.py` — Variance Inflation Factor

## Diagnostics (separate from computation)
- [x] Create `macro_intelligence/econometrics/heteroskedasticity.py` — Breusch-Pagan
- [x] Create `macro_intelligence/econometrics/diagnostics.py` — Durbin-Watson, Jarque-Bera, Residual + Model Diagnostics
- [x] Create `macro_intelligence/econometrics/intervals.py` — Confidence + Prediction intervals
- [x] Create `macro_intelligence/econometrics/information_criteria.py` — AIC, BIC

## Tier / guard integration
- [x] Add `econometrics` tier to `audit_mil.py` and `guards.py` (rank 8)
- [x] Extend CI guards: econometrics is ONLY owner of ADF, KPSS, Granger, Engle-Granger, VIF, Breusch-Pagan, Jarque-Bera, Durbin-Watson

## Tests
- [x] Create `tests/unit/test_macro_intelligence/econometrics/` — unit, integration, edge cases, determinism, serialization, immutability, numerical reference validation

## Documentation
- [x] Create `docs/ECONOMETRICS_ENGINE.md`
- [x] Create `ECONOMETRICS_ENGINE_REPORT.md`

## Verification
- [x] Run MIL test suite (green)
- [x] Run V1 test suite (green, no frozen-core changes)
- [x] Run `audit_mil.py` — clean
