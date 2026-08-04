# ResearchOS Macro Intelligence Layer — Econometrics Engine Architecture

**Version:** ecm/v1
**Status:** ARCHITECTURALLY FROZEN — Phase 3 Econometrics Engine
**Classification:** Internal — Quantitative Platform

---

## Table of Contents

1. [Architecture Role](#1-architecture-role)
2. [Dependency Boundaries](#2-dependency-boundaries)
3. [Module Layout](#3-module-layout)
4. [Result Contracts](#4-result-contracts)
5. [Algorithms](#5-algorithms)
6. [Single-Ownership Rule](#6-single-ownership-rule)
7. [Invariants](#7-invariants)
8. [Extension Rules](#8-extension-rules)
9. [Limitations](#9-limitations)

---

## 1. Architecture Role

The **Econometrics Engine** is a new tier inside the Macro Intelligence Layer
(MIL). It is a canonical, deterministic, immutable econometrics engine that
owns every advanced econometric algorithm: multiple/polynomial/logistic
regression, ACF/PACF, stationarity (ADF, KPSS), cointegration (Engle-Granger),
causality (Granger), VIF, heteroskedasticity (Breusch-Pagan), diagnostics
(Durbin-Watson, Jarque-Bera), intervals, and information criteria.

It is **not** a trading engine and **not** an execution layer. It computes
statistical and econometric quantities only, and every result is
provenance-tracked and deterministic.

### 1.1 The Econometrics Chain

```
Frozen statistical outputs (statistics layer)
        ↓
Econometric analysis (ADF, KPSS, cointegration, causality, VIF, regression)
        ↓
Diagnostics & intervals (Durbin-Watson, Jarque-Bera, CI, PI)
        ↓
Information criteria (AIC, BIC)
        ↓
Auditable econometric intelligence
```

### 1.2 What Econometrics Owns (and Does Not)

| Owns (econometric computation) | Does NOT own |
|---|---|
| Multiple / polynomial / logistic regression | Single-variable OLS (delegated to Statistics) |
| ACF / PACF | Basic descriptive statistics (mean, std, skewness) |
| ADF / KPSS stationarity | Basic z-scores |
| Engle-Granger cointegration | Distribution CDFs / erf |
| Granger causality | Provenance envelope (Statistics owns `StatisticalProvenance`) |
| VIF | |
| Breusch-Pagan | |
| Durbin-Watson / Jarque-Bera | |
| Confidence / prediction intervals | |
| AIC / BIC | |

---

## 2. Dependency Boundaries

The Econometrics Engine depends **only** on the Statistics layer (for
canonical OLS, descriptive statistics, distributions, and the provenance
envelope). It never depends on higher tiers (Relationships, Regime, Knowledge).

### 2.1 Strict Dependency Direction

```
contracts
    ↓
time
    ↓
interfaces
    ↓
...
    ↓
statistics
    ↓
econometrics            ← NEW TIER (rank 8)
    ↓
relationships
    ↓
regime
    ↓
knowledge
```

### 2.2 Consumption Contract

Econometrics consumes:
- `statistics.regression.linear_regression` / `_canonical_ols` for the 1-D
  OLS case (delegation, never duplication).
- `statistics.descriptive` (mean, std, skewness, kurtosis).
- `statistics.distributions` (t-distribution p-value, normal CDF).
- `statistics.provenance.StatisticalProvenance` (the provenance envelope).

The engine never mutates its inputs. All result models are frozen dataclasses.

---

## 3. Module Layout

```
macro_intelligence/econometrics/
├── __init__.py                 # Package exports (ecm/v1)
├── models.py                   # Frozen result dataclasses + deterministic_hash
├── matrix.py                   # Minimal matrix algebra (transpose, matmul, solve)
├── regression.py               # Multiple / polynomial / logistic regression
├── autocorrelation.py          # ACF, PACF
├── stationarity.py             # ADF, KPSS
├── cointegration.py            # Engle-Granger
├── causality.py                # Granger causality
├── vif.py                      # Variance Inflation Factor
├── heteroskedasticity.py       # Breusch-Pagan
├── diagnostics.py              # Durbin-Watson, Jarque-Bera, residual/model diagnostics
├── intervals.py                # Confidence + prediction intervals
└── information_criteria.py     # AIC, BIC
```

### 3.1 Component Responsibilities

| Module | Responsibility |
|---|---|
| `models.py` | Immutable result contracts (RegressionResult, TestResult, ResidualDiagnostics, IntervalResult, InformationCriteria, ModelDiagnostics) + deterministic SHA-256 hashing. |
| `matrix.py` | Minimal, pure-Python matrix algebra (transpose, matmul, Gaussian elimination with pivoting). |
| `regression.py` | Multiple/polynomial/logistic regression. 1-D OLS delegates to canonical Statistics OLS. |
| `autocorrelation.py` | ACF and PACF. |
| `stationarity.py` | ADF and KPSS with ridge fallback for singular designs. |
| `cointegration.py` | Engle-Granger two-step cointegration test. |
| `causality.py` | Granger causality test. |
| `vif.py` | Variance Inflation Factor. |
| `heteroskedasticity.py` | Breusch-Pagan test. |
| `diagnostics.py` | Durbin-Watson, Jarque-Bera, residual + model diagnostics (separate from fit). |
| `intervals.py` | Confidence and prediction intervals. |
| `information_criteria.py` | AIC, BIC. |

---

## 4. Result Contracts

All models are `@dataclass(frozen=True)`. Every result:

- Carries a `StatisticalProvenance` envelope (dataset_id, dataset_version,
  dataset_hash, computation_method, method_version, parameters).
- Computes a deterministic `result_hash` (SHA-256 over canonical JSON, sorted
  keys, compact separators). Runtime timestamps never enter the hash.
- Freezes mutable collections (lists → tuples, dicts → MappingProxyType).
- Implements `to_dict()` / `from_dict()` for stable round-trip serialization.

### 4.1 Contracts

| Contract | Purpose |
|---|---|
| `RegressionResult` | Coefficients, R², adjusted R², SEs, t-stats, p-values, fitted, residuals, method, version, convergence, provenance, hash. |
| `TestResult` | Generic hypothesis-test result (statistic, p-value, critical values, significance, parameters, provenance, hash). |
| `ResidualDiagnostics` | Mean, std, skewness, kurtosis, JB, DW, BP, p-values, provenance, hash. |
| `IntervalResult` | Confidence or prediction interval (level, lower, upper, kind, provenance, hash). |
| `InformationCriteria` | AIC, BIC, log-likelihood, n_observations, n_parameters, provenance, hash. |
| `ModelDiagnostics` | Aggregate of regression + residual diagnostics + information criteria. |

---

## 5. Algorithms

All algorithms are deterministic, stateless, pure-Python.

### 5.1 Regression

- **Multiple regression** — closed-form OLS via normal equations
  (`X'X` then solve). Owns multiple/polynomial/logistic.
- **Polynomial regression** — builds a Vandermonde-style matrix and uses
  multiple-regression OLS.
- **Logistic regression** — Newton-Raphson, deterministic, bounded iterations,
  convergence report.
- **Univariate OLS** — delegates to `statistics.regression` canonical OLS
  (MIL-ECM-005: never duplicates 1-D OLS).

### 5.2 Time-series / Hypothesis tests

- **ACF / PACF** — autocorrelation and partial autocorrelation functions.
- **ADF** — Augmented Dickey-Fuller with ridge fallback for singular/near-
  singular design matrices (pure linear trend no longer raises).
- **KPSS** — Kwiatkowski-Phillips-Schmidt-Shin stationarity test.
- **Engle-Granger** — two-step cointegration test with length alignment.
- **Granger** — Granger causality F-test.
- **VIF** — Variance Inflation Factor for multicollinearity.

### 5.3 Diagnostics

- **Durbin-Watson** — autocorrelation of residuals. DW near 2 = no
  autocorrelation.
- **Jarque-Bera** — normality of residuals.
- **Breusch-Pagan** — heteroskedasticity.
- **residual_diagnostics / model_diagnostics** — aggregate diagnostics,
  computed from residuals **after** fitting (never inside a regression class).

### 5.4 Intervals & Information criteria

- **Confidence interval** — `estimate ± t_crit * standard_error`.
- **Prediction interval** — `prediction ± t_crit * s * sqrt(1 + 1/n)`.
- **AIC / BIC** — information criteria for model comparison.

---

## 6. Single-Ownership Rule

The Econometrics Engine is the **single canonical owner** of the econometric
algorithms listed above. No other MIL tier may re-implement them. The
Relationships, Regime, and Knowledge layers must consume econometric outputs
— never re-implement ADF, KPSS, Granger, Engle-Granger, VIF, Breusch-Pagan,
Jarque-Bera, or Durbin-Watson.

Conversely, the Econometrics Engine must **not** duplicate the Statistics
layer's canonical single-variable OLS (MIL-ECM-005). It delegates that case.

This is enforced by the `check_econometric_single_owner` architecture guard.

---

## 7. Invariants

| ID | Invariant |
|---|---|
| MIL-ECM-001 | Every econometric result is immutable and deterministic. |
| MIL-ECM-002 | Provenance attaches via `StatisticalProvenance`. |
| MIL-ECM-004 | Econometrics owns multiple/polynomial/logistic regression. |
| MIL-ECM-005 | Econometrics never duplicates single-variable OLS. |
| MIL-ECM-011 | Econometrics owns Breusch-Pagan. |
| MIL-ECM-012 | Econometrics owns diagnostics; diagnostics are separated from fit. |
| MIL-ECM-013 | Econometrics owns confidence/prediction intervals. |

Additional derived invariants:
- Runtime timestamps never affect the deterministic hash (MIL-DET-001).
- No `random`, `uuid`, wall-clock, or unseeded RNG in any hash.
- No dependency on ResearchOS V1 core, Quant Engine, or Experiment framework.
- No external ML libraries (numpy/pandas/torch/tensorflow/sklearn).
- Result models are frozen dataclasses with `to_dict()`/`from_dict()`.

---

## 8. Extension Rules

1. **Never modify existing algorithms.** Future changes create a new version
   (e.g., `ecm/adf/v2`) rather than mutating old results.
2. **Never recompute statistics in higher tiers.** Relationships, Regime, and
   Knowledge consume econometric outputs only.
3. **Add new econometric tests as new modules** in `econometrics/`, each
   owning its algorithm and carrying a versioned invariant.
4. **Keep all new models frozen dataclasses** with deterministic hashing.
5. **Keep provenance mandatory** for every new econometric result.
6. **Delegate single-variable OLS** to the canonical Statistics owner.

---

## 9. Limitations

- **Pure-Python only:** no external ML / numerical libraries. This keeps the
  engine deterministic and dependency-free but may be slower than vectorized
  implementations for large matrices.
- **Approximate p-values:** p-values use t-distribution approximations; they
  are for research screening, not exact inference.
- **Not predictive:** econometrics characterizes structure (stationarity,
  cointegration, causality, diagnostics); it does not forecast prices.
- **Not a trading signal:** outputs are descriptive statistical artifacts.
- **No persistence/scheduling/API:** this phase deliberately adds no storage,
  scheduler, UI, API, database, or real-time wiring.

---

*Document Version: ecm/v1*
*Last Updated: 2026-08-03*
*Classification: Internal — Quantitative Platform Architecture*
